all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

ALL_INV=$(shell cat .make/inventorynumbers.lst)
OUT=work
PAGEXMLDIR=$(OUT)/pagexml
XMIDIR=$(OUT)/xmi

.make/:
	mkdir -p $@
data/pagexml/:
	mkdir -p $@
$(OUT)/annotation-lists/:
	mkdir -p $@

.make/inventorynumbers.lst: | .make/
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

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

.make/xmicas-%: data/xmicas/%.zip | .make/
	@mkdir -p $(XMIDIR)
	unzip -o -qq -j $< -d $(XMIDIR)/$*
	@touch $@

.make/annotation-pages-%: .make/pagexml-% | .make/
	@touch $@

#.PHONY: $(addprefix annotation-pages-,$(ALL_INV))
#annotation-pages-%: .make/annotation-pages-%
.make/word-offsets-%: .make/pagexml-% scripts/gt-extract-htr-word-offsets.py
	poetry run ./scripts/gt-extract-htr-word-offsets.py \
	  --output-dir $(OUT)/$*/htr-word-offsets \
	  $(PAGEXMLDIR)/$*/NL*.xml
	@touch $@

typesystem.xml:
	echo "missing file: data/typesystem.xml"

.make/normalized-text-%: .make/word-offsets-% .make/xmicas-% typesystem.xml scripts/gt_ner_xmi_to_wa.py
	poetry run ./scripts/gt_ner_xmi_to_wa.py \
	  --pagexml-dir      $(PAGEXMLDIR) \
	  --xmi-dir          $(XMIDIR) \
	  --word-offsets-dir $(OUT)/$*/htr-word-offsets \
	  --type-system      typesystem.xml \
	  --output-dir       $(OUT) \
	  --inv-nr           $*
	@touch $@

$(OUT)/%/annotations/transcriptions/: .make/pagexml-% .make/normalized-text-% scripts/gt-generate-transcription-annotation-pages.py
	@mkdir -p $@
	for t in $(OUT)/$*/NL*.txt; do \
		base=$$(basename $$t|sed -e 's/.txt//'); \
		poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
		--pagexml    $(PAGEXMLDIR)/$*/$$base.xml \
		--pagetext   $(OUT)/$*/$$base.txt \
		--output-dir $(OUT)/$*/transcriptions & \
	done
	wait

$(OUT)/%/ner-annotations.json: .make/normalized-text-%
	echo "made $(OUT)/$*/ner-annotations.json"

$(OUT)/%/annotations/entities/: $(OUT)/%/ner-annotations.json ./scripts/gt-group-to-annotation-page.py
	@mkdir -p $@
	poetry run ./scripts/gt-group-to-annotation-page.py $(OUT)/$*/ner-annotations.json

$(OUT)/annotation-lists/%.zip: $(OUT)/%/annotations/transcriptions/ $(OUT)/%/annotations/entities/ | $(OUT)/annotation-lists/
	cd $(OUT)/$*/annotations/ && zip --quiet -r ../../annotation-lists/$*.zip entities transcriptions
	
#.PHONY: $(addprefix annotation-lists-,$(ALL_INV))
annotation-lists-%: $(OUT)/annotation-lists/%.zip
	$(MAKE) $(OUT)/annotation-lists/$*.zip

.PHONY: all-annotation-lists
all-annotation-lists: $(addprefix annotation-lists-,$(ALL_INV))

.PHONY: help
help:
	@echo "available make targets:"
	@echo "  make annotation-lists-<invnr>"
	@echo "  make all-annotation-lists"
