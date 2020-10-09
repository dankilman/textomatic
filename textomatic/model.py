from dataclasses import dataclass
from typing import Any


@dataclass
class ProcessedCommand:
    cmd: str
    delimiter: str = None
    output: Any = None
    input: Any = None
    structure: object = None
    types: object = None
    has_header: bool = False
    headers: dict = None


@dataclass
class ProcessedInput:
    rows: list
    headers: dict


@dataclass
class NotSet:
    pass


@dataclass
class Missing:
    pass


NO_DEFAULT = NotSet()
MISSING = Missing()
