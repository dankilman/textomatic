import ast
import json

from textomatic.context import ProcessContext
from textomatic.processor import parser, outputs, inputs, macros
from textomatic.exceptions import ProcessException
from textomatic.model import ProcessedInput, ProcessedCommand, NO_DEFAULT, MISSING

DEFAULT_CMD = ProcessedCommand("")


def get(attr, _):
    def fn(v):
        result = v[attr]
        if result is MISSING:
            raise IndexError(f"Missing {attr}")
        return result

    return fn


def getsafe(attr, default=None):
    def fn(v):
        try:
            result = v[attr]
            if result is MISSING:
                result = default
            return result
        except Exception:
            return default

    return fn


def process(text: str, cmd: str, ctx: ProcessContext, trigger: str = None):
    processed_cmd, changed = _process_cmd(ctx, cmd)
    input_objs = inputs.registry.get(processed_cmd)
    output_objs = outputs.registry.get(processed_cmd)

    if trigger == "cmd" and not changed:
        return None

    if trigger != "cmd" or any(attr in changed for attr in ["delimiter", "inputs", "has_header", "raw"]):
        rows, headers_list = text, []
        for input_obj in input_objs:
            prev_headers = headers_list
            rows, headers_list = input_obj.get_rows(rows, processed_cmd)
            headers_list = headers_list or prev_headers
        headers = {i: h for i, h in enumerate(headers_list)}
        ctx.processed_input = ProcessedInput(rows, headers)
        if headers:
            processed_cmd.has_header = True
    else:
        headers = ctx.processed_input.headers
        rows = ctx.processed_input.rows
    rows = _process_rows(processed_cmd, headers, rows)
    processed_cmd.headers = _extract_output_headers(processed_cmd.structure, headers)

    result = rows
    for output_obj in output_objs:
        result = output_obj.create_output(result, processed_cmd)
    return result


def _extract_output_headers(structure: parser.StructureData, input_headers):
    if not structure or not structure.fields:
        return input_headers
    result = {}
    for i, field in enumerate(structure.fields):
        result[i] = _extract_structure_field_name(field, input_headers)
    return result


def _extract_structure_field_name(field: parser.ParseData, headers):
    if isinstance(field, parser.KeyToValueData):
        name = field.key.value
    elif isinstance(field, parser.RefData):
        first, rest = field.value[0], field.value[1:]
        if isinstance(first, parser.LocData):
            num = first.value
            if num > 0:
                num -= 1
            else:
                num += len(headers)
            if num in headers:
                first_name = headers[num]
            else:
                first_name = str(first.value)
        elif isinstance(first, parser.IdData):
            first_name = first.value
        else:
            raise ProcessException(f"Unexpected first field: {first}")
        name = ".".join([first_name] + [str(f.value) for f in rest])
    else:
        raise ProcessException(f"Unexpected field: {field}")
    return name


def _process_rows(processed_cmd, headers, rows):
    if processed_cmd.raw:
        return rows
    headers_inverse = {h: i for i, h in headers.items()}
    type_processors = _build_row_types_processor(processed_cmd.types, headers_inverse)
    structure_processor = _build_row_structure_processor(processed_cmd.structure, headers, headers_inverse)
    return [_process_row(type_processors, structure_processor, r) for r in rows]


def _process_row(type_processors, structure_processor, row):
    if type_processors:
        row = row[:]
        for i, type_processor, optional_ref, optional_type, default in type_processors:
            try:
                value = row[i]
                if value is MISSING:
                    if optional_ref:
                        row[i] = default
                        continue
                    else:
                        raise IndexError(f"Missing index {i}")
                try:
                    row[i] = type_processor(value)
                except ProcessException:
                    raise
                except Exception:
                    if not optional_type:
                        raise
                    row[i] = default
            except IndexError:
                if not optional_ref:
                    raise
    return structure_processor(row)


def _build_row_types_processor(types, headers_inverse):
    type_processors = []
    if not types:
        return type_processors
    saw_header = False
    for i, col_type in enumerate(types):
        if isinstance(col_type, parser.TypeDefData):
            if saw_header:
                raise ProcessException("Cannot specify types for indexed columns after named columns")
            type_def = col_type
            optional_type = type_def.optional
            optional_ref = optional_type
            default = type_def.default
        elif isinstance(col_type, parser.KeyToValueData):
            saw_header = True
            type_def = col_type.value
            optional_type = type_def.optional
            default = type_def.default
            if isinstance(col_type.key, parser.LocData):
                optional_ref = col_type.key.optional
                i = col_type.key.value
                if i > 0:
                    i -= 1
            elif isinstance(col_type.key, parser.IdData):
                optional_ref = col_type.key.optional
                header = col_type.key.value
                i = headers_inverse[header]
            else:
                raise ProcessException(f"Unknown key type: {col_type.key}")
        else:
            raise ProcessException(f"Unknown col_type: {col_type}")
        row_type_processor = _build_type_processor(type_def.type)
        if default is not NO_DEFAULT and not (optional_ref or optional_type):
            optional_ref = True
            optional_type = True
        if default is NO_DEFAULT:
            default = None
        else:
            try:
                default = ast.literal_eval(default)
            except Exception as e:
                raise ProcessException(f"Invalid default literal value: {default}") from e
        type_processors.append((i, row_type_processor, optional_ref, optional_type, default))
    return type_processors


def _build_type_processor(t):
    if t in {"_", "s"}:
        return str
    elif t == "f":
        return float
    elif t == "i":
        return int
    elif t == "b":
        return lambda v: str(v).lower() in {"true", "yes", "y", "on", "1"}
    elif t == "j":
        return lambda v: json.loads(str(v))
    elif t == "l":
        return lambda v: ast.literal_eval(str(v))
    elif t == "d":
        raise ProcessException("Dates are not supported yet")
    else:
        raise ProcessException(f"Unsupported column type: {t}")


