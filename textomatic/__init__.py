__version__ = "0.2.0"
from textomatic.processor import inputs, outputs

register_input = inputs.registry.register
register_output = outputs.registry.register
