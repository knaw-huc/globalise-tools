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
	qlever index \
	  --cat-input-files "zcat $(OUT)/*.nq.gz" \
	  --parallel-parsing true \
	  --format nq \
	  --overwrite-existing \
	  --stxxl-memory 10G

.PHONY: test-index
test-index:
	qlever index \
	  --cat-input-files "zcat $(OUT)/999*.nq.gz" \
	  --parallel-parsing true \
	  --format nq \
	  --overwrite-existing \
	  --stxxl-memory 10G

.PHONY: start
start:
	qlever start

.PHONY: stop
stop:
	qlever stop

.PHONY: ll-query
expensive-query:
	qlever query 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?class (SAMPLE(?labels) AS ?label) (COUNT(DISTINCT ?instance) AS ?count) WHERE { ?instance a ?class .  FILTER (!isBlank(?class)) OPTIONAL { ?class rdfs:label ?labels } } GROUP BY ?class'

.PHONY: upgrade
upgrade:
	sudo apt upgrade qlever -y && sudo apt autoremove -y

.PHONY: help
help:
	@echo "available \`make' targets:"
	@echo -e "  $(BLUE)index$(RESET)    - index the quads of all entities annotation pages in qlever"
	@echo -e "  $(BLUE)start$(RESET)    - start the qlever server"
	@echo -e "  $(BLUE)stop$(RESET)     - stop the qlever server"
	@echo -e "  $(BLUE)upgrade$(RESET)  - upgrade qlever"
	@echo -e "  $(BLUE)ll-query$(RESET) - execute the expensive LL query"

#curl -s localhost:7019 -H "Accept: text/tab-separated-values" --data-urlencode query='select ?rel ?target where { "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:entities:NL-HaNA_1.04.02__9999_0002#annotation:16" ?rel ?target }'
#curl -s localhost:7019 -H "Accept: text/tab-separated-values" --data-urlencode query='select ?sub ?rel ?obj where { ?sub ?rel ?obj }'
#curl -s localhost:7019 -H "Accept: text/csv" --data-urlencode query='select ?rel ?obj where { <https://github.com/knaw-huc/globalise-tools/blob/2026.02.13/scripts/gt_create_annotation_lists_for_inventory_number.py> ?rel ?obj }'
