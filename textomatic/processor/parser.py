import string
from dataclasses import dataclass
from typing import List, Union, Any

from pyparsing import (
    Literal,
    ZeroOrMore,
    Empty,
    Word,
    Optional,
    Combine,
    printables,
    nums,
    QuotedString,
    Suppress,
    Forward,
    alphanums,
)

from textomatic.exceptions import ProcessException
from textomatic.model import NO_DEFAULT


class ParseData:
    pass


@dataclass
class KeyToValueData(ParseData):
    key: Any
    value: Any


@dataclass
class TypeDefData(ParseData):
    type: str
    optional: bool
    default: Any


@dataclass
class StructureData(ParseData):
    type: str
    fields: object


@dataclass
class RefData(ParseData):
    value: list
    default: Any


@dataclass
class LocData(ParseData):
    value: object
    optional: bool = False


@dataclass
class IdData(ParseData):
    value: object
    optional: bool = False


@dataclass
class ProcessorData(ParseData):
    alias: str
    args: str


# general
OptionalMarker = Optional("?")("optional")
PrintablesReducedForDefault = Word(string.printable, excludeChars="/")
PrintablesReducedForArgs = Word(string.printable, excludeChars="`")
Default = Optional(Combine(Suppress("/") + PrintablesReducedForDefault + Suppress("/")))("default")

# ref
Loc = Combine(Optional("-") + Word(nums)) + OptionalMarker
Loc.setParseAction(lambda t: [LocData(int(t[0]), optional=bool(t.optional))])
PrintablesReducedForId = Word(printables, excludeChars="}]),./:?")
FreeFormForId = QuotedString("'") | QuotedString('"') | PrintablesReducedForId
Id = FreeFormForId + OptionalMarker
Id.setParseAction(lambda t: [IdData(t[0], optional=bool(t.optional))])
Ref = Loc | Id
RefPath = (Ref + ZeroOrMore(Suppress(".") + Ref))("ref_path") + Default

# types
AnyType = Word("sifbjld_", exact=1) + OptionalMarker + Default
AnyType.setParseAction(lambda t: [TypeDefData(t[0], optional=bool(t.optional), default=t.default or NO_DEFAULT)])
DefaultType = Empty()
DefaultType.setParseAction(lambda t: [TypeDefData("_", optional=False, default=NO_DEFAULT)])
RefToType = Ref + Suppress(":") + AnyType
RefToType.setParseAction(lambda t: [KeyToValueData(t[0], t[1])])
TypeDef = RefToType | AnyType | DefaultType
Types = (TypeDef + ZeroOrMore(Suppress(",") + TypeDef))("types")
Types.setParseAction(lambda t: [t.types.asList()])

# structure
Structure = Forward()
StructureRef = RefPath.copy()
StructureRef.setParseAction(lambda t: [RefData(t.ref_path.asList(), default=t.default or NO_DEFAULT)])
StructureOrRef = Structure | StructureRef
IdToStructureOrRef = Id + Suppress(":") + StructureOrRef
IdToStructureOrRef.setParseAction(lambda t: [KeyToValueData(t[0], t[1])])
Field = IdToStructureOrRef | StructureOrRef
Fields = (Field + ZeroOrMore(Suppress(",") + Field))("fields")
Fields.setParseAction(lambda t: [t.fields.asList()])
Structure << ("[" + Fields + "]" | "{" + Fields + "}" | "(" + Fields + ")" | "d(" + Fields + ")" | "s(" + Fields + ")")
Structure.setParseAction(lambda t: [StructureData(t[0] + t[-1], t[1])])
EmptyStructure = Literal("[]") | "{}" | "()" | "d()" | "s()"
EmptyStructure.setParseAction(lambda t: [StructureData(t[0], [])])
TopLevelStructure = EmptyStructure | Structure

# processor (inputs/outputs)
ProcessorArgsInner = Optional(PrintablesReducedForArgs)
ProcessorArgs = (Suppress("`") + ProcessorArgsInner + Suppress("`"))("args")
ProcessorAlias = Word(alphanums)("alias")
Processor = ProcessorAlias + Optional(ProcessorArgs)
Processor.setParseAction(lambda t: [ProcessorData(t.alias, (t.args or [""])[0])])
Processors = (Processor + ZeroOrMore(Suppress(",") + Processor))("processors")
Processors.setParseAction(lambda t: [t.processors.asList()])


# api
def parse_types(expr) -> List[Union[KeyToValueData, TypeDefData]]:
    return _parse(Types, expr)


def parse_structure(expr) -> StructureData:
    return _parse(TopLevelStructure, expr)


def parse_processors(expr) -> ProcessorData:
    return _parse(Processors, expr)


# internal
def _parse(element, expr):
    try:
        parsed = element.parseString(expr, parseAll=True)
    except Exception:
        raise ProcessException(f"Not a valid expresion: {expr}")
    return parsed.asList()[0]
