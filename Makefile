all: help
SHELL=/bin/bash

data/iiif-url-mapping.csv: scripts/gt-map-pagexml-to-iiif-url.py data/NL-HaNA_1.04.02_mets.csv
	poetry run scripts/gt-map-pagexml-to-iiif-url.py --data-dir data

data/generale_missiven.csv:
	wget https://datasets.iisg.amsterdam/api/access/datafile/10784 --output-document data/generale_missiven.csv

data/document_metadata.csv:
	wget https://raw.githubusercontent.com/globalise-huygens/annotation/main/2023/documents/document_metadata.csv?token=GHSAT0AAAAAAB5IWT2N2Q3F56VQALTYBSDQZHPKMAA --output-document data/document_metadata.csv

data/pagexml_map.json: data/pagexml-2023-05-30-contents.txt scripts/gt-create-pagexml-map.py
	poetry run scripts/gt-create-pagexml-map.py

data/scan_url_mapping.json: scripts/gt-extract-scan-url-mapping.py
	poetry run scripts/gt-extract-scan-url-mapping.py

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

.PHONY: test-untangle
test-untangle: data/iiif-url-mapping.csv data/pagexml_map.json data/scan_url_mapping.json
	poetry run ./scripts/gt-untangle-globalise.py -cd conf -cn test.yaml
#	make test-missive-annotations
#	make test-inception-annotations

.PHONY: test-missive-annotations
test-missive-annotations: out/*/web_annotations.json data/generale_missiven.csv data/iiif-url-mapping.csv scripts/gt-create-missive-annotations.py conf/test.yaml
	poetry run ./scripts/gt-create-missive-annotations.py -cd conf -cn test.yaml

.PHONY: test-inception-annotations
test-inception-annotations: data/2024/document_metadata.csv data/iiif-url-mapping.csv scripts/gt-convert-inception-annotations-2024.py conf/test.yaml
	poetry run ./scripts/gt-convert-inception-annotations-2024.py -cd conf -cn test.yaml

.PHONY: test-xmi-generation
test-xmi-generation: data/2024/document_metadata.csv scripts/gt-import-document.py conf/test.yaml
	poetry run ./scripts/gt-import-document.py -cd conf -cn test.yaml

.PHONY: prod-xmi-generation
prod-xmi-generation: data/2024/document_metadata.csv scripts/gt-import-document.py conf/prod.yaml
	poetry run ./scripts/gt-import-document.py -cd conf -cn prod.yaml

.PHONY: install
install:
	poetry update
	poetry install

.PHONY: watch-mongodb-data-space
watch-mongodb-data-space:
	kubectl exec -it $(shell kubectl get pods -o custom-columns=POD_ID:.metadata.name -l app=globalise-annorepo-mongodb --no-headers) -- watch -n 60 -d df -h /data/db

.PHONY: process-manifests
process-manifests:
	poetry run ./scripts/gt-process-manifests.py

.PHONY: test-paragraph-extraction
test-paragraph-extraction:
		poetry run ./scripts/gt-extract-paragraph-text.py

.PHONY: run-inception
run-inception:
	cd ~/workspaces/globalise/inception-local/ && docker-compose up --detach && open http://localhost:8088/

.PHONY: stop-inception
stop-inception:
	cd ~/workspaces/globalise/inception-local/ && docker-compose down

.PHONY: browse-globalise-inception
browse-globalise-inception:
	open https://text-annotation.huc.knaw.nl/

.PHONY: help
help:
	@echo "make-tools for globalise-tools"
	@echo
	@echo "Please use \`make <target>', where <target> is one of:"
	@echo "  install                    - to install the necessary requirements"
	@echo "  install-spacy-model        - to load the 'nl_core_news_lg' language model used by spacy"
#	@echo "  extract-all            		to extract text and annotations from all document directories"
	@echo "  web-annotations            - to generate the web-annotations"
	@echo
	@echo "  run-inception              - to start a local inception"
	@echo "  stop-inception             - to stop the local inception"
	@echo
	@echo "  test-untangle              - to generate and upload segmented text and web-annotations using test settings"
	@echo "  test-missive-annotations   - to generate general missive web-annotations using test settings"
	@#echo "  test-inception-annotations - to generate document web-annotations from the inception export using test settings"
	@echo "  test-xmi-generation        - to generate xmi using test settings"
	@echo "  prod-xmi-generation        - to generate xmi using prod settings"
	@echo
	@echo "  test-paragraph-extraction  - to generate logical and physical text segment files"
	@echo
	@echo "  sample                     - to extract a sample of web annotations where every type is represented"
	@echo
	@echo "  browse-globalise-inception - to open the globalise inception in a browser"
	@echo
