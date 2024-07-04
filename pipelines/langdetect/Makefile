.SHELLFLAGS = -o pipefail -c
.PHONY: deps lists lines pages stats dist top100tokens frompagexml
.DELETE_ON_ERROR:

PAGEXML_PATH = /home/proycon/exp/globalize-pagexml/
VOC_GROUNDTRUTH_PATH = /home/proycon/exp/voc-groundtruth/

lineinput_tsv := $(wildcard *-lines.tsv)
lineoutput_tsv := $(lineinput_tsv:%-lines.tsv=%-lines.lang.tsv)
output_tsv := $(lineinput_tsv:%-lines.tsv=%-all.lang.tsv)

parinput_tsv := $(wildcard *-paragraphs.tsv)
paroutput_tsv := $(parinput_tsv:%-paragraphs.tsv=%-paragraphs.lang.tsv)

all: stats pages.lang.csv nondutch-pages.lang.tsv

lines: $(lineoutput_tsv)
paragraphs: $(paroutput_tsv)
output: $(output_tsv)
pages: pages.lang.tsv

deps:
	cargo install lingua-cli lexmatch

clean:
	-rm *-lines.lang.tsv *-lines.lexmatch.tsv *-paragraphs.lang.tsv *-pages.lang.tsv *.lst stats *.tmp

%-lines.lang.tsv: %-lines.tsv
	cut -f 1,2,3,4,5 "$<" | tail --lines +2  > "$@.left.tmp"
	cut -f 6 "$<" | tail --lines +2 | lingua-cli -n -l nl,en,fr,de,la,it,pt,es,da,id > "$@.linguacli.tmp"
	cut -f 6 "$<" | tail --lines +2 | lexmatch -i --coverage-matrix -l lexicons/nl_voc.tsv -l lexicons/nl.tsv -l lexicons/en.tsv -l lexicons/de.tsv -l lexicons/da.tsv -l lexicons/fr.tsv -l lexicons/la.tsv -l lexicons/it.tsv -l lexicons/es.tsv -l lexicons/pt.tsv -l lexicons/id.tsv --min-token-length 3 - | tail --lines +2 | cut -f 2- >  "$@.lexmatch.tmp"
	echo -e "inv_nr	page_no	textregion_id	textregion_type	line_id	lang	confidence	line_text	nl_voc	nl	en	de	da	fr	la	it	es	pt	id	total" > "$@"
	paste "$@.left.tmp" "$@.linguacli.tmp" "$@.lexmatch.tmp" >> "$@"
	rm "$@.left.tmp" "$@.linguacli.tmp" "$@.lexmatch.tmp"

%-paragraphs.lang.tsv: %-paragraphs.tsv
	cut -f 1,2,3 "$<" | tail --lines +2  > "$@.left.tmp"
	cut -f 4 "$<" | tail --lines +2 | lingua-cli --minlength 20 --confidence 0.6 -n -l nl,en,fr,de,la,it,pt,es,da,id > "$@.right.tmp"
	echo -e "inv_nr	page_no	textarea_id	lang	confidence	text" > "$@"
	paste "$@.left.tmp" "$@.right.tmp" >> "$@"
	rm "$@.left.tmp" "$@.right.tmp"

lists: $(output_tsv)
	-rm *.lst
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$5 != "") print $$7 >> $$6".lst" }'

parlists: paragraphs 
	-rm *.lst
	cat *-paragraphs.lang.tsv | awk -F "\t" '{ if ($$4 != "lang") print $$6 >> $$4".par.lst" }'

stats: lists
	wc -l *.lst | tee $@

%-all.lang.tsv: %-lines.lang.tsv
	./gt-classify-language.py $< > $@

pages.lang.tsv: $(output_tsv)
	head -n 1 10000-all.lang.tsv > $@
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$3 == "") print $$0 }' >> $@

regions.lang.tsv: $(output_tsv)
	head -n 1 10000-all.lang.tsv > $@
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$3 != "" && $$5 == "") print $$0 }' >> $@

nondutch-pages.lang.tsv: $(output_tsv)
	head -n 1 10000-all.lang.tsv > $@
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$3 == "" && $$6 != "unknown" && $$8 == "0") print $$0 }' >> $@

unknown-pages.lang.tsv: $(output_tsv)
	head -n 1 10000-all.lang.tsv > $@
	cat *-all.lang.tsv | awk -F "\t" '{ if ($$1 != "inv_nr" && $$3 == "" && $$6 == "unknown") print $$0 }' >> $@

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
	./gt-extract-lines.py -i $(PAGEXML_PATH) 
