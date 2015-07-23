# coding: utf-8
import math

ESC_MAP = {
    'b': r'\b',
    'f': r'\f',
    'n': r'\n',
    'r': r'\r',
    't': r'\t'
}
ESC_MAP_V = ESC_MAP.values()
FLOAT_D = ['.', 'e', 'E']
JSON_FALSE = 'false'
JSON_NULL = 'null'
JSON_TRUE = 'true'
NUMSTART = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '+', '.']
NUMCHARS = NUMSTART + FLOAT_D
WS = [' ', '\t', '\r', '\n', '\b', '\f']


class JSONStream:
    def __init__(self, data):
        self.buf = data
        self.length = len(data)
        self.buflist = []
        self.pos = 0

    def next(self):
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        newpos = min(self.pos + 1, self.length)
        r = self.buf[self.pos:newpos]
        self.pos = newpos
        return r

    def write(self, s):
        spos = self.pos
        slen = self.length
        if spos == slen:
            self.buflist.append(s)
            self.length = self.pos = spos + len(s)
            return
        if spos > slen:
            self.buflist.append('\0' * (spos - slen))
            slen = spos
        newpos = spos + len(s)
        if spos < slen:
            if self.buflist:
                self.buf += ''.join(self.buflist)
            self.buflist = [self.buf[:spos], s, self.buf[newpos:]]
            self.buf = ''
            if newpos > slen:
                slen = newpos
        else:
            self.buflist.append(s)
            slen = newpos
        self.length = slen
        self.pos = newpos

    def seek(self, pos):
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        self.pos = max(0, pos)

    def getvalue(self):
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        return self.buf

    def previous(self):
        self.seek(self.pos-1)

    def substr(self, pos, length):
        return self.getvalue()[pos:pos+length]


def skip_whitespace(stm):
    while True:
        c = stm.next()
        if c not in WS:
            stm.previous()
            return


def decode_fixed(stm, s, v):
    for rc in s[1:]:
        if stm.next() != rc:
            raise ValueError("Unexpected character found when decoding '%s'" % s)
    return v


def decode_false(stm):
    return decode_fixed(stm, JSON_FALSE, False)


def decode_true(stm):
    return decode_fixed(stm, JSON_TRUE, True)


def decode_null(stm):
    return decode_fixed(stm, JSON_NULL, None)


def decode_number(stm):
    is_float = False
    stm.previous()
    pos = stm.pos
    c = stm.next()
    while True:
        if c not in NUMCHARS:
            if pos >= 1:
                stm.previous()
            break
        elif c in FLOAT_D:
            is_float = True
        c = stm.next()
    s = stm.substr(pos, stm.pos - pos)
    return float(s) if is_float else long(s)


def decode_escape(stm):
    c = stm.next()
    e = ESC_MAP.get(c, None)
    if e is not None:
        return e
    elif c != 'u':
        return c
    return (
            r'\u' +
            stm.next() +
            stm.next() +
            stm.next() +
            stm.next()
        ).decode('unicode_escape').encode('utf-8')


def decode_string(stm):
    r = []
    while True:
        c = stm.next()
        if c == '':
            raise ValueError("JSON data truncated")
        elif c == '\\':
            r.append(decode_escape(stm))
        elif c == '"':
            return ''.join(r)
        else:
            r.append(c)


def encode_string(stm, string):
    stm.write('"')
    for c in string:
        if c in ESC_MAP_V:
            stm.write(c)
        elif ord(c) <= 127:
            stm.write(c if c != '"' else '\\"')
        else:
            stm.write('\\u%04x' % ord(c))
    stm.write('"')


def decode_array(stm):
    r = []
    while True:
        skip_whitespace(stm)
        c = stm.next()
        if c == '':
            raise ValueError("JSON data truncated")
        elif c == ',':
            r.append(decode_any(stm))
        elif c == ']':
            return r
        elif not r:
            stm.previous()
            r.append(decode_any(stm))
        else:
            raise ValueError("Failed to decode an array")


def encode_list(stm, lst):
    first = True
    stm.write('[')
    for obj in lst:
        if not first:
            stm.write(',')
        first = False
        encode_any(stm, obj)
    stm.write(']')


def decode_object(stm):
    r = {}
    while True:
        skip_whitespace(stm)
        c = stm.next()
        if c == '"':
            key = decode_string(stm)
            c = stm.next()
            if c != ':':
                raise ValueError("Expecting ':' delimiter")
            value = decode_any(stm)
            r[key] = value
        elif c == '}':
            return r
        elif c == ',':
            skip_whitespace(stm)
            if stm.next() != '"':
                raise ValueError("Expecting property name")
            stm.previous()
        elif not c or not r:
            raise ValueError("JSON data truncated")


def encode_dict(stm, dct):
    first = True
    stm.write('{')
    for key, val in dct.items():
        if not first:
            stm.write(',')
        first = False
        if not isinstance(key, basestring):
            key = str(key)
        encode_string(stm, key)
        stm.write(':')
        encode_any(stm, val)
    stm.write('}')


def decode_any(stm):
    skip_whitespace(stm)
    c = stm.next()
    if not c:
        return None
    elif c == '"':
        return decode_string(stm)
    elif c == '{':
        return decode_object(stm)
    elif c == '[':
        return decode_array(stm)
    elif c in NUMSTART:
        return decode_number(stm)
    elif c == 't':
        return decode_true(stm)
    elif c == 'f':
        return decode_false(stm)
    elif c == 'n':
        return decode_null(stm)
    else:
        raise ValueError('Expected object, array or value')


def encode_any(stm, obj):
    if isinstance(obj, (list, tuple, set)):
        encode_list(stm, obj)
    elif hasattr(obj, 'items'):
        encode_dict(stm, obj)
    elif hasattr(obj, '__iter__'):
        encode_dict(stm, obj)
    elif isinstance(obj, bool):
        stm.write(JSON_TRUE if obj else JSON_FALSE)
    elif isinstance(obj, type(None)):
        stm.write(JSON_NULL)
    elif isinstance(obj, (int, long)):
        stm.write("%d" % obj)
    elif isinstance(obj, float):
        # http://tools.ietf.org/html/rfc4627#section-2.4
        if math.isinf(obj) or math.isnan(obj):
            raise ValueError("Numeric values that cannot be represented as sequences of digits (such as Infinity and NaN) are not permitted.")
        stm.write("%s" % obj)
    elif isinstance(obj, basestring):
        encode_string(stm, obj)
    elif hasattr(obj, '__unicode__'):
        encode_string(stm, unicode(obj))
    elif hasattr(obj, '__str__'):
        encode_string(stm, str(obj))
    else:
        raise ValueError("unsupported type '%s'" % type(obj))


def loads(data):
    return decode_any(JSONStream(data))


def dumps(obj):
    stm = JSONStream('')
    encode_any(stm, obj)
    return stm.getvalue()


if __name__ == '__main__':
    import json
    # a2 = loads('{"a2"121')
    print dumps({1: "aaa", 2: "bbb"})
    # print a2
