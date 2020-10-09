from dataclasses import dataclass
from pprint import pprint
from typing import List, Callable

import pytest

from textomatic.processor.parser import parse_structure, parse_types, ParseData, parse_processor

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


processor_tests = [
    "i",
    "i()",
    "i(one, two, three)",
    "ii",
    "ii()",
    "ii(one, two, three)",
]


@dataclass
class Case:
    name: str
    test_group: List[str]
    fn: Callable


@pytest.mark.parametrize(
    "case",
    [
        Case("structure", structure_tests, parse_structure),
        Case("types", types_tests, parse_types),
        Case("processor", processor_tests, parse_processor),
    ],
    ids=lambda case, *_: case.name,
)
def test_parser(case: Case):
    print()
    for test in case.test_group:
        print(f"## expr: {test}")
        result = case.fn(test)
        pprint(result)
