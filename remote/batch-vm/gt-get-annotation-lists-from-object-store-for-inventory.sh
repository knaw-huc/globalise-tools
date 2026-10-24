#!/usr/bin/env bash

main(){
  inv=$1
  for a in transcriptions entities events; do
    mkdir -p work/$inv/$a
    s5cmd cp s3://globalise-data/annotations/$a/NL-HaNA_1.04.02_${inv}_* work/$inv/$a >/dev/null
    for f in work/$inv/$a/*.json; do
      mv $f $f.gz
    done
  done
}

main $1