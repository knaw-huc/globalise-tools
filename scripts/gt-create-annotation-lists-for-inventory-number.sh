#!/usr/bin/env bash

inv=$1
poetry run ./scripts/gt-create-annotation-lists-for-inventory-number.py \
  --pagexml-dir  work/pagexml/$inv \
  --xmi-dir      work/xmi/$inv \
  --output-dir   work/$inv \
  --git-commit   2026.02.13 \
  --manifest     data/manifests/$inv.json \
  --type-system  data/typesystem.xml \
  $inv