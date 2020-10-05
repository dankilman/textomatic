from dataclasses import dataclass


@dataclass
class ProcessedCommand:
    cmd: str
    delimiter: str = None
    output: str = "l"
    input: str = "c"
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
