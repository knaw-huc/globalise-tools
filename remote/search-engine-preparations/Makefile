SHELL=/bin/bash

JAVA_OPTS = --enable-native-access=ALL-UNNAMED
JAR = globalise-ktools.jar

.SECONDARY:
.DELETE_ON_ERROR:

all: prepare-work data/concept-index.json data/documents-per-inventory.json

globalise-tools/data/globalise-inventories.json:
	cd globalise-tools && $(MAKE) data/globalise-inventories.json

data:
	@mkdir -p data

data/concept-uuids.lst: | data
	s5cmd ls "s3://globalise-data/objects/thesaurus/*-*-*.json" | awk '{sub(/\.json$$/,"",$$NF); print $$NF}' > $@

data/facets.json data/concept-index.json: data/concept-uuids.lst globalise-tools/data/globalise-inventories.json $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-concept-index --concept-uuids-file $< --inventories-file globalise-tools/data/globalise-inventories.json --out-file $@

data/documents.csv: | data
	s5cmd cp s3://globalise-data/objects/document/documents.csv data/documents.csv.gz
	gunzip data/documents.csv.gz

data/documents-per-inventory.json: data/documents.csv $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-document-definitions --in-file $< --out-file $@

#work/%/entity_links.csv work/%/entity_annotations.csv: prepare-work
#	@:

work/%/entity_annotations.csv:
	mkdir -p work/$*
	s5cmd cp "s3://globalise-data/objects/inventory/$*.csv" $@.gz
	gunzip --force $@.gz
#	curl -Ls --compressed http://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/objects/inventory/$*.csv > $@

work/%/entity_links.csv:
	mkdir -p work/$*
	s5cmd cp "s3://globalise-data/objects/inventory/links/$*.csv" $@.gz
	gunzip --force $@.gz
#	curl -Ls --compressed http://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/objects/inventory/links/$*.csv > $@
#	grep -l AccessDenied $@ && rm $@ || echo -n # remove if it's not a csv, continue otherwise

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
	for x in x??; do echo -n "make --jobs --keep-going " > $$x.sh; cat $$x | tr '\n' ' ' >>$$x.sh; done && \
	chmod a+x *.sh
	for j in work/x*.sh; do ./$$j; done

.PHONY: all-inventory-index-metadata
all-inventory-index-metadata: data/inventorynumbers.lst
	cd work && \
	cat ../data/inventorynumbers.lst | while read i; do echo "work/$$i/index.json" ; done | split -l 50 && \
	for x in x??; do echo -n "cd globalise-tools && make --jobs --keep-going " > $$x.sh; cat $$x | tr '\n' ' ' >>$$x.sh; done && \
	chmod a+x *.sh
	for j in work/x*.sh; do ./$$j; done

work/%/index.json: work/%/entity_hierarchy.json work/%/annotation_enhancements.json
	cd globalise-tools && $(MAKE) --jobs work/$*/index.json

work/%/index.json.gz: work/%/index.json
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

work/facets.json: data/facets.json
	cp $< $@

work/facets.json.gz: work/facets.json
	gzip --force $<

.make/upload-facets: work/facets.json.gz | .make
	s5cmd cp \
	  --content-type "application/json" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/facets.json \
	  > /dev/null
	@echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:facets.json"
	@touch $@
