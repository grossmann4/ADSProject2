# ADS Project 2

## Names and Unis
* Ryan Grossmann (rg3398)
* Matthew Bu (mb4753)

## Files
* download_finetuned.sh - shell script to download fine tuned SpanBERT classifier
* example_relations.py - example code for relation extraction
* main.py - main python file responsible for performing the relation extraction
* spacy_help_functions.py - helper functions for extracting relations
* spanbert.py - file used to run SpanBERT classifier
* /pytorch_pretrained_bert - files necessary to run SpanBERT classifier
* requirements.txt - python modules required to run main.py

## How To Run
* pip3 install -r requirements.txt
* bash download_finetuned.sh
* python3 main.py [-spanbert|-gpt3] <google api key> <google engine id> <openai secret key> <r> <t> <q> <k>

## Internal Design
* Libraries:
    * sys - for getting the program's input parameters
    * urllib.request - for opening webpage urls
    * bs4 - for parsing the webpage text
    * defaultdict - for using python dictionaries
    * spacy - for sentence and named entity identification
    * spanbert - for spanbert classifier
    * spacy_help_functions - for relation extraction
    * googleapiclient - for running google searches
    * openai - for running gpt3 queries
* Functions:
    * def get_google_search_items(api_key, engine_id, words): for searching google and getting the top ten results
    * def get_formatted_items(items): formatting the webpages into a dictionary
    * def get_website(url): scrape the webpage for the plaintext
    * def run_spanbert(examples, T, spanbert_model): run the spanbert classifier over 

testing: python3 main.py -spanbert AIzaSyBh546gYpsBnKcTEdBi-jagSb9gEIoRj6s fb8c9f64780d3213f openai 2 0.4 "milky way" 2
