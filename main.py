import sys
import json
import math
import urllib.request
import bs4
import sys
from collections import defaultdict

from googleapiclient.discovery import build

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

def main():
    if len(sys.argv) < 9:
        print('Required input format: python3 project2.py [-spanbert|-gpt3] <google api key> <google engine id> <openai secret key> <r> <t> <q> <k>')
        return

    OPTION = sys.argv[1]
    if OPTION != '-spanbert' or OPTION != '-gpt3':
        print('Required input format: python3 project2.py [-spanbert|-gpt3] <google api key> <google engine id> <openai secret key> <r> <t> <q> <k>')
        return 0
    
    GOOGLE_API_KEY = sys.argv[2]
    GOOGLE_ENGINE_ID = sys.argv[3]
    OPEN_AI_KEY = sys.argv[4]
    R = sys.argv[5]
    if R < 1 or R > 4:
        print('r has to be between 1 and 4')
        return 0
    T = sys.argv[6]
    if T < 0 or T > 1:
        print('t has to be between 0 and 1')
        return 0
    Q = sys.argv[7].split()
    K = sys.argv[8]
    if K < 0:
        print('k has to be greater than 0')
        return 0
    
    # Initialize X, the set of extracted tuples, as the empty set.
    X = []

    # Query your Google Custom Search Engine to obtain the URLs for the top-10 webpages for query q
    def run_query(words):
        # Make search API call
        items = get_google_search_items(GOOGLE_API_KEY, GOOGLE_ENGINE_ID, Q)

        # Format items to desired output
        output = get_formatted_items(items)
    
    
    return 0

if __name__ == "__main__":
    main()