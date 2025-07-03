This is a pipeline for language detection on the Globalise HTR output.

The raw results are delivered in <https://github.com/globalise-huygens/language-identification-data> , where the methodology is also described in detail. An architecture schema is provided at the bottom of this readme.

## Usage

You will need a Linux/BSD/macOS system with `make`, `cargo`, `rustc` and a
recent enough `python3` (>= 3.12). On Ubuntu/Debian Linux this is accomplished with `apt
install make cargo python`.

First clone this git repository. Then from this directory, run the following to
check and install necessary dependencies. 

```
$ make setup
```

This will check necessary dependencies, create a Python virtual environment
with the globalise-tools, and compile and install
[lingua-cli](https://github.com/proycon/lingua-cli) and
[lexmatch](https://github.com/proycon/lexmatch) which are used for language detection.

Activate the Python virtual environment that was created in the above step: 

```
$ source env/bin/activate
```

Next, extract data from the globalise page XMLs as follows, pass the path where
your globalise page XMLs are (grouped in directories corresponding with
inventory numbers). This will create many `*-lines.tsv` files that will be the
input for the actual pipeline:

```
$ make fromxml 
```

You can pass the path where the PageXML files are extracted (as obtained from https://hdl.handle.net/10622/LVXSBW) by appending or prepending the following to the above command:

```
PAGEXML_PATH=/path/to/pagexml
```

It defaults to a `pagexml/` directory in the current working directory.

Then run the actual language detection pipeline as follows:

```
$ make all
```


**Note:** Processing may take a long time if done serially, it is therefore
strongly recommended to make use of multiple CPU cores by passing `-j 20`
(example for 20 cores) to `make` to speed up to process.

The main results will be in `pages.lang.tsv`, secondary results in
`nondutch-pages.lang.tsv` (everything that includes another language) and
`unknown-pages.lang.tsv` (everything that could not be identified).

## Docker

You can also run all of this in a docker container. First run `make docker` from the repository root directory (i.e. not this one!). Then copy and edit `docker.template.env` to set your paths. You can then run `make docker-run` from THIS directory, it will first run the `frompagexml` make target and then the `all` step. Alternatively, you can run `make docker-run-shell` to be dropped in an interactive shell so you can run these yourself.

## Architecture

```mermaid
%%{init: {"flowchart": {"htmlLabels": true}} }%%
flowchart TD
    pagexml@{ shape: docs, label: "Globalise PageXML input"}
    gt_extract_lines["gt-extract-lines<br>(extracts lines)"]
    gt_classify_language["gt-classify-language<br>(language classification per page/paragraph/region)"]

    pagexml --> gt_extract_lines --> lines_tsv

    lines_tsv@{ shape: docs, label: "*-lines.tsv<br><i>(Raw lines)</i>"}
    lines_lang_tsv@{ shape: docs, label: "*-lines.tsv<br><i>(Raw lines with language information)</i>"}

    lexicons@{ shape: docs, label: "Lexicons<br><i>(per-language)</i>"}
    lexicons --> lexmatch

    linguacli["<b>lingua-cli</b><br><i>(Language classification via built-in character n-gram models)</i>"]
    lexmatch["<b>lexmatch</b><br><i>(Language classification via lexicon lookup)</i>"]

    lines_tsv --> linguacli 
    lines_tsv --> lexmatch 
    linguacli  --> lines_lang_tsv
    lexmatch  --> lines_lang_tsv

    lines_lang_tsv --> gt_classify_language

    gt_classify_language --> pages_lang_tsv
    gt_classify_language --> nondutchpages_lang_tsv
    gt_classify_language --> unknownpages_lang_tsv


    pages_lang_tsv@{ shape: docs, label: "pages.lang.tsv<br>(pages that have dutch)"}
    nondutchpages_lang_tsv@{ shape: docs, label: "nondutch-pages.lang.tsv<br>(pages that have another language than dutch)"}
    unknownpages_lang_tsv@{ shape: docs, label: "unknown-pages.lang.tsv<br>(pages that could not be identified)"}

    subgraph intermediate_results
        direction LR
        pages_lang_tsv@{ shape: docs, label: "pages.lang.tsv<br>(pages that have dutch)"}
        nondutchpages_lang_tsv@{ shape: docs, label: "nondutch-pages.lang.tsv<br>(pages that have another language than dutch)"}
        unknownpages_lang_tsv@{ shape: docs, label: "unknown-pages.lang.tsv<br>(pages that could not be identified)"}
    end

    corrections_lang_tsv@{ shape: doc, label: "corrections.lang.tsv<br><i>Manual corrections (input)</i>"}

    gt_merge_manual_corrections["gt-merge-manual-corrections<br>(consolidates automatic output with manual corrections)"]

    corrections_lang_tsv --> gt_merge_manual_corrections
    pages_lang_tsv --> gt_merge_manual_corrections --> pages_withcorrections_lang_tsv
    nondutchpages_lang_tsv --> gt_merge_manual_corrections --> nondutchpages_withcorrections_lang_tsv
    unknownpages_lang_tsv --> gt_merge_manual_corrections --> unknownpages_withcorrections_lang_tsv

    subgraph final_results
        direction LR
        pages_withcorrections_lang_tsv@{ shape: docs, label: "pages.lang.tsv<br>(pages that have dutch)"}
        nondutchpages_withcorrections_lang_tsv@{ shape: docs, label: "nondutch-pages.lang.tsv<br>(pages that have another language than dutch)"}
        unknownpages_withcorrections_lang_tsv@{ shape: docs, label: "unknown-pages.lang.tsv<br>(pages that could not be identified)"}
    end
```

* Arrow follow data flow direction
* Rectangles represent processes
* All ``gt-*`` processes refer to globalise-tools, as provided by this repository


