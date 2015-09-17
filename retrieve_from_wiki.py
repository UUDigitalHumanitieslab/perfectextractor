import codecs
import requests

TITLE = 'Category:Ergatief_werkwoord_in_het_Nederlands'

with codecs.open('data/nl_aux_be.txt', 'wb', 'utf-8') as f:
    continue_url = ''

    params = dict({'action': 'query', 'list': 'categorymembers', 'cmtitle': TITLE, 'format': 'json'})
    while True:
        params['cmcontinue'] = continue_url

        r = requests.get('https://nl.wiktionary.org/w/api.php', params=params)
        j = r.json()
        for member in j['query']['categorymembers']:
            f.write(member['title'] + '\n')

        # Continue to next URL
        if 'continue' not in j:
            break
        continue_url = j['continue']['cmcontinue']
