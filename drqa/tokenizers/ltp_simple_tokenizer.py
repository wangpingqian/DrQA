
import re
import unicodedata
from pyltp import Segmentor

from .tokenizer import Tokens, Tokenizer


class LTPSimpleTokenizer(Tokenizer):
    def __init__(self, **kwargs):
        if len(kwargs.get('annotators', {})) > 0:
            logger.warning('%s only tokenizes! Skipping annotators: %s' %
                           (type(self).__name__, kwargs.get('annotators')))
        self.annotators = set()
        self.data_dir = '/var/yr/zhouxiang/data/ltp_data'
        self.segmentor = Segmentor()
        self.segmentor.load(path.join(self.data_dir, 'cws.model'))

    def tokenize(self, text):
        normal_text = unicodedata.normalize('NFKC', text).replace('\\', ' ')
        #print(normal_text)
        normal_text = re.sub(r'[ \t]+', normal_text, ' ').strip()
        if len(normal_text) == 0:
            print('EMPTY LINE: %s' % normal_text)
            return "",None
        clean_text = normal_text.split(' ')
        words = [word for split in clean_text for word in list(self.segmentor.segment(split))]
        spans = []
        offset = 0
        for word in words:
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
        for tup in zip(words, text_ws, spans):
            data.append(tup)
        return tokens(data, self.annotators)

    
