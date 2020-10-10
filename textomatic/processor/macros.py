from textomatic.exceptions import ProcessException

macros = {}


def as_list(args):
    return [args]


def macro(alias, split=None):
    def wrap(fn):
        macros[alias] = {
            "fn": fn,
            "split": split or as_list,
        }
        return fn

    return wrap


@macro("jq")
def jq_macro(expression=""):
    return f"r;o:jq`{expression}`"


def get(alias):
    try:
        return macros[alias]
    except KeyError:
        raise ProcessException(f"Unregistered macro {alias}")
