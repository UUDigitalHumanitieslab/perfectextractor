# time-in-translation
Retrieving present perfects from multilingual corpora

This small set of scripts allows for extraction of present perfects from a POS-tagged, sentence-aligned multilingual corpus encoded in the TEI format.
 
== Recognizing Present Perfects == 

In English, a present perfect is easily recognizable as has/have plus a past participle:

    (1) I have seen that movie twenty times.

The only difficulty in finding present perfects in English is that there might be words between the auxiliary verb 'to have' and the past participle: 

    (2) Nobody has ever climbed that mountain. 
    
In some languages (e.g. French), the present perfect can be formed with both 'to have' and 'to be'. 
The past participle governs which auxiliary verb is employed: 

    (3) J'ai vu quelque chose
    (4) Le garçon est sorti
    
The script handles these by a list of verbs that use 'to be' as auxiliary. 
The script ""retrieve_from_wiki.py"" extracts these verbs from wiktionary. 

== Dutch Parallel Corpus ==

The script has been tested with the Dutch Parallel Corpus (DPC). 
This corpus consists of three languages: Dutch, French and English.  
The configuration can be found in ""dpc.cfg"".
