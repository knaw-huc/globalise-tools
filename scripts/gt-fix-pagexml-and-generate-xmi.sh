#!/usr/bin/env bash
INV=$1
INDIR=~/c/data/globalise/pagexml/$INV
OUTDIR=out-local/fixed-pagexml/$INV
md $OUTDIR
cp $INDIR/*xml $OUTDIR
poetry run ./scripts/gt_fix_reading_order2.py -i ~/c/data/globalise/pagexml -o $OUTDIR $INV