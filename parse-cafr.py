#!/usr/bin/env python3.7
import argparse
from collections import defaultdict
import copy
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


ALTO_STRING = "{http://www.loc.gov/standards/alto/ns-v3#}String"
ALTO_SPACE = "{http://www.loc.gov/standards/alto/ns-v3#}SP"


def middle(x, w):
    return (2 * x + w) / 2


def parse_alto_xml(f):
    tree = ET.parse(f)
    root = tree.getroot()
    lines = (
        root.find("{http://www.loc.gov/standards/alto/ns-v3#}Layout")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}Page")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}PrintSpace")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}ComposedBlock")
        .find("{http://www.loc.gov/standards/alto/ns-v3#}TextBlock")
    )

    header_start = None
    header_end = None
    for i, l in enumerate(lines):
        words = l.findall(ALTO_STRING)

        content = " ".join([w.attrib["CONTENT"] for w in words])
        m = re.search("[a-zA-Z]+\s+\d{1,2},\s+\d{4}", content)
        if m is not None:
            header_start = i + 1
            continue

        m = re.search("\$", content)
        if m is not None:
            header_end = i
            break

    # Find the columns
    column_bounds = []
    for i, l in enumerate(lines):
        for w in l.findall(ALTO_STRING):
            m = re.search("\$|\%", w.attrib["CONTENT"])
            if m is None:
                continue
            found = False
            xpos = int(w.attrib["HPOS"])
            for b in column_bounds[::-1]:
                if abs(xpos - b) < 100:
                    found = True
                    break
            if not found:
                column_bounds.append(xpos)

    # Pick some far off point to catch all cells in the last column
    column_bounds.append(column_bounds[-1] * 2)

    # TODO: add column header detection
    # header_words = defaultdict(list)
    # prev_col = column_bounds[0]
    # for b in column_bounds[1:]:
    #    for l in lines[header_start:header_end]:
    #        for word in l.findall(ALTO_STRING):
    #            xpos, width = int(word.attrib["HPOS"]), int(word.attrib["WIDTH"])
    #            if xpos < prev_col:
    #                continue
    #            if middle(xpos, width) < b:
    #                header_words[prev_col].append(word.attrib["CONTENT"])
    #    prev_col = b

    # columns = sorted(
    #    [(cmid, " ".join(word_stack)) for cmid, word_stack in header_words.items()],
    #    key=lambda x: x[0],
    # )

    rows = []
    for l in lines:
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
            for i, b in enumerate(column_bounds):
                if middle(xpos, width) < b:
                    cols[i].append(word.attrib["CONTENT"])
                    break

        rows.append((label, dict(cols)))

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

    return len(column_bounds) - 1, output


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
        stdin=png_proc.stdout,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    assert png_proc.wait() == 0, png_proc.stderr.read().decode("uft-8")
    assert alto_proc.wait() == 0, alto_proc.stderr.read().decode("uft-8")

    return parse_alto_xml(alto_proc.stdout)


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

    num_columns, rows = parse_pdf(
        args.pdf_path, args.pages, args.rotate, args.vertical_concat
    )

    if args.format == "json":
        print(json.dumps(rows, indent=4))
    elif args.format == "csv":
        for row in rows:
            parts = [row["label"].replace(",", "")]
            for i in range(num_columns):
                parts.append(str(row["column_data"].get(i, "-")))
            print(",".join(parts))


if __name__ == "__main__":
    main()
