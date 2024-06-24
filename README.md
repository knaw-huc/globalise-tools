# globalise-tools

tools for various globalise tasks

in `scripts/`:

### `gt-xmi-to-wa.py`

converts entity and event annotations in xmi files to web annotations

indicate the required typesystem file using the `-t` parameter

indicate the output directory using the `-o` parameter 

example usage: `poetry run ./scripts/gt-xmi-to-wa.py -t inception-exports/TypeSystem.xml -o out inception-exports/*xmi`
