import os
from dataclasses import dataclass

import pytest

from textomatic.context import ProcessContext
from textomatic.exceptions import ProcessException
from textomatic.processor.process import process


@dataclass
class Case:
    name: str
    input_text: str
    cmd: str
    expected_output: str
    skipped = False
    process_ctx = ProcessContext()


def load_cases(name):
    with open(os.path.join(os.path.dirname(__file__), "cases", f"{name}.txt")) as f:
        cases = f.read()
    cases = [c.strip() for c in cases.split("---") if c.strip()]
    parsed_cases = []
    for case in cases:
        case_parts = case.split("--")
        assert len(case_parts) == 4
        case_parts = [c.strip() for c in case_parts]
        case = Case(*case_parts)
        if case.name.startswith("#"):
            case.skipped = True
        parsed_cases.append(case)
    return parsed_cases


def with_cases(name):
    return pytest.mark.parametrize("case", load_cases(name), ids=lambda c: f"{c.name} [{c.cmd}]")


def run_and_assert_process(case):
    if case.skipped:
        raise pytest.skip()
    try:
        result = process(
            text=case.input_text,
            cmd=case.cmd,
            ctx=case.process_ctx,
        ).strip()
        assert (
            result == case.expected_output
        ), f'''
"{result}"
============
"{case.expected_output}"'''
    except (ProcessException, IndexError, KeyError, ValueError, TypeError):
        if case.expected_output != "ERROR":
            raise
