from pprint import pprint

from textomatic.processor.parser import parse_structure, parse_types

types_tests = [
    ",f,",
    "s, s, s,",
    "s, s, s",
    "f, i, s",
    ',,d,j,one: s, two: f, "three 3": i',
    "1:l, one: s, -22: j, two: f, \"three 3\": i, 'four 444': d",
    """ i/"one two three" /""",
]

structure_tests = [
    "{}",
    "d()",
    "s()",
    "()",
    "[]",
    "{a}",
    "{1?}",
    "{a?}",
    "{a.b?}",
    "{a?.b?}",
    "{k:a?.b?}",
    "{k:a?.b.-1?}",
    "{a,b}",
    "{a:b}",
    "{a,b,c:a,d:1,e:-1}",
    "d(a,b,c:a)",
    "s(a)",
    "(a,c,2)",
    "[a,a,c]",
    "{one: {a,b}, two: [a, b], three: (a,3), four: {c:d,e}, five: d(1,2)}",
    "({a,b}, (b,3))",
    "[(a,a), [b,b], {c,d:c}]",
    "[a.key1, a.key2]",
    '["name 1".key1]',
    '["name.1".-2.key3."hello there"]',
    "{a/one two three/}",
]


def test_parser_sanity():
    tests = [
        (structure_tests, parse_structure),
        (types_tests, parse_types),
    ]
    for test_group, fn in tests:
        print(f"@@@@@@ {fn.__name__} @@@@@@")
        for test in test_group:
            print(f"## expr: {test}")
            result = fn(test)
            pprint(result)
        print()
