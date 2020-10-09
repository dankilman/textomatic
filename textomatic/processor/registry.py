from textomatic.exceptions import ProcessException
from textomatic.model import ProcessedCommand


class Registry:
    def __init__(self, attr, tpe, default_alias, data=None):
        self.attr = attr
        self.type = tpe
        self.data = data or {}
        self.default_alias = default_alias

    def register(self, alias, value):
        assert issubclass(value, self.type) or isinstance(value, self.type)
        self.data[alias] = value

    def get(self, processed_cmd: ProcessedCommand, safe=False):
        default = self.data[self.default_alias]
        processor_data = getattr(processed_cmd, self.attr)
        if not processor_data:
            return default
        alias = processor_data.alias
        args = processor_data.args
        try:
            obj_or_cls = self.data[alias]
        except KeyError:
            if safe:
                return default
            raise ProcessException(f"Unregistered {self.type.__name__.lower()}: {alias}")
        if isinstance(obj_or_cls, type) and issubclass(obj_or_cls, self.type):
            return obj_or_cls(args)
        else:
            return obj_or_cls
