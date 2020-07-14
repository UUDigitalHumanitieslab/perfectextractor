# PefectExtractor
*Extracting Perfects (and related forms) from parallel corpora*

This command-line application allows for extraction of Perfects (and related forms, like the Recent Past construction in French and Spanish) from part-of-speech-tagged, lemmatized and sentence-aligned parallel corpora encoded in XML.
 
## Recognizing Perfects 

In English, a *present perfect* is easily recognizable as a present form of *to have* plus a past participle, like in (1):

    (1) I have seen that movie twenty times.

However, one difficulty in finding Perfects in most languages is that there might be words between the auxiliary and the past participle, like in (2):

    (2) Nobody has ever climbed that mountain.

Furthermore, languages have passive forms that generally require the past participle of *to be* to be interjected, like in (3):

    (3) The bill has been paid by John.
     
In English, there is the additional issue of the *present perfect continuous*, which in form shares the first part of the construction with the *present perfect*, like in (4):

    (4) He has been waiting here for two hours.
    
In some languages (e.g. French, German, and Dutch), the Perfect can be formed with both Have and Be. 
The past participle governs which auxiliary verb is used, as (5) and (6) show.

    (5) J'ai vu quelque chose [lit. I have seen some thing]
    (6) Elle est arrivé [lit. She is arrived]
    
For French, this is a closed list 
([DR and MRS P. VANDERTRAMP](https://en.wikipedia.org/wiki/Pass%C3%A9_compos%C3%A9#Auxiliary_.22.C3.8Atre.22)), 
but for other languages, this might be a more open class.

The last common issue with finding Perfects is that in e.g. Dutch and German, the Perfect might appear before the auxiliary verb in subordinate clauses. (7) is an example: 

    (7) Dat is de stad waar hij gewoond heeft. [lit. This is the city where he lived has]
    
The extraction script provided here takes care of all these issues, and can have language-specific settings. 

### Implementation 

The extraction script (`apps/extractor/perfectextractor.py`) is implemented using the [lxml XML toolkit](http://lxml.de/). 

The script looks for auxiliary verbs (using a [XPath expression](https://en.wikipedia.org/wiki/XPath)), and for each of these, 
it tries to find a past participle on the right hand side of the sentence (or left hand side in Dutch/German), allowing for words between the verbs, 
though this lookup stops at the occurrence of other verbs, punctuation and coordinating conjunctions.

The script also allows for extraction of *present perfect continuous* forms. 

The script handles these by a list of verbs that use Be as auxiliary. 
The function *get_ergative_verbs* in `extractor/wiktionary.py` extracts these verbs from [Wiktionary](https://en.wiktionary.org) for Dutch.
This function uses the [Requests: HTTP for Humans](http://docs.python-requests.org/) package.
For German, the list is compiled from [this list](https://deutsch.lingolia.com/en/grammar/verbs/sein-haben).

## Recognizing Recent Pasts

Most Romance languages share a grammaticalized construction to refer to events in the recent past, e.g. the *passé récent* in French and the *pasado reciente* in Spanish.
In English, typically a *present perfect* alongside the adverb *just* is used to convey this meaning, commonly referred to as *perfect of recent past* (Comrie 1985) or *hot news perfect* (McCawley 1971).

The French *passé récent* is formed with a present tense of *venir* 'come' followed by the particle *de* and an infinitive, as in (8) below.
 
    (8) Je viens de voir Marie. [lit. I come DE see Mary] 
    
The Spanish *pasado reciente* is (quite similarly) formed with a present tense of *acabar* 'finish' followed by the particle *de* and an infinitive, as in (9) below.

    (9) Acabo de ver a María. [lit. I finish DE see Mary]

The extraction script (`apps/extractor/recentpastextractor.py`) provided here allows export of these constructions from parallel corpora.  

## Other extractors

This application also allows extraction from parallel corpora based on part-of-speech tags or regexes. 

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

The extraction has also been implemented for the open parallel corpus [OPUS](http://opus.nlpl.eu/), that contains most notably the [Europarl Corpus](http://opus.nlpl.eu/Europarl.php) and the [OpenSubtitles Corpus](http://opus.nlpl.eu/OpenSubtitles.php).
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

* An implementation of the corpus in the `corpora` directory (see `corpora/europarl` for an example).
* A configuration file in this directory (see `corpora/europarl/europarl.cfg` for an example).
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
