from prompt_toolkit.styles import style_from_pygments_cls, Style, merge_styles
from pygments.styles import get_style_by_name

pygments_style_name = "monokai"
pygments_style = style_from_pygments_cls(get_style_by_name(pygments_style_name))

STATUS_BAR = "status-bar"
STATUS_BAR_ERROR = "status-bar-error"
STATUS_BAR_NOTIFY = "status-bar-notify"
TEXTBOX = "textbox"
TEXTBOX_FOCUSED = "textbox-focused"
COMMAND_FOCUSED = "command-focused"

custom_style = Style(
    [
        ("cursor-line", "bg:#222 nounderline"),
        (STATUS_BAR, "bg:#333"),
        (STATUS_BAR_ERROR, "fg:#fff bg:#8A000D"),
        (STATUS_BAR_NOTIFY, "fg:#fff bg:#3E7259"),
        (TEXTBOX, "bg:#333"),
        (TEXTBOX_FOCUSED, "bg:#60AF8C fg:#000"),
        (COMMAND_FOCUSED, "fg:ansiblue bold"),
        ("frame.label", "fg:#000"),
    ]
)

application_style = merge_styles([pygments_style, custom_style])
