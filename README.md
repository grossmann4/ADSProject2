# ADS Project 2

## Names and Unis
* Ryan Grossmann (rg3398)
* Matthew Bu (mb4753)

## Files
* download_finetuned.sh - shell script to download fine tuned SpanBERT classifier
* example_relations.py - example code for relation extraction
* gpt3_transcript.txt - gpt3 run transcript
* main.py - main python file responsible for performing the relation extraction
* spacy_help_functions.py - helper functions for extracting relations
* spanbert.py - file used to run SpanBERT classifier
* spanbert_transcript.txt - spanbert run transcript
* /pytorch_pretrained_bert - files necessary to run SpanBERT classifier
* requirements.txt - python modules required to run main.py

## How To Run
* Follow all installation steps in the Description at http://www.cs.columbia.edu/~gravano/cs6111/Proj2/ 
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
    * re - for regular expressions
    * time - for spacing out openai requests
* Functions:
    * def get_google_search_items(api_key, engine_id, words): for searching google and getting the top ten results
    * def get_formatted_items(items): formatting the webpages into a dictionary
    * def get_website(url): scrape the webpage for the plaintext
    * def run_spanbert(examples, T, spanbert_model, R): run the spanbert classifier over named entities
    * def get_openai_completion(prompt, model, max_tokens, temperature = 0.2, top_p = 1, frequency_penalty = 0, presence_penalty =0): run openai query on prompt
    * def run_gpt3(sentence, valid_relation): create gpt3 prompt and format relation results
    * def extract(text, R, T, OPTION, spanbert_model, nlp, valid_relation): extract named entities and sentences
    * def main(): main program logic
    
## Step 3
* 

## Keys
* Search Engine: fb8c9f64780d3213f
* API Key: API Key: AIzaSyBh546gYpsBnKcTEdBi-jagSb9gEIoRj6s
