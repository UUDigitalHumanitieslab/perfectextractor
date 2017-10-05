# Time in Translation
*Extracting present perfects from a multilingual corpus*

This small set of scripts allows for extraction of present perfects from a POS-tagged, lemmatized and sentence-aligned multilingual corpus encoded in XML.
 
## Recognizing Present Perfects 

In English, a present perfect is easily recognizable as has/have plus a past participle:

    (1) I have seen that movie twenty times.

However, one difficulty in finding present perfects in most languages is that there might be words between the auxiliary verb 'to have' and the past participle: 

    (2) Nobody has ever climbed that mountain.
     
In English, there is the additional problem of the present perfect continuous, which shares the first part of the construction with the present perfect: 

    (3) He has been waiting here for two hours.
    
In some languages (e.g. French/Dutch), the present perfect can be formed with both 'to have' and 'to be'. 
The past participle governs which auxiliary verb is employed: 

    (4) J'ai vu quelque chose [lit. I have seen something]
    (5) Elle est arrivé [lit. She is arrived]
    
For French, this is a closed list 
([DR and MRS P. VANDERTRAMP](https://en.wikipedia.org/wiki/Pass%C3%A9_compos%C3%A9#Auxiliary_.22.C3.8Atre.22)), 
but for other languages, this might be a more open class.

The last common issue with present perfects is that in e.g. Dutch and German, the present perfect might appear before the auxiliary verb in subordinate clauses. An example: 

    (6) Dat is de stad waar hij gewoond heeft. [lit. This is the city where he lived has]
    
The extraction script should take care of these four issues, and be able to have language-specific settings. 

## Implementation 

The extraction script (`extractor/prefectextractor.py`) is implemented using the [lxml XML toolkit](http://lxml.de/). 

The script looks for auxiliary verbs (using a [XPath expression](https://en.wikipedia.org/wiki/XPath)), and for each of these, 
it tries to find a past participle on the right hand side of the sentence (or left hand side in Dutch/German), allowing for words between the verbs, 
though this lookup stops at the occurrence of other verbs, punctuation and coordinating conjunctions.

The script also allows for extraction of present perfect continuous forms. 

The script handles these by a list of verbs that use 'to be' as auxiliary. 
The function *get_ergative_verbs* in `extractor/wiktionary.py` extracts these verbs from [Wiktionary](https://en.wiktionary.org) for Dutch.
This function uses the [Requests: HTTP for Humans](http://docs.python-requests.org/) package.
For German, the list is compiled from [this list](https://deutsch.lingolia.com/en/grammar/verbs/sein-haben).

## Corpora

### Dutch Parallel Corpus

The extraction was first tested with the [Dutch Parallel Corpus](http://www.kuleuven-kulak.be/DPC).
This corpus (that uses the [TEI format](http://www.tei-c.org/)) consists of three languages: Dutch, French and English. 
The configuration for this corpus can be found in `config/dpc.cfg`.
Example documents from this corpus are included in the `tests/data/dpc` directory.
The data for this corpus is **closed source**, to retrieve the corpus, you'll have to contact the authors on the cited website.
After you've obtained the data, you can place these in the `data` directory, and then run:

    python run_dpc.py

### Europarl Corpus

The extraction has also been implemented for the [Europarl Corpus](http://opus.lingfil.uu.se/Europarl.php).
This corpus (that uses the [XCES format](http://www.tei-c.org/) for alignment) consists of a wide variety of languages. 
The configuration for this corpus can be found in `config/europarl.cfg`: implementations have been made for Dutch, English, French, German and Spanish. 
Example documents from this corpus are included in the `tests/data/europarl` directory.
The data for this corpus is **open source**: you can download the corpus and the alignment files from the cited website.
After you've obtained the data, you can place these in the `data` directory, and then run:

    python run_europarl.py

### Implementing your own corpus

If you want to implement the extraction for another corpus, you'll have to create: 

* An implementation of the `PerfectExtractor` in the `extractor` directory (see `extractor/europarl_extractor` for an example).
* A configuration file in the `config` directory (see `config/europarl.cfg` for an example).
* A main file in the main directory that creates the extractor and loops over the corpus files (see `run_europarl.py` for an example).

## Tests

The unit tests can be run using: 

    python -m unittest discover

A coverage report can be generated (after installing [coverage.py](https://coverage.readthedocs.io/en/coverage-4.2/)) using:

    coverage run --source . -m unittest discover
    coverage html
