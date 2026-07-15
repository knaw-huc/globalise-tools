SHELL=/bin/bash

JAVA_OPTS = --enable-native-access=ALL-UNNAMED
JAR = globalise-ktools.jar

.SECONDARY:
.DELETE_ON_ERROR:

all: prepare-work data/concept-index.json data/documents-per-inventory.json

data:
	@mkdir -p data

data/concept-uuids.lst: | data
	s5cmd ls "s3://globalise-data/objects/thesaurus/*-*-*.json" | awk '{sub(/\.json$$/,"",$$NF); print $$NF}' > $@

data/concept-index.json: data/concept-uuids.lst $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-concept-index --in-file $< --out-file $@

data/documents.csv: | data
	s5cmd cp s3://globalise-data/objects/document/documents.csv data/documents.csv.gz
	gunzip data/documents.csv.gz

data/documents-per-inventory.json: data/documents.csv $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-document-definitions --in-file $< --out-file $@

work/%/entity_links.csv work/%/entity_annotations.csv: prepare-work

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

work/%/entity_hierarchy.json: work/%/entity_links.csv work/%/entity_annotations.csv data/concept-index.json $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  aggregate-entity-hierarchies-per-page \
	  --entity-links-file       work/$*/entity_links.csv \
	  --entity-annotations-file work/$*/entity_annotations.csv \
	  --concept-index-file      data/concept-index.json \
	  --out-file                $@

work/%/annotation_enhancements.json: work/%/entity_links.csv $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  enhance-annotations \
	  --entity-links-file       work/$*/entity_links.csv \
	  --out-file                $@

prepare-inventory-%: work/%/entity_hierarchy.json work/%/annotation_enhancements.json
	@:

.PHONY: prepare-all-inventories
prepare-all-inventories: data/inventorynumbers.lst
	cd work && \
	cat ../data/inventorynumbers.lst | sed -e "s/^/prepare-inventory-/" | split -l 50 && \
	for x in x??; do echo -n "make --jobs " > $$x.sh; cat $$x | tr '\n' ' ' >>$$x.sh; done && \
	chmod a+x *.sh
	for j in work/x*.sh; do ./$$j; done

