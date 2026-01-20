#!/usr/bin/env bash

# create transcriptions and entries annotation pages for all the pagexml files in the given inv_nr
ZIPDIR=~/c/data/globalise
PAGEXMLDIR=work/pagexml
XMIDIR=work/xmi
OUT=work

inv_nr=$1

extract-word-offsets() {
  echo "1/4: extract word offsets"
  poetry run ./scripts/gt-extract-htr-word-offsets.py \
    --output-dir $OUT/${inv_nr}/htr-word-offsets \
    $PAGEXMLDIR/${inv_nr}/NL*.xml
}

generate-web-annotations() {
  echo "2/4: generate entity web annotations"
  poetry run ./scripts/gt_ner_xmi_to_wa.py \
    --pagexml-dir      $PAGEXMLDIR \
    --xmi-dir          $XMIDIR \
    --word-offsets-dir $OUT/${inv_nr}/htr-word-offsets \
    --manifests-dir    /Users/bram/workspaces/globalise/manifests/inventories \
    --type-system      data/typesystem.xml \
    --output-dir       $OUT \
    --inv-nr           ${inv_nr}
}

group-to-annotation-page() {
  ## group web annotations to annotation pages
  echo "3/4: group ner annotations to annotation pages"
  poetry run ./scripts/gt-group-to-annotation-page.py $OUT/${inv_nr}/ner-annotations.json
}

generate-transcription-annotation-pages() {
  echo "4/4: generate transcription annotation pages"
  for t in $OUT/${inv_nr}/NL*.txt; do
    base=$(basename $t|sed -e 's/.txt//')
    poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
      --pagexml    $PAGEXMLDIR/${inv_nr}/${base}.xml \
      --pagetext   $OUT/${inv_nr}/${base}.txt \
      --output-dir $OUT/${inv_nr}/transcriptions &
  done
  wait
}

if ! [[ -d $PAGEXMLDIR/${inv_nr} ]]; then
  mkdir -p $PAGEXMLDIR
  unzip $ZIPDIR/pagexml/${inv_nr}.zip -d $PAGEXMLDIR
fi

if ! [[ -d $XMIDIR/${inv_nr} ]]; then
  mkdir -p $XMIDIR
  unzip $ZIPDIR/xmicas/${inv_nr}.zip -d $XMIDIR
fi

time extract-word-offsets && \
time generate-web-annotations && \
time group-to-annotation-page && \
time generate-transcription-annotation-pages && \
echo "done!"
