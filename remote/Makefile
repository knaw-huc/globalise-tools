all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

ALL_INV=$(shell cat .make/inventorynumbers.lst)
OUT=work
PAGEXMLDIR=$(OUT)/pagexml
XMIDIR=$(OUT)/xmi
MANIFESTSDIR=data/manifests/
COMMIT=2026.01.30

.make/:
	mkdir -p $@

$(OUT)/annotation-lists/:
	mkdir -p $@

.make/inventorynumbers.lst: | .make/
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

.make/init: | .make/
	cp pyproject.toml pyproject.toml.bak
	grep -v Users pyproject.toml.bak > pyproject.toml
	poetry lock
	poetry install
	mv inventory2timespan.json document_data.json data/
	touch $@

data/pagexml/:
	mkdir -p $@

data/pagexml/%.zip: | data/pagexml/
	@if [ -z "$$SSHUSER" ]; then \
		echo "SSHUSER is not set: user for hucdrive.huc.knaw.nl"; \
		exit 1; \
	fi
	@if [ -z "$$SSHPASS" ]; then \
		echo "SSHPASS is not set: password for SSHUSER"; \
		exit 1; \
	fi
	sshpass -e scp -P 2222 ${SSHUSER}@hucdrive.huc.knaw.nl:globalise/$*-pagexml.zip $@

.make/pagexml-%: data/pagexml/%.zip | .make/
	@mkdir -p $(PAGEXMLDIR)
	unzip -o --qq -j $< -d $(PAGEXMLDIR)/$*/
	@touch $@

data/xmicas/:
	mkdir -p $@

data/xmicas/%.zip: | data/xmicas/
	@if [ -z "$$SSHUSER" ]; then \
		echo "SSHUSER is not set: user for hucdrive.huc.knaw.nl"; \
		exit 1; \
	fi
	@if [ -z "$$SSHPASS" ]; then \
		echo "SSHPASS is not set: password for SSHUSER"; \
		exit 1; \
	fi
	sshpass -e scp -P 2222 ${SSHUSER}@hucdrive.huc.knaw.nl:globalise/$*-xmi.zip $@

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

.make/normalized-text-%: .make/word-offsets-% .make/xmicas-% typesystem.xml scripts/gt_ner_xmi_to_wa.py .make/init
	poetry run ./scripts/gt_ner_xmi_to_wa.py \
	  --pagexml-dir      $(PAGEXMLDIR) \
	  --xmi-dir          $(XMIDIR) \
	  --word-offsets-dir $(OUT)/$*/htr-word-offsets \
	  --type-system      typesystem.xml \
	  --output-dir       $(OUT) \
	  --manifests-dir    $(MANIFESTSDIR) \
	  --inv-nr           $*
	@touch $@

$(OUT)/%/annotations/transcriptions/: .make/pagexml-% .make/normalized-text-% scripts/gt-generate-transcription-annotation-pages.py .make/init
	@mkdir -p $@
	for t in $(OUT)/$*/NL*.txt; do \
		base=$$(basename $$t .txt); \
		poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
			--git-commit $(COMMIT) \
			--pagexml    $(PAGEXMLDIR)/$*/$$base.xml \
			--pagetext   $(OUT)/$*/$$base.txt \
			--output-dir $(OUT)/$*/annotations/transcriptions & \
	done
	wait

$(OUT)/%/ner-annotations.json: .make/normalized-text-% ./scripts/gt_ner_xmi_to_wa.py .make/init
	poetry run ./scripts/gt_ner_xmi_to_wa.py \
    --git-commit       $(COMMIT) \
    --pagexml-dir      $(PAGEXMLDIR) \
    --xmi-dir          $(XMIDIR) \
    --word-offsets-dir $(OUT)/$*/htr-word-offsets \
    --manifests-dir    $(MANIFESTSDIR) \
    --type-system      typesystem.xml \
    --output-dir       $(OUT) \
    --inv-nr           $*

$(OUT)/%/annotations/entities/: $(OUT)/%/ner-annotations.json ./scripts/gt-group-to-annotation-page.py .make/init
	@mkdir -p $@
	poetry run ./scripts/gt-group-to-annotation-page.py \
	    --git-commit    $(COMMIT) \
	 	--manifests-dir $(MANIFESTSDIR) \
		$(OUT)/$*/ner-annotations.json

$(OUT)/annotation-lists/%.zip: $(OUT)/%/annotations/transcriptions/ $(OUT)/%/annotations/entities/ | $(OUT)/annotation-lists/
	cd $(OUT)/$*/annotations/ && zip --quiet -r ../../annotation-lists/$*.zip entities transcriptions
	
#.PHONY: $(addprefix annotation-lists-,$(ALL_INV))
annotation-lists-%: $(OUT)/annotation-lists/%.zip
	$(MAKE) $(OUT)/annotation-lists/$*.zip

.PHONY: all-annotation-lists
all-annotation-lists: .make/inventorynumbers.lst $(addprefix annotation-lists-,$(ALL_INV))

.PHONY: help
help:
	@echo "available make targets:"
	@echo "  make annotation-lists-<invnr>"
	@echo "  make all-annotation-lists"
