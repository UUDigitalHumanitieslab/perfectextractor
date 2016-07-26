# Time in Translation
*Extracting present perfects from a multilingual corpus*

This small set of scripts allows for extraction of present perfects from a POS-tagged, lemmatized and sentence-aligned multilingual corpus encoded in the [TEI format](http://www.tei-c.org/).
 
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

The last common issue with present perfects is that in e.g. Dutch, the present perfect might appear before the auxiliary verb in subordinate clauses. An example: 

    (6) Dat is de stad waar hij gewoond heeft. [lit. This is the city where he lived has]
    
The extraction script should take care of these four issues, and be able to have language-specific settings. 

## Implementation 

The extraction script (`extractor\prefectextractor.py`) is implemented using the [lxml XML toolkit](http://lxml.de/). 

The script looks for auxiliary verbs (using a [XPath expression](https://en.wikipedia.org/wiki/XPath)), and for each of these, 
it tries to find a past participle on the right hand side of the sentence (or left hand side in Dutch), allowing for words between the verbs, 
though this lookup stops at the occurrence of other verbs, punctuation and coordinating conjunctions.

The script allows for additional extraction of present perfect continuous forms. 

The script handles these by a list of verbs that use 'to be' as auxiliary. 
The function *get_ergative_verbs* in `extractor\wiktionary.py` extracts these verbs from [Wiktionary](https://en.wiktionary.org) for Dutch.
This function uses the [Requests: HTTP for Humans](http://docs.python-requests.org/) package.
For German, the list is compiled from https://deutsch.lingolia.com/en/grammar/verbs/sein-haben

## Dutch Parallel Corpus

The script has been tested with the [Dutch Parallel Corpus](http://www.kuleuven-kulak.be/DPC). 
This corpus consists of three languages: Dutch, French and English. 
The configuration for this corpus can be found in `config\dpc.cfg`.
An example document from this corpus is included in the `tests\data` directory.
