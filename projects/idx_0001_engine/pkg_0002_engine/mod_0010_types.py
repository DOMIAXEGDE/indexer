"""Lossless wire types and explicitly namespaced logical pointers."""
from __future__ import annotations

import base64 as mod_0101_base64
import dataclasses as mod_0102_dataclasses
import re as mod_0103_re
from typing import Any as type_0104_any


class type_0105_error(Exception):
    """An operational error, separate from a mathematical undefined outcome."""
    def __init__(var_0106_self, var_0107_code: str, var_0108_message: str, var_0109_details=None):
        super().__init__(var_0108_message)
        var_0106_self.attr_0110_code = var_0107_code
        var_0106_self.attr_0111_details = var_0109_details


@mod_0102_dataclasses.dataclass(frozen=True)
class type_0112_pointer:
    """A permanent address within one record, generator, or configuration namespace."""
    attr_0113_kind: str
    attr_0114_namespace: str
    attr_0115_id: int

    def __post_init__(var_0116_self):
        if var_0116_self.attr_0113_kind not in ('record', 'generator', 'configuration'):
            raise type_0105_error('malformed_pointer', 'Unknown pointer kind.')
        if not isinstance(var_0116_self.attr_0114_namespace, str) or not mod_0103_re.fullmatch(r'[A-Za-z0-9_.-]+', var_0116_self.attr_0114_namespace):
            raise type_0105_error('malformed_pointer', 'Namespace must contain letters, digits, dot, underscore, or hyphen.')
        if type(var_0116_self.attr_0115_id) is not int or var_0116_self.attr_0115_id < 0:
            raise type_0105_error('malformed_pointer', 'Pointer ID must be a nonnegative integer.')

    def __str__(var_0116_self):
        return f'idx:{var_0116_self.attr_0113_kind}:{var_0116_self.attr_0114_namespace}:' + fn_0129_decimal(var_0116_self.attr_0115_id)

    def fn_0117_dict(var_0116_self):
        """Expose ordinary protocol field names without losing integer precision."""
        return {'kind': var_0116_self.attr_0113_kind, 'namespace': var_0116_self.attr_0114_namespace, 'id': var_0116_self.attr_0115_id}


def fn_0118_pointer(var_0119_value: type_0104_any) -> type_0112_pointer:
    """Parse an explicit pointer; ordinary alias text is handled by the resolver."""
    if isinstance(var_0119_value, type_0112_pointer):
        return var_0119_value
    if isinstance(var_0119_value, dict) and set(var_0119_value) == {'kind', 'namespace', 'id'}:
        return type_0112_pointer(var_0119_value['kind'], var_0119_value['namespace'], var_0119_value['id'])
    if isinstance(var_0119_value, str):
        var_0120_parts = var_0119_value.split(':')
        if len(var_0120_parts) == 4 and var_0120_parts[0] == 'idx' and mod_0103_re.fullmatch(r'0|[1-9][0-9]*', var_0120_parts[3]):
            return type_0112_pointer(var_0120_parts[1], var_0120_parts[2], fn_0134_integer(var_0120_parts[3]))
    raise type_0105_error('malformed_pointer', 'Expected a structured pointer or idx:<kind>:<namespace>:<id>.')


