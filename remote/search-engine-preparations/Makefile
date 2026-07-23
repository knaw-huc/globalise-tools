SHELL=/bin/bash

JAVA_OPTS = --enable-native-access=ALL-UNNAMED
JAR = globalise-ktools.jar
INVNUM_PATH=/data/globalise_qlever/search-engine-preparations/data/inventorynumbers.lst
#INVNUM_PATH=~/workspaces/globalise/globalise-ktools/data/inventorynumbers.lst

RED=\033[1;31m
GREEN=\033[1;32m
YELLOW=\033[1;33m
BLUE=\033[1;34m
RESET=\033[0m

.SECONDARY:
.DELETE_ON_ERROR:

all: help
#all: prepare-work data/concept-index.json data/documents-per-inventory.json

globalise-tools/data/globalise-inventories.json:
	cd globalise-tools && $(MAKE) --jobs data/globalise-inventories.json

data:
	@mkdir -p data

data/concept-uuids.lst: | data
	s5cmd ls "s3://globalise-data/objects/thesaurus/*-*-*.json" | awk '{sub(/\.json$$/,"",$$NF); print $$NF}' > $@

data/facets.json data/concept-index.json: data/concept-uuids.lst globalise-tools/data/globalise-inventories.json $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-concept-index --concept-uuids-file $< --inventories-file globalise-tools/data/globalise-inventories.json --out-file data/concept-index.json

data/documents.csv: | data
	s5cmd cp s3://globalise-data/objects/document/documents.csv data/documents.csv.gz
	gunzip data/documents.csv.gz

data/documents-per-inventory.json: data/documents.csv data/all-page-ids.lst $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-document-definitions --in-file $< --page-ids-file data/all-page-ids.lst --out-file $@

#work/%/entity_links.csv work/%/entity_annotations.csv: prepare-work
#	@:

work/%/annotation_enhancements.json: work/%/entity_links.csv $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  enhance-annotations \
	  --entity-links-file       work/$*/entity_links.csv \
	  --out-file                $@

work/%/entity_annotations.csv:
	mkdir -p work/$*
	s5cmd cp "s3://globalise-data/objects/inventory/$*.csv" $@.gz
	gunzip --force $@.gz
#	curl -Ls --compressed http://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/objects/inventory/$*.csv > $@

work/%/entity_links.csv:
	mkdir -p work/$*
	s5cmd cp "s3://globalise-data/objects/inventory/links/$*.csv" $@.gz
	gunzip --force $@.gz

work/%/entity_hierarchy.json: work/%/entity_links.csv work/%/entity_annotations.csv data/concept-index.json $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  aggregate-entity-hierarchies-per-page \
	  --entity-links-file       work/$*/entity_links.csv \
	  --entity-annotations-file work/$*/entity_annotations.csv \
	  --concept-index-file      data/concept-index.json \
	  --out-file                $@

work/%/index.json: work/%/entity_hierarchy.json work/%/annotation_enhancements.json
	cd globalise-tools && $(MAKE) --jobs work/$*/index.json

work/%/index.json.gz: work/%/index.json
	gzip --force $<

work/facets.json: data/facets.json
	cp $< $@

work/facets.json.gz: work/facets.json
	gzip --force $<

.make:
	mkdir -p $@

.make/upload-index-%: work/%/index.json.gz | .make
	s5cmd cp \
	  --content-type "application/json" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/$*.index.json \
	  > /dev/null
	@echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$*.index"
	@touch $@

.make/upload-facets: work/facets.json.gz | .make
	s5cmd cp \
	  --content-type "application/json" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/facets.json \
	  > /dev/null
	@echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:facets.json"
	@touch $@

.PHONY: prepare-work
prepare-work: data/concept-uuids.lst data/documents.csv
	mkdir -p work && \
	cd work && \
	s5cmd cp "s3://globalise-data/objects/inventory/*.csv" .  && \
	for d in *.csv links/*.csv; do mv $$d $$d.gz; done && \
	for d in *.csv.gz; do \
		gunzip --force $$d; \
		i=$${d/.csv.gz/}; \
		mkdir -p $$i; \
		mv $$i.csv $$i/entity_annotations.csv; \
		gunzip --force links/$$i.csv.gz; \
		mv links/$$i.csv $$i/entity_links.csv; \
	done && \
	find . -depth -empty -delete

.PHONY: prepare-inventory-%
prepare-inventory-%: work/%/entity_hierarchy.json work/%/annotation_enhancements.json
	@:

.PHONY: clean
clean:
	rm -rf .make work/*

.PHONY: clean-%
clean-%:
	rm -rf .make/*-$* work/$*/

.PHONY: update-documents-csv
update-documents-csv: data/documents.csv
	@:

.PHONY: prepare-all-inventories
prepare-all-inventories: $(INVNUM_PATH)
	cd work && \
	cat $(INVNUM_PATH) | sed -e "s/^/prepare-inventory-/" | split -l 50 && \
	for x in x??; do echo -n "make --jobs --keep-going " > $$x.sh; cat $$x | tr '\n' ' ' >>$$x.sh; done && \
	chmod a+x *.sh
	for j in work/x*.sh; do ./$$j; done

.PHONY: upload-facets
upload-facets: .make/upload-facets
	@:

.PHONY: ui-%
ui-%: .make/upload-index-%
	# clean up some afterwards to save storage space
	rm -rf work/$*/entities work/$*/transcriptions work/$*/*.csv

.PHONY: upload-all-inventory-index-metadata
# command line in work/x??.sh must be <= 4095 chars
upload-all-inventory-index-metadata: $(INVNUM_PATH)
	cd work && \
	cat $(INVNUM_PATH) | while read i; do echo "ui-$$i" ; done | split -l 400 && \
	for x in x??; do echo -n "make -k -j 13 " > $$x.sh; cat $$x | tr '\n' ' ' >> $$x.sh; rm $$x; chmod a+x $$x.sh; done
	for j in work/x*.sh; do ./$$j && rm $$j; done

.PHONY: help
help:
	@echo -e "make-tools for $(GREEN)globalise search engine preparations$(RESET)"
	@echo
	@echo -e "Please use \`$(YELLOW)make <target>$(RESET)', where $(YELLOW)<target>$(RESET) is one of:"
	@echo -e "  $(BLUE)clean$(RESET)           - clean up the generated files"
	@echo -e "  $(BLUE)clean-<invnum>$(RESET)  - clean up the generated files, just for the given inventory number"
	@echo
	@echo -e "  $(BLUE)update-documents-csv$(RESET) - to download the latest version of $(GREEN)documents.csv$(RESET) from the object store"
	@echo
	@echo -e "  $(BLUE)upload-facets$(RESET)        - to generate $(GREEN)facets.json$(RESET) and upload it to https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:facets.json"
	@echo
	@echo -e "  $(BLUE)work/<invnum>/index.json$(RESET)            - to generate $(GREEN)index.json$(RESET) for the given inventory number without also uploading it"
	@echo -e "  $(BLUE)ui-<invnum>$(RESET)                         - to generate $(GREEN)index.json$(RESET) for the given inventory number and upload it to https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:<invnum>.index"
	@echo -e "  $(BLUE)upload-all-inventory-index-metadata$(RESET) - to generate $(GREEN)index.json$(RESET) for all inventory numbers and upload them to https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:<invnum>.index"
