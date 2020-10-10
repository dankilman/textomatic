from textwrap import dedent

from prompt_toolkit import Application, HTML
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout import (
    Layout,
    HSplit,
    VSplit,
    Window,
    BufferControl,
    DynamicContainer,
    FloatContainer,
    Float,
    ConditionalContainer,
)
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.lexers import PygmentsLexer, DynamicLexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.widgets import FormattedTextToolbar, VerticalLine, Dialog, Label

from textomatic import context
from textomatic.app import style
from textomatic.app.lexer import CommandLexer
from textomatic.processor import outputs, inputs
from textomatic.exceptions import ProcessException
from textomatic.app.keys import kb, cmd_kb
from textomatic.processor.process import process
from textomatic.app.style import application_style
from textomatic.app.widgets import textbox
from textomatic.processor.registry import Registry
from textomatic.text import as_printable


class AppBuilder:
    def __init__(self):
        self.ctx = context.get()
        self.process_ctx = context.get_process()
        self.ctx.process_fn = self.process_key
        self.lexer_threshold = 10000
        self.input_lexer = ToggledLexer(inputs.registry, take_last=False)
        self.output_lexer = ToggledLexer(outputs.registry, take_last=True)

    def create_app(self, focus):
        ctx = self.ctx
        ctx.cmd_buffer.on_text_changed += self.process_key
        ctx.input_buffer.on_text_changed += self.process_key
        ctx.cmd_buffer.cursor_position = len(ctx.cmd_buffer.text)
        if focus:
            focused_element = {
                "COMMAND": ctx.cmd_buffer,
                "c": ctx.cmd_buffer,
                "INPUT": ctx.input_buffer,
                "i": ctx.input_buffer,
                "OUTPUT": ctx.output_buffer,
                "o": ctx.output_buffer,
            }[focus]
        else:
            focused_element = ctx.cmd_buffer if ctx.input_buffer.text else ctx.input_buffer
        layout = Layout(
            FloatContainer(
                HSplit(
                    [
                        self.create_boxes(),
                        self.create_status_bar(),
                        self.create_cmd_bar(),
                    ]
                ),
                floats=[
                    Float(self.create_help()),
                ],
            ),
            focused_element=focused_element,
        )
        return Application(
            key_bindings=kb,
            editing_mode=EditingMode.VI,
            clipboard=PyperclipClipboard(),
            color_depth=ColorDepth.from_env() or ColorDepth.DEPTH_24_BIT,
            full_screen=True,
            mouse_support=True,
            include_default_pygments_style=False,
            style=application_style,
            layout=layout,
        )

    def process_key(self, trigger=None):
        ctx = self.ctx
        ctx.current_error = None
        ctx.display_help = False
        self.input_lexer.enabled = len(ctx.input_buffer.text) < self.lexer_threshold
        if not ctx.live and trigger != "run":
            ctx.dirty = True
            return
        if trigger:
            trigger = "cmd" if trigger is ctx.cmd_buffer else "input"
        try:
            result = process(
                text=ctx.input_buffer.text,
                cmd=ctx.cmd_buffer.text,
                ctx=self.process_ctx,
                trigger=trigger,
            )
            if result is not None:
                if not isinstance(result, str):
                    result = str(result)
                self.output_lexer.enabled = len(result) < self.lexer_threshold
                ctx.output_buffer._set_text(result)
            ctx.dirty = False
        except Exception as e:
            if ctx.non_interactive:
                raise
            if isinstance(e, ProcessException):
                ctx.current_error = str(e)
            else:
                ctx.current_error = f"{e.__class__.__name__}: {e}"

    def create_status_bar(self):
        ctx = self.ctx
        process_ctx = self.process_ctx

        def _get_text():
            cmd = process_ctx.processed_command
            if ctx.current_error:
                result = ["{current_error}"]
            else:
                current = ctx.app.layout.current_buffer
                focused = {
                    id(ctx.cmd_buffer): "COMMAND",
                    id(ctx.input_buffer): "INPUT",
                    id(ctx.output_buffer): "OUTPUT",
                }[id(current)]
                mode = "live" if ctx.live else "manual"
                elem = "ansired" if ctx.dirty else "ansigreen"
                mode = f"<{elem}>{mode}</{elem}>"
                result = [
                    f"{ctx.app.vi_state.input_mode}|",
                    f"{focused}|",
                    f"{mode}|",
                    "in:{input}|",
                    "out:{output}|",
                    "delim:{delimiter}|",
                    f"header:{str(cmd.has_header).lower()}|",
                    f"raw:{str(cmd.raw).lower()}",
                ]
                if ctx.copied_to_clipboard:
                    result.append(" [Copied output to clipboard]")
            inp = ",".join([i.alias for i in cmd.inputs or []] or ["c"])
            out = ",".join([o.alias for o in cmd.outputs or []] or ["l"])
            return HTML("".join(result)).format(
                input=inp,
                output=out,
                delimiter=as_printable(cmd.delimiter) or "auto",
                current_error=str(ctx.current_error),
            )

        def _get_style():
            if ctx.copied_to_clipboard:
                cls = style.STATUS_BAR_NOTIFY
            elif ctx.current_error:
                cls = style.STATUS_BAR_ERROR
            else:
                cls = style.STATUS_BAR
            return f"class:{cls}"

        return VSplit([FormattedTextToolbar(_get_text)], style=_get_style)

    def create_boxes(self):
        ctx = self.ctx
        input_box = textbox(ctx.input_buffer, "INPUT", lexer=self.input_lexer)
        output_box = textbox(ctx.output_buffer, "OUTPUT", lexer=self.output_lexer)
        vertical_boxes = VSplit([input_box, VerticalLine(), output_box])
        horizontal_boxes = HSplit([input_box, output_box])
        return DynamicContainer(lambda: vertical_boxes if ctx.box_veritcal_orientation else horizontal_boxes)

    def create_cmd_bar(self):
        ctx = self.ctx

        def get_cmd_prefix():
            has_focus = ctx.app.layout.current_buffer is ctx.cmd_buffer
            cls = style.COMMAND_FOCUSED
            if has_focus:
                text = f"<{cls}>> </{cls}>"
            else:
                text = "> "
            return HTML(text)

        return Window(
            BufferControl(
                ctx.cmd_buffer,
                focus_on_click=True,
                input_processors=[BeforeInput(get_cmd_prefix)],
                key_bindings=cmd_kb,
                lexer=PygmentsLexer(CommandLexer),
            ),
            height=1,
        )

    def create_help(self):
        ctx = self.ctx
        dialog = Dialog(
            Label(
                dedent(
                    """
                    Tab               Switch focus between INPUT/OUTPUT/COMMAND
                    Ctrl-P            Copy OUTPUT to clipboard
                    Ctrl-O            Exit and print OUTPUT to stdout
                    Ctrl-C            Exit
                    Ctrl-T            Toggle vertical/horizontal view
                    Ctrl-L            Toggle live/manual mode
                    Ctrl-R            Run processing (when in manual mode)
                    Enter/Ctrl-M      Run processing (when in manual mode, in COMMAND)
                    F1                Toggle help
                """
                ).strip(),
                dont_extend_width=False,
                dont_extend_height=False,
            ),
            title="Help",
        )
        return ConditionalContainer(dialog, Condition(lambda: ctx.display_help))


class ToggledLexer(DynamicLexer):
    def __init__(self, registry: Registry, take_last):
        self.enabled = True
        self.registry = registry

        def get_lexer():
            if not self.enabled:
                return None
            process_ctx = context.get_process()
            processors = self.registry.get(process_ctx.processed_command, safe=True)
            processor = processors[-1] if take_last else processors[0]
            return PygmentsLexer(processor.lexer)

        super().__init__(get_lexer)


def process_one():
    builder = AppBuilder()
    builder.process_key()


def create_app(focus):
    builder = AppBuilder()
    builder.process_key()
    return builder.create_app(focus)
