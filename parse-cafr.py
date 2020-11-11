#!/usr/bin/env python3.7
import argparse
from collections import defaultdict
import copy
import itertools
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import cv2 as cv
import numpy as np

ALTO_STRING = "{http://www.loc.gov/standards/alto/ns-v3#}String"
ALTO_SPACE = "{http://www.loc.gov/standards/alto/ns-v3#}SP"


def middle(a, b):
    return (a + b) / 2.0


def join_words(words):
    ret = words[0]
    for w in words[1:]:
        if ret[-1] == "-":
            ret = ret + w
        else:
            ret = ret + " " + w
    return ret


def parse_alto_xml(alto_bytes, png_bytes):
    parser = ET.XMLParser()
    parser.feed(alto_bytes.decode("utf-8"))
    root = parser.close()
    lines = (
        root.find("{http://www.loc.gov/standards/alto/ns-v3#}Layout")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}Page")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}PrintSpace")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}ComposedBlock")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}TextBlock")
    )

    # Find the columns.
    header_end = None
    header_end_ypos = None
    column_bounds = []
    for i, l in enumerate(lines):
        for w in l.findall(ALTO_STRING):
            # "%" seems to be a pretty common mispelling of "$"
            m = re.search("\$", w.attrib["CONTENT"])
            if m is None:
                continue
            found = False
            xpos = int(w.attrib["HPOS"])
            if header_end is None:
                header_end = i
            if header_end_ypos is None:
                header_end_ypos = int(l.attrib["VPOS"])
            for b in column_bounds[::-1]:
                if abs(xpos - b) < 100:
                    found = True
                    break
            if not found:
                column_bounds.append(xpos)
                column_bounds = sorted(column_bounds)

    col_width = 0.0
    prev_col = column_bounds[0]
    for c in column_bounds[1:]:
        col_width += c - prev_col
        prev_col = c
    col_width /= len(column_bounds)

    # Pick some far off point to catch all cells in the last column.
    column_bounds.append(column_bounds[-1] + col_width)

    # Find dividing lines between differnet levels of headers
    header_dividers = set({})
    img = cv.imdecode(np.frombuffer(png_bytes, np.uint8), cv.IMREAD_GRAYSCALE)
    edges = cv.Canny(img, 50, 150, apertureSize=3)
    img_lines = cv.HoughLinesP(edges, 1, np.pi / 180, 1000, col_width, 0)
    for line in img_lines:
        x1, y1, x2, y2 = line[0]
        if y1 < header_end_ypos:
            header_dividers.add(y1)
            continue
        if y2 < header_end_ypos:
            header_dividers.add(y2)
            continue
    header_dividers = sorted(list(header_dividers), reverse=True)
    print(header_dividers)

    # Try to detect column headers.
    a, b = itertools.tee(range(len(column_bounds)))
    next(b, None)
    col_pairs = list(zip(a, b))
    column_headers = defaultdict(list)
    below_first = True
    for i, l in enumerate(lines[:header_end][::-1]):
        ypos = int(l.attrib["VPOS"])
        if below_first and ypos > header_dividers[0]:
            continue
        if below_first:
            while header_dividers[0] > ypos:
                header_dividers = header_dividers[1:]
            below_first = False
        if ypos < header_dividers[0]:
            continue

        acc = []
        range_start = column_bounds[col_pairs[0][0]]
        range_end = range_start
        for c in l.findall(ALTO_STRING):
            xstart, width = int(c.attrib["HPOS"]), int(c.attrib["WIDTH"])
            xend = xstart + width

            col = col_pairs[-1][0]
            for j, k in col_pairs:
                x1, x2 = column_bounds[j], column_bounds[k]
                if xstart > x1 and xend < x2:
                    col = j
                    break
            column_headers[col].append(c.attrib["CONTENT"])

    column_headers = {k: join_words(v[::-1]) for k, v in column_headers.items()}
    column_headers = [column_headers.get(i, "") for i in range(len(column_bounds) - 1)]

    # Match rows and cells up to columns.
    rows = []
    for l in lines[header_end:]:
        words = l.findall(ALTO_STRING)

        label_start = None
        for i, word in enumerate(words[::-1]):
            m = re.match("[a-zA-Z]", word.attrib["CONTENT"])
            if m is not None:
                label_start = len(words) - i
                break

        if label_start is None:
            continue

        label = " ".join([w.attrib["CONTENT"] for w in words[:label_start]])

        cols = defaultdict(list)
        for word in words[label_start:]:
            xpos, width = int(word.attrib["HPOS"]), int(word.attrib["WIDTH"])
            col = col_pairs[-1][0]
            for j, k in col_pairs:
                x1, x2 = column_bounds[j], column_bounds[k]
                mid = middle(xpos, xpos + width)
                if x1 < mid and mid < x2:
                    col = j
                    break
            cols[col].append(word.attrib["CONTENT"])

        rows.append((label, dict(cols)))

    # Arrange the rows in an easier to digest format.
    output = []
    for label, row in rows:
        entry = {
            "label": label,
            "column_data": {},
        }

        for k, parts in row.items():
            val = "".join(parts)
            val = re.sub(r"[^0-9\(\)\{\}]", "", val)
            if val in ("", "-"):
                continue

            m = re.search(r"[\(\{]?([0-9]+)[\)\}]?", val)
            if m is not None:
                negm = re.search(r"[\(\{]([0-9]+)[\)\}]", val)
                val = float(m.groups()[0])
                if negm is not None:
                    val *= -1
                entry["column_data"][k] = val
        output.append(entry)

    return column_headers, output


