.PHONY: setup all frompagexml
.DELETE_ON_ERROR:

THREADS = 20


#these can be injected/overriden via the environment:
PAGEXML_PATH = ./globalize-pagexml/
VOC_GROUNDTRUTH_PATH = ./voc-groundtruth/

setup:
	@echo "Checking if common dependencies are available"
	command -V sed awk paste cat wc tee tr cut head tail python3 colibri-patternmodeller hyphertool
	@echo "Setting up Python virtual environment and installing globalise-tools"
	[ ! -e env ] && python3 -m venv env; source env/bin/activate; cd ../../; pip install .
	cargo install finalfusion-utils
	@echo "Activate the virtual environment with: source env/bin/activate , then run: make frompagexml PAGEXML_PATH=/path/to/globalise-pagexml && make all"

all: all.freqs docker

docker:
	docker build --no-cache -t registry.diginfra.net/mvg/globalise-kweepeer:latest .

docker-cached:
	docker build -t registry.diginfra.net/mvg/globalise-kweepeer:latest .

docker-run: docker
	docker run --rm -t -i -p 8080:8080 registry.diginfra.net/mvg/globalise-kweepeer:latest

run:
	kweepeer --config all.config.toml

frompagexml:
	#creates the lineinput_tsv files from pagexml, has to be invoked manually, ensure the gt-extract-lines.py script is linked and the virtualenv activated if needed
	gt-extract-lines -i $(PAGEXML_PATH) 

all.txt:
	cat *-lines.tsv | grep paragraph | cut -d"	" -f 6 > $@

all.tok.txt: all.txt
	@echo "Dehyphenation and tokenisation"
	#language parameter is irrelevant here
	hyphertool --language nl --dehyphenate "„¬-" --prefix-dehyphenation "„" $< | sed -E 's/(\w+)([,\.\?:;„`"/–]+)/\1 \2/g' > $@

all.tok.colibri.dat: all.tok.txt
	@echo "encoding corpus"
	colibri-classencode $<

all.freqs: all.tok.colibri.dat
	@echo "computing term frequencies"
	colibri-patternmodeller -f all.tok.colibri.dat -c all.tok.colibri.cls -t 2 -l 1 -u -P | cut -d"	" -f 1,2 | grep -E "^[A-Za-z]+\s" | sort -k2 -rn >$@

globalize-embeddings.fifu: all.tok.txt
	finalfrontier skipgram --dims 300 --model structgram --epochs 10 --mincount 10 --threads ${THREADS} $< $@

nl_voc.tsv:
	-xmllint --xpath '//*[local-name() = "TextRegion"]/*[local-name() = "TextEquiv"]/*[local-name() = "Unicode"]/text()' $(VOC_GROUNDTRUTH_PATH)/*xml | sed -e 's/&#13;//g' -e 's/&amp;/\&/g' > $@.tmp
	ucto -Lgeneric -l -m -n $@.tmp $@.tok.tmp 
	cat $@.tok.tmp | lingua-cli --confidence 0.6 -n -l nl,en,fr,de,la,it,pt,es,da,id | awk -F "\t" '{ if ($$1 == "nl") print $$3 }' | sed -e 's/ /\n/g' | grep -E "[[:alpha:]:\-]{2,}+" | sort | uniq -c | sort -rn | awk '{ print $$2"\t"$$1 }' > $@
	rm $@.tmp $@.tok.tmp

%.tsv: %.jsonld
	#Convert a SKOS JSON-LD to a TSV file that can be used by kweepeer's lookup module or analiticcl module
	skos2variants --dataset $< > $@

links-proycon-pollux:
	#personal dev environment
	ln -s /home/proycon/exp/globalize-pagexml/
	ln -s /home/proycon/exp/voc-groundtruth/
