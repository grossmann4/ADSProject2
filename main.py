import sys
import json
import math
import urllib.request
import bs4
import sys
from collections import defaultdict
import spacy
import spanbert as span
import spacy_help_functions as sp
from googleapiclient.discovery import build

MAX_ITEMS = 10
ENTS = ['ORG', 'PERSON', 'LOC', 'GPE', 'DATE']

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

def extract(text, R, T):
    res = defaultdict(int)
    # Set entities of interest
    if R in [1, 2, 4]:
        entities_of_interest = ["PERSON", "ORGANIZATION"]
    else:
        entities_of_interest = ["PERSON", "Location", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]

    # Initialize spacy
    nlp = spacy.load("en_core_web_lg")
    # Load spanbert model
    spanbert_model = span.SpanBERT("./pretrained_spanbert")

    # Split plaintext into sentences and extract relations
    # doc = nlp(text)
    doc = nlp("Bill Gates stepped down as chairman of Microsoft in February 2014 and assumed a new post as technology adviser to support the newly appointed CEO Satya Nadella.")

    for sent in doc.sents:
        # create entity pairs for each sentence
        ents = sp.create_entity_pairs(sent, entities_of_interest)
        # print("ENTS: {}".format(ents))
        # if there are no named entities, go to next sentence
        if not ents:
            continue
        
        # format the entity pairs and only add the desired entity pairs
        examples = []
        for ep in ents:
            if R in [1, 2]:
                if ep[1][1] == 'PERSON' and ep[2][1] == 'ORGANIZATION':
                    examples.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})
                elif ep[2][1] == 'PERSON' and ep[1][1] == 'ORGANIZATION':
                    examples.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})
            elif R == 3:
                if ep[1][1] == 'PERSON' and ep[2][1] in ["Location", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]:
                    examples.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})
                elif ep[2][1] == 'PERSON' and ep[1][1] in ["Location", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]:
                    examples.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})
            else:
                if ep[1][1] == 'ORGANIZATION' and ep[2][1] == 'PERSON':
                    examples.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})
                elif ep[2][1] == 'ORGANIZATION' and ep[1][1] == 'PERSON':
                    examples.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})
        # print("EXAMPLES: {}".format(examples))
        # run spanbert if there are relevant entity pairs
        if examples:
            preds = spanbert_model.predict(examples)
            print('here')
            print(examples)
        # otherwise go to next sentence
        else:
            continue

        # taken from spacy_help_functions
        # retrieves spanbert entity pairs
        for ex, pred in list(zip(examples, preds)):
            relation = pred[0]
            if relation == 'no_relation':
                continue
            print("\n\t\t=== Extracted Relation ===")
            print("\t\tTokens: {}".format(ex['tokens']))
            subj = ex["subj"][0]
            obj = ex["obj"][0]
            confidence = pred[1]
            print("\t\tRelation: {} (Confidence: {:.3f})\nSubject: {}\tObject: {}".format(relation, confidence, subj, obj))
            if confidence > T:
                if res[(subj, relation, obj)] < confidence:
                    res[(subj, relation, obj)] = confidence
                    print("\t\tAdding to set of extracted relations")
                else:
                    print("\t\tDuplicate with lower confidence than existing record. Ignoring this.")
            else:
                print("\t\tConfidence is lower than threshold confidence. Ignoring this.")
            print("\t\t==========")

    return res

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
            relations = extract(plaintext, R, T)
            print(relations)
            break
    return 0

if __name__ == "__main__":
    main()