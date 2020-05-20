import codecs
import requests


def get_translations(word, language_from, language_to):
    results = []

    params = dict({'action': 'query', 'prop': 'iwlinks', 'titles': word, 'iwprefix': language_to, 'format': 'json'})

    r = requests.get('https://' + language_from + '.wiktionary.org/w/api.php', params=params)
    j = r.json()
    for page in j['query']['pages'].values():
        if 'iwlinks' in page:
            for link in page['iwlinks']:
                results.append(link['*'])

    return results


def get_ergative_verbs():
    title = 'Category:Ergatief_werkwoord_in_het_Nederlands'
    with codecs.open('../data/nl_aux_be.txt', 'w', 'utf-8') as f:
        continue_url = ''

        params = dict({'action': 'query', 'list': 'categorymembers', 'cmtitle': title, 'format': 'json'})
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


if __name__ == "__main__":
    get_ergative_verbs()
