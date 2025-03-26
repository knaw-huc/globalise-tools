# Globalise Query Expansion service

This contains the [configuration](all.config.toml) and [build files](Makefile)
for the query expansion service for Globalise, powered by 
[kweepeer](https://github.com/knaw-huc/kweepeer). An
internal test instance is deployed at <https://kweepeer.dev.huc.knaw.nl> (KNAW
VPN required).
 
The following modules are configured:

| ID                  | Name                           | Module Type   | Description & Source |
| ------------------- | ------------------------------ | ------------- | -------------------- |
| `inthistlex`        | INT Historisch Lexicon         | Lookup        | INT Historisch Lexicon (version 2022-02-04, note: the lexicon itself is not freely distributable, required permission from IVDNT and therefore not included in this repo) |
| `odwn`              | Open Dutch Wordnet             | Lookup      | Data from [Open Dutch Wordnet](https://github.com/cltl/OpenDutchWordnet) |
| `nl_voc_analiticcl` | NL VOC groundtruth lexicon     | Analiticcl    | Lexicon with frequency information extracted from ground-truth data of VOC archives. PageXML retrieved from <https://zenodo.org/records/6414086/files/VOC%20Ground%20truths%20of%20the%20trainingset%20in%20PAGE%20xml.7z?download=1>. See <https://zenodo.org/record/6414086> for context. In preprocessing, this data was tokenised with [ucto](https://github.com/LanguageMachines/ucto) and filtered by language (dutch) using [lingua-cli](https://github.com/proycon/lingua-cli). A lexicon with frequency information was extracted using [Colibri Core](https://github.com/proycon/colibri-core) with occurrence threshold >= 1. |
| `nl_voc_fst`  | NL VOC groundtruth lexicon           | FST    | Same lexicon as above (but without frequency information), levensthein distance 2. |
| `extracted_analiticcl` | Extracted Globalise lexicon (all t>1) | Analiticcl | Extracted lexicon with frequency information. This is data extracted from the entire globalise corpus (from the PageXMLs) after rudimentary tokenisation and dehyphenation, no language detection/filtering. A lexicon with frequency information was extracted using [Colibri Core](https://github.com/proycon/colibri-core) with occurrence threshold >= 2. |
| `extracted_fst` | Extracted Globalise lexicon (all t>1) | FST | Same source as above (but without frequency information). |
| `embeddings`    | Globalise Word Embeddings | FinalFusion | Semantic similarity using vector comparison on word embeddings trained on the same sources as above, using [finalfrontier](https://finalfusion.github.io/finalfrontier) |
| `beroepen`    | Beroepen | Lookup | Extracted from a temporary development version (20250326) of the [Occupations Thesaurus for Globalise](https://digitaalerfgoed.poolparty.biz/globalise/thesaurus), official version is still pending. Converted with [skos2variants](https://github.com/knaw-huc/skos2variants). |
