import sys
import json
import math
import urllib.request
import bs4
import sys
from collections import defaultdict
import spacy
from SpanBERT import spanbert
from SpanBERT import spacy_help_functions as sp
from googleapiclient.discovery import build

MAX_ITEMS = 10

def get_google_search_items(api_key, engine_id, words):
    service = build(
        "customsearch", "v1", developerKey=api_key
    )

    res = (
        service.cse()
        .list(
            q=" ".join(words),
            cx=engine_id,
        )
        .execute()
    )

    # Get top ten items
    items = res['items'][:MAX_ITEMS]
    return items

def get_formatted_items(items):
    def get_attr(item):
        return {'title': item['title'], 'url': item['link'], 'description': item['snippet']}
    return [get_attr(i) for i in items]

def get_website(url):
    # try to open the url
    try:
        r = urllib.request.urlopen(url)
        html = r.read()
    except urllib.error.HTTPError as e:
        return 0
    # extract text and clean up newline/spaces
    soup = bs4.BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    # maybe look into taking off first few chars of text if its unneccessary
    return text

def extract(text):
    sentences = []
    relations = []
    # Initialize spacy
    nlp = spacy.load("en_core_web_lg")
    # Split plaintext into sentences
    doc = nlp(text)
    for sent in doc:
        print(sent)
        # sentences.append(sent.text)
        # print(sent.text)
        # # Extract entities
        # entity = nlp(sent.text)
        # for ent in entity.ents:
        #     relations.append([ent.text, ent.label_])
        #     # print(ent.text, ent.start_char, ent.end_char, ent.label_)
    return sentences, relations

def main():
    if len(sys.argv) < 9:
        print('Required input format: python3 project2.py [-spanbert|-gpt3] <google api key> <google engine id> <openai secret key> <r> <t> <q> <k>hi')
        return

    OPTION = sys.argv[1]
    if OPTION != '-spanbert' and OPTION != '-gpt3':
        print('Required input format: python3 project2.py [-spanbert|-gpt3] <google api key> <google engine id> <openai secret key> <r> <t> <q> <k>')
        return 0
    
    GOOGLE_API_KEY = sys.argv[2]
    GOOGLE_ENGINE_ID = sys.argv[3]
    OPEN_AI_KEY = sys.argv[4]
    R = float(sys.argv[5])
    if R not in [1, 2, 3, 4]:
        print('r has to be an integer between 1 and 4')
        return 0
    T = float(sys.argv[6])
    if T < 0 or T > 1:
        print('t has to be between 0 and 1')
        return 0
    Q = sys.argv[7].split()
    K = int(sys.argv[8])
    if K < 0:
        print('k has to be greater than 0')
        return 0
    
    # Initialize X, the set of extracted tuples, as the empty set.
    X = []
    # Initialize URLS so we can see if a url has already been opened
    URLS = []

    # TODO: make sure this part goes in a loop
    # Query your Google Custom Search Engine to obtain the URLs for the top-10 webpages for query q
    # Make search API call
    items = get_google_search_items(GOOGLE_API_KEY, GOOGLE_ENGINE_ID, Q)

    # Format items to desired output
    output = get_formatted_items(items)
    
    # Get text from each url
    for doc in output:
        url = doc['url']
        # If url already seen, continue
        if url in URLS:
            continue
        else:
            # add url to URLS and get 10000 chars of text
            URLS.append(url)
            plaintext = get_website(url)
            if plaintext == 0:
                continue
            if len(plaintext) > 10000:
                plaintext = plaintext[:10000]
            # split text into sentences and extract entities
            sentences, named_entities = extract(plaintext)
            break
    return 0

if __name__ == "__main__":
    main()