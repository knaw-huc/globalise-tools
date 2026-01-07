#!/usr/bin/env bash

# create transcriptions and entries annotation pages for all the pagexml files in the given inv_nr
ZIPDIR=~/c/data/globalise
PAGEXMLDIR=work/pagexml
XMIDIR=work/xmi
OUT=work

inv_nr=$1

if ! [[ -d $PAGEXMLDIR/${inv_nr} ]]; then
  mkdir -p $PAGEXMLDIR
  unzip $ZIPDIR/pagexml/${inv_nr}.zip -d $PAGEXMLDIR
fi

if ! [[ -d $XMIDIR/${inv_nr} ]]; then
  mkdir -p $XMIDIR
  unzip $ZIPDIR/xmicas/${inv_nr}.zip -d $XMIDIR
fi

# extract word offsets
for t in $PAGEXMLDIR/${inv_nr}/NL*.xml; do
  base=$(basename $t|sed -e 's/.xml//')
  poetry run ./scripts/gt-extract-htr-word-offsets.py \
    --pagexml    $PAGEXMLDIR/${inv_nr}/${base}.xml \
    --output-dir $OUT/${inv_nr}/htr-word-offsets
done

# generate wwb annotations
poetry run ./scripts/gt_ner_xmi_to_wa.py \
  --pagexml-dir      $PAGEXMLDIR \
  --xmi-dir          $XMIDIR \
  --word-offsets-dir $OUT/${inv_nr}/htr-word-offsets \
  --type-system      data/typesystem.xml \
  --output-dir       $OUT \
  --text-repo        https://globalise.tt.di.huc.knaw.nl/textrepo \
  --api-key          ${TEXTREPO_API_KEY} \
  --inv-nr           ${inv_nr}

# generate transcription annotation pages
for t in $OUT/${inv_nr}/NL*.txt; do
  base=$(basename $t|sed -e 's/.txt//')
  poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
    --pagexml    $PAGEXMLDIR/${inv_nr}/${base}.xml \
    --pagetext   $OUT/${inv_nr}/${base}.txt \
    --output-dir $OUT/${inv_nr}/transcriptions
done

# group web annotations to annotation pages
poetry run ./scripts/gt-group-to-annotation-page.py $OUT/${inv_nr}/ner-annotations.json