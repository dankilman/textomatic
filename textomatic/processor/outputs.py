import csv
import io
import json
import pprint

from tabulate import tabulate
from pygments.lexer import Lexer
from pygments.lexers.data import JsonLexer
from pygments.lexers.html import HtmlLexer
from pygments.lexers.python import PythonLexer

from textomatic.exceptions import ProcessException
from textomatic.model import ProcessedCommand

DEFAULT_LEXER = PythonLexer


class Output:
    lexer = DEFAULT_LEXER

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        raise NotImplementedError


class PythonLiteralOutput(Output):
    lexer = PythonLexer

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        return pprint.pformat(
            rows,
            indent=1,
            compact=False,
            sort_dicts=False,
        )


class JsonOutput(Output):
    lexer = JsonLexer

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        return json.dumps(rows, indent=4)


class JsonLinesOutput(Output):
    lexer = JsonLexer

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        return "\n".join(json.dumps(r) for r in rows)


class CSVOutput(Output):
    lexer = JsonLexer

    class Dialect(csv.Dialect):
        delimiter = ","
        doublequote = True
        escapechar = "\\"
        lineterminator = "\n"
        quotechar = '"'
        quoting = csv.QUOTE_ALL
        skipinitialspace = True
        strict = False

    dialect = Dialect()

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        out = io.StringIO()
        writer = csv.writer(out, self.dialect)
        if processed_command.headers:
            writer.writerow(processed_command.headers.values())
        writer.writerows(rows)
        return out.getvalue()


class TableOutput(Output):
    lexer = JsonLexer

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        kwargs = {}
        if processed_command.headers:
            kwargs["headers"] = processed_command.headers.values()
        return tabulate(rows, tablefmt="fancy_grid", **kwargs)


class HTMLOutput(Output):
    lexer = HtmlLexer

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        kwargs = {}
        if processed_command.headers:
            kwargs["headers"] = processed_command.headers.values()
        return tabulate(rows, tablefmt="html", **kwargs)


def get_lexer(processed_cmd: ProcessedCommand) -> Lexer:
    try:
        return _get_output(processed_cmd).lexer
    except ProcessException:
        return DEFAULT_LEXER


def create_output(rows, processed_cmd: ProcessedCommand) -> str:
    return _get_output(processed_cmd).create_output(rows, processed_cmd)


def _get_output(processed_cmd: ProcessedCommand) -> Output:
    try:
        return outputs[processed_cmd.output]
    except KeyError:
        raise ProcessException(f"Unregistered output: {processed_cmd.output}")


outputs = {
    "l": PythonLiteralOutput(),
    "j": JsonOutput(),
    "jl": JsonLinesOutput(),
    "c": CSVOutput(),
    "t": TableOutput(),
    "h": HTMLOutput(),
}


def register(alias, output_object):
    outputs[alias] = output_object
