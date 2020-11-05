# cafr-parser

Many state and municipal governments in the United States, though not required
by law in most places, publish annual financial reports in a format specified by
the Governmental Accounting Standards Board (GASB). This report is called a
Comprehensive Annual Financial Report (CAFR). While some governments legally
require that CAFRs be published in machine readable formats like XML-based
eXtensible Business Reporting Language (XBLR), they are in the minority. Many
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

# Functionality

* DONE Simple batch processing
* DONE Extraction of CAFR table text from local PDFs
* TODO Extraction of CAFR table text from remote PDFs
* TODO Translation of Statement of Net Position text into machine-readable format
* TODO Translation of Statement of Activities text into machine-readable format
* TODO Translation of Balance Sheet text into machine-readable format
* TODO Translation of generic table text to machine-readable format
* TODO Automatic report discovery

# Usage

These scripts work in two steps, as described below. Note, these scripts are
primarly only useful when you want to: 
* extract multiple tables from one report
* or extract tables from multiple reports

If you only want to extract text from a single PDF the oneliner below will dump
the extracted text to stdout. If the page you want to parse is sideways (not
uncommon for financial reports) you can add `-rotate <degrees>` before `png:-`
and it'll be rotated clockwise before trying to throw OCR at it.
```
convert -density 1200 -antialias "pdf:<pdf_path>[<page>]" -quality 100 png:- | tesseract - - --dpi 1200 --psm 6
```

## 1. Extracting Text from PDFs with `pdfs2txt.py`

`pdfs2txt.py` accepts a simple config file that describes a batch of pdfs to
extract table text from. The config is just a JSON object with a single key,
`cafrs`.
```
{
	"cafrs": [
		...
	]
}
```

The value of `cafrs` is a list of objects that include paths to PDFs to read
from, a list of pages where relevant tables can be found, and some metadata to
use for output file naming. The basic schema is:
```
{
	"city": "<string>",
	"state": "<string>",
	"year": <int>,
	"path": "<string>",
	"pages": [...]
}
```

The value of `pages` is a list containing entries of the form:
```
{
	"report": "<string>",
	"pageno": <int>,
	"rotate": <int>,
}
```

The `report` field indicates which section of the CAFR this page corresponds to
(e.g. the statement of net position). If multiple pages are associated with the
same report, they will be sorted in ascending page order and concatenated in
the output.

For each page in the `pages` list, `pdfs2text.py` will save a copy to
`PNG_OUT_DIR/<year>-<city>-<state>-<report>-<pageno>.png`. This may be useful
for validating the extracted text by hand.

For each report discovered in the `pages` list, `pdfs2txt.py` will output the
extracted text to `TXT_OUT_DIR/<year>-<city>-<state>-<report>.txt`

The `rotate` field is an optional number of degrees to rotate clockwise before
applying OCR. Negative values will cause counter-clockwise rotattion.

See `examples/config.json` for a few examples.

## 2. Translating Extracted Text with XXX

TODO
