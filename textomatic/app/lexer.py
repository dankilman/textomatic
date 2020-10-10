from pygments.lexer import RegexLexer, bygroups
from pygments.token import Text, Keyword, Operator


class CommandLexer(RegexLexer):
    tokens = {
        "root": [
            (r"([iosthrd])(:)", bygroups(Keyword, Text)),
            (r";", Operator),
            (r".", Text),
        ],
    }