def parse_pdf(
    pdf_path,
    pages,
    rotate=None,
    vertical_concat=False,
):
    cmd = [
        "convert",
        "-density",
        "1200",
        "-antialias",
        f"pdf:{pdf_path}[{pages}]",
        "-quality",
        "100",
    ]

    if rotate is not None:
        cmd.extend(["-rotate", str(rotate)])

    if vertical_concat:
        cmd.append("-append")
    else:
        cmd.append("+append")

    cmd.append("png:-")

    png_proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    png_out, _ = png_proc.communicate()

    cmd = [
        "tesseract",
        "-",
        "-",
        "--dpi",
        "1200",
        "--psm",
        "6",
        "alto",
    ]
    alto_proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    alto_out, _ = alto_proc.communicate(input=png_out)

    return parse_alto_xml(alto_out, png_out)


def main():
    parser = argparse.ArgumentParser(
        description="Convert batches of PDF-formatted CAFRs into text"
    )
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file to convert")
    parser.add_argument(
        "pages",
        type=str,
        help="Pages to convert (zero-indexed). Accepts list: <int>[,<int>...] or range <int>[-<int>]",
    )
    parser.add_argument(
        "-v",
        "--vertical-concat",
        action="store_true",
        help="By default, pages are concatenated horizontally. "
        "If this flag is set, they will be concatenated vertically",
    )
    parser.add_argument(
        "-r",
        "--rotate",
        type=int,
        help="Number of degrees to rotate clockwise before extracting text from pages."
        "Negative value will rotate counter-clockwise.",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="csv",
        help="Output format. Currently support json and csv. (Default: csv)",
    )
    args = parser.parse_args()

    headers, rows = parse_pdf(
        args.pdf_path, args.pages, args.rotate, args.vertical_concat
    )

    if args.format == "json":
        for row in rows:
            row["column_data"] = {headers[k]: v for k, v in row["column_data"].items()}
        print(json.dumps(rows, indent=4))
    elif args.format == "csv":
        print(",".join(["label"] + headers))
        for row in rows:
            parts = [row["label"].replace(",", "")]
            for i in range(len(headers)):
                parts.append(str(row["column_data"].get(i, "-")))
            print(",".join(parts))


if __name__ == "__main__":
    main()
