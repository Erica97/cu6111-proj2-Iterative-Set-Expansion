# cu-e6111-proj2
## Team
Rong Bai, rb3512

Jiawen Li, jl6121

## Files List
```
.
└── proj2.tar.gz
  ├── extractor_help.py       # relation extraction pipeline
  ├── main.py                 # main entry
  ├── spacy_help_functions.py # provided spacy helper
  ├── spanbert.py             # provided spanbert model
  ├── README.md
  └── transcript.txt          # test results for: 2 0.7 "bill gates microsoft" 10
  
```
Please note that we do not submit 2 pretrained folders: `pretrained_spanbert`, `pytorch_pretrained_bert`. They should be placed under the same directory as the main.py file.

## How To Run
### Dependencies
```bash
pip3 install beautifulsoup4 
pip3 install -U pip setuptools wheel
pip3 install -U spacy
python3 -m spacy download en_core_web_lg
pip3 install google-api-python-client
```
### Run
If query is separated by space, please use double quotes to wrap it.
```bash
python3 main.py <google_api_key> <google_engine_id> <relation> <confidence_threshold> <seed_query> <number_of_tuples_in_output>
```
## Design

### Internal Design

The `extractor_help.py` script is modified from the provided `example_relations.py`. We implemented a function called `extract_relation_from_text` which takes in 4 input arguments: 
- the raw text extracted by beautifulsoup4 in a single returned webpage(URL) for the seed query;
- the relation type (must be 1,2,3 or 4):
   - 1 : "per : schools_attended"
   - 2 : "per : employee_of"
   - 3 : "per : cities_of_residence"
   - 4 : "org : top_members/employees";
- the confidence threshold, a numeric value between 0 and 1;
- k : the desired number of tuples in the output.

This function returns a list of tuples in the form of (dictionary of entity pair, extraction confidence).

In `main.py` we first initialize an empty dictionary `extracted_tuples` where the keys should be subject:object pairs, and the values are tuples in the form of (extraction confidence, True/False) where the boolean value means whether the key pair has been used for querying. We then start the search with all parameters described in the Run section above, using Google API to get the URLs for top-10(or less) webpages for a query. For each query iteration, we keep track of visited URL sites using a set `urls_set` and we only keep URLs that are not seen in previous iterations for current iteration. 
Next, the algorithm performs Iterative Set Expansion(ISE) which will be described in the next section. After ISE, we check for exact key duplicates in `extracted_tuples` 
and only keep the highest extraction confidence value. Finally, we sort items in `extracted_tuples` by its extraction confidence in descending order, 
and automatically set the new query `q` to be the pair with the highest extraction confidence, and set its boolean value to True. We check whether there are `k` items in `extracted_tuples`; if so, the program terminates immediately.
### Iterative Set Expansion Algorithm (step 3)
We use `new_urls_set` to store the URLs for current query iteration(that are not seen before). For each URL, we run the `extract_tuples` function. It uses `requests.get` to retrieve webpages which times out in 10 seconds(skip this URL if it takes more than 10 seconds to respond), and only keep the first 20,000 characters(or less) of the raw text retrieved by `Beautiful Soup`. We also use `re` to better extract raw text, by filtering out unicode characters.
The returned text for the URL is then used as a parameter to the `extract_relation_from_text` function imported from `extractor_help.py`, therefore we get a list of tuples of entity pairs and extraction confidence.
The function `extract_relation_from_text` maps given relation to subject-object entity types by using `relations` and `relation_entity_type_map`. 
Next, apply spacy model to raw text to extract sentences. For each sentence, we use `create_entity_pairs` function from `spacy_help_functions.py` 
and the filtered entities of interest to get all candidate subject-object entity pairs. To keep subject-object pairs of the right type for the target relation, we match named entities recognized by `spaCy` with subject entity type and object entity type in `relation_entity_type_map`. 
We only focus on 4 types of target relations, and ignore candidate pairs subject entities with date/location types. Next, we feed the recognized subject and object named entity pair, the given relation and the sentence to `spanBERT` to get a list of predicted (relation, confidence) pairs.
We use the variable `r_all` to count the number of predictions matching the target relation, and the variable `r_target` to count the number of predictions matching the target relation and with confidence no less than the given confidence threshold. When there are k tuples meeting all requirements in the `tuples` list, the program terminates.
### External Library
Beside `spaCy`, `spanBERT`, `Beautiful Soup` and `Google API Client`, we also import `re` to better extract raw text, as well as `requests` to handle Google API search.
## credentials
Search Engine JSON API Key: `AIzaSyAA6dhVPPVCI-JfqTgWw51WnnrSbbIyaa8`

Search Engine ID: `d8910217929b314ff`
