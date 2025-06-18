#!/usr/bin/env bash
INV=$1
INDIR=~/c/data/globalise/pagexml/$INV
OUTDIR=out-local/fixed-pagexml/$INV
mkdir -p $OUTDIR
cp -a $INDIR/*xml $OUTDIR
poetry run ./scripts/gt_fix_reading_order2.py -i out-local/fixed-pagexml -o $OUTDIR $INV
poetry run ./scripts/gt-pagexml-to-uima-cas.py -o $OUTDIR $OUTDIR/*.xml
chmod a-x $OUTDIR/*.xm?
(cd out-local/fixed-pagexml && zip -qr $INV-pagexml.zip $INV/*.xml && zip -qr $INV-xmi.zip $INV/*.xmi)