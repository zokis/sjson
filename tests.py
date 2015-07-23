import sjson
import unittest

DICTS = [
    (' \n{ "a":\n"1"\t\t}  ', {"a": '1'}),
    ('\n{\n \r\t } \r\n', {}),
    ('{"a":1}', {"a": 1}),
    ('{"a":[{},{}]}', {'a': [{}, {}]}),
    ('{"abcdef": "ghijkl"}', {'abcdef': 'ghijkl'}),
    ('{}', {}),
]

STRS = [
    ('"\\ \\x\\y\\z\\ "', ' xyz '),
    ('"\n\tindent\r\n"', '\n\tindent\r\n'),
    ('"abc\\"def\\"ghi"', 'abc"def"ghi'),
    ('"foo bar baz"', 'foo bar baz'),
    ('', None),
]

LISTS = [
    (' [\r\t \n] \n', []),
    (' \n[ \n\t1,\t2,3 ] \t', [1, 2, 3]),
    ('[1,-2,3]', [1, -2, 3]),
    ('[[1,-2],["a","-b"]]', [[1, -2], ["a", "-b"]]),
    ('[]', []),

]

INTS = [
    ('-1', -1),
    ('-159357', -159357),
    ('0', 0),
    ('159357', 159357),
    ('1593574625', 1593574625),
    ('15935746825857898540', 15935746825857898540L),
    ('25', 25),
    ('6660666066606660666', 6660666066606660666L),
]

FLOATS = [
    ('-.1', -0.1),
    ('-1.0', -1.0),
    ('-1E-25', -1E-25),
    ('-1E25', -1E25),
    ('-3.14159', -3.14159),
    ('.1', .1),
    ('1.0', 1.0),
    ('1.1593587412512101e21', 1.1593587412512101e21),
    ('12E-2', 12E-2),
    ('1E11', 1E11),
    ('3.14159', 3.14159),
]

FIXED = [
    ('false', False),
    ('null', None),
    ('true', True),
]

MALFORMED = [
    "[#",
    "[1, , ",
    "[1, , ,]",
    "[12,]",
    "[123",
    "[123, ]",
    "[@]",
    '["a","b"',
    '["marcelo]',
    '[nulo]',
    '[trur]',
    '[false',
    '[falze]',
    'zokis',
    '{"123"',
    '{"123":',
    '{"123"}',
    '{"a:"b"}',
    '{',
    '{,}',
    '{123: 456}',
]


class TestSjsonParse(unittest.TestCase):

    def _run(self, cases):
        for js, py in cases:
            r = sjson.loads(js)
            self.assertEquals(r, py)

    def test_dict(self):
        self._run(DICTS)

    def test_list(self):
        self._run(LISTS)

    def test_string(self):
        self._run(STRS)

    def test_integer(self):
        self._run(INTS)

    def test_floats(self):
        self._run(FLOATS)

    def test_null_and_bool(self):
        self._run(FIXED)

    def test_malformed(self):
        for js in MALFORMED:
            self.assertRaises(ValueError, sjson.loads, js)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
