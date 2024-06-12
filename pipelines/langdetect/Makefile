.SHELLFLAGS = -o pipefail -c
.PHONY: deps lists lines pages stats dist
.DELETE_ON_ERROR:

input_tsv := $(wildcard *-lines.tsv)
output_tsv := $(input_tsv:%-lines.tsv=%-lines.lang.tsv)
output_pages_tsv := $(input_tsv:%-lines.tsv=%-pages.lang.tsv)

all: stats nondutch.pages.tsv

lines: $(output_tsv)
pages: lines $(output_pages_tsv)

deps:
	cargo install lingua-cli

clean:
	-rm *-lines.lang.tsv *-pages.lang.tsv *.lst stats

%-lines.lang.tsv: %-lines.tsv
	cut -f 1,2,3 "$<" | tail --lines +2  > "$@.left.tmp"
	cut -f 4 "$<" | tail --lines +2 | lingua-cli --minlength 20 --confidence 0.6 -n -l nl,en,fr,de,la,it,pt,es,da,id > "$@.right.tmp"
	echo -e "inv_nr	page_no	line_id	lang	confidence	line_text" > "$@"
	paste "$@.left.tmp" "$@.right.tmp" >> "$@"
	rm "$@.left.tmp" "$@.right.tmp"

lists: lines 
	-rm *.lst
	cat *-lines.lang.tsv | awk -F "\t" '{ if ($$4 != "lang") print $$6 >> $$4".lst" }'

stats: lines lists
	wc -l *.lst | tee $@

%-pages.lang.tsv: %-lines.lang.tsv
	python classify_pages.py $< > $@

nondutch.pages.tsv: pages
	echo -e "inv_nr	page_no	lang	score" > "$@"
	cat *-pages.lang.tsv | awk -F "\t" '{ if ($$3 != "nl" && $$3 != "lang") print $$0 }' >> $@

dist: globalise-langdetect.tar.xz

%.top100tokens.lst: %.lst
	cat $< | sed 's/ /\n/g' | sort | uniq -c | sort -rn | head -n 100 > $@

globalise-langdetect.tar.xz: stats nondutch.pages.tsv
	tar -cvJf globalize-langdetect.tar.xz *.lang.tsv *.pages.tsv nondutch.pages.tsv *.lst stats
