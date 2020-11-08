# cafr-parser

Many state and municipal governments in the United States, though not required
by law in most places, publish annual financial reports in a format specified by
the Governmental Accounting Standards Board (GASB). This report is called a
Comprehensive Annual Financial Report (CAFR). While some governments legally
require that CAFRs be published in machine readable formats like XML-based
eXtensible Business Reporting Language (XBRL), they are in the minority. Many
governments still make their CAFRs publicly available in PDF format, though.

This repository contains some python scripts that you can use to parse CAFRs in
PDF format. Since many of these PDFs are just scans of paper copies of the CAFR
and since making sense of raw text from PDFs is somewhat tricky-- in
particular, trying to extract tablur data and dealing with different character
encodings-- these scripts rely on OCR-- which is quite good when it comes to
extracting computer generated text from images nowadays.

# Dependencies

* python (tested with 3.7 or newer. 2 might work)
* ImageMagick (tested with 7.0.10-24)
* tesseract (tested with 4.1.1)

You can find releases for each of theese at the links below:

* https://www.python.org/downloads/
* https://imagemagick.org/script/download.php
* https://github.com/tesseract-ocr/tesseract/releases

# Usage

If you have a CAFR saved at `some-city-2019.pdf` with the Statement of Net
Position, Statement of Activities, and Balance Sheet on pages 52, 53, and 54
respectively. You could extract the tables in CSV format with the following
script.
```
./parse-cafr.py some-city-2019.pdf 51 > net-position.csv
./parse-cafr.py some-city-2019.pdf 52 > activities.csv
./parse-cafr.py some-city-2019.pdf 53 > balance-sheet.csv
```

You can dump the extracted table as JSON by passing adding `--format json` to
the command line. The output will be a list of rows formatted like:
```
{
	"label": "<row label>",
	"column_data": {
		"<column_idx>": <currency>,
		...
	}
}
```

See the [tutorial](TUTORIAL.md) for more detailed usage info.
