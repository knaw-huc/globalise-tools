all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[0;33m
BLUE=\033[0;34m
RESET=\033[0m

pagexml_directory := ~/c/data/globalise/pagexml
xmi_directory := ~/c/data/globalise/ner

data/iiif-url-mapping.csv: scripts/gt_map_pagexml_to_iiif_url.py data/NL-HaNA_1.04.02_mets.csv
	poetry run gt-map-pagexml-to-iiif-url --data-dir data

data/generale_missiven.csv:
	wget https://datasets.iisg.amsterdam/api/access/datafile/10784 --output-document data/generale_missiven.csv

data/document_metadata.csv:
	wget https://raw.githubusercontent.com/globalise-huygens/annotation/main/2023/documents/document_metadata.csv?token=GHSAT0AAAAAAB5IWT2N2Q3F56VQALTYBSDQZHPKMAA --output-document data/document_metadata.csv

data/pagexml_map.json: scripts/gt-create-pagexml-map.py data/external_ids.csv
	poetry run scripts/gt-create-pagexml-map.py

data/scan_url_mapping.json: scripts/gt-extract-scan-url-mapping.py
	poetry run scripts/gt-extract-scan-url-mapping.py

data/inventory2dates.json:
	echo -e "$(RED)Contact Leon van Wissen for $@ ('een mapping tussen inventarisnummer en datum')$(RESET)"

data/inventory2timespan.json: data/inventory2dates.json scripts/gt_convert_inventory_dates.py poetry_scripts.py
	poetry run gt-convert-inventory-dates
	poetry run gt-validate-inventory-timespan-completeness

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
	poetry run scripts/gt-untangle-globalise.py -cd conf -cn test.yaml
#	make test-missive-annotations
#	make test-inception-annotations

.PHONY: test-missive-annotations
test-missive-annotations: out/*/web_annotations.json data/generale_missiven.csv data/iiif-url-mapping.csv scripts/gt-create-missive-annotations.py conf/test.yaml
	poetry run scripts/gt-create-missive-annotations.py -cd conf -cn test.yaml

.PHONY: test-inception-annotations
test-inception-annotations: data/2024/document_metadata.csv data/iiif-url-mapping.csv scripts/gt-convert-inception-annotations-2024.py conf/test.yaml
	poetry run scripts/gt-convert-inception-annotations-2024.py -cd conf -cn test.yaml

.PHONY: test-xmi-generation
test-xmi-generation: data/2024/document_metadata.csv scripts/gt-import-document.py conf/test.yaml
	poetry run scripts/gt-import-document.py -cd conf -cn test.yaml

.PHONY: prod-xmi-generation
prod-xmi-generation: data/2024/document_metadata.csv scripts/gt-import-document.py conf/prod.yaml
	poetry run scripts/gt-import-document.py -cd conf -cn prod.yaml

.PHONY: convert-example-xmi
convert-example-xmi:
	scripts/gt-convert-example-xmi.sh

.PHONY: fix-reading-order
fix-reading-order:
	poetry run gt-fix-reading-order -i ~/e/globalise/pagexml/2023-09/1.04.02 -o out-local/fixed-pagexml -m data/document_metadata.csv -m data/document_metadata_esta.csv | tee > out-local/fix-reading-order.log

.PHONY: extract-paragraph-text
extract-paragraph-text:
	poetry run scripts/gt-extract-paragraph-text.py -i ~/e/globalise/pagexml/2023-09/1.04.02 -o out-local | tee > out-local/extract-paragraph-text.log

.PHONY: install
install:
	poetry update
	poetry install

.PHONY: watch-mongodb-data-space
watch-mongodb-data-space:
	kubectl exec -it $(shell kubectl get pods -o custom-columns=POD_ID:.metadata.name -l app=globalise-annorepo-mongodb --no-headers) -- watch -n 60 -d df -h /data/db

.PHONY: process-manifests
process-manifests:
	poetry run scripts/gt-process-manifests.py

.PHONY: test-paragraph-extraction
test-paragraph-extraction:
	poetry run scripts/gt-extract-paragraph-text.py

.PHONY: run-provenance
run-provenance:
	cd ~/workspaces/provenance/provenance-server && make run-server

.PHONY: run-inception
run-inception:
	cd ~/workspaces/globalise/inception-local/ && docker compose up --detach && open http://localhost:8088/

.PHONY: process-ner-xmi
process-ner-xmi: scripts/gt_ner_xmi_to_wa.py $(pagexml_directory) $(xmi_directory) data/typesystem.xml
	@if [[ -z "${TEXTREPO_API_KEY}" ]]; then echo -e "$(RED)ENV variable TEXTREPO_API_KEY not set, set and retry$(RESET)" && exit 1 ; fi
	poetry run gt-ner-xmi-to-wa \
		--pagexml-dir ~/c/data/globalise/pagexml \
		--xmi-dir ~/c/data/globalise/ner \
		--type-system=data/typesystem.xml \
		--output-dir=out \
		--text-repo=https://globalise.tt.di.huc.knaw.nl/textrepo \
		--api-key=$(TEXTREPO_API_KEY)

out/3598/ner-annotations.json: scripts/gt_ner_xmi_to_wa.py $(wildcard $(pagexml_directory)/3598/*.xml) $(wildcard .local/new/3598/*.xmi) data/typesystem.xml
	@if [[ -z "${TEXTREPO_API_KEY}" ]]; then echo -e "$(RED)ENV variable TEXTREPO_API_KEY not set, set and retry$(RESET)" && exit 1 ; fi
	poetry run gt-ner-xmi-to-wa \
		--pagexml-dir ~/c/data/globalise/pagexml \
		--xmi-dir .local/new \
		--type-system=data/typesystem.xml \
		--output-dir=out \
		--text-repo=https://globalise.tt.di.huc.knaw.nl/textrepo \
		--api-key=$(TEXTREPO_API_KEY) \
		--inv-nr=3598

.PHONY: process-ner-xmi-3598
process-ner-xmi-3598: out/3598/ner-annotations.json

.PHONY: stop-inception
stop-inception:
	cd ~/workspaces/globalise/inception-local/ && docker-compose down

.PHONY: browse-globalise-inception
browse-globalise-inception:
	open https://text-annotation.huc.knaw.nl/

.PHONY: version-update-patch
version-update-patch:
	poetry run version patch

.PHONY: version-update-minor
version-update-minor:
	poetry run version minor

.PHONY: version-update-major
version-update-major:
	poetry run version major

.PHONY: detect-copy-paste
detect-copy-paste:
	pmd cpd --minimum-tokens 50 --dir globalise_tools --dir scripts --language python | less

.PHONY: docker
docker:
	docker build -t knaw-huc/globalise-tools .

.PHONY: docker-run
docker-run:
	docker run -t -i -v .:/data knaw-huc/globalise-tools


.PHONY: help
help:
	@echo -e "make-tools for $(GREEN)globalise-tools$(RESET)"
	@echo
	@echo -e "Please use \`$(YELLOW)make <target>$(RESET)', where $(YELLOW)<target>$(RESET) is one of:"
	@echo -e "  $(BLUE)install$(RESET)                    - to install the necessary requirements"
	@echo -e "  $(BLUE)install-spacy-model$(RESET)        - to load the 'nl_core_news_lg' language model used by spacy"
	@echo
	@echo -e "  $(BLUE)docker$(RESET)                     - build a docker container containing everything"
	@echo -e "  $(BLUE)docker-run$(RESET)                 - run the docker container interactively (build it first)"
#	@echo -e "  $(BLUE)extract-all$(RESET)            		to extract text and annotations from all document directories"
#	@echo -e "  $(BLUE)web-annotations$(RESET)            - to generate the web-annotations"
	@echo
	@echo -e "  $(BLUE)version-update-patch$(RESET)       - to update the project version to the next patch version"
	@echo -e "  $(BLUE)version-update-minor$(RESET)       - to update the project version to the next minor version"
	@echo -e "  $(BLUE)version-update-major$(RESET)       - to update the project version to the next major version"
	@echo
	@echo -e "  $(BLUE)run-provenance$(RESET)             - to start a local provenance server"
	@echo -e "  $(BLUE)run-inception$(RESET)              - to start a local inception"
	@echo -e "  $(BLUE)stop-inception$(RESET)             - to stop the local inception"
	@echo
	@echo -e "  $(BLUE)test-untangle$(RESET)              - to generate and upload segmented text and web-annotations using test settings"
#	@echo -e "  $(BLUE)test-missive-annotations$(RESET)   - to generate general missive web-annotations using test settings"
#	@echo -e "  $(BLUE)test-inception-annotations$(RESET) - to generate document web-annotations from the inception export using test settings"
	@echo -e "  $(BLUE)test-xmi-generation$(RESET)        - to generate xmi using test settings"
	@echo -e "  $(BLUE)prod-xmi-generation$(RESET)        - to generate xmi using prod settings"
	@echo
	@echo -e "  $(BLUE)process-ner-xmi$(RESET)            - to generate web annotations from the ner enriched xmi files"
	@echo
	@echo -e "  $(BLUE)convert-example-xmi$(RESET)        - to generate web annotations from the example set of xmi files"
	@echo -e "  $(BLUE)fix-reading-order$(RESET)          - to generate pagexml with corrected reading order"
	@echo
	@echo -e "  $(BLUE)test-paragraph-extraction$(RESET)  - to generate logical and physical text segment files"
	@echo -e "  $(BLUE)extract-paragraph-text$(RESET)     - to generate a tsv file with the paragraph text of the pagexml"
	@echo
	@echo -e "  $(BLUE)sample$(RESET)                     - to extract a sample of web annotations where every type is represented"
	@echo -e "  $(BLUE)detect-copy-paste$(RESET)          - find code duplication"
	@echo
	@echo -e "  $(BLUE)browse-globalise-inception$(RESET) - to open the globalise inception in a browser"
	@echo
