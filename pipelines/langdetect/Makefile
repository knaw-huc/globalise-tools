.SHELLFLAGS = -o pipefail -c
.PHONY: setup lists lines pages stats dist top100tokens frompagexml withcorrections clean docker-run
.DELETE_ON_ERROR:

#these can be injected/overriden via the environment or you can set up symlinks
#(@proycon: use make links-proycon-pollux to set up symlinks on pollux, do not use in combination with docker)
PAGEXML_PATH = ./pagexml/
VOC_GROUNDTRUTH_PATH = ./voc-groundtruth/
MANUAL_CORRECTIONS = ./language-identification-data/corrections/corrections.lang.tsv
PUBLISH_PATH = ./publish/

DOCKER_ENV_FILE = ./docker.env

lineinput_tsv := $(wildcard *-lines.tsv)
lineoutput_tsv := $(lineinput_tsv:%-lines.tsv=%-lines.lang.tsv)
output_tsv := $(lineinput_tsv:%-lines.tsv=%-all.lang.tsv)

all: stats pages.lang.tsv nondutch-pages.lang.tsv unknown-pages.lang.tsv

lines: $(lineoutput_tsv)
output: $(output_tsv)
pages: pages.lang.tsv

setup:
	@echo "Checking if common dependencies are available"
	command -V sed awk paste cat wc tee tr cut head tail python3
	@echo "Installing dependencies (requires cargo+rustc)"
	command -v lingua-cli || cargo install lingua-cli
	command -v lexmatch || cargo install lexmatch
	@echo "Setting up Python virtual environment and installing globalise-tools"
	[ ! -e env ] && python3 -m venv env; source env/bin/activate; cd ../../; pip install .
	if [ ! -e "$MANUAL_CORRECTIONS" ]; then git clone git@github.com:globalise-huygens/language-identification-data/ && ln -s language-identification-data/corrections/corrections.lang.tsv && ln -s language-identification-data/latin-script-pages/ publish; fi
	@echo "Activate the virtual environment with: source env/bin/activate , then run: make frompagexml PAGEXML_PATH=/path/to/globalise-pagexml && make all"

docker-run:
	@echo "(Note: this requires a docker.env file, copy and edit docker.template.env)"
	source $(DOCKER_ENV_FILE) && docker run -t -i -v ./Makefile:/data/Makefile -v $$LANGDETECT_PATH:/data -v $$PAGEXML_PATH:/data/pagexml -v $$VOC_GROUNDTRUTH_PATH:/data/voc-groundtruth -v $$LANGIDENT_DATA_PATH:/data/language-identification-data --env-file $(DOCKER_ENV_FILE) knaw-huc/globalise-tools

clean:
	-rm *.lang.tsv *.lst stats *.tmp

%-lines.lang.tsv: %-lines.tsv
	cut -f 1,2,3,4,5 "$<" | tail --lines +2  > "$@.left.tmp"
	cut -f 6 "$<" | tail --lines +2 | lingua-cli -n -l nl,en,fr,de,la,it,pt,es,da,id > "$@.linguacli.tmp"
	cut -f 6 "$<" | tail --lines +2 | lexmatch -i --coverage-matrix -l lexicons/nl_voc.tsv -l lexicons/nl.tsv -l lexicons/en.tsv -l lexicons/de.tsv -l lexicons/da.tsv -l lexicons/fr.tsv -l lexicons/la.tsv -l lexicons/it.tsv -l lexicons/es.tsv -l lexicons/pt.tsv -l lexicons/id.tsv --min-token-length 3 - | tail --lines +2 | cut -f 2- >  "$@.lexmatch.tmp"
	echo -e "inv_nr	page_no	textregion_id	textregion_type	line_id	lang	confidence	line_text	nl_voc	nl	en	de	da	fr	la	it	es	pt	id	total" > "$@"
	paste "$@.left.tmp" "$@.linguacli.tmp" "$@.lexmatch.tmp" >> "$@"
	rm "$@.left.tmp" "$@.linguacli.tmp" "$@.lexmatch.tmp"

lists: $(output_tsv)
	-rm *.lst
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$5 != "") print $$7 >> $$6".lst" }'

parlists: paragraphs 
	-rm *.lst
	cat *-paragraphs.lang.tsv | awk -F "\t" '{ if ($$4 != "lang") print $$6 >> $$4".par.lst" }'

stats: lists
	wc -l *.lst | tee $@

%-all.lang.tsv: %-lines.lang.tsv
	gt-classify-language $< > $@

pages.lang.tsv: $(output_tsv)
	head -n 1 10000-all.lang.tsv | cut -f 1,2,6 > $@
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$3 == "") print $$1"\t"$$2"\t"$$6 }' | sort -k 1n,2n >> $@

