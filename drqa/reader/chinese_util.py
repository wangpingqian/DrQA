# -*- coding: utf-8 -*-
# """汉字处理的工具:
# 判断unicode是否是汉字，数字，英文，或者其他字符。
# 全角符号转半角符号。"""

import re
from zhon.hanzi import punctuation as cn_punct
from string import punctuation as en_punct

def ToUnicode(s):
    if isinstance(s, unicode):
        return s
    else:
        return unicode(s, 'utf-8')

def ToUnicode2(table):
    import copy
    table2 = copy.deepcopy(table)
    for i in range(len(table)):
        for j in range(len(table[i])):
            table2[i][j] = ToUnicode(table[i][j])
    return table2

def is_chinese(uchar):
    """判断一个unicode字符是否是中文"""
    if u'\u4e00' <= uchar <= u'\u9fa5':
        return True
    else:
        return False

def is_pure_chinese(ustring):
    """判断一个unicode字符串是否全部都是中文"""
    for uchar in ustring:
        if not is_chinese(uchar):
            return False
    return True

def contains_chinese(ustring):
    """判断一个unicode字符串是否包含中文"""
    for uchar in ustring:
        if is_chinese(uchar):
            return True
    return False

def contains_space(ustring):
    """判断一个unicode字符串是否包含空格"""
    if ' ' in ustring or '\t' in ustring:
        return True
    return False

def is_number(uchar):
    """判断一个unicode是否是数字"""
    if u'\u0030' <= uchar <= u'\u0039':
        return True
    else:
        return False

def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
        return True
    else:
        return False

def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
        return True
    else:
        return False

def B2Q(uchar):
    """半角转全角"""
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7e:  # 不是半角字符就返回原来的字符
        return uchar
    if inside_code == 0x0020:  # 除了空格其他的全角半角的公式为:半角=全角-0xfee0
        inside_code = 0x3000
    else:
        inside_code += 0xfee0
    return chr(inside_code)

def Q2B(uchar):
    """全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
        return uchar
    return chr(inside_code)

def stringB2Q(ustring):
    """字符串半角转全角"""
    return "".join([B2Q(uchar) for uchar in ustring])

def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])

def remove_punct(ustring):
    return re.sub("[{}{}]+".format(cn_punct, en_punct), " ", ustring)

def reduce_space(ustring):
    return re.sub('[\s\t]+', ' ', ustring)

def normalize(ustring):
    ustring = stringQ2B(ustring).lower().strip()
    ustring = remove_punct(ustring)
    ustring = reduce_space(ustring)
    return ustring

def string2List(ustring):
    """将ustring按照中文，字母，数字分开"""
    retList = []
    utmp = []
    for uchar in ustring:
        if is_other(uchar):
            if len(utmp) == 0:
                continue
            else:
                retList.append("".join(utmp))
                utmp = []
        else:
            utmp.append(uchar)
    if len(utmp) != 0:
        retList.append("".join(utmp))
    return retList

def rm_cnbookmark(ustring):
    result, _ = re.subn(u"[\u300a\u300b]+", "", ustring)
    return result


if __name__ == "__main__":
    # test Q2B and B2Q
    for i in range(0x0020, 0x007F):
        print(Q2B(B2Q(chr(i))), B2Q(chr(i)))

    # test uniform
    ustring = u'中国 人名ａ高频Ａ'
    ustring = uniform(ustring)
    ret = string2List(ustring)
