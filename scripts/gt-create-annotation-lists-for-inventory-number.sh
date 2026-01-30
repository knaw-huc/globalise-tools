#!/usr/bin/env bash

# create transcriptions and entries annotation pages for all the pagexml files in the given inv_nr
ZIPDIR=~/c/data/globalise
PAGEXMLDIR=work/pagexml
XMIDIR=work/xmi
MANIFESTDIR=/Users/bram/workspaces/globalise/manifests/inventories
OUT=work
COMMIT=2026.01.30
inv_nr=$1

extract-word-offsets() {
  echo "1/5: extract word offsets"
  poetry run ./scripts/gt-extract-htr-word-offsets.py \
    --output-dir $OUT/${inv_nr}/htr-word-offsets \
    $PAGEXMLDIR/${inv_nr}/NL*.xml
}

generate-web-annotations() {
  echo "2/5: generate entity web annotations"
  poetry run ./scripts/gt_ner_xmi_to_wa.py \
    --git-commit       $COMMIT \
    --pagexml-dir      $PAGEXMLDIR \
    --xmi-dir          $XMIDIR \
    --word-offsets-dir $OUT/${inv_nr}/htr-word-offsets \
    --manifests-dir    $MANIFESTDIR \
    --type-system      data/typesystem.xml \
    --output-dir       $OUT \
    --inv-nr           ${inv_nr}
}

group-to-annotation-page() {
  ## group web annotations to annotation pages
  echo "3/5: group ner annotations to annotation pages"
  poetry run ./scripts/gt-group-to-annotation-page.py \
    --git-commit       $COMMIT \
    --manifests-dir $MANIFESTDIR \
    $OUT/${inv_nr}/ner-annotations.json
}

generate-transcription-annotation-pages() {
  echo "4/5: generate transcription annotation pages"
  for t in $OUT/${inv_nr}/NL*.txt; do
    base=$(basename $t .txt)
    poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
      --git-commit       $COMMIT \
      --pagexml    $PAGEXMLDIR/${inv_nr}/${base}.xml \
      --pagetext   $OUT/${inv_nr}/${base}.txt \
      --output-dir $OUT/${inv_nr}/transcriptions &
  done
  wait
}

zip-annotation-pages() {
  echo "5/5: zip annotation pages"
  mkdir -p $OUT/annotationlists
  zip=${inv_nr}-annotation-lists.zip
  (cd $OUT/${inv_nr} && zip -q ../annotationlists/$zip {entities,transcriptions}/*.json) && \
  sshpass -e scp -P 2222 $OUT/annotationlists/$zip bramb@hucdrive.huc.knaw.nl:/annotationlists/ && \
  rm -rf $OUT/annotationlists/$zip $PAGEXMLDIR/${inv_nr} && \
  echo $inv_nr >>$OUT/inv_done.lst
}

echo "conversion of ${inv_nr} starting at:"
date

if ! [[ -d $PAGEXMLDIR/${inv_nr} ]]; then
  mkdir -p $PAGEXMLDIR
  unzip -q $ZIPDIR/pagexml/${inv_nr}.zip -d $PAGEXMLDIR
fi

if ! [[ -d $XMIDIR/${inv_nr} ]]; then
  mkdir -p $XMIDIR
  unzip -q $ZIPDIR/xmicas/${inv_nr}.zip -d $XMIDIR
fi

time extract-word-offsets && \
time generate-web-annotations && \
time group-to-annotation-page && \
time generate-transcription-annotation-pages && \
zip-annotation-pages && \
echo "conversion finished at:"
date
