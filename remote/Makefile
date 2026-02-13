all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

OUT=work
PAGEXMLDIR=$(OUT)/pagexml
XMIDIR=$(OUT)/xmi
MANIFESTSDIR=data/manifests
ALL_INV=$(shell cat $(OUT)/inventorynumbers.lst)
COMMIT=2026.02.05

# gate task to limit parallelism
.PHONY: hucdrive-gate
.NOTPARALLEL: hucdrive-gate
hucdrive-gate:
	@:

.PHONY: check-ssh
check-ssh:
	@if [ -z "$$SSHUSER" ]; then \
		echo "SSHUSER is not set: user for hucdrive.huc.knaw.nl"; \
		exit 1; \
	fi
	@if [ -z "$$SSHPASS" ]; then \
		echo "SSHPASS is not set: password for SSHUSER"; \
		exit 1; \
	fi

.make/:
	mkdir -p $@

$(OUT)/inventorynumbers.lst: | data/xmicas/
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

.make/init: $(OUT)/inventorynumbers.lst
	cp pyproject.toml pyproject.toml.bak
	grep -v Users pyproject.toml.bak > pyproject.toml
	poetry install
	mv inventory2timespan.json document_data.json data/
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

#.PHONY: $(addprefix annotation-pages-,$(ALL_INV))
#annotation-pages-%: .make/annotation-pages-%
.make/word-offsets-%: .make/pagexml-% scripts/gt-extract-htr-word-offsets.py .make/init
	poetry run ./scripts/gt-extract-htr-word-offsets.py \
	  --output-dir $(OUT)/$*/htr-word-offsets \
	  $(PAGEXMLDIR)/$*/NL*.xml
	@touch $@

typesystem.xml:
	echo "missing file: data/typesystem.xml"

$(OUT)/%/ner-annotations.json: .make/word-offsets-% .make/xmicas-% typesystem.xml scripts/gt_ner_xmi_to_wa.py .make/init
	poetry run ./scripts/gt_ner_xmi_to_wa.py \
	  --git-commit       $(COMMIT) \
	  --pagexml-dir      $(PAGEXMLDIR) \
	  --xmi-dir          $(XMIDIR) \
	  --word-offsets-dir $(OUT)/$*/htr-word-offsets \
	  --type-system      typesystem.xml \
	  --output-dir       $(OUT) \
	  --manifests-dir    $(MANIFESTSDIR) \
	  --inv-nr           $*
	@touch $@

.make/transcriptions-%: .make/pagexml-% $(OUT)/%/ner-annotations.json scripts/gt-generate-transcription-annotation-pages.py .make/init
	@mkdir -p $(OUT)/$*/transcriptions
	for t in $(OUT)/$*/NL*.txt; do \
		base=$$(basename $$t .txt); \
		poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
			--git-commit $(COMMIT) \
			--pagexml    $(PAGEXMLDIR)/$*/$$base.xml \
			--pagetext   $(OUT)/$*/$$base.txt \
			--output-dir $(OUT)/$*/transcriptions & \
	done
	wait
	@touch $@

.make/entities-%: $(OUT)/%/ner-annotations.json ./scripts/gt-group-to-annotation-page.py .make/init
	@mkdir -p $(OUT)/$*/entities
	poetry run ./scripts/gt-group-to-annotation-page.py \
	    --git-commit    $(COMMIT) \
	 	--manifests-dir $(MANIFESTSDIR) \
		$(OUT)/$*/ner-annotations.json
	@touch $@

.make/combined-%: .make/init scripts/gt-create-annotation-lists-for-inventory-number.sh .make/xmicas-% typesystem.xml .make/pagexml-%
	./scripts/gt-create-annotation-lists-for-inventory-number.sh $*
	@touch $@

$(OUT)/annotation-lists/:
	mkdir -p $@

$(OUT)/annotation-lists/%.zip: .make/transcriptions-% .make/entities-% | $(OUT)/annotation-lists/
	cd $(OUT)/$*/ && zip -qrm ../annotation-lists/$*.zip {entities,transcriptions}/*.json
	
#.PHONY: $(addprefix annotation-lists-,$(ALL_INV))
annotation-lists-%: $(OUT)/annotation-lists/%.zip | hucdrive-gate
	$(MAKE) $(OUT)/annotation-lists/$*.zip
	sshpass -e scp -P 2222 $(OUT)/annotation-lists/$*.zip ${SSHUSER}@hucdrive.huc.knaw.nl:annotationlists/$*-annotation-lists.zip && rm $(OUT)/annotation-lists/$*.zip

.PHONY: all-annotation-lists
all-annotation-lists: $(OUT)/inventorynumbers.lst $(addprefix annotation-lists-,$(ALL_INV))

$(OUT)/inv-done.lst:
	@touch $@

$(OUT)/inv-done-sorted.lst: $(OUT)/inv-done.lst
	sort -nu $(OUT)/inv-done.lst > $@

$(OUT)/inv-todo.lst: $(OUT)/inv-done-sorted.lst $(OUT)/inventorynumbers.lst
	#diff --suppress-common-lines --strip-trailing-cr --minimal $(OUT)/inventorynumbers.lst $(OUT)/inv-done-sorted.lst | grep "<" | sed -e "s/< //" > $@
	diff -wB work/inventorynumbers.lst work/inv-done-sorted.lst | grep "^-" | grep -v "lst" | sed -e "s/^-//" | sort -un > $@

.PHONY: help
help:
	@echo "available make targets:"
	@echo "  make annotation-lists-<invnr>"
	@echo "  make all-annotation-lists"
