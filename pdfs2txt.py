#!/usr/bin/env python3.7
import argparse
from collections import defaultdict
from concurrent import futures
import json
import os
import subprocess


def convert_to_png(
    pdf_path=None,
    png_path=None,
    year=None,
    city=None,
    state=None,
    report=None,
    pageno=None,
    rotate=None,
    png_dir=None,
    txt_dir=None,
):
    print(f"PDF->PNG {pdf_path}[{pageno}] {png_path}")
    cmd = [
        "convert",
        "-density",
        "1200",
        "-antialias",
        f"{pdf_path}[{pageno-1}]",
        "-quality",
        "100",
    ]
    if rotate is not None:
        cmd.extend(["-rotate", str(rotate)])
    cmd.append(png_path)
    subprocess.check_call(cmd)

    return (png_path, f"{txt_dir}/{year}-{city}-{state}-{report}.txt")


def convert_to_txt(png_paths, txt_path):
    with open(txt_path, "wb") as f:
        for png_path in png_paths:
            print(f"PNG->TXT {png_path} {txt_path}")
            cmd = [
                "tesseract",
                png_path,
                "-",
                "--dpi",
                "1200",
                "--psm",
                "6",
            ]
            subprocess.check_call(
                cmd,
                stdin=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdout=f,
            )


def main():
    parser = argparse.ArgumentParser(
        description="Convert batches of PDF-formatted CAFRs into text"
    )
    parser.add_argument("config_path", type=str, help="Path to the config file to use")
    parser.add_argument(
        "-p",
        "--png-out-dir",
        default="png",
        type=str,
        help="Directory to dump PNGs of extracted pages into",
    )
    parser.add_argument(
        "-t",
        "--txt-out-dir",
        default="txt",
        type=str,
        help="Directory to dump extraced text into",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite outputs if they already exist",
    )
    parser.add_argument(
        "-n",
        "--num-workers",
        default=1,
        type=int,
        help="Number of conversions to perform in parallel",
    )
    args = parser.parse_args()

    pdfconv_args = []
    txt_inputs = defaultdict(list)

    # Load the config file and queue up an reports we might need to extract.
    with open(args.config_path, "r") as f:
        config = json.load(f)

        for cafr in config["cafrs"]:
            reports = defaultdict(list)
            for p in cafr["pages"]:
                reports[p["report"]].append(
                    (
                        p["pageno"],
                        p.get("rotate", None),
                    )
                )

            for k in reports:
                reports[k] = sorted(reports[k], key=lambda x: x[0])

            for report, pages in reports.items():
                print(
                    f"Found {report} on page(s) {','.join([str(p[0]) for p in pages])} for {cafr['city']}, {cafr['state']} in {cafr['year']}"
                )
                for p in pages:
                    pdfconv_args.append(
                        {
                            "pdf_path": cafr["path"],
                            "year": cafr["year"],
                            "city": cafr["city"],
                            "state": cafr["state"],
                            "report": report,
                            "pageno": p[0],
                            "rotate": p[1],
                        }
                    )

    # Stage 1: Convert report pages from PDFs into PNGs
    with futures.ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        jobs = []
        for kwargs in pdfconv_args:
            png_path = f"{args.png_out_dir}/{kwargs['year']}-{kwargs['city']}-{kwargs['state']}-{kwargs['report']}-{kwargs['pageno']}.png"
            if os.path.exists(png_path) and not args.overwrite:
                print(f"SKIP {png_path} already exists")
                continue
            jobs.append(
                executor.submit(
                    convert_to_png,
                    png_path=png_path,
                    png_dir=args.png_out_dir,
                    txt_dir=args.txt_out_dir,
                    **kwargs,
                )
            )

        for j in futures.as_completed(jobs):
            png, txt = j.result()
            txt_inputs[txt].append(png)

    # Stage 2: Extract tables from the PNGs
    # TODO(melvin): Might have a lot of unnecessary idle time with this barrier
    # between pdf->png and png->txt when dealing with many multi-page reports.
    # If we do some fancy dependency tracking here and dispatch png->txt as soon
    # as needed pngs are ready, we could avoid that.
    for k in txt_inputs:
        txt_inputs[k] = sorted(txt_inputs[k])

    with futures.ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        jobs = []
        for txt, pngs in txt_inputs.items():
            if os.path.exists(txt) and not args.overwrite:
                print(f"SKIP {txt} already exists")
                continue
            jobs.append(
                executor.submit(
                    convert_to_txt,
                    pngs,
                    txt,
                )
            )
        for j in futures.as_completed(jobs):
            j.result()


if __name__ == "__main__":
    main()
