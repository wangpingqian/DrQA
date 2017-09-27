
import unicodedata
import copy
import json
import pexpect
import re
from os import path
from pyltp import Segmentor
from pyltp import Postagger
from pyltp import NamedEntityRecognizer

from .tokenizer import Tokens, Tokenizer

class LTPTokenizer(Tokenizer):

    def __init__(self, **kwargs):
        self.annotators = copy.deepcopy(kwargs.get('annotators', set()))
        self.data_dir = '/var/yr/zhouxiang/data/ltp_data'
        #print(self.data_dir)
        self.segmentor = Segmentor()
        self.segmentor.load(path.join(self.data_dir, 'cws.model'))
        self.postagger = Postagger()
        self.postagger.load(path.join(self.data_dir, 'pos.model'))
        self.ne_recognizer = NamedEntityRecognizer()
        self.ne_recognizer.load(path.join(self.data_dir, 'ner.model'))

    #def __del__(self):
    #    self.segmentor.release()
    #    self.postagger.release()
    #    self.ne_recognizer.release()

    def tokenize(self, text):
        normal_text = unicodedata.normalize('NFKC', text).replace('\\', ' ')
        #print(normal_text)
        normal_text = re.sub(r'[ \n\t]+', normal_text, ' ').strip()
        if len(normal_text) == 0:
            print('EMPTY LINE: %s' % normal_text)
            return "",None
        clean_text = normal_text.split(' ')
        words = [word for split in clean_text for word in list(self.segmentor.segment(split))]
        postags = list(self.postagger.postag(words))
        netags = list(self.ne_recognizer.recognize(words, postags))
        #print(words)
        #print(postags)
        #print(netags)
        spans = []
        lemmas = []
        offset = 0
        for word in words:
            lemmas.append(word)
            word_start = normal_text.find(word, offset)
            if word_start == -1:
                raise RuntimeError('%s not found in\n%s\n[%d:]' % (word, normal_text, offset))
            word_end = word_start + len(word)
            spans.append((word_start, word_end))
            offset = word_end
        text_ws = []
        for i in range(len(spans)):
            start_ws = spans[i][0]
            end_ws = spans[i][1] if i+1 >= len(spans) else spans[i+1][0]
            text_ws.append(normal_text[start_ws: end_ws])
        data = []
        for tup in zip(words, text_ws, spans, postags, lemmas, netags):
            data.append(tup)
        return normal_text,Tokens(data, self.annotators)

if __name__ == '__main__':
    tokenizer = LTPTokenizer(**{'annotators': {'lemma', 'pos', 'ner'}})
    data = tokenizer.tokenize('元芳你怎么看？ 我趴窗户上看')
    for item in data:
        print(item)

