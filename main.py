import sys
import urllib.request
import bs4
import sys
from collections import defaultdict
import spacy
import spanbert as span
import spacy_help_functions as sp
from googleapiclient.discovery import build
import openai
import re
import time

# max webpages
MAX_ITEMS = 10
# entities of interest
ENTS = ['ORG', 'PERSON', 'LOC', 'GPE', 'DATE']

RELATION_TEXT_MAPPING = {
    'Schools_Attended' : 'per:schools_attended',
    'Work_For' : 'per:employee_of',
    'Live_In' : 'per:cities_of_residence',
    'Top_Member_Employees' : 'org:top_members/employees'
}

R_INT_MAPPING = {
    1 : 'Schools_Attended',
    2 : 'Work_For',
    3 : 'Live_In',
    4 : 'Top_Member_Employees'
}

# searches google and returns the top 10 webpages
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

# formats the webpages into dictionary
def get_formatted_items(items):
    def get_attr(item):
        return {'title': item['title'], 'url': item['link'], 'description': item['snippet']}
    return [get_attr(i) for i in items]

# scrape the webpage and return the plaintext
def get_website(url):
    # try to open the url
    try:
        r = urllib.request.urlopen(url)
        html = r.read()
    except urllib.error.HTTPError as e:
        print('Website could not be opened, moving on to next one.\n')
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

def run_spanbert(examples, T, spanbert_model, R):
    # Initialize return dictionary
    res = defaultdict(int)

    preds = spanbert_model.predict(examples)

    # taken from spacy_help_functions
    # retrieves spanbert entity pairs
    l = list(zip(examples, preds))
    for ex, pred in l:
        relation = pred[0]
        if relation == 'no_relation':
            continue
        if relation != RELATION_TEXT_MAPPING[R_INT_MAPPING[R]]:
            continue
        print("\n\t\t=== Extracted Relation ===")
        print("\t\tInput Tokens: {}".format(ex['tokens']))
        subj = ex["subj"][0]
        obj = ex["obj"][0]
        confidence = pred[1]
        print("\t\tOutput Confidence: {:.6f} ; Subject: {} ; Object: {}".format(confidence, subj, obj))
        if confidence > T:
            if res[(subj, relation, obj)] < confidence:
                res[(subj, relation, obj)] = confidence
                print("\t\tAdding to set of extracted relations")
            else:
                print("\t\tDuplicate with lower confidence than existing record. Ignoring this.")
        else:
            print("\t\tConfidence is lower than threshold confidence. Ignoring this.")
        print("\t\t==========\n")
    return res, len(l)

# TODO
def get_openai_completion(prompt, model, max_tokens, temperature = 0.2, top_p = 1, frequency_penalty = 0, presence_penalty =0):
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    response_text = response['choices'][0]['text']
    return response_text

def run_gpt3(sentence, valid_relation):
    print("\n\t\t=== Extracted Relation ===")
    print("\t\tSentence: {}".format(sentence))

    prompt_text = '''
                    Given a sentence, extract all the valid relations between nouns in tuple format (subject, relation, object).
                    If the relation is Schools_Attended, use format (person, Schools_Attended, institution).
                    If the relation is Work_For, use format (employee, Work_For, organization).
                    If the relation is Live_In, use format (resident, Live_In, place).
                    If the relation is Top_Member_Employees, use format (employee, Top_Member_Employees, organization).
                    Avoid generic pronouns.
                    valid relations: {}
                    sentence: {}
                    extracted: 
                    '''.format(valid_relation, sentence)

    model = 'text-davinci-003'
    max_tokens = 100
    temperature = 0.2
    top_p = 1
    frequency_penalty = 0
    presence_penalty = 0

    response_text = get_openai_completion(prompt_text, model, max_tokens, temperature, top_p, frequency_penalty, presence_penalty)
    
    # (Bill Gates, Schools_Attended), (Bill Gates, Work_For, Microsoft), (John Smith, Work_For, Microsoft), (Bill Gates, Top_Member_Employees, Microsoft), (John Smith, Top_Member_Employees, Microsoft)
    tuple_strs = re.split(r',\s*(?![^()]*\))', response_text)
    tuples = [tuple(s.replace('(', '').replace(')', '').split(',')) for s in tuple_strs]

    result = {}

    # transform data to output
    for t in tuples:
        if len(t) < 3:
            continue
        if not RELATION_TEXT_MAPPING.get(t[1].strip()):
            continue

        relation = RELATION_TEXT_MAPPING.get(t[1].strip())
        new_tup = (t[0].strip(), relation, t[2].strip())

        print("\t\tSubject: {} ; Object: {} ;".format(new_tup[0], new_tup[2]))

        if result.get(new_tup):
            print("\t\tDuplicate. Ignoring this.")
            continue

        print("\t\tAdding to set of extracted relations")
        print("\t\t==========\n")
        result[new_tup] = 1.0

    return result, len(tuples)

