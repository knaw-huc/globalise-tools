#!/usr/bin/env bash

inv=$1

for f in work/$inv/{document.txt,entity-tags.json} ; do
  gzip --force $f
done

s5cmd cp --content-type "text/plain;charset=UTF-8" --content-encoding "gzip" "work/$inv/document.txt.gz" s3://globalise-data/objects/inventory/$inv.txt > /dev/null
echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$inv.txt"
s5cmd cp --content-type "application/json" --content-encoding "gzip" "work/$inv/entity-tags.json.gz" s3://globalise-data/objects/inventory/$inv.index.json > /dev/null
echo "Uploaded: https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:$inv.index"
