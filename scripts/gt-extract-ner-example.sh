#!/usr/bin/env bash

extract_example_annotation() {
    type=$1
    num=$2
#    echo jq -s ".[] | select(.id==\"urn:example:globalise:annotation:NL-HaNA_1.04.02_3598_0797:$num\")" .local/3598_0797.json
    echo "=> .local/3598_0797/$type.json"
    jq -s ".[] | select(.id==\"urn:example:globalise:annotation:NL-HaNA_1.04.02_3598_0797:$num\")" .local/3598_0797.json > .local/3598_0797/$type.json
    sleep 15s
    echo "jsonld2ttl .local/3598_0797/$type.json > .local/3598_0797/$type.ttl"
    echo "=> .local/3598_0797/$type.ttl"
    jsonld2ttl .local/3598_0797/$type.json > .local/3598_0797/$type.ttl
}

echo "extracting annotations for 3598_0797:"
jq -c '.[] | select(.id | startswith("urn:example:globalise:annotation:NL-HaNA_1.04.02_3598_0797:") )' out/3598/ner-annotations.json > .local/3598_0797.json
extract_example_annotation cmty_name 287
extract_example_annotation cmty_qual 285
extract_example_annotation cmty_quant 313
extract_example_annotation date 270
extract_example_annotation doc 272
extract_example_annotation eth_rel 298
extract_example_annotation loc_adj 301
extract_example_annotation loc_name 273
#extract_example_annotation org 373
extract_example_annotation per_attr 283
extract_example_annotation per_name 280
#extract_example_annotation prf 378
extract_example_annotation ship 282
extract_example_annotation ship_type 282
extract_example_annotation status 296
