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

if __name__ == "__main__":
    print get_translations('aantonen', 'nl', 'en')