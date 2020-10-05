from prompt_toolkit.layout import HSplit, Window, BufferControl
from prompt_toolkit.widgets import FormattedTextToolbar

from textomatic import context
from textomatic.app import style


def textbox(buffer, title, lexer=None):
    def get_style():
        ctx = context.get()
        if ctx.app.layout.current_buffer is buffer:
            cls = style.TEXTBOX_FOCUSED
        else:
            cls = style.TEXTBOX
        return f"class:{cls}"

    return HSplit(
        [
            FormattedTextToolbar(
                text=title,
                style=get_style,
            ),
            Window(
                cursorline=True,
                content=BufferControl(
                    buffer=buffer,
                    focus_on_click=True,
                    lexer=lexer,
                ),
                ignore_content_width=True,
            ),
        ]
    )
