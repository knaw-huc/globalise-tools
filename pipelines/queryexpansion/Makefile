.PHONY: setup all frompagexml
.DELETE_ON_ERROR:

THREADS = 20

#these can be injected/overriden via the environment:
PAGEXML_PATH = /home/proycon/exp/globalize-pagexml/

setup:
	@echo "Checking if common dependencies are available"
	command -V sed awk paste cat wc tee tr cut head tail python3 colibri-patternmodeller hyphertool
	@echo "Setting up Python virtual environment and installing globalise-tools"
	[ ! -e env ] && python3 -m venv env; source env/bin/activate; cd ../../; pip install .
	cargo install finalfusion-utils
	@echo "Activate the virtual environment with: source env/bin/activate , then run: make frompagexml PAGEXML_PATH=/path/to/globalise-pagexml && make all"

all: all.freqs

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
