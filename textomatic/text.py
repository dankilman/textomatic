import string
import unicodedata


def as_printable(s):
    if not s:
        return s
    r = []
    for c in s:
        if c in string.printable:
            r.append(c)
        elif unicodedata.category(c).startswith("C"):
            r.append("?")
        else:
            r.append(c)
    return "".join(r)
