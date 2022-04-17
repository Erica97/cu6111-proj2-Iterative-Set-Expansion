import sys
import requests
import re
from bs4 import BeautifulSoup

from googleapiclient.discovery import build

from extractor_help import extract_relation_from_text, relations, indention


def find_tuple_with_highest_confidence(tuples):
    max_conf = 0
    max_tp = None
    for tp in tuples:
        if tuples[tp] > max_conf:
            max_conf = tuples[tp]
            max_tp = tp
    return max_tp


def read_from_url(url: str):
    text = ''
    try:
        f = requests.get(url, timeout=10)
        soup = BeautifulSoup(f.text, features='html.parser')
        text = re.sub(r'(\n)+|[^\x00-\x7F]+', ' ', soup.get_text())
    finally:
        if len(text) > 20000:
            print(f'{indention * 1}Trimming webpage context from {len(text)} to 20000')
        else:
            print(f'{indention * 1}Webpage length (num characters): {len(text)}')
        return text if len(text) < 20000 else text[:20000]


def extract_tuples(url, r, t, k):
    print(f'{indention * 1}Fetching text from url ...')
    text = read_from_url(url)
    return extract_relation_from_text(text, r, t, k)


def main(api_key, engine_id, r, t, q, k):
    extracted_tuples = dict()
    urls_set = set()
    iter_index = 0
    print('Parameters:')
    print(f'Client key	= {api_key}')
    print(f'Engine key	= {engine_id}')
    print(f'Relation	= {relations[r]}')
    print(f'Threshold	= {t}')
    print(f'Query		= {" ".join(q)}')
    print(f'# of Tuples	= {k}')

    while len(extracted_tuples) < k:
        service = build("customsearch", "v1", developerKey=api_key)
        rsp = service.cse().list(
            q=' '.join(q),
            cx=engine_id,
            start=0,
        ).execute()

        print(f'=========== Iteration: {iter_index} - Query: {" ".join(q)} ===========')
        iter_index += 1
        if 'items' in rsp:
            new_urls_set = set()
            for item in rsp['items']:
                if item['link'] not in urls_set:
                    new_urls_set.add(item['link'])
                    urls_set.add(item['link'])
            for idx, url in enumerate(new_urls_set, start=1):
                print(f'URL ( {idx} / {len(new_urls_set)}): {url}')
                tuples = extract_tuples(url, r, t, k)
                for tp in tuples:
                    pair = (tp[0]["subj"][0], tp[0]["obj"][0])
                    if pair not in extracted_tuples:
                        extracted_tuples[pair] = (tp[1][1], False)
                    elif extracted_tuples[pair][0] < tp[1][1]:
                        extracted_tuples[pair] = (tp[1][1], extracted_tuples[pair][1])
        tmp = sorted(extracted_tuples.items(), key=lambda x: x[1][0], reverse=True)
        q = list(filter(lambda x: x[1][1] is False, tmp))[0][0]
        extracted_tuples[q] = (extracted_tuples[q][0], True)
        print(f'================== ALL RELATIONS for {relations[r]} ( {len(extracted_tuples)} ) =================')
        for tp in tmp:
            print('Confidence: {:<7} | Subject: {:<28} | Object: {}'.format(tp[1][0], tp[0][0], tp[0][1]))
        if len(extracted_tuples) >= k:
            break
    print(f'Total # of iterations = {iter_index}')


if __name__ == '__main__':
    if len(sys.argv) != 7:
        print('Usage: python main.py <google_api_key> <google_engine_id> <relation> '
              '<confidence_threshold> <seed_query> <output_tuple_numbers>')

    google_api_key = sys.argv[1]
    google_engine_id = sys.argv[2]
    relation = int(sys.argv[3])
    threshold = float(sys.argv[4])
    query = sys.argv[5]
    output_number = int(sys.argv[6])

    if relation < 1 or relation > 4:
        print('Relation must be 1, 2, 3 or 4')
        exit(1)
    if threshold < 0 or threshold > 1:
        print('Confidence threshold must be between 0 and 1')
        exit(1)
    if output_number < 0:
        print('Output tuple numbers must be a positive integer')
        exit(1)
    print('Extracting tuples...')
    main(google_api_key, google_engine_id, relation, threshold, query.split(), output_number)
