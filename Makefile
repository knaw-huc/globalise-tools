all: help
SHELL=/bin/bash

.PHONY: extract-all
extract-all:
	poetry run scripts/globalise-extract-text.py data/[0-9]* && mv *.{txt,json} out/

.PHONY: install-spacy-model
install-spacy-model:
	poetry run python -m spacy download nl_core_news_lg

.PHONY: help
help:
	@echo "make-tools for globalise-tools"
	@echo
	@echo "Please use \`make <target>', where <target> is one of:"
	@echo "  extract-all           to extract text and annotations from all document directories"
	@echo "  install-spacy-model   to load the 'nl_core_news_lg'	 language model used by spacy"
	@echo
