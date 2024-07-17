This is a pipeline for language detection on the Globalise HTR output.

## Usage

You will need a Linux/BSD/macOS system with `make`, `cargo`, `rustc` and a
recent enough `python3`. On Ubuntu/Debian Linux this is accomplished with `apt
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
$ make fromxml PAGEXML_PATH=/path/to/globalise-pagexml
```

Then run the actual language detection pipeline as follows:

```
$ make all
```

**Note:** Processing may take a long time if done serially, it is therefore
strongly recommended to make use of multiple CPU cores by passing `-j 20`
(example for 20 cores) to `make` to speed up to process.

The main results will be in `pages.lang.tsv`, secondary results in
`nondutch-pages.lang.tsv`, `mixed-pages.lang.tsv` and `unknown-pages.lang.tsv`.
