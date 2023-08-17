all: help
SHELL=/bin/bash

.PHONY: extract-all
extract-all:
	poetry run scripts/gt-extract-text.py --iiif-mapping-file data/iiif-url-mapping.csv data/[0-9]* && mv *.{txt,json,conll} out/

.PHONY: sample
sample:
	poetry run scripts/gt-select-annotations.py > out/sample.json

.PHONY: install-spacy-model
install-spacy-model:
	poetry run python -m spacy download nl_core_news_lg

.PHONY: web-annotations
web-annotations:
	poetry run scripts/gt-convert-webanno-tsv-to-web-annotations.py > out/entity-annotations.json

.PHONY: install
install:
	poetry update
	poetry install

.PHONY: test-run
test-run:
	poetry run ./scripts/gt-extract-documents.py -cd conf -cn test.yaml

.PHONY: help
help:
	@echo "make-tools for globalise-tools"
	@echo
	@echo "Please use \`make <target>', where <target> is one of:"
	@echo "  install                to install the necessary requirements"
#	@echo "  extract-all            to extract text and annotations from all document directories"
#	@echo "  web-annotations        to generate the web-annotations"
	@echo "  test-run               to extract document text and web annotations using test settings
	@echo "  sample                 to extract a sample of web annotations where every type is represented"
	@echo "  install-spacy-model    to load the 'nl_core_news_lg' language model used by spacy"
	@echo
