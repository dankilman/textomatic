import json
import shlex
from typing import List, Any, Mapping

import clevercsv
from pygments.lexer import Lexer
from pygments.lexers.data import JsonLexer
from pygments.lexers.python import PythonLexer
from pygments.lexers.special import TextLexer

from textomatic.exceptions import ProcessException
from textomatic.model import ProcessedCommand, MISSING

DEFAULT_LEXER = PythonLexer


class Input:
    lexer = DEFAULT_LEXER

    def get_rows(self, text: str, processed_cmd: ProcessedCommand) -> (List[Any], Mapping[int, str]):
        raise NotImplementedError


class CSVInput(Input):
    lexer = PythonLexer

    def get_rows(self, text: str, processed_cmd: ProcessedCommand) -> (List[Any], Mapping[int, str]):
        headers_list = []
        delimiters = [processed_cmd.delimiter] if processed_cmd.delimiter else None
        dialect = clevercsv.Sniffer().sniff(text[:10000], delimiters=delimiters)
        raw_lines = [line.strip() for line in text.split("\n") if line.strip()]
        reader = clevercsv.reader(raw_lines, dialect=dialect)
        rows = list(reader)
        if processed_cmd.has_header and rows:
            headers_list, rows = rows[0], rows[1:]
        return rows, headers_list


class JsonLinesInput(Input):
    lexer = JsonLexer

    def get_rows(self, text: str, processed_cmd: ProcessedCommand) -> (List[Any], Mapping[int, str]):
        json_rows = [json.loads(line.strip()) for line in text.split("\n") if line.strip()]
        headers_list = []
        seen_headers = set()
        for row in json_rows:
            for k in row:
                if k in seen_headers:
                    continue
                headers_list.append(k)
                seen_headers.add(k)
        rows = []
        for json_row in json_rows:
            row = [json_row.get(h, MISSING) for h in headers_list]
            rows.append(row)
        return rows, headers_list


class ShellInput(Input):
    lexer = TextLexer

    def get_rows(self, text: str, processed_cmd: ProcessedCommand) -> (List[Any], Mapping[int, str]):
        rows = []
        lines = text.split("\n")
        header_line = []
        if processed_cmd.has_header:
            header_line, lines = shlex.split(lines[0], posix=True), lines[1:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            row = shlex.split(line, posix=True)
            rows.append(row)
        return rows, header_line


def get_lexer(processed_cmd: ProcessedCommand) -> Lexer:
    try:
        return _get_input(processed_cmd).lexer
    except ProcessException:
        return DEFAULT_LEXER


def get_rows(text, processed_cmd: ProcessedCommand):
    return _get_input(processed_cmd).get_rows(text, processed_cmd)


def _get_input(processed_cmd: ProcessedCommand):
    try:
        return inputs[processed_cmd.input]
    except KeyError:
        raise ProcessException(f"Unregistered input: {processed_cmd.input}")


inputs = {
    "c": CSVInput(),
    "jl": JsonLinesInput(),
    "sh": ShellInput(),
}


def register(alias, input_object):
    inputs[alias] = input_object
