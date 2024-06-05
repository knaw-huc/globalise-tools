.SHELLFLAGS = -o pipefail -c
.PHONY: deps
.DELETE_ON_ERROR:

input_tsv := $(wildcard *-lines.tsv)
output_tsv := $(input_tsv:%-lines.tsv=%-lines.lang.tsv)

all: $(output_tsv)

deps:
	cargo install lingua-cli

%-lines.lang.tsv: %-lines.tsv
	cut -f 1,2,3 "$<" | tail --lines +2  > "$@.left.tmp"
	cut -f 4 "$<" | tail --lines +2 | lingua-cli -n -l nl,en,fr,de,la,it,es > "$@.right.tmp"
	echo -e "inv_nr	page_no	line_id	lang	confidence	line_text" > "$@"
	paste "$@.left.tmp" "$@.right.tmp" >> "$@"
	rm "$@.left.tmp" "$@.right.tmp"
