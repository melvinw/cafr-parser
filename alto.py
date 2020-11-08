#!/usr/bin/env python3.7
from collections import defaultdict
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from pprint import pprint


ALTO_STRING = "{http://www.loc.gov/standards/alto/ns-v3#}String"
ALTO_SPACE = "{http://www.loc.gov/standards/alto/ns-v3#}SP"


def middle(x, w):
    return (2 * x + w) / 2


def main():
    tree = ET.parse(sys.argv[1])
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
        m = re.match("(?i)(primary\s+government|component\s+unit)", content)
        if m is not None:
            header_start = i + 1
            continue

        m = re.match("(?i)^assets$", content)
        if m is not None:
            header_end = i
            break

    boundaries = []
    last_header = lines[header_end - 1]
    for c in last_header.findall(ALTO_SPACE):
        xpos, width = int(c.attrib["HPOS"]), int(c.attrib["WIDTH"])
        if width > 75:
            boundaries.append((xpos, width))
    last_col = middle(*boundaries[-1]) + 1

    buckets = defaultdict(list)
    for l in lines[header_start:header_end]:
        for word in l.findall(ALTO_STRING):
            xpos, width = int(word.attrib["HPOS"]), int(word.attrib["WIDTH"])
            bound = last_col
            for b in boundaries:
                if xpos < middle(*b):
                    bound = middle(*b)
                    break
            buckets[bound].append(word.attrib["CONTENT"])

    columns = sorted(
        [(cmid, " ".join(word_stack)) for cmid, word_stack in buckets.items()],
        key=lambda x: x[0],
    )

    rows = []
    for l in lines[header_end:]:
        cols = defaultdict(list)
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

        for word in words[label_start:]:
            xpos, width = int(word.attrib["HPOS"]), int(word.attrib["WIDTH"])
            col = columns[-1][1]
            for cmid, name in columns:
                if middle(xpos, width) < cmid:
                    col = name
                    break
            cols[col].append(word.attrib["CONTENT"])

        rows.append((int(words[0].attrib["HPOS"]), label, dict(cols)))

    output = []
    category_stack = []
    for xpos, lbl, row in rows:
        if len(row) == 0:
            if len(category_stack) > 1:
                category_stack.pop()
            category_stack.append((xpos, lbl))
            continue

        if len(category_stack) > 0 and xpos - category_stack[-1][0] < -10:
            category_stack.pop()

        entry = {
            "label": lbl,
            "categories": [clbl for _, clbl in category_stack],
            "data": {},
        }

        for k, parts in row.items():
            val = "".join(parts)
            val = re.sub(r"[^0-9()\{\}]", "", val)
            if val in ("", "-"):
                continue

            m = re.search(r"[\({]?([0-9]+)[\)}]?", val)
            entry["data"][k] = float(m.groups()[0])
        output.append(entry)

    print(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()
