all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

OUT=work
PAGEXMLDIR=$(OUT)/pagexml
XMIDIR=$(OUT)/xmi
MANIFESTSDIR=data/manifests
ALL_INV=$(shell cat $(OUT)/inventorynumbers.lst)
COMMIT=2026.02.16

GREEN=\033[1;32m
RED=\033[1;31m
BLUE=\033[1;34m
RESET=\033[0m

# gate task to limit parallelism
.PHONY: hucdrive-gate
.NOTPARALLEL: hucdrive-gate
hucdrive-gate:
	@:

.PHONY: check-ssh
check-ssh:
	@if [ -z "$$SSHUSER" ]; then \
		echo -e "$(RED)SSHUSER is not set: user for hucdrive.huc.knaw.nl$(RESET)"; \
		exit 1; \
	fi
	@if [ -z "$$SSHPASS" ]; then \
		echo -e "$(RED)SSHPASS is not set: password for SSHUSER$(RESET)"; \
		exit 1; \
	fi

.make/:
	mkdir -p $@

$(OUT)/inventorynumbers.lst: | data/xmicas/
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

.PHONY: init
init: .make/init
.make/init: $(OUT)/inventorynumbers.lst | .make/
	cp pyproject.toml pyproject.toml.bak
	grep -v Users pyproject.toml.bak > pyproject.toml
	poetry install
	mv inventory2timespan.json document_data.json typesystem.xml data/
	@touch $@

data/pagexml/:
	mkdir -p $@

data/pagexml/%.zip: REMOTE_SUFFIX = pagexml

data/xmicas/%.zip:  REMOTE_SUFFIX = xmi

data/%/%.zip: | hucdrive-gate check-ssh data/%/
	sshpass -e scp -P 2222 \
	  $(SSHUSER)@hucdrive.huc.knaw.nl:globalise/$*-$(REMOTE_SUFFIX).zip \
	  $@

.make/pagexml-%: data/pagexml/%.zip | .make/
	@mkdir -p $(PAGEXMLDIR)
	unzip -o --qq -j $< -d $(PAGEXMLDIR)/$*/
	@touch $@

data/xmicas/:
	mkdir -p $@

.make/xmicas-%: data/xmicas/%.zip | .make/
	@mkdir -p $(XMIDIR)
	unzip -o -qq -j $< -d $(XMIDIR)/$*
	@touch $@

.make/annotation-pages-%: .make/pagexml-% | .make/
	@touch $@

data/typesystem.xml:
	@echo -e "$(RED)missing file: data/typesystem.xml$(RESET)"

.make/combined-%: .make/init scripts/gt-create-annotation-lists-for-inventory-number.sh .make/xmicas-% data/typesystem.xml .make/pagexml-%
	./scripts/gt-create-annotation-lists-for-inventory-number.sh $* && rm -rf {$(PAGEXMLDIR),$(XMIDIR)}/$*/ .make/{pagexml,xmicas}-$*
	@touch $@

$(OUT)/annotation-lists/:
	mkdir -p $@

$(OUT)/annotation-lists/%.zip: .make/combined-% | $(OUT)/annotation-lists/
	cd $(OUT)/$*/ && zip -qrm ../annotation-lists/$*.zip {entities,transcriptions}/*.json && cd .. && find $* -depth -empty -delete
	
$(OUT)/inv-done.lst:
	@touch $@

$(OUT)/inv-done-sorted.lst: $(OUT)/inv-done.lst
	sort -u $(OUT)/inv-done.lst | sort -n > $@

$(OUT)/inv-todo.lst: $(OUT)/inv-done-sorted.lst $(OUT)/inventorynumbers.lst
	#diff --suppress-common-lines --strip-trailing-cr --minimal $(OUT)/inventorynumbers.lst $(OUT)/inv-done-sorted.lst | grep "<" | sed -e "s/< //" > $@
	diff -wB $(OUT)/{inventorynumbers,inv-done-sorted}.lst | grep "^-" | grep -v "lst" | sed -e "s/^-//" | sort -u | sort -n > $@

annotation-lists-%: $(OUT)/annotation-lists/%.zip | hucdrive-gate
#	$(MAKE) $(OUT)/annotation-lists/$*.zip
#	sshpass -e scp -P 2222 $(OUT)/annotation-lists/$*.zip ${SSHUSER}@hucdrive.huc.knaw.nl:annotationlists/$*-annotation-lists.zip && rm $(OUT)/annotation-lists/$*.zip
	mv $(OUT)/annotation-lists/$*.zip $(OUT)/annotation-lists/$*-annotation-lists.zip

.PHONY: all-annotation-lists
all-annotation-lists: $(OUT)/inventorynumbers.lst $(addprefix annotation-lists-,$(ALL_INV))

$(OUT)/%.nq.gz: $(OUT)/annotation-lists/%-annotation-lists.zip ./scripts/rewrite_context.py
	@echo -e "$(BLUE)---[ $$(date +"%Y-%m-%d %H:%M:%S") $(GREEN)Generating: $@$(BLUE) ]---$(RESET)"
	mkdir -p $(OUT)/$*/ && \
        cd $(OUT)/$*/ && \
        unzip -o -qq ../annotation-lists/$*-annotation-lists.zip
	mkdir -p $(OUT)/$*/fixed
	for j in $(OUT)/$*/entities/*.json; do \
		cat $$j \
		| sed -e 's|"@context":"http://iiif.io/api/presentation/3/context.json",||g' \
		| ./scripts/rewrite_context.py > $(OUT)/$*/fixed/$$(basename $$j) ; \
	done
	export JVM_ARGS="-Xmx4g -Xms4g -XX:+UseG1GC -XX:+UseStringDeduplication" && \
	riot --quiet --syntax json-ld --output=nquads $(OUT)/$*/fixed/*.json | sort -u | gzip > $(OUT)/$*.nq.gz && \
	rm -rf $(OUT)/$*/
	@echo -e "$(BLUE)---[ $$(date +"%Y-%m-%d %H:%M:%S") $(GREEN)Generated : $@$(BLUE) ]---$(RESET)"


.PHONY: generate-all-n-quads
generate-all-n-quads: scripts/gt-generate-all-n-quads.sh
	./scripts/gt-generate-all-n-quads.sh

.PHONY: fix-all-n-quads
fix-all-n-quads: scripts/gt-fix-n-quads.sh $(wildcard $(OUT)/*.nq.gz)
	./scripts/gt-fix-n-quads.sh

fix-n-quads-%: $(OUT)/%.nq.gz
	zcat $(OUT)/$*.nq.gz \
	| sed -e 's|file:///data/globalise-data/annotation-lists/$(OUT)/.*/fixed/|http://globalise.nl/ns/|g' \
	| sed -e 's|http://globalise.nl/ns/ExchangeUnit|https://w3id.org/globalise/ontology/G4_Exchange_Unit|g' \
	| sed -e 's|http://xmlns.com/foaf/0.1/Person|http://www.cidoc-crm.org/cidoc-crm/E21_Person|g' \
	| gzip > $(OUT)/$*.fixed.nq.gz \
	&& mv $(OUT)/$*.fixed.nq.gz $(OUT)/$*.nq.gz

upload-%: $(OUT)/annotation-lists/%-annotation-lists.zip
	mkdir -p $(OUT)/$*/ && \
	cd $(OUT)/$*/ && \
	unzip -o -qq ../annotation-lists/$*-annotation-lists.zip && \
	for j in {entities,transcriptions}/*.json ; do \
	  gzip --force $$j && \
	  mv $$j.gz $$j ; \
	done
	#@echo -e "$(BLUE)uploading annotation lists for $* ...$(RESET)"
	#s5cmd cp --content-type "application/json" --content-encoding "gzip" "$(OUT)/$*/*" s3://globalise-data/annotations/ > /dev/null
	#@echo -e "$(GREEN)done, cleaning up ...$(RESET)"
	#rm -rf $(OUT)/$*/

.PHONY: upload-all
upload-all: scripts/gt-upload-all-annotation-lists.sh
	./scripts/gt-upload-all-annotation-lists.sh

$(OUT)/%/document.txt.gz: $(OUT)/%/document.txt
	gzip --force $<

.make/upload-document-txt-%: $(OUT)/%/document.txt.gz | .make/
	s5cmd cp \
	  --content-type "text/plain;charset=UTF-8" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/$*.txt \
	  > /dev/null
	@echo "uploaded https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$*.txt"
	@touch $@

$(OUT)/%/entity-tags.json.gz: $(OUT)/%/entity-tags.json
	gzip --force $<

.make/upload-entity-tags-%: $(OUT)/%/entity-tags.json.gz | .make/
	s5cmd cp \
	  --content-type "application/json" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/$*.index.json \
	  > /dev/null
	@echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$inv.index"
	@touch $@

$(OUT)/%/index.json: | $(OUT)/%/
	curl -Ls --compressed https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$*.index > $@

$(OUT)/%/entity_linking.csv: scripts/gt_make_entity_linking_csv.py $(OUT)/%/entities $(OUT)/%/index.json
	poetry run gt-make-entity-linking-csv $*

$(OUT)/%/entity_linking.csv.gz: $(OUT)/%/entity_linking.csv
	gzip --force $<

.make/upload-csv-%: $(OUT)/%/entity_linking.csv.gz | .make/
	s5cmd cp \
	  --content-type "text/csv;charset=UTF-8" \
	  --content-encoding "gzip" \
	  $< \
	  s3://globalise-data/objects/inventory/$*.csv \
	  > /dev/null
	@echo "uploaded https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$*.csv"
	@touch $@

.PHONY: help
help:
	@echo "available \`make' targets:"
	@echo -e "  $(BLUE)init$(RESET)                     - set up the environment for the scripts to run in"
	@echo -e "  $(BLUE)annotation-lists-<invnr>$(RESET) - generate entities and transcription annotation pages for the given inventory number"
	@echo -e "  $(BLUE)all-annotation-lists$(RESET)     - generate all entities and transcription annotation pages"
	@echo
	@echo -e "  $(BLUE)upload-<invnr>$(RESET)           - upload the annotation lists of the given inventory number to the object store"
	@echo -e "  $(BLUE)upload-all$(RESET)               - upload all annotation lists to the object store"
	@echo
	@echo -e "  $(BLUE)$(OUT)/<invnr>.nq.gz$(RESET)       - convert all entities annotation pages for the given inventory number to a gzipped list of unique n-quads"
	@echo -e "  $(BLUE)generate-all-n-quads$(RESET)     - convert all entities annotation pages for all inventory numbers to gzipped lists of unique n-quads"
	@echo -e "  $(BLUE)qlever-index$(RESET)             - index the quads of all entities annotation pages in qlever"

#curl -s localhost:7019 -H "Accept: text/tab-separated-values" --data-urlencode query='select ?rel ?target where { "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:entities:NL-HaNA_1.04.02__9999_0002#annotation:16" ?rel ?target }'
#curl -s localhost:7019 -H "Accept: text/tab-separated-values" --data-urlencode query='select ?sub ?rel ?obj where { ?sub ?rel ?obj }'
#curl -s localhost:7019 -H "Accept: text/csv" --data-urlencode query='select ?rel ?obj where { <https://github.com/knaw-huc/globalise-tools/blob/2026.02.13/scripts/gt_create_annotation_lists_for_inventory_number.py> ?rel ?obj }'


