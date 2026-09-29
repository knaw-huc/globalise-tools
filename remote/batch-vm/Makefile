all: help

.SECONDARY:
.DELETE_ON_ERROR:

TAG = globalise-ktools
JAR = globalise-ktools.jar
JAVA_OPTS = --enable-native-access=ALL-UNNAMED
DOCKER_DOMAIN = registry.diginfra.net/tt
SHELL = /bin/bash
RED = \033[1;31m
GREEN = \033[1;32m
YELLOW = \033[1;33m
BLUE = \033[1;34m
RESET = \033[0m

ES_PORT=3535
REMOTE_ES=index.globalise.huygens.knaw.nl
INVNUM_PATH=/data/globalise_qlever/search-engine-preparations/data/inventorynumbers.lst

#------------------------------------------------------------

FORCE:

.make:
	@mkdir -p .make

data/:
	@mkdir -p $@

data/eventmapping.json: | data/
	@echo "find the latest version of eventmapping.json on https://github.com/globalise-huygens/glob-portal-infomodel/issues/82"
	#curl -Ls --compressed https://github.com/user-attachments/files/30279994/eventmapping.json > $@

data/all-page-ids.lst: | data/
	@echo "missing file: all-page-ids.lst containing all page ids, from NL-HaNA_1.04.02_10000_0001 to NL-HaNA_1.04.02_9999_0540"

.make/documents-csv-timestamp: FORCE | .make
	s5cmd ls "s3://globalise-data/objects/document/documents.csv" > .make/documents-csv-timestamp.new
	cmp .make/documents-csv-timestamp.new .make/documents-csv-timestamp 2>/dev/null || mv .make/documents-csv-timestamp.new .make/documents-csv-timestamp

work/documents.csv: .make/documents-csv-timestamp
	curl -s --compressed https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/objects/document/documents.csv > $@

work/documents-per-inventory.json: work/documents.csv data/all-page-ids.lst $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) generate-document-definitions --in-file $< --page-ids-file data/all-page-ids.lst --out-file $@

work/concept-uuids.lst: FORCE
	s5cmd ls "s3://globalise-data/objects/thesaurus/*-*-*-*.json" | awk '{sub(/\.json$$/,"",$$NF); print $$NF}' > $@

work/facets.json: work/concept-index.json
	@:

data/inventory2dates.json: | data/
	echo -e "$(RED)Contact Leon van Wissen for $@ ('a mapping between inventory number and date')$(RESET)"

work/globalise-inventories.json: data/inventory2dates.json work/all-page-ids.lst work/1.04.02.xml
	@cd globalise-tools && $(MAKE) $@

work/concept-index.json: work/concept-uuids.lst work/globalise-inventories.json $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  generate-concept-index \
	  --concept-uuids-file $< \
	  --inventories-file work/globalise-inventories.json \
	  --out-file $@

work/%/entity_annotations.csv:
	mkdir -p work/$*
	curl -Ls --compressed http://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/objects/inventory/$*.csv > $@

work/%/entity_links.csv:
	mkdir -p work/$*
	curl -Ls --compressed http://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/objects/inventory/links/$*.csv > $@

work/%/entity_hierarchy.json: work/%/entity_links.csv work/%/entity_annotations.csv $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  aggregate-entity-hierarchies-per-page \
	  --entity-links-file       work/$*/entity_links.csv \
	  --entity-annotations-file work/$*/entity_annotations.csv \
	  --concept-index-file      work/concept-index.json \
	  --out-file                $@

work/%/annotation_enhancements.json: work/%/entity_links.csv $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  enhance-annotations \
	  --entity-links-file       work/$*/entity_links.csv \
	  --out-file                $@



#work/%/index.json:
#	mkdir -p work/$*
#	curl -Ls --compressed https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$*.index > $@

work/persons.json:# $(JAR)
	java $(JAVA_OPTS) -jar $(JAR) \
	  generate-person-index-file \
	  --out-file $@ \
	  2>&1 \
	  > work/make-person-index-file.log \
	  && ntfy-success -m "make-person-index-file succeeded" \
	  || ntfy-failure -m "make-person-index-file failed"

#------------------------------------------------------------

.PHONY: facets-file
facets-file: work/facets.json
	@:

.PHONY: person-index-file
person-index-file: work/persons.json
	$:

.PHONY: refresh-data-files
refresh-data-files: work/documents-per-inventory.json work/concept-index.json
	$:

.PHONY: documents-per-inventory-json
documents-per-inventory-json: work/documents-per-inventory.json

.PHONY: show-usage
show-usage: $(JAR)
	@java $(JAVA_OPTS) -jar $(JAR)

#------------------------------------------------------------

work/persons.json.gz: work/persons.json
	gzip --force $<

.make/upload-persons-json: work/persons.json.gz | .make
	s5cmd cp \
	  --content-type "application/json;charset=UTF-8" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/persons.json \
	  > /dev/null
	@echo "uploaded https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:persons"
	@touch $@

.PHONY: upload-person-index-file
upload-person-index-file: .make/upload-persons-json
	$:

#------------------------------------------------------------
work/facets.json: work/facets.json
	cp $< $@

work/facets.json.gz: work/facets.json
	gzip --force $<

.make/upload-facets-json: work/facets.json.gz | .make
	s5cmd cp \
	  --content-type "application/json;charset=UTF-8" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/facets.json \
	  > /dev/null
	@echo "uploaded https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:facets"
	@touch $@

.PHONY: upload-facets-file
upload-facets-file: .make/upload-facets-json
	$:

#------------------------------------------------------------

.PHONY: upload-event-pages-%
upload-event-pages-%: work/%/events/
	cd $< && for g in *.gz; do mv $$g $${g/.gz/}; done
	@echo -e "$(BLUE)uploading annotation lists for $* ...$(RESET)"
	s5cmd cp --content-type "application/json" --content-encoding "gzip" "work/$*/events" s3://globalise-data/annotations/ > /dev/null
	cd $< && for g in *.json; do mv $$g $$g.gz; done

#------------------------------------------------------------

.PHONY: upload-all-annotation-pages
# command line in work/x??.sh must be <= 4095 chars
upload-all-annotation-pages: $(INVNUM_PATH)
	@ntfy -m "upload-all-annotation-pages: started"
	cd work/ && \
	cat $(INVNUM_PATH) | while read i; do echo "upload-$$i" ; done | split -l 350 && \
	for x in x??; do echo -n "make -k -j 14 " > $$x.sh; cat $$x | tr '\n' ' ' >> $$x.sh; rm $$x; chmod a+x $$x.sh; done
	for j in work/x*.sh; do ./$$j && rm $$j; done
	@ntfy -m "upload-all-annotation-pages: finished"

.PHONY: upload-%
upload-%: work/%/events/ work/%/transcriptions/ work/%/entities/
	@echo -e "$(BLUE)uploading annotation lists for $* ...$(RESET)"
	for d in transcriptions entities events; do \
	  (cd work/$* && \
	    (cd $$d && for g in *.gz; do mv $$g $${g/.gz/}; done) && \
	    s5cmd cp --content-type "application/json" --content-encoding "gzip" "$$d" s3://globalise-data/annotations/ > /dev/null && \
	    (cd $$d && for g in *.json; do mv $$g $$g.gz; done) \
	  ) \
	done

#------------------------------------------------------------

work/%/index.json:
	cd globalise-tools && $(MAKE) $@

work/%/index.json.gz: work/%/index.json
	gzip --force $<

.make/upload-index-%: work/%/index.json.gz | .make
	s5cmd cp \
	  --content-type "application/json" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/$*.index.json \
	  > /dev/null
	@echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$*.index"
	@touch $@

.PHONY: ui-%
ui-%: .make/upload-index-%
	# clean up some afterwards to save storage space
	rm -rf work/$*/entities work/$*/transcriptions work/$*/*.csv

.PHONY: upload-all-document-index-files
upload-all-document-index-files:
	@ntfy -m "upload-all-document-index-files: started"
	cd work/ && \
	rm -rf upload-all-document-index-files && \
	mkdir -p upload-all-document-index-files && \
	cat $(INVNUM_PATH) | while read i; do echo "ui-$$i" ; done | split -l 350 && \
	for x in x??; do echo -n "make -k -j 14 " > upload-all-document-index-files/$$x.sh; cat $$x | tr '\n' ' ' >> upload-all-document-index-files/$$x.sh; rm $$x; chmod a+x upload-all-document-index-files/$$x.sh; done
	for j in work/upload-all-document-index-files/x*.sh; do ./$$j && rm $$j; done
	rm -rf work/upload-all-document-index-files; done
	@ntfy -m "upload-all-document-index-files: finished"

#------------------------------------------------------------

.PHONY: help
help:
	@echo -e "make-tools for $(GREEN)$(TAG)$(RESET)"
	@echo
	@echo -e "Please use \`$(YELLOW)make <target>$(RESET)', where $(YELLOW)<target>$(RESET) is one of:"
	@echo -e "  $(BLUE)show-usage$(RESET)                 - to run the app jar without parameters"
	@echo
	@echo -e "  $(BLUE)facets-file$(RESET)                - to generate the facets.json file containing the facet info per facet id"
	@echo -e "  $(BLUE)upload-facets-file$(RESET)         - to upload facets.json to https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:facets.json"
	@echo
	@echo -e "  $(BLUE)person-index-file$(RESET)          - to aggregate person data to a json file for indexing"
	@echo -e "  $(BLUE)upload-person-index-file$(RESET)   - to upload persons.json to https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:persons.json"
	@echo
	@echo -e "  $(BLUE)upload-all-document-index-files$(RESET) - to generate indx.json for all indexes and upload them to https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:*.index"
