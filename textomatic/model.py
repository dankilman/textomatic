from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class ProcessedCommand:
    cmd: str
    delimiter: str = None
    outputs: List[Any] = field(default_factory=list)
    inputs: List[Any] = field(default_factory=list)
    structure: object = None
    types: object = None
    has_header: bool = False
    headers: dict = None
    raw: bool = False


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
