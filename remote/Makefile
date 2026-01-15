all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

pagexml_directory := pagexml
xmi_directory := xmicas

ALL_INV=$(shell cat .make/inventorynumbers.lst)
OUT=work
PAGEXMLDIR=work/pagexml
XMIDIR=work/xmi

.make:
	mkdir -p $@
work/%/:
	mkdir -p $@
data/pagexml:
	mkdir -p $@
work/annotation-lists:
	mkdir -p $@

.make/inventorynumbers.lst: | .make
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

data/pagexml/%.zip: | data/pagexml
	./scripts/get-pagexml-zip.sh $*

.make/pagexml-%: data/pagexml/%.zip | work/%/ .make
	unzip -qq -j $< -d $(PAGEXMLDIR)/$*/
	@touch $@

.make/xmicas-%: data/xmicas/%.zip | work/%/ .make
	unzip -qq -j $< -d ${XMIDIR}/$*
	@touch $@

.make/annotation-pages-%: .make/pagexml-% | .make
	echo "done"
	@touch $@

#.PHONY: $(addprefix annotation-pages-,$(ALL_INV))
#annotation-pages-%: .make/annotation-pages-%
.make/word-offsets-%: ./scripts/gt-extract-htr-word-offsets.py .make/pagexml-%
	poetry run ./scripts/gt-extract-htr-word-offsets.py \
	  --output-dir ${OUT}/$*/htr-word-offsets \
	  ${PAGEXMLDIR}/$*/NL*.xml
	@touch $@

.make/normalized-text-%: .make/word-offsets-% data/typesystem.xml .make/xmicas-% ./scripts/gt_ner_xmi_to_wa.py
	poetry run ./scripts/gt_ner_xmi_to_wa.py \
	  --pagexml-dir      ${PAGEXMLDIR} \
	  --xmi-dir          ${XMIDIR} \
	  --word-offsets-dir ${OUT}/$*/htr-word-offsets \
	  --type-system      data/typesystem.xml \
	  --output-dir       ${OUT} \
	  --inv-nr           $*
	@touch $@

work/%/annotations/transcriptions: .make/pagexml-% ./scripts/gt-generate-transcription-annotation-pages.py .make/normalized-text-%
	@mkdir -p $@
	for t in $OUT/${inv_nr}/NL*.txt; do
		base=$(basename $t|sed -e 's/.txt//')
		poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
		--pagexml    ${PAGEXMLDIR}/$*/${base}.xml \
		--pagetext   ${OUT}/$*/${base}.txt \
		--output-dir ${OUT}/$*/transcriptions &
	done
	wait

${OUT}/%/ner-annotations.json: .make/normalized-text-%

work/%/annotations/entities: ${OUT}/%/ner-annotations.json ./scripts/gt-group-to-annotation-page.py
	@mkdir -p $@
	poetry run ./scripts/gt-group-to-annotation-page.py ${OUT}/$*/ner-annotations.json

work/annotation-lists/%.zip: work/%/annotations/transcriptions work/%/annotations/entities | work/annotation-lists
	cd work/$*/annotations/ && zip --quiet -r ../../annotation-lists/$*.zip entities transcriptions
	
#.PHONY: $(addprefix annotation-lists-,$(ALL_INV))
annotation-lists-%: work/annotation-lists/%.zip
	$(MAKE) work/annotation-lists/$*.zip

.PHONY: all-annotation-lists
all-annotation-lists: $(addprefix annotation-lists-,$(ALL_INV))

.PHONY: help
help:
	@echo "make annotation-lists-<invnr>"
	@echo "make all-annotation-lists"
