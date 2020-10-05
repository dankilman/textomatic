from contextvars import ContextVar
from dataclasses import dataclass

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer

from textomatic.model import ProcessedCommand, ProcessedInput


@dataclass
class AppContext:
    app: Application = None
    process_fn = None
    box_veritcal_orientation = True
    display_help = False
    print_output_on_exit: bool = False
    non_interactive = False
    live = True

    current_error: str = None
    copied_to_clipboard = False
    dirty = False

    cmd_buffer: Buffer = Buffer(multiline=False)
    input_buffer: Buffer = Buffer()
    output_buffer: Buffer = Buffer(read_only=True)


@dataclass
class ProcessContext:
    processed_command: ProcessedCommand = ProcessedCommand("")
    processed_input: ProcessedInput = None


_current = ContextVar("current", default=AppContext())
_current_process = ContextVar("current_process", default=ProcessContext())


def get() -> AppContext:
    return _current.get()


def get_process() -> ProcessContext:
    return _current_process.get()


def reset():
    _current.set(AppContext())


def reset_process():
    _current_process.set(ProcessContext())
