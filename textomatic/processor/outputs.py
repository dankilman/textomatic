import csv
import io
import json
import pprint

from pygments.lexers.special import TextLexer
from tabulate import tabulate
from pygments.lexers.data import JsonLexer
from pygments.lexers.html import HtmlLexer
from pygments.lexers.python import PythonLexer

from textomatic.model import ProcessedCommand
from textomatic.processor.common import run_jq
from textomatic.processor.registry import Registry

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


class JQOutput(Output):
    lexer = JsonLexer

    def __init__(self, args):
        self.args = args

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        return run_jq(rows, self.args)


class NopOutput(Output):
    lexer = TextLexer

    def create_output(self, rows, processed_command: ProcessedCommand) -> str:
        return rows


registry = Registry(
    attr="outputs",
    tpe=Output,
    default_alias="l",
    data={
        "l": PythonLiteralOutput(),
        "j": JsonOutput(),
        "jl": JsonLinesOutput(),
        "c": CSVOutput(),
        "t": TableOutput(),
        "h": HTMLOutput(),
        "jq": JQOutput,
        "n": NopOutput(),
    },
)
