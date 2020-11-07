#!/usr/bin/env python3.7
import argparse
from collections import defaultdict
import enum
import json
import os
import re
import readline
import sys


def rlinput(prompt, init=""):
    editor = os.getenv("EDITOR", "vi")
    readline.parse_and_bind(f"set editing-mode {editor}")
    readline.set_startup_hook(lambda: readline.insert_text(init))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def extract_sections(lines, valid_row, sec_patterns):
    """
    Returns a a map of section headings to a list of raw lines of text.
    """

    curr_sec = None
    sec_lines = defaultdict(list)
    for l in lines:
        for pat, sec in sec_patterns.items():
            if re.match(pat, l) is not None:
                curr_sec = sec
                break

        if valid_row.match(l) is None:
            continue

        if curr_sec is not None:
            sec_lines[curr_sec].append(l)

    return sec_lines


def split_rows(sections, currency_match, label_match):
    """
    Returns a map of sections to a list of lists of the form:

        (<row_label>, [<currency>,...])
    """

    ret = defaultdict(list)
    for sec, lines in sections.items():
        for l in lines:
            cols = []
            words = re.split(f"\s+", l)[::-1]

            label_words = None
            for i, w in enumerate(words):
                cmatch = re.match(currency_match, w)
                lmatch = re.match(label_match, w)

                if cmatch is None and lmatch is None:
                    continue
                elif cmatch is not None and lmatch is None:
                    cols.append(w)
                elif lmatch is not None:
                    if label_words is None:
                        label_words = len(words[i:])
                    cols.extend(words[i:])
                    break

            cols.reverse()
            ret[sec].append([" ".join(cols[:label_words])] + cols[label_words:])

    return ret


def normalize(sections, currency_pattern, negative_currency_pattern):
    """
    Returns a a map of section headings to a list of rows with all cells
    converted to floats.
    """

    def normalize_cell(cell):
        cmatch = re.match(currency_pattern, cell)
        nmatch = re.search(negative_currency_pattern, cell)
        if cell == "-":
            return 0

        if nmatch is not None:
            norm = re.sub(r"[^0-9\.]", "", nmatch.groups()[0])
            return float(norm) * -1
        elif cmatch is not None:
            norm = re.sub(r"[^0-9\.]", "", cell)
            return float(norm)

        return cell

    ret = defaultdict(list)
    for sec, rows in sections.items():
        for i, row in enumerate(rows):
            new_row = row[:1]
            for j, cell in enumerate(row[1:]):
                try:
                    new_row.append(normalize_cell(cell))
                except Exception as e:
                    meta = f"({sec} row {i + 1}/{len(rows)})"
                    msgs = [
                        f"{meta} Failed to convert column {j} to float.",
                        " " * (len(meta) + 1) + "Fix or type SKIP and press enter.",
                    ]
                    div = "=" * max(map(len, msgs))
                    print(div)
                    for msg in msgs:
                        print(msg)
                    print(div)
                    print()
                    correction = rlinput("> ", str(cell))
                    if correction != "SKIP":
                        new_row.append(normalize_cell(correction))
            ret[sec].append(new_row)

    return ret


def sanitize(sections, lo, hi):
    """
    Step through every row in the given sections and prompt for corrections of
    rows with cells outside of the interval (lo, hi).

    Returns a a map of section headings to a list of sanitized rows.
    """
    ret = defaultdict(list)
    for sec, rows in sections.items():
        violations = defaultdict(list)
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                if not isinstance(cell, float):
                    continue
                if abs(cell) < lo or abs(cell) > hi:
                    violations[i].append(j)

        for i, row in enumerate(rows):
            if i not in violations or len(violations[i]) == 0:
                ret[sec].append(row)
                continue

            if len(violations[i]) == 1:
                weirdos = f"in column {violations[i][0]}"
            else:
                weirdos = [str(v + 1) for v in violations[i]]
                weirdos = f"in columns {', '.join(weirdos[:-1])}, and {weirdos[-1]}"

            meta = f"({sec} row {i + 1}/{len(rows)})"
            msg = f"{meta} Found entries beyond value threshold {weirdos}."
            div = "=" * len(msg)
            print(div)
            print(msg)
            print(" " * (len(meta) + 1) + "Fix or type SKIP and press enter..")
            print(div)
            correction = rlinput("> ", str(row))
            if correction != "SKIP":
                ret[sec].append(eval(correction))
            print()

    return ret


def parse_txt(config, txt_path):
    lines = []
    with open(txt_path, "r") as f:
        lines.extend(f.read().split("\n"))

    sections = extract_sections(
        lines, config["valid_row_pattern"], config["section_patterns"]
    )
    sections = split_rows(sections, config["currency_pattern"], config["label_pattern"])
    sections = normalize(
        sections,
        config["currency_pattern"],
        config["negative_currency_pattern"],
    )
    sections = sanitize(
        sections,
        config["value_threshold"][0],
        config["value_threshold"][1],
    )

    ret = []
    for sec in config["sections"]:
        for row in sections[sec]:
            ret.append([sec] + row)

    return ret


def main():
    parser = argparse.ArgumentParser(description="XXX")
    parser.add_argument(
        "config_path",
        type=str,
        help="Path to the config file to use",
    )
    parser.add_argument("input_path", type=str, help="Path to the file to parse")
    parser.add_argument("-o", "--output", type=str, help="Path to write output to")
    parser.add_argument(
        "-s",
        "--separator",
        type=str,
        default=",",
        help="String to use as a seperator between fields",
    )
    args = parser.parse_args()

    # Load the config
    config = {}
    with open(args.config_path, "r") as f:
        config = json.load(f)

    # Set some defaults
    config["currency_pattern"] = re.compile(
        config.get("currency_pattern", r"\(?([0-9,\.]|\-)+\)?")
    )
    config["negative_currency_pattern"] = re.compile(
        config.get("negative_currency_pattern", r"\(([0-9,\.]+)\)?")
    )
    config["label_pattern"] = re.compile(config.get("label_pattern", r"[a-zA-Z_]+"))
    config["valid_row_pattern"] = re.compile(
        config.get("valid_row_pattern", r".{,1} ?\D+(\d|-).*")
    )
    config["value_threshold"] = tuple(
        config.get("value_threshold", (1000.0, 1000000000.0))
    )

    # Parse the inputs
    out_lines = parse_txt(config, args.input_path)

    # Write everything out.
    outf = sys.stdout
    if args.output is not None:
        outf = open(args.output, "w")

    output = "\n".join([args.separator.join(map(str, l)) for l in out_lines])
    output += "\n"
    outf.write(output)

    if args.output is not None:
        outf.close()


if __name__ == "__main__":
    main()
