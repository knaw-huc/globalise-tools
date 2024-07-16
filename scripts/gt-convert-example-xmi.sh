#!/usr/bin/env bash
find ~/workspaces/globalise/globalise-web-annotation-examples -iname "*.xmi" | while read -r f; do
  poetry run ./scripts/gt_xmi_to_wa.py -t inception-exports/TypeSystem.xml -o ~/workspaces/globalise/globalise-web-annotation-examples "$f"
  echo
done
cd ~/workspaces/globalise/globalise-web-annotation-examples && (\
  for d in [1-9]*; do
    mv *$d*.* "$d"/
  done
  for j in */*.json; do
    ~/workspaces/golden-agents/golden-agents-htr/scripts/jsonld-to-graph.py -v http://undefined.com $j > "${j/json/ttl}"
  done
)