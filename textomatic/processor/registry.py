from textomatic.exceptions import ProcessException
from textomatic.model import ProcessedCommand


class Registry:
    def __init__(self, attr, tpe, default_alias, data=None, default_raw="n"):
        self.attr = attr
        self.type = tpe
        self.data = data or {}
        self.default_alias = default_alias
        self.default_raw = default_raw

    def register(self, alias):
        def registrar(value):
            assert (isinstance(value, type) and issubclass(value, self.type)) or isinstance(value, self.type)
            self.data[alias] = value
            return value

        return registrar

    def get(self, processed_cmd: ProcessedCommand, safe=False):
        if processed_cmd.raw:
            default = [self.data[self.default_raw]]
        else:
            default = [self.data[self.default_alias]]
        data_processors_configs = getattr(processed_cmd, self.attr)
        if not data_processors_configs:
            return default
        result = []
        for data_processor_config in data_processors_configs:
            alias = data_processor_config.alias
            args = data_processor_config.args
            try:
                obj_or_cls = self.data[alias]
            except KeyError:
                if safe:
                    return default
                raise ProcessException(f"Unregistered {self.type.__name__.lower()}: {alias}")
            if isinstance(obj_or_cls, type) and issubclass(obj_or_cls, self.type):
                result.append(obj_or_cls(args))
            else:
                result.append(obj_or_cls)
        return result
