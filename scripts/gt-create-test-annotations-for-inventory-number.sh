#!/usr/bin/env bash

# create transcriptions and entries annotation pages for all the pagexml files in the given inv_nr

inv_nr=$1
poetry run ./scripts/gt_ner_xmi_to_wa.py \
  --pagexml-dir ~/c/data/globalise/pagexml \
  --xmi-dir .local/new \
  --type-system=data/typesystem.xml \
  --output-dir=out \
  --text-repo=https://globalise.tt.di.huc.knaw.nl/textrepo \
  --api-key=${TEXTREPO_API_KEY} \
  --inv-nr=${inv_nr}
for t in out/${inv_nr}/NL*txt; do
  base=$(basename $t|sed -e 's/.txt//')
  poetry run ./scripts/gt-generate-transcription-annotation-pages.py \
    -o out/${inv_nr}/transcriptions \
    -p ~/c/data/globalise/pagexml/${inv_nr}/${base}.xml \
    -t out/${inv_nr}/${base}.txt
done
poetry run ./scripts/gt-group-to-annotation-page.py out/${inv_nr}/ner-annotations.json