# pycerpt [![Build Status](https://travis-ci.org/MerlinB/pycerpt.svg?branch=master)](https://travis-ci.org/MerlinB/pycerpt)


Pycerpt is a  command line utility for extracting highlighted text from PDFs.


## Quickstart
Get the latest version: `pip install pycerpt`

Generate markdown with `excerpt test.pdf` or save to a file with `excerpt test.pdf > out.md` or `excerpt test.pdf out.md`.

### Generating PDFs
For PDF generation additional dependencies are needed: `pip install pycerpt[pdf]`.  
Usage: `excerpt test.pdf out.pdf`