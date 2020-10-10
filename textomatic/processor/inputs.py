import json
import shlex
from typing import List, Any, Mapping

import clevercsv
from pygments.lexers.data import JsonLexer
from pygments.lexers.python import PythonLexer
from pygments.lexers.special import TextLexer

from textomatic.model import ProcessedCommand, MISSING
from textomatic.processor.common import run_jq
from textomatic.processor.registry import Registry

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


class JQInput(Input):
    lexer = JsonLexer

    def __init__(self, args):
        self.args = args

    def get_rows(self, text: str, processed_cmd: ProcessedCommand) -> (List[Any], Mapping[int, str]):
        return run_jq(text, self.args), []


class NopInput(Input):
    lexer = TextLexer

    def get_rows(self, text: str, processed_cmd: ProcessedCommand) -> (List[Any], Mapping[int, str]):
        return text, []


registry = Registry(
    attr="inputs",
    tpe=Input,
    default_alias="c",
    data={
        "c": CSVInput(),
        "jl": JsonLinesInput(),
        "sh": ShellInput(),
        "jq": JQInput,
        "n": NopInput(),
    },
)
