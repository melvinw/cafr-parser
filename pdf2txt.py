#!/usr/bin/env python3.7
import argparse
from collections import defaultdict
from concurrent import futures
import json
import os
import subprocess


def pdf_to_txt(
    pdf_path=None,
    year=None,
    city=None,
    state=None,
    report=None,
    pageno=None,
    rotate=None,
    txt_dir=None,
    overwrite=False,
):
    txt_path = f"{txt_dir}/{year}-{city}-{state}-{report}-{pageno}.txt"

    if os.path.exists(txt_path) and not overwrite:
        print(f"SKIP {txt_path} already exists")
        return

    print(f"{pdf_path}[{pageno}] -> {txt_path}")
    cmd = [
        "convert",
        "-density",
        "1200",
        "-antialias",
        f"pdf:{pdf_path}[{pageno-1}]",
        "-quality",
        "100",
    ]
    if rotate is not None:
        cmd.extend(["-rotate", str(rotate)])
    cmd.append("png:-")
    png_proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
    )

    with open(txt_path, "wb") as f:
        cmd = [
            "tesseract",
            "-",
            "-",
            "--dpi",
            "1200",
            "--psm",
            "6",
        ]
        txt_proc = subprocess.check_call(
            cmd,
            stdin=png_proc.stdout,
            stderr=subprocess.DEVNULL,
            stdout=f,
        )

    assert png_proc.wait() == 0


def main():
    parser = argparse.ArgumentParser(
        description="Convert batches of PDF-formatted CAFRs into text"
    )
    parser.add_argument("config_path", type=str, help="Path to the config file to use")
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

    # Convert report pages from PDFs into PNGs
    with futures.ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        jobs = []
        for kwargs in pdfconv_args:
            jobs.append(
                executor.submit(
                    pdf_to_txt,
                    txt_dir=args.txt_out_dir,
                    overwrite=args.overwrite,
                    **kwargs,
                )
            )
        for j in futures.as_completed(jobs):
            j.result()


if __name__ == "__main__":
    main()
