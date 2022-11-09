all: help
SHELL=/bin/bash

.PHONY: extract-all
extract-all:
	@echo `for d in data/[0-9]*; do poetry run scripts/globalise-extract-text.py $$d; done && mv [0-9]*.{txt,json} out/`

.PHONY: help
help:
	@echo "make-tools for globalise-tools"
	@echo
	@echo "Please use \`make <target>', where <target> is one of:"
	@echo "  extract-all   to extract text and annotations from all document directories"
	@echo
