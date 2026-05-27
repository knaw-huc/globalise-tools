#!/usr/bin/env bash

inv=$1
wd=work/$inv
mkdir $wd
(cd $wd && unzip ../annotation-lists/$inv-annotation-lists.zip)
poetry run scripts/gt_make_annotate_filter_input.py $inv
rm -rf $wd/{entities,transcriptions,entity-tags.tsv}
