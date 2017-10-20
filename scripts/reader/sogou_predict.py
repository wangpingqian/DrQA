#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""A script to make and save model predictions on an input dataset."""

import codecs
import os
import time
import torch
import argparse
import logging
import json

from tqdm import tqdm
from drqa.reader import Predictor
from drqa.reader import chinese_util

logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s: [ %(message)s ]', '%m/%d/%Y %I:%M:%S %p')
console = logging.StreamHandler()
console.setFormatter(fmt)
logger.addHandler(console)

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str,
                    default='/var/yr/zhouxiang/DrQA/data/sogouqa/valid_factoid_1.json',
                    help='sogouqa validation datasets')
parser.add_argument('--model', type=str,
                    default='/tmp/drqa-models/20171014-ff3ffc09.mdl',
                    help='Path to model to use')
parser.add_argument('--embedding-file', type=str,
                    default='vector_up2date.txt',
                    help=('Expand dictionary to use all pretrained '
                          'embeddings in this file.'))
parser.add_argument('--out-dir', type=str,
                    default='/var/yr/zhouxiang/DrQA/data/sogouqa',
                    help=('Directory to write prediction file to '
                          '(<dataset>-<model>.preds)'))
parser.add_argument('--tokenizer', type=str, default='ltp',
                    help=("String option specifying tokenizer type to use "
                          "(e.g. 'corenlp')"))
parser.add_argument('--num-workers', type=int, default=None,
                    help='Number of CPU processes (for tokenizing, etc)')
parser.add_argument('--no-cuda', action='store_true',
                    help='Use CPU only')
parser.add_argument('--gpu', type=int, default=-1,
                    help='Specify GPU device id to use')
parser.add_argument('--batch-size', type=int, default=128,
                    help='Example batching size')
parser.add_argument('--top-n', type=int, default=1,
                    help='Store top N predicted spans per example')
parser.add_argument('--official', action='store_true',
                    help='Only store single top span instead of top N list')
args = parser.parse_args()
t0 = time.time()

args.cuda = not args.no_cuda and torch.cuda.is_available()
if args.cuda:
    torch.cuda.set_device(args.gpu)
    logger.info('CUDA enabled (GPU %d)' % args.gpu)
else:
    logger.info('Running on CPU only.')

predictor = Predictor(
    args.model,
    args.tokenizer,
    args.embedding_file,
    args.num_workers,
)
if args.cuda:
    predictor.cuda()


# ------------------------------------------------------------------------------
# Read in dataset and make predictions.
# ------------------------------------------------------------------------------

# 读取加载待预测数据
examples = []               # examples should be the context question pairs
qids = []                   # qids should be the corresponding ids
# for SQuAD json file
# with open(args.dataset) as f:
#     data = json.load(f)['data']
#     for article in data:
#         for paragraph in article['paragraphs']:                 # paragraph
#             context = paragraph['context']                      # 
#             for qa in paragraph['qas']:
#                 qids.append(qa['id'])
#                 examples.append((context, qa['question']))

with open(args.dataset) as f:
    normalize = chinese_util.normalize
    for line in f:
        item = json.loads(line)
        question = normalize(item['query'])
        context = normalize(' '.join([p['passage_text'] for p in item['passages']]))
        examples.append((context, question))
        qids.append(item['query_id'])

results = {}
for i in tqdm(range(0, len(examples), args.batch_size)):
    predictions = predictor.predict_batch(
        examples[i:i + args.batch_size], top_n=args.top_n
    )
    for j in range(len(predictions)):
        # Official eval expects just a qid --> span
        if args.official:
            results[qids[i + j]] = predictions[j][0][0]

        # Otherwise we store top N and scores for debugging.
        else:
            results[qids[i + j]] = [(p[0], float(p[1])) for p in predictions[j]]

model = os.path.splitext(os.path.basename(args.model or 'default'))[0]
basename = os.path.splitext(os.path.basename(args.dataset))[0]
outfile = os.path.join(args.out_dir, basename + '-' + model + '.preds')

logger.info('Writing results to %s' % outfile)
with codecs.open(outfile, 'w', encoding='utf-8') as f:
    for k,v in sorted(results.items(), key=lambda x:int(x[0]), reverse=False):
        f.write(("%s\t%s\n") % (k,v[0]))
    #json.dump(results, f)

logger.info('Total time: %.2f' % (time.time() - t0))
