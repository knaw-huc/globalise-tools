all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

OUT=../work
ALL_INV=$(shell cat $(OUT)/inventorynumbers.lst)

GREEN=\033[1;32m
RED=\033[1;31m
BLUE=\033[1;34m
RESET=\033[0m

$(OUT)/inventorynumbers.lst: | ../data/xmicas/
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

.PHONY: index
qlever-index: globalise.settings.json

globalise.settings.json: $(wildcard $(OUT)/*.nq.gz)
	cd index && qlever index \
	  --input-files "../$(OUT)/*.nq.gz" \
	  --cat-input-files zcat \
	  --parallel-parsing true \
	  --format nq \
	  --overwrite-existing \
	  --stxxl-memory 10G


.PHONY: help
help:
	@echo "available \`make' targets:"
	@echo -e "  $(BLUE)index$(RESET)  - index the quads of all entities annotation pages in qlever"

#curl -s localhost:7019 -H "Accept: text/tab-separated-values" --data-urlencode query='select ?rel ?target where { "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:entities:NL-HaNA_1.04.02__9999_0002#annotation:16" ?rel ?target }'
#curl -s localhost:7019 -H "Accept: text/tab-separated-values" --data-urlencode query='select ?sub ?rel ?obj where { ?sub ?rel ?obj }'
#curl -s localhost:7019 -H "Accept: text/csv" --data-urlencode query='select ?rel ?obj where { <https://github.com/knaw-huc/globalise-tools/blob/2026.02.13/scripts/gt_create_annotation_lists_for_inventory_number.py> ?rel ?obj }'