def fn_0121_wire(var_0122_value):
    """Encode every integer and byte sequence with an explicit lossless JSON type."""
    if isinstance(var_0122_value, type_0112_pointer):
        return fn_0121_wire(var_0122_value.fn_0117_dict())
    if type(var_0122_value) is int:
        return {'type': 'integer', 'value': fn_0129_decimal(var_0122_value)}
    if isinstance(var_0122_value, bytes):
        return {'type': 'bytes', 'encoding': 'base64', 'value': mod_0101_base64.b64encode(var_0122_value).decode('ascii')}
    if isinstance(var_0122_value, (list, tuple)):
        return [fn_0121_wire(var_0123_item) for var_0123_item in var_0122_value]
    if isinstance(var_0122_value, dict):
        if any(not isinstance(var_0124_key, str) for var_0124_key in var_0122_value):
            raise type_0105_error('invalid_input', 'JSON object keys must be strings.')
        if (set(var_0122_value) == {'type', 'value'} and var_0122_value.get('type') == 'integer') or (set(var_0122_value) == {'type', 'encoding', 'value'} and var_0122_value.get('type') == 'bytes') or (set(var_0122_value) == {'type', 'entries'} and var_0122_value.get('type') == 'object'):
            return {'type': 'object', 'entries': [[var_0124_key, fn_0121_wire(var_0123_item)] for var_0124_key, var_0123_item in var_0122_value.items()]}
        return {var_0124_key: fn_0121_wire(var_0123_item) for var_0124_key, var_0123_item in var_0122_value.items()}
    return var_0122_value


def fn_0125_unwire(var_0126_value):
    """Decode reserved integer/bytes tags; plain JSON integers are also accepted."""
    if isinstance(var_0126_value, dict):
        if set(var_0126_value) == {'type', 'entries'} and var_0126_value.get('type') == 'object':
            if not isinstance(var_0126_value['entries'], list) or any(not isinstance(var_0128_item, list) or len(var_0128_item) != 2 or not isinstance(var_0128_item[0], str) for var_0128_item in var_0126_value['entries']):
                raise type_0105_error('invalid_input', 'Malformed escaped object.')
            if len({var_0128_item[0] for var_0128_item in var_0126_value['entries']}) != len(var_0126_value['entries']):
                raise type_0105_error('invalid_input', 'Duplicate escaped object keys.')
            return {var_0127_key: fn_0125_unwire(var_0128_item) for var_0127_key, var_0128_item in var_0126_value['entries']}
        if set(var_0126_value) == {'type', 'value'} and var_0126_value['type'] == 'integer':
            if not isinstance(var_0126_value['value'], str) or not mod_0103_re.fullmatch(r'0|-?[1-9][0-9]*', var_0126_value['value']):
                raise type_0105_error('invalid_input', 'Malformed tagged integer.')
            return fn_0134_integer(var_0126_value['value'])
        if set(var_0126_value) == {'type', 'encoding', 'value'} and var_0126_value['type'] == 'bytes':
            if var_0126_value['encoding'] != 'base64':
                raise type_0105_error('invalid_input', 'Unsupported byte encoding.')
            return mod_0101_base64.b64decode(var_0126_value['value'], validate=True)
        return {var_0127_key: fn_0125_unwire(var_0128_item) for var_0127_key, var_0128_item in var_0126_value.items()}
    if isinstance(var_0126_value, list):
        return [fn_0125_unwire(var_0128_item) for var_0128_item in var_0126_value]
    return var_0126_value


def fn_0129_decimal(var_0130_number):
    """Format exact integers without altering Python's global decimal conversion guard."""
    var_0131_chunks = []
    var_0132_sign = '-' if var_0130_number < 0 else ''
    var_0130_number = abs(var_0130_number)
    if var_0130_number == 0:
        return '0'
    while var_0130_number:
        var_0130_number, var_0133_chunk = divmod(var_0130_number, 1000000000)
        var_0131_chunks.append(var_0133_chunk)
    return var_0132_sign + str(var_0131_chunks[-1]) + ''.join(f'{var_0133_chunk:09d}' for var_0133_chunk in reversed(var_0131_chunks[:-1]))


def fn_0134_integer(var_0135_decimal):
    """Parse an already validated decimal string in bounded-size chunks."""
    var_0136_negative = var_0135_decimal.startswith('-')
    var_0135_decimal = var_0135_decimal.lstrip('-')
    var_0137_number = 0
    for var_0138_position in range(0, len(var_0135_decimal), 9):
        var_0139_segment = var_0135_decimal[var_0138_position:var_0138_position + 9]
        var_0137_number = var_0137_number * 10 ** len(var_0139_segment) + int(var_0139_segment)
    return -var_0137_number if var_0136_negative else var_0137_number
