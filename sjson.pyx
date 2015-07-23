cdef extern from "math.h":
    int isnan(double x)
    int isinf(double x)

cdef:
    dict ESC_MAP = {
        'b': r'\b',
        'f': r'\f',
        'n': r'\n',
        'r': r'\r',
        't': r'\t'
    }
    char* FLOAT_D = '.eE'
    char* JSON_FALSE = 'false'
    char* JSON_NULL = 'null'
    char* JSON_TRUE = 'true'
    char* NUMSTART = '1234567890-+.'
    char* NUMCHARS = '1234567890-+.eE'
    list ESC_MAP_V = ['\b', '\f', '\n', '\r', '\t']
    list WS = [' ', '\b', '\f', '\n', '\r', '\t']


cdef class JSONStream:
    cdef readonly basestring buf
    cdef readonly int pos, length
    cdef readonly list buflist

    def __init__(JSONStream self, basestring data):
        self.buf = data
        self.length = len(data)
        self.buflist = []
        self.pos = 0

    cpdef basestring next(JSONStream self):
        cdef:
            int newpos
            basestring r
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        newpos = min(self.pos + 1, self.length)
        r = self.buf[self.pos:newpos]
        self.pos = newpos
        return r

    cpdef write(JSONStream self, object s):
        cdef:
            int spos = self.pos, slen = self.length, newpos
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

    cdef void seek(JSONStream self, int pos):
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        self.pos = max(0, pos)

    cpdef basestring getvalue(JSONStream self):
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        return self.buf

    cpdef previous(JSONStream self):
        self.seek(self.pos-1)

    cpdef basestring substr(JSONStream self, int pos, int length):
        return self.getvalue()[pos:pos+length]


cdef void skip_whitespace(JSONStream stm):
    cdef basestring c
    while 1:
        c = stm.next()
        if c not in WS:
            stm.previous()
            return


cdef object decode_fixed(JSONStream stm, char* s, object v):
    cdef basestring rc
    for rc in s[1:]:
        if stm.next() != rc:
            raise ValueError("Unexpected character found when decoding '%s'" % s)
    return v


cdef object decode_false(JSONStream stm):
    return decode_fixed(stm, JSON_FALSE, False)


cdef object decode_true(JSONStream stm):
    return decode_fixed(stm, JSON_TRUE, True)


cdef object decode_null(JSONStream stm):
    return decode_fixed(stm, JSON_NULL, None)


cdef decode_number(JSONStream stm):
    cdef:
        int is_float = 0, pos
        basestring c, s
    stm.previous()
    pos = stm.pos
    c = stm.next()
    while 1:
        if c == '' or c not in NUMCHARS:
            if pos >= 1:
                stm.previous()
            break
        elif c in FLOAT_D:
            is_float = 1
        c = stm.next()
    s = stm.substr(pos, stm.pos - pos)
    return float(s) if is_float else long(s)


cdef decode_escape(JSONStream stm):
    cdef:
        basestring c = stm.next(), e = ESC_MAP.get(c, None)
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


cdef decode_string(JSONStream stm):
    cdef:
        list r = []
        basestring c
    while 1:
        c = stm.next()
        if c == '':
            raise ValueError("JSON data truncated")
        elif c == '\\':
            r.append(decode_escape(stm))
        elif c == '"':
            return ''.join(r)
        else:
            r.append(c)


cdef encode_string(JSONStream stm, basestring string):
    cdef basestring c
    stm.write('"')
    for c in string:
        if c in ESC_MAP_V:
            stm.write(c)
        elif ord(c) <= 127:
            stm.write(c if c != '"' else '\\"')
        else:
            stm.write('\\u%04x' % ord(c))
    stm.write('"')


cdef list decode_array(JSONStream stm):
    cdef:
        list r = []
        basestring c
    while 1:
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


cdef void encode_list(JSONStream stm, list lst):
    cdef:
        int first = 1
        object obj
    stm.write('[')
    for obj in lst:
        if not first:
            stm.write(',')
        first = 0
        encode_any(stm, obj)
    stm.write(']')


cdef dict decode_object(JSONStream stm):
    cdef:
        dict r = {}
        basestring c, key
        object value
    while 1:
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
        elif c == '' or not r:
            raise ValueError("JSON data truncated")


cdef void encode_dict(JSONStream stm, dict dct):
    cdef:
        int first = 1
        object key, val
    stm.write('{')
    for key, val in dct.items():
        if not first:
            stm.write(',')
        first = 0
        if not isinstance(key, basestring):
            key = str(key)
        encode_string(stm, key)
        stm.write(':')
        encode_any(stm, val)
    stm.write('}')


cdef object decode_any(JSONStream stm):
    cdef basestring c
    skip_whitespace(stm)
    c = stm.next()
    if c == '':
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


cdef void encode_any(JSONStream stm, object obj):
    if isinstance(obj, (tuple, set)):
        encode_list(stm, list(obj))
    elif isinstance(obj, list):
        encode_list(stm, obj)
    elif isinstance(obj, dict):
        encode_dict(stm, obj)
    elif isinstance(obj, bool):
        stm.write(JSON_TRUE if obj else JSON_FALSE)
    elif isinstance(obj, type(None)):
        stm.write(JSON_NULL)
    elif isinstance(obj, (int, long)):
        stm.write("%d" % obj)
    elif isinstance(obj, float):
        # http://tools.ietf.org/html/rfc4627#section-2.4
        if isinf(obj) or isnan(obj):
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


cpdef object loads(basestring data):
    return decode_any(JSONStream(data))


cpdef char* dumps(object obj):
    cdef JSONStream stm = JSONStream('')
    encode_any(stm, obj)
    return stm.getvalue()
