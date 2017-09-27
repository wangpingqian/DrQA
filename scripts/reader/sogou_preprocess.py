#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""Preprocess the SQuAD dataset for training."""

import argparse
import os
import sys
import json
import random
import time

from multiprocessing import Pool
from multiprocessing.util import Finalize
from functools import partial
from drqa import tokenizers

# ------------------------------------------------------------------------------
# Tokenize + annotate.
# ------------------------------------------------------------------------------

TOK = None


def init(tokenizer_class, options):
    global TOK
    TOK = tokenizer_class(**options)
    #Finalize(TOK, TOK.shutdown, exitpriority=100)


def tokenize(text):
    """Call the global process tokenizer on the input text."""
    global TOK
    normal_text, tokens = TOK.tokenize(text)
    if tokens == None: return None
    output = {
        'normal_text': normal_text,
        'words': tokens.words(),
        'offsets': tokens.offsets(),
        'pos': tokens.pos(),
        'lemma': tokens.lemmas(),
        'ner': tokens.entities(),
    }
    return output


# ------------------------------------------------------------------------------
# Process dataset examples
# ------------------------------------------------------------------------------


def load_dataset(path):
    """Load json file and store fields separately."""
    output = {'qids': [], 'questions': [], 'answers': [],
              'contexts': [], 'qid2cid': []}

    with open(path) as f:
        qaid = 100001
        for line in f:
            item = json.loads(line)
            if len(item['query']) == 0 or len(item['answer']) == 0: continue
            for passage in item['passages']:
                if len(passage) == 0: continue
                output['contexts'].append(passage['passage_text'])
                output['qids'].append(str(qaid))
                output['questions'].append(item['query'])
                output['qid2cid'].append(len(output['contexts']) - 1)
                output['answers'].append(item['answer'])
                qaid += 1
    print(len(output['questions']),len(output['contexts']))
    return output


def find_answer(offsets, begin_offset, end_offset):
    """Match token offsets with the char begin/end offsets of the answer."""
    start = [i for i, tok in enumerate(offsets) if tok[0] == begin_offset]
    end = [i for i, tok in enumerate(offsets) if tok[1] == end_offset]
    assert(len(start) <= 1)
    assert(len(end) <= 1)
    if len(start) == 1 and len(end) == 1:
        return start[0], end[0]


def process_dataset(data, tokenizer, workers=None):
    """Iterate processing (tokenize, parse, etc) dataset multithreaded."""
    tokenizer_class = tokenizers.get_class(tokenizer)
    init(tokenizer_class,  {'annotators': {'lemma'}})
    q_tokens = []
    c_tokens = []
    print("tokenizing questions ...")
    make_pool = partial(Pool, workers, initializer=init)
    workers1 = make_pool(initargs=(tokenizer_class, {'annotators': {'lemma'}}))
    q_tokens = workers1.map(tokenize, data['questions'])
    workers1.close()
    workers1.join()

    print("tokenizing contexts ...")
    workers2 = make_pool(
        initargs=(tokenizer_class, {'annotators': {'lemma', 'pos', 'ner'}})
    )
    c_tokens = workers2.map(tokenize, data['contexts'])
    workers2.close()
    workers2.join()
    assert(len(q_tokens) == len(c_tokens))
    for idx in range(len(q_tokens)):
        if q_tokens[idx] == None  or c_tokens[data['qid2cid'][idx]] == None:
            continue
        normal_question = q_tokens[idx]['normal_text']
        normal_context = c_tokens[data['qid2cid'][idx]]['normal_text']
        question = q_tokens[idx]['words']
        qlemma =   q_tokens[idx]['lemma']
        document = c_tokens[data['qid2cid'][idx]]['words']
        offsets =  c_tokens[data['qid2cid'][idx]]['offsets']
        lemma = c_tokens[data['qid2cid'][idx]]['lemma']
        pos =   c_tokens[data['qid2cid'][idx]]['pos']
        ner =   c_tokens[data['qid2cid'][idx]]['ner']
        ans_tokens = []
        ans = data['answers'][idx]  # answer the text
        ans_start = data['contexts'][idx].find(ans)
        ans_end = ans_start + len(ans)
        found = find_answer(offsets, ans_start, ans_end)
        if found:
            ans_tokens.append(found)
            yield {
              'id': data['qids'][idx],
              'question': question,
              'document': document,
              'offsets': offsets,
              'answers': ans_tokens,
              'qlemma': qlemma,
              'lemma': lemma,
              'pos': pos,
              'ner': ner,
              'normal_question': normal_question,
              'normal_context': normal_context,
              'text_answer': ans
            }


# -----------------------------------------------------------------------------
# Commandline options
# -----------------------------------------------------------------------------


parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', type=str, help='Path to sogouqa data directory',
                    default='/var/yr/zhouxiang/DrQA/data/sogouqa')
parser.add_argument('--out_dir', type=str, help='Path to output file dir',
                    default='/var/yr/zhouxiang/DrQA/data/sogouqa')
parser.add_argument('--split', type=str, help='Filename for train/dev split',
                    default='train_factoid_1')
                    #default='examples')
parser.add_argument('--workers', type=int, default=None)
parser.add_argument('--tokenizer', type=str, default='ltp')
args = parser.parse_args()

t0 = time.time()

in_file = os.path.join(args.data_dir, args.split + '.json')
print('Loading dataset %s' % in_file, file=sys.stderr)
dataset = load_dataset(in_file)

random.shuffle(dataset)

out_file = os.path.join(
    args.out_dir, '%s-processed-%s.txt' % (args.split, args.tokenizer)
)
print('Will write to file %s' % out_file, file=sys.stderr)
with open(out_file, 'w') as f:
    for ex in process_dataset(dataset, args.tokenizer, args.workers):
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

print('Total time: %.4f (s)' % (time.time() - t0))