# extract the relations for a webpage via spanbert
def extract(text, R, T, OPTION, spanbert_model, nlp, valid_relation):
    res = defaultdict(int)
    # Set entities of interest
    if R in [1, 2, 4]:
        entities_of_interest = ["PERSON", "ORGANIZATION"]
    else:
        entities_of_interest = ["PERSON", "LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]
    
    # Split plaintext into sentences and extract relations
    print('Annotating the webpage using spacy...')
    doc = nlp(text)

    print(
        '''
        Extracted {} sentences. Processing each sentence one by one to check for presence of right pair of named entity types; 
        if so, will run the second pipeline ...
        '''.format(len(list(doc.sents)))
        )

    # doc = nlp("Bill Gates stepped down as chairman of Microsoft in February 2014 and assumed a new post as technology adviser to support the newly appointed CEO Satya Nadella.")
    extracted_count = 0
    overall = 0
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
                if ep[1][1] == 'PERSON' and ep[2][1] in ["LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]:
                    examples.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})
                elif ep[2][1] == 'PERSON' and ep[1][1] in ["LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]:
                    examples.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})
            else:
                if ep[1][1] == 'ORGANIZATION' and ep[2][1] == 'PERSON':
                    examples.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})
                elif ep[2][1] == 'ORGANIZATION' and ep[1][1] == 'PERSON':
                    examples.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})

        # print("EXAMPLES: {}".format(examples))

        # if there are examples, find relations
        if examples:
            extracted_count = extracted_count + 1
            if OPTION == '-spanbert':
                r, total = run_spanbert(examples, T, spanbert_model, R)
                res.update(r)
            else:
                r, total = run_gpt3(sent.text, valid_relation)
                res.update(r)
                time.sleep(1.5)
            overall = overall + total
            
            # print('here')
            # print(examples)
        # otherwise go to next sentence
        else:
            continue
    
    print('Extracted annotations for  {}  out of total  {}  sentences'.format(extracted_count, len(list(doc.sents))))
    print('Relations extracted from this website: {} (Overall: {})'.format(len(res.keys()), overall))
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
    openai.api_key = OPEN_AI_KEY
    R = int(sys.argv[5])
    if R not in [1, 2, 3, 4]:
        print('r has to be an integer between 1 and 4')
        return 0
    T = float(sys.argv[6])
    if T < 0 or T > 1:
        print('t has to be between 0 and 1')
        return 0
    Q = sys.argv[7].split()
    K = int(sys.argv[8])
    if K <= 0:
        print('k has to be greater than 0')
        return 0
    
    # Initialize X, the set of extracted tuples, as the empty set.
    X = []
    # Initialize URLS so we can see if a url has already been opened
    URLS = []

    print(
            '''
            Parameters:
            Client key      = {}
            Engine key      = {}
            OpenAI key      = {}
            Method  = {}
            Relation        = {}
            Threshold       = {}
            Query           = {}
            # of Tuples     = {}
            Loading necessary libraries; This should take a minute or so ...)
            '''.format(
                GOOGLE_API_KEY,
                GOOGLE_ENGINE_ID,
                OPEN_AI_KEY,
                OPTION,
                R_INT_MAPPING.get(R),
                T,
                Q,
                K
            )
        )

    iteration = 0
    while True:
        print('=========== Iteration: {} - Query: {} ==========='.format(iteration, Q))
        iteration = iteration + 1
        res = defaultdict(int) 

        # Query your Google Custom Search Engine to obtain the URLs for the top-10 webpages for query q
        # Make search API call
        items = get_google_search_items(GOOGLE_API_KEY, GOOGLE_ENGINE_ID, Q)

        # Format items to desired output
        output = get_formatted_items(items)
        
        # Initialize spacy
        nlp = spacy.load("en_core_web_lg")

        if OPTION == '-spanbert':
            # Load spanbert model
            spanbert_model = span.SpanBERT("./pretrained_spanbert")
        else:
            spanbert_model = 0

        # Get text from each url
        url_num = 1
        for doc in output:
            print('URL ( {} / {}): {}'.format(url_num, len(output), doc))
            print('Fetching text from url ...')
            url = doc['url']

            url_num = url_num + 1

            # If url already seen, continue
            if url in URLS:
                continue
            else:
                # add url to URLS and get 10000 chars of text
                URLS.append(url)
                
                # print('1')
                plaintext = get_website(url)
                # print('2')
                # if url cannot be opened, go to next one
                if plaintext == 0:
                    continue
                if len(plaintext) > 10000:
                    print('Trimming webpage content from {} to 10000 characters'.format(len(plaintext)))
                    plaintext = plaintext[:10000]

                print('Webpage length (num characters): {}'.format(len(plaintext)))

                # split text into sentences and extract entities
                relations = extract(plaintext, R, T, OPTION, spanbert_model, nlp, R_INT_MAPPING.get(R))
                res.update(relations)

        # if res has at least K tuples, stop and return
        sorted_res = dict(reversed(sorted(res.items(), key=lambda x:x[1])))
        if len(res.items()) >= K or len(res.items()) == 0:
            break
        
        # Else continue loop
        # Take first item of dict and use as query
        top_tup = next(iter(sorted_res))
        Q = ' '.join(top_tup)


    print('================== ALL RELATIONS for {} ( {} ) ================='.format(RELATION_TEXT_MAPPING[R_INT_MAPPING[R]], len(sorted_res)))

    for tup, confidence in sorted_res.items():
        print('Confidence: {}            | Subject: {}              | Object: {}'.format(confidence, tup[0], tup[2]))
    print('Total # of iterations = {}'.format(iteration))
    return 0

if __name__ == "__main__":
    main()
