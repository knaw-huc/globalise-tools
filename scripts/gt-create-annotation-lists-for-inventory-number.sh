#!/usr/bin/env bash

inv=$1
poetry run gt-create-annotation-lists-for-inventory-number \
  --pagexml-dir  work/pagexml/$inv \
  --xmi-dir      work/$inv/xmi \
  --output-dir   work/$inv \
  --git-commit   2026.08.04 \
  --manifest     data/manifests/$inv.json \
  --type-system  data/typesystem.xml \
  --event-mapping data/eventmapping.json \
  $inv