#!/usr/bin/env bash

extract_example_annotation() {
    type=$1
    num=$2
    echo "=> .local/3598/$type.json"
    jq -s ".[] | select(.id==\"urn:example:globalise:annotation:NL-HaNA_1.04.02_3598_$num\")" .local/3598.json > .local/3598/$type.json
    sleep 15s
    echo "jsonld2ttl .local/3598/$type.json > .local/3598/$type.ttl"
    echo "=> .local/3598/$type.ttl"
    jsonld2ttl .local/3598/$type.json > .local/3598/$type.ttl
}

echo "extracting annotations for 3598:"
jq -c '.[] | select(.id | startswith("urn:example:globalise:annotation:NL-HaNA_1.04.02_3598_") )' out/3598/ner-annotations.json > .local/3598.json
extract_example_annotation cmty_name 0797:287
extract_example_annotation cmty_qual 0797:285
extract_example_annotation cmty_quant 0797:313
extract_example_annotation date 0797:270
extract_example_annotation doc 0797:272
extract_example_annotation eth_rel 0797:298
extract_example_annotation loc_adj 0797:301
extract_example_annotation loc_name 0797:273
extract_example_annotation org 0013:191
extract_example_annotation per_attr 0797:283
extract_example_annotation per_name 0797:280
extract_example_annotation prf 0015:179
extract_example_annotation ship 0797:282
extract_example_annotation ship_type 0797:281
extract_example_annotation status 0797:296