def _build_row_structure_processor(structure, headers, headers_inverse):
    def replace_missing_from_row(r):
        return [replace_missing(v) for v in r]

    def replace_missing(v):
        return None if v is MISSING else v

    if not structure:
        return lambda r: replace_missing_from_row(r)

    def impl(data: parser.ParseData, values):
        if isinstance(data, parser.StructureData):
            assert values
            if not data.fields:
                if data.type == "[]":
                    return lambda r: replace_missing_from_row(r)
                elif data.type == "()":
                    return lambda r: tuple(replace_missing(i) for i in r)
                elif data.type == "s()":
                    return lambda r: set(replace_missing(i) for i in r)
                elif data.type in {"{}", "d()"}:
                    return lambda r: dict(zip(headers.values(), replace_missing_from_row(r)))
                else:
                    raise ProcessException(f"Unsupported data type: {data.type}")
            else:
                values = [impl(f, values=True) for f in data.fields]
                if data.type == "[]":
                    return lambda row: [v(row) for v in values]
                elif data.type == "()":
                    return lambda row: tuple(v(row) for v in values)
                elif data.type == "s()":
                    return lambda row: set(v(row) for v in values)
                elif data.type in {"{}", "d()"}:
                    keys = [impl(f, values=False) for f in data.fields]
                    return lambda row: dict(zip(keys, [v(row) for v in values]))
                else:
                    raise ProcessException(f"Unsupported data type: {data.type}")
        elif isinstance(data, parser.KeyToValueData):
            if values:
                return impl(data.value, values=True)
            else:
                return data.key.value
        elif isinstance(data, parser.RefData):
            if values:
                path = data.value
                default = data.default
                has_default = default is not NO_DEFAULT
                if has_default:
                    try:
                        default = ast.literal_eval(default)
                    except Exception as e:
                        raise ProcessException(f"Invalid default literal value: {default}") from e
                else:
                    default = None
                has_optional = any(
                    (isinstance(p, parser.IdData) and p.optional) or (isinstance(p, parser.LocData) and p.optional)
                    for p in path
                )
                value_processor = []
                for part in path:
                    getter = get
                    if isinstance(part, parser.IdData):
                        if part.optional or (has_default and not has_optional):
                            getter = getsafe
                        key = part.value
                        if not value_processor:
                            index = headers_inverse.get(key)
                            value_processor.append(getter(index, default))
                        else:
                            value_processor.append(getter(key, default))
                    elif isinstance(part, parser.LocData):
                        if part.optional or (has_default and not has_optional):
                            getter = getsafe
                        index = part.value
                        if not value_processor:
                            if index > 0:
                                index -= 1
                        value_processor.append(getter(index, default))
                    else:
                        raise ProcessException(f"Unexpected part {part}")

                def fn(row):
                    result = row
                    for p in value_processor:
                        result = p(result)
                        if result is default:
                            break
                    return result

                return fn
            else:
                return _extract_structure_field_name(data, headers)
        else:
            raise ProcessException(f"Unsupported parser data: {data}")

    return impl(structure, values=True)


def _process_cmd(ctx, cmd) -> ProcessedCommand:
    cmd = cmd.strip()

    if cmd.startswith("@"):
        alias, *args = cmd.split(" ", 1)
        alias = alias[1:]
        macro = macros.get(alias)
        if args:
            args = macro["split"](args[0].strip())
        cmd = macro["fn"](*args)

    changed = set()
    if cmd == ":" or (ctx.processed_command and ctx.processed_command.cmd == cmd):
        return ctx.processed_command, changed

    previous_command = ctx.processed_command
    result = ProcessedCommand(cmd)

    if cmd.startswith(":") and len(cmd) >= 2:
        cmd_separator = cmd[1]
        cmd = cmd[2:]
    else:
        cmd_separator = ";"
    for expression in cmd.split(cmd_separator):
        expression = expression.strip()
        if not expression:
            continue
        if expression == "h":
            result.has_header = True
            continue
        if expression == "r":
            result.raw = True
            continue
        expression_split = expression.split(":", 1)
        if len(expression_split) < 2:
            continue
        expression_type, expression_body = expression_split
        expression_type, expression_body = expression_type.strip(), expression_body.strip()
        if expression_type not in "dhtsio":
            raise ProcessException(f"Unsupported command type: {expression_type}")
        elif expression_type == "d":
            if expression_body.startswith("\\"):
                expression_body = ast.literal_eval(f'"{expression_body}"')
            result.delimiter = expression_body or DEFAULT_CMD.delimiter
        elif expression_type == "t":
            if expression_body:
                result.types = parser.parse_types(expression_body)
            else:
                result.types = DEFAULT_CMD.types
        elif expression_type == "s":
            if expression_body:
                result.structure = parser.parse_structure(expression_body)
            else:
                result.structure = DEFAULT_CMD.structure
        elif expression_type == "i":
            if expression_body:
                result.inputs = parser.parse_processors(expression_body)
            else:
                result.input = DEFAULT_CMD.inputs
        elif expression_type == "o":
            if expression_body:
                result.outputs = parser.parse_processors(expression_body)
            else:
                result.outputs = DEFAULT_CMD.outputs
        else:
            raise ProcessException("Unexpected")

    previous_command.cmd = cmd
    ctx.processed_command = result
    for attr in ["cmd", "delimiter", "outputs", "inputs", "structure", "types", "has_header", "raw"]:
        if getattr(previous_command, attr) != getattr(result, attr):
            changed.add(attr)
    return result, changed
