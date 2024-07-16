This is a pipeline for language detection on the Globalise HTR output.

## Usage

Clone this git repository, from this directory, run the following to check and
install necessary dependencies.

```
$ make setup
```

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

The main results will be in `pages.lang.tsv`.
