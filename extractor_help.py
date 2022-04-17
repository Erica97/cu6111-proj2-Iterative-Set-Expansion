import spacy

from spanbert import SpanBERT
from spacy_help_functions import get_entities, create_entity_pairs

# entities_of_interest = ["ORGANIZATION", "PERSON", "LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]

# Load spacy model
nlp = spacy.load("en_core_web_lg")
# Load pre-trained SpanBERT model
spanbert = SpanBERT("./pretrained_spanbert")
# relation entity type map
relation_entity_type_map = {  # relation: ([subject_entity_type], [object_entity_type])
    1: (["PERSON"], ["ORGANIZATION"]),
    2: (["PERSON"], ["ORGANIZATION"]),
    3: (["PERSON"], ["LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]),
    4: (["ORGANIZATION"], ["PERSON"]),
}

relations = {
    1: 'per:schools_attended',
    2: 'per:employee_of',
    3: 'per:cities_of_residence',
    4: 'org:top_members/employees',
}

indention = '\t'


def extract_relation_from_text(text, relation_type, confidence_threshold, k):
    tuples = []
    doc = nlp(text)
    entities_of_interest = relation_entity_type_map[relation_type][0] + relation_entity_type_map[relation_type][1]
    sent_len = len(list(doc.sents))
    print(f'{indention*1}Annotating the webpage using spacy...')
    print(f'{indention*1}Extracted {sent_len} sentences. Processing each sentence one by one to check for presence of '
          f'right pair of named entity types; if so, will run the second pipeline ...')

    r_all = 0
    r_target = 0
    for idx, sentence in enumerate(doc.sents, start=1):
        # create entity pairs
        candidate_pairs = []
        sentence_entity_pairs = create_entity_pairs(sentence, entities_of_interest)

        for ep in sentence_entity_pairs:
            if ep[1][1] in relation_entity_type_map[relation_type][0] \
                    and ep[2][1] in relation_entity_type_map[relation_type][1]:
                candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  # e1=Subject, e2=Object
            elif ep[1][1] in relation_entity_type_map[relation_type][1] \
                    and ep[2][1] in relation_entity_type_map[relation_type][0]:
                candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  # e1=Object, e2=Subject

        # Classify Relations for all Candidate Entity Pairs using SpanBERT
        candidate_pairs = [p for p in candidate_pairs if
                           not p["subj"][1] in ["DATE", "LOCATION"]]  # ignore subject entities with date/location type
        if idx % 5 == 0 or idx == sent_len:
            print(f'{indention*1}Processed {idx} / {sent_len} sentences')
        if len(candidate_pairs) == 0:
            continue

        relation_preds = spanbert.predict(candidate_pairs)  # get predictions: list of (relation, confidence) pairs

        for ex, pred in list(zip(candidate_pairs, relation_preds)):
            if pred[0] == relations[relation_type]:
                r_all += 1
                print(f'{indention*2}=== Extracted Relation ===')
                print(f'{indention*2}Input tokens: {ex["tokens"]}')
                print(f'{indention*2}Output Confidence: {pred[1]} ; Subject: {ex["subj"][0]} ; Object: {ex["obj"][0]} ;')
                if pred[1] >= confidence_threshold:
                    print(f'{indention*2}===========================')
                    r_target += 1
                    tuples.append((ex, pred))
                else:
                    print(f'{indention*2}Confidence is lower than threshold confidence. Ignoring this.')
                    print(f'{indention*2}===========================')
        if len(tuples) >= k:
            break
    print(f'{indention*1}Extracted annotations for  {r_all}  out of total  {sent_len}  sentences')
    print(f'{indention*1}Relations extracted from this website: {r_target} (Overall: {r_all})')
    print()
    print()
    return tuples
