# PefectExtractor
*Extracting present perfects (and related forms) from parallel corpora*

This small set of scripts allows for extraction of present perfects (and related forms, like the recent past construction in French and Spanish) from part-of-speech-tagged, lemmatized and sentence-aligned parallel corpora encoded in XML.
 
## Recognizing Perfects 

In English, a present perfect is easily recognizable as has/have plus a past participle:

    (1) I have seen that movie twenty times.

However, one difficulty in finding present perfects in most languages is that there might be words between the auxiliary verb 'to have' and the past participle: 

    (2) Nobody has ever climbed that mountain.
     
In English, there is the additional problem of the present perfect continuous, which shares the first part of the construction with the present perfect: 

    (3) He has been waiting here for two hours.
    
In some languages (e.g. French/Dutch), the present perfect can be formed with both 'to have' and 'to be'. 
The past participle governs which auxiliary verb is used:

    (4) J'ai vu quelque chose [lit. I have seen something]
    (5) Elle est arrivé [lit. She is arrived]
    
For French, this is a closed list 
([DR and MRS P. VANDERTRAMP](https://en.wikipedia.org/wiki/Pass%C3%A9_compos%C3%A9#Auxiliary_.22.C3.8Atre.22)), 
but for other languages, this might be a more open class.

The last common issue with present perfects is that in e.g. Dutch and German, the present perfect might appear before the auxiliary verb in subordinate clauses. An example: 

    (6) Dat is de stad waar hij gewoond heeft. [lit. This is the city where he lived has]
    
The extraction script provided here takes care of these four issues, and can have language-specific settings. 

## Implementation 

The extraction script (`apps/extractor/perfectextractor.py`) is implemented using the [lxml XML toolkit](http://lxml.de/). 

The script looks for auxiliary verbs (using a [XPath expression](https://en.wikipedia.org/wiki/XPath)), and for each of these, 
it tries to find a past participle on the right hand side of the sentence (or left hand side in Dutch/German), allowing for words between the verbs, 
though this lookup stops at the occurrence of other verbs, punctuation and coordinating conjunctions.

The script also allows for extraction of present perfect continuous forms. 

The script handles these by a list of verbs that use 'to be' as auxiliary. 
The function *get_ergative_verbs* in `extractor/wiktionary.py` extracts these verbs from [Wiktionary](https://en.wiktionary.org) for Dutch.
This function uses the [Requests: HTTP for Humans](http://docs.python-requests.org/) package.
For German, the list is compiled from [this list](https://deutsch.lingolia.com/en/grammar/verbs/sein-haben).

### Implementing other extractors

More info on this later.

## Corpora

### Dutch Parallel Corpus

The extraction was first tested with the [Dutch Parallel Corpus](http://www.kuleuven-kulak.be/DPC).
This corpus (that uses the [TEI format](http://www.tei-c.org/)) consists of three languages: Dutch, French and English. 
The configuration for this corpus can be found in `corpora/dpc/dpc.cfg`.
Example documents from this corpus are included in the `tests/data/dpc` directory.
The data for this corpus is **closed source**, to retrieve the corpus, you'll have to contact the authors on the cited website.
After you've obtained the data, you can run the extraction script with:

    python extract.py <folder> en fr nl --corpus=dpc --extractor=perfect

### OPUS Corpora

The extraction has also been implemented for the OPUS Corpora, most notably the [Europarl Corpus](http://opus.lingfil.uu.se/Europarl.php).
This corpus (that uses the [XCES format](http://www.tei-c.org/) for alignment) consists of a wide variety of languages. 
The configuration for this corpus can be found in `corpora/europarl/europarl.cfg`: implementations have been made for Dutch, English, French, German and Spanish. 
Example documents from this corpus are included in the `tests/data/europarl` directory.
The data for this corpus is **open source**: you can download the corpus and the alignment files from the cited website.
After you've obtained the data, you can run the extraction script with:

    python extract.py <folder> en de es --corpus=europarl --extractor=perfect

### BNC Corpus

The extraction has also been implemented for the monolingual BNC Corpus.
The data for this corpus is **open source**: you can download the corpus from the cited website.
After you've obtained the data, you can run the extraction script with:

    python extract.py <folder> en --corpus=bnc --extractor=perfect

### Implementing your own corpus

If you want to implement the extraction for another corpus, you'll have to create: 

* An implementation of the corpus in the `extractor` directory (see `extractor/europarl_extractor` for an example).
* A configuration file in the `config` directory (see `config/europarl.cfg` for an example).
* An entry in the main script (see `extract.py`)

## Other options to the extraction script

You can view all options of the extraction script by typing:

    python extract.py --help

Do note that at this point in time, not all options are available in all corpora.
Feel free to send a pull request once you have implemented an option, or to request one by creating an issue. 

## Other scripts

### pick_alignments

This script allows to filter the alignment file based on (for example) a file prefix.
This is helpful in the case of large alignment files, as is e.g. the case for the Europarl corpus.
Example usage:

    python pick_alignments.py 

### merge_results

This script allows to merge results from various files.
Example usage:

    python merge_results.py 

### splitter

This script allows to split a big corpus into subparts and then to run the extractors.
Example usage:

    python splitter.py 

## Tests

The unit tests can be run using: 

    python -m unittest discover -b

A coverage report can be generated (after installing [coverage.py](https://coverage.readthedocs.io/en/coverage-4.2/)) using:

    coverage run --source . -m unittest discover -b
    coverage html

## Citing

If you happen to have used (parts of) this project for your research, please refer to this paper:

[van der Klis, M., Le Bruyn, B., de Swart, H. (2017)](http://www.aclweb.org/anthology/E17-2080). Mapping the Perfect via Translation Mining. *Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers* 2017, 497-502.
