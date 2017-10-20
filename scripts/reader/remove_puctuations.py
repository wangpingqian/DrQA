
import re

from zhon.hanzi import punctuation as cn_punct
from string import punctuation as en_punct

def remove_punct(line):
    return re.sub("[{}{} ]+".format(cn_punct, en_punct), " ", line)