regions.lang.tsv: $(output_tsv)
	head -n 1 10000-all.lang.tsv > $@
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$3 != "" && $$5 == "") print $$0 }' >> $@

nondutch-pages.lang.tsv: $(output_tsv)
	#everything that is not exclusively dutch
	echo "$(shell head -n 1 10000-all.lang.tsv | cut -f 1,2,6)	page_text	url"  > $@
	cat *-all.lang.tsv | awk -F "\t" 'BEGIN { prev="" } ! /^inv_nr/ { if (prev != $$1$$2) { t = ""; }; if ($$3 == "" && $$6 != "unknown" && $$6 != "nld") { print $$1"\t"$$2"\t"$$6"\t"t"\thttps://transcriptions.globalise.huygens.knaw.nl/detail/urn:globalise:NL-HaNA_1.04.02_"$$1"_"$$2; t=""; } else { t=t " " $$7; } prev=$$1$$2; }' | sort -k 1n,2n >> $@

unknown-pages.lang.tsv: $(output_tsv)
	echo "$(shell head -n 1 10000-all.lang.tsv | cut -f 1,2,6)	page_text	url"  > $@
	cat *-all.lang.tsv | awk -F "\t" 'BEGIN { prev="" } ! /^inv_nr/ { if (prev != $$1$$2) { t = ""; }; if ($$3 == "" && $$6 == "unknown") { print $$1"\t"$$2"\t"$$6"\t"t"\thttps://transcriptions.globalise.huygens.knaw.nl/detail/urn:globalise:NL-HaNA_1.04.02_"$$1"_"$$2; t=""; } else { t=t " " $$7; } prev=$$1$$2; }' | sort -k 1n,2n >> $@

pages-withcorrections.lang.tsv: pages.lang.tsv
	gt-merge-manual-corrections --all $< $(MANUAL_CORRECTIONS) > $@

%-withcorrections.lang.tsv: %.lang.tsv
	gt-merge-manual-corrections $< $(MANUAL_CORRECTIONS) > $@

withcorrections: pages-withcorrections.lang.tsv nondutch-pages-withcorrections.lang.tsv unknown-pages-withcorrections.lang.tsv

publish: withcorrections
	cp -f pages-withcorrections.lang.tsv "$(PUBLISH_PATH)pages.lang.tsv"
	cp -f nondutch-pages-withcorrections.lang.tsv "$(PUBLISH_PATH)nondutch-pages.lang.tsv"
	cp -f unknown-pages-withcorrections.lang.tsv "$(PUBLISH_PATH)unknown-pages.lang.tsv"

dist: globalise-langdetect.tar.xz

top100tokens: nl.top100tokens.lst en.top100tokens.lst fr.top100tokens.lst de.top100tokens.lst la.top100tokens.lst it.top100tokens.lst pt.top100tokens.lst es.top100tokens.lst da.top100tokens.lst id.top100tokens.lst

%.top100tokens.lst: %.lst
	cat $< | sed 's/ /\n/g' | sort | uniq -c | sort -rn | head -n 100 > $@

globalise-langdetect.tar.xz: stats nondutch-pages.lang.tsv
	tar -cvJf globalize-langdetect.tar.xz *.lang.tsv *.lst stats

nl_voc.tsv:
	-xmllint --xpath '//*[local-name() = "TextRegion"]/*[local-name() = "TextEquiv"]/*[local-name() = "Unicode"]/text()' $(VOC_GROUNDTRUTH_PATH)/*xml | sed -e 's/&#13;//g' -e 's/&amp;/\&/g' > $@.tmp
	ucto -Lgeneric -l -m -n $@.tmp $@.tok.tmp 
	cat $@.tok.tmp | lingua-cli --confidence 0.6 -n -l nl,en,fr,de,la,it,pt,es,da,id | awk -F "\t" '{ if ($$1 == "nl") print $$3 }' | sed -e 's/ /\n/g' | grep -E "[[:alpha:]:\-]{2,}+" | sort | uniq -c | sort -rn | awk '{ print $$2"\t"$$1 }' > $@
	rm $@.tmp $@.tok.tmp

frompagexml:
	#creates the lineinput_tsv files from pagexml, has to be invoked manually, ensure the gt-extract-lines.py script is linked and the virtualenv activated if needed
	gt-extract-lines -i $(PAGEXML_PATH) 

links-proycon-pollux:
	#set up personal dev environment using symlinks (do not user in combination with docker)
	ln -s /home/proycon/exp/globalize-pagexml/ $(PAGEXML_PATH)
	ln -s /home/proycon/exp/voc-groundtruth/ $(VOC_GROUNDTRUTH_PATH)
	ln -s /home/proycon/work/globalise-language-identification-data $(LANGIDENT_DATA_PATH)
