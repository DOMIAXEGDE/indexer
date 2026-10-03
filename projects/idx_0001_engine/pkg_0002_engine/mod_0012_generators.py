"""Byte-exact, ordinal-addressed ports of omicron 1.c--6.cpp generators.

Specifications contain decoded Unicode text; encoding to UTF-8 happens before
Cartesian selection or reversal, matching the C++ string byte semantics. Window
and output-path controls do not participate in immutable generator namespaces.
Import accepts one complete cppdb source block; concatenated object blocks must
be split at their magic headers and imported with their individual specifications.
"""

import hashlib as mod_5101_hashlib
import json as mod_5102_json
from collections.abc import Iterator as cls_5103_Iterator, Mapping as cls_5104_Mapping


const_5105_alphabets = {
    "original": b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n",
    "safe": b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    "digits": b"0123456789",
    "lower": b"abcdefghijklmnopqrstuvwxyz",
}
const_5106_provenance = {
    "configure_1": {"legacy": "1.c", "record_format": "4.cpp"},
    "configure_2": {"legacy": "2.c", "record_format": "5.cpp"},
    "configure_3": {"legacy": "3.c", "record_format": "6.cpp"},
}
const_5107_magic = b"# cppdb-configure-source v1"


def fn_5010_integer(var_5110_value: object, var_5111_label: str) -> int:
    """Validate an actual nonnegative Python integer, excluding booleans."""
    if type(var_5110_value) is not int or var_5110_value < 0:
        raise ValueError(var_5111_label + " must be a nonnegative integer")
    return var_5110_value


def fn_5001_spec(var_5112_mapping: cls_5104_Mapping) -> dict:
    """Normalize a source specification, retaining record-affecting metadata.

Source structural limits are preserved (widths 16/18/64 and repeat 1,000,000),
but totals and ordinals use arbitrary-precision Python integers. Text is already
decoded, unlike CLI source flags that first process backslash escapes.
"""
    if not isinstance(var_5112_mapping, cls_5104_Mapping):
        raise ValueError("Generator specification must be a mapping")
    if any(not isinstance(var_5119_key, str) for var_5119_key in var_5112_mapping):
        raise ValueError("Generator field names must be text")
    var_5113_kind = var_5112_mapping.get("source_kind", "configure_1")
    if not isinstance(var_5113_kind, str) or var_5113_kind not in const_5106_provenance:
        raise ValueError("Unknown source_kind")
    var_5114_ignored = {"start", "limit", "window", "output_target", "output_path"}
    if var_5113_kind in {"configure_1", "configure_2"}:
        var_5115_allowed = {"source_kind", "alphabet_name", "width"} | var_5114_ignored
        var_5116_width = fn_5010_integer(var_5112_mapping.get("width", 4 if var_5113_kind == "configure_1" else 7), "width")
        if not 1 <= var_5116_width <= (16 if var_5113_kind == "configure_1" else 18):
            raise ValueError("Width exceeds source structural bounds")
        var_5117_alphabet = var_5112_mapping.get("alphabet_name", "original" if var_5113_kind == "configure_1" else "decimal_digits")
        if not isinstance(var_5117_alphabet, str):
            raise ValueError("alphabet_name must be text")
        var_5117_alphabet = var_5117_alphabet.lower()
        if var_5113_kind == "configure_2" and var_5117_alphabet == "digits":
            var_5117_alphabet = "decimal_digits"
        if var_5117_alphabet not in (const_5105_alphabets if var_5113_kind == "configure_1" else {"decimal_digits"}):
            raise ValueError("Unknown alphabet_name")
        var_5118_spec = {"source_kind": var_5113_kind, "width": var_5116_width, "alphabet_name": var_5117_alphabet}
    else:
        var_5118_spec = {
            "source_kind": var_5113_kind, "object_name": "x33", "input_name": "x1",
            "input_value": "0123456789", "input_width": 7, "flow_name": "x15",
            "flow_type": "cartesian", "output_name": "x31", "separator": "\n",
            "prefix": "", "suffix": "",
        }
        var_5115_allowed = set(var_5118_spec) | var_5114_ignored
        var_5118_spec.update({var_5119_key: var_5120_value for var_5119_key, var_5120_value in var_5112_mapping.items() if var_5119_key in var_5118_spec})
        var_5116_width = fn_5010_integer(var_5118_spec["input_width"], "input_width")
        if var_5116_width == 0:
            raise ValueError("input_width must be positive")
        for var_5119_key in ("object_name", "input_name", "input_value", "flow_name", "flow_type", "output_name", "separator", "prefix", "suffix"):
            if not isinstance(var_5118_spec[var_5119_key], str):
                raise ValueError(var_5119_key + " must be text")
            try:
                var_5118_spec[var_5119_key].encode("utf-8")
            except UnicodeEncodeError as var_5121_error:
                raise ValueError(var_5119_key + " must be valid Unicode") from var_5121_error
        for var_5119_key in ("object_name", "input_name", "flow_name", "output_name"):
            if not var_5118_spec[var_5119_key]:
                raise ValueError(var_5119_key + " must not be empty")
        for var_5119_key in ("input_value", "separator", "prefix", "suffix"):
            if len(var_5118_spec[var_5119_key].encode("utf-8")) > 4096:
                raise ValueError(var_5119_key + " exceeds 4096 bytes")
        var_5122_flow = var_5118_spec["flow_type"].lower()
        var_5122_flow = {"product": "cartesian", "combinations": "cartesian", "echo": "literal"}.get(var_5122_flow, var_5122_flow)
        if var_5122_flow not in {"cartesian", "literal", "repeat", "reverse"}:
            raise ValueError("Unknown flow_type")
        var_5118_spec["flow_type"] = var_5122_flow
        if var_5122_flow == "cartesian" and (not var_5118_spec["input_value"] or var_5116_width > 64):
            raise ValueError("Cartesian flow requires a nonempty input and width at most 64")
        if var_5122_flow == "repeat" and var_5116_width > 1000000:
            raise ValueError("Repeat count exceeds source structural bound 1000000")
    if set(var_5112_mapping) - var_5115_allowed:
        raise ValueError("Unknown generator fields: " + repr(sorted(set(var_5112_mapping) - var_5115_allowed)))
    return var_5118_spec


def fn_5002_namespace(var_5118_spec: cls_5104_Mapping) -> str:
    """Fingerprint normalized source semantics independently from export window."""
    var_5123_encoding = mod_5102_json.dumps({"format": "cppdb-v1-utf8-bytes", "spec": fn_5001_spec(var_5118_spec)}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "gen_" + mod_5101_hashlib.sha256(var_5123_encoding).hexdigest()


def fn_5011_alphabet(var_5118_spec: dict) -> bytes:
    """Return the source's byte alphabet without deduplicating symbols."""
    if var_5118_spec["source_kind"] == "configure_3":
        return var_5118_spec["input_value"].encode("utf-8")
    return const_5105_alphabets["digits" if var_5118_spec["source_kind"] == "configure_2" else var_5118_spec["alphabet_name"]]


def fn_5003_total(var_5118_spec: cls_5104_Mapping) -> int:
    """Return the exact count without generating any records."""
    var_5118_spec = fn_5001_spec(var_5118_spec)
    if var_5118_spec["source_kind"] != "configure_3":
        return len(fn_5011_alphabet(var_5118_spec)) ** var_5118_spec["width"]
    if var_5118_spec["flow_type"] == "repeat":
        return var_5118_spec["input_width"]
    if var_5118_spec["flow_type"] == "cartesian":
        return len(fn_5011_alphabet(var_5118_spec)) ** var_5118_spec["input_width"]
    return 1


def fn_5012_escape(var_5124_bytes: bytes) -> bytes:
    """Escape bytes exactly as C++ escape_field, retaining high bytes verbatim."""
    var_5125_output = bytearray()
    for var_5126_byte in var_5124_bytes:
        if var_5126_byte in {92, 10, 13, 9}:
            var_5125_output.extend({92: b"\\\\", 10: b"\\n", 13: b"\\r", 9: b"\\t"}[var_5126_byte])
        elif var_5126_byte < 32 or var_5126_byte == 127:
            var_5125_output.extend(("\\x%02X" % var_5126_byte).encode("ascii"))
        else:
            var_5125_output.append(var_5126_byte)
    return bytes(var_5125_output)


def fn_5013_checksum(var_5124_bytes: bytes) -> str:
    """Return the lowercase zero-padded 64-bit FNV-1a checksum."""
    var_5127_hash = 14695981039346656037
    for var_5126_byte in var_5124_bytes:
        var_5127_hash = ((var_5127_hash ^ var_5126_byte) * 1099511628211) & ((1 << 64) - 1)
    return f"{var_5127_hash:016x}"


def fn_5004_record(var_5118_spec: cls_5104_Mapping, var_5128_ordinal: int) -> dict:
    """Resolve an ordinal directly to its payload, rendering, and source fields.

Raw bytes are authoritative. The text fields are previews decoded with
replacement; hex fields preserve invalid UTF-8 produced by byte-level flows.
"""
    var_5118_spec = fn_5001_spec(var_5118_spec)
    var_5128_ordinal = fn_5010_integer(var_5128_ordinal, "ordinal")
    if var_5128_ordinal >= fn_5003_total(var_5118_spec):
        raise ValueError("Ordinal is outside the generator domain")
    var_5113_kind = var_5118_spec["source_kind"]
    var_5122_flow = var_5118_spec.get("flow_type", "cartesian")
    var_5129_input = fn_5011_alphabet(var_5118_spec)
    if var_5122_flow == "cartesian":
        var_5116_width = var_5118_spec.get("width", var_5118_spec.get("input_width"))
        var_5130_payload = bytearray(var_5116_width)
        var_5131_remainder = var_5128_ordinal
        for var_5132_position in range(var_5116_width - 1, -1, -1):
            var_5131_remainder, var_5133_index = divmod(var_5131_remainder, len(var_5129_input))
            var_5130_payload[var_5132_position] = var_5129_input[var_5133_index]
        var_5130_payload = bytes(var_5130_payload)
    else:
        var_5130_payload = var_5129_input[::-1] if var_5122_flow == "reverse" else var_5129_input
    var_5134_rendered = var_5118_spec.get("prefix", "").encode("utf-8") + var_5130_payload + var_5118_spec.get("suffix", "").encode("utf-8")
    var_5135_record = {
        "source_kind": var_5113_kind, "namespace": fn_5002_namespace(var_5118_spec),
        "ordinal": var_5128_ordinal, "payload_bytes": var_5130_payload, "rendered_bytes": var_5134_rendered,
        "payload_hex": var_5130_payload.hex(), "rendered_hex": var_5134_rendered.hex(),
        "payload_text": var_5130_payload.decode("utf-8", errors="replace"), "rendered_text": var_5134_rendered.decode("utf-8", errors="replace"),
        "byte_length": len(var_5130_payload), "fnv1a64": fn_5013_checksum(var_5134_rendered),
    }
    if var_5113_kind == "configure_3":
        var_5135_record.update({var_5119_key: var_5118_spec[var_5119_key] for var_5119_key in ("object_name", "input_name", "flow_name", "output_name", "flow_type")})
    else:
        var_5135_record.update({"role": "numeric_object_handle" if var_5113_kind == "configure_2" else "generated_symbol_candidate", "width": var_5118_spec["width"]})
    return var_5135_record


def fn_5005_generate(var_5118_spec: cls_5104_Mapping, var_5136_start: int = 0, var_5137_limit: int = 10000) -> cls_5103_Iterator[dict]:
    """Lazily iterate an explicitly bounded ordinal window (default 10,000)."""
    var_5118_spec = fn_5001_spec(var_5118_spec)
    var_5136_start = fn_5010_integer(var_5136_start, "start")
    var_5137_limit = fn_5010_integer(var_5137_limit, "limit")
    for var_5128_ordinal in range(var_5136_start, min(fn_5003_total(var_5118_spec), var_5136_start + var_5137_limit)):
        yield fn_5004_record(var_5118_spec, var_5128_ordinal)


def fn_5014_headers(var_5118_spec: dict, var_5136_start: int, var_5138_count: int) -> dict:
    """Construct ordered source metadata with original spellings and semantics."""
    var_5113_kind = var_5118_spec["source_kind"]
    var_5139_headers = {"source_kind": var_5113_kind, "role": {"configure_1": "generated_symbol_candidate", "configure_2": "numeric_object_handle", "configure_3": "configured_object_fabric"}[var_5113_kind], "record_mode": "line" if var_5113_kind == "configure_2" else "escaped_line"}
    if var_5113_kind == "configure_3":
        var_5139_headers.update({
            "object_name": var_5118_spec["object_name"], "input_name": var_5118_spec["input_name"],
            "input_width": str(var_5118_spec["input_width"]), "input_size": str(len(fn_5011_alphabet(var_5118_spec))),
            "flow_name": var_5118_spec["flow_name"], "flow_type": var_5118_spec["flow_type"],
            "output_name": var_5118_spec["output_name"], "separator": var_5118_spec["separator"],
            "prefix": var_5118_spec["prefix"], "suffix": var_5118_spec["suffix"],
        })
    else:
        var_5139_headers.update({"width": str(var_5118_spec["width"]), "alphabet_name": var_5118_spec["alphabet_name"], "alphabet_size": str(len(fn_5011_alphabet(var_5118_spec)))})
    var_5140_total = fn_5003_total(var_5118_spec)
    var_5139_headers.update({"expected_total": str(var_5140_total), "start": str(var_5136_start), "emitted_records": str(var_5138_count), "truncated": "true" if var_5136_start + var_5138_count < var_5140_total else "false"})
    return {var_5119_key: fn_5012_escape(var_5120_value.encode("utf-8")) for var_5119_key, var_5120_value in var_5139_headers.items()}


def fn_5015_line(var_5135_record: dict) -> bytes:
    """Serialize a validated record to the exact corresponding cppdb line."""
    var_5141_fields = [b"record", str(var_5135_record["ordinal"]).encode("ascii")]
    if var_5135_record["source_kind"] == "configure_3":
        var_5141_fields.extend(fn_5012_escape(var_5135_record[var_5119_key].encode("utf-8")) for var_5119_key in ("object_name", "input_name", "flow_name", "output_name", "flow_type"))
    else:
        var_5141_fields.append(var_5135_record["role"].encode("ascii"))
    var_5141_fields.extend((str(var_5135_record["byte_length"]).encode("ascii"), var_5135_record["fnv1a64"].encode("ascii"), fn_5012_escape(var_5135_record["payload_bytes"])))
    if var_5135_record["source_kind"] == "configure_3":
        var_5141_fields.append(fn_5012_escape(var_5135_record["rendered_bytes"]))
    return b"\t".join(var_5141_fields)


def fn_5006_export(var_5118_spec: cls_5104_Mapping, var_5136_start: int = 0, var_5137_limit: int = 10000) -> bytes:
    """Export one bounded cppdb block; a larger limit must be supplied explicitly."""
    var_5118_spec = fn_5001_spec(var_5118_spec)
    var_5136_start = fn_5010_integer(var_5136_start, "start")
    var_5137_limit = fn_5010_integer(var_5137_limit, "limit")
    var_5138_count = min(var_5137_limit, max(0, fn_5003_total(var_5118_spec) - var_5136_start))
    var_5142_lines = [const_5107_magic]
    var_5142_lines.extend(b"# " + var_5119_key.encode("ascii") + b"=" + var_5120_value for var_5119_key, var_5120_value in fn_5014_headers(var_5118_spec, var_5136_start, var_5138_count).items())
    var_5142_lines.extend(fn_5015_line(var_5135_record) for var_5135_record in fn_5005_generate(var_5118_spec, var_5136_start, var_5137_limit))
    return b"\n".join(var_5142_lines) + b"\n"


def fn_5016_header_integer(var_5139_headers: dict, var_5119_key: str) -> int:
    """Parse a canonical unsigned ASCII integer from required source metadata."""
    var_5120_value = var_5139_headers.get(var_5119_key, b"")
    if not var_5120_value or any(var_5126_byte < 48 or var_5126_byte > 57 for var_5126_byte in var_5120_value) or (len(var_5120_value) > 1 and var_5120_value.startswith(b"0")):
        raise ValueError("Missing or malformed integer header " + var_5119_key)
    return int(var_5120_value)


def fn_5007_import(var_5143_data: bytes, var_5118_spec: cls_5104_Mapping | None = None) -> dict:
    """Validate and import one cppdb source block with immutable source identity.

All metadata and record bytes are independently regenerated from the supplied
or reconstructible specification, verifying checksum, lengths, order, escapes,
window and truncation together. configure_3 requires the complete input spec
because its header omits input_value. LF and Windows CRLF framing are accepted.
"""
    if not isinstance(var_5143_data, bytes) or not var_5143_data.endswith(b"\n"):
        raise ValueError("Input must be a complete newline-terminated bytes block")
    var_5142_lines = var_5143_data.replace(b"\r\n", b"\n").split(b"\n")[:-1]
    if not var_5142_lines or var_5142_lines[0] != const_5107_magic:
        raise ValueError("Missing cppdb-configure-source v1 header")
    var_5139_headers = {}
    var_5144_body = []
    for var_5145_line in var_5142_lines[1:]:
        if var_5145_line == const_5107_magic:
            raise ValueError("Concatenated source blocks must be imported individually")
        if var_5145_line.startswith(b"# ") and not var_5144_body:
            var_5146_parts = var_5145_line[2:].split(b"=", 1)
            if len(var_5146_parts) != 2:
                raise ValueError("Malformed metadata header")
            try:
                var_5119_key = var_5146_parts[0].decode("ascii")
            except UnicodeDecodeError as var_5121_error:
                raise ValueError("Non-ASCII metadata key") from var_5121_error
            if var_5119_key in var_5139_headers:
                raise ValueError("Duplicate metadata header " + var_5119_key)
            var_5139_headers[var_5119_key] = var_5146_parts[1]
        else:
            var_5144_body.append(var_5145_line)
    var_5136_start = fn_5016_header_integer(var_5139_headers, "start")
    var_5138_count = fn_5016_header_integer(var_5139_headers, "emitted_records")
    if var_5138_count != len(var_5144_body):
        raise ValueError("emitted_records does not match complete record count")
    if var_5118_spec is None:
        if var_5139_headers.get("source_kind") == b"configure_3":
            raise ValueError("configure_3 import requires an explicit source specification including input_value")
        try:
            var_5118_spec = {
                "source_kind": var_5139_headers["source_kind"].decode("ascii"),
                "width": fn_5016_header_integer(var_5139_headers, "width"),
                "alphabet_name": var_5139_headers["alphabet_name"].decode("ascii"),
            }
        except (KeyError, UnicodeDecodeError) as var_5121_error:
            raise ValueError("Header cannot reconstruct a source specification") from var_5121_error
    if isinstance(var_5118_spec, cls_5104_Mapping) and var_5139_headers.get("source_kind") == b"configure_3" and "input_value" not in var_5118_spec:
        raise ValueError("configure_3 import requires explicit input_value in its source specification")
    var_5118_spec = fn_5001_spec(var_5118_spec)
    var_5147_expected = fn_5014_headers(var_5118_spec, var_5136_start, var_5138_count)
    if var_5118_spec["source_kind"] == "configure_1" and "alphabet_name" in var_5139_headers:
        var_5139_headers["alphabet_name"] = var_5139_headers["alphabet_name"].lower()
    if var_5139_headers != var_5147_expected:
        raise ValueError("Source metadata does not match its specification and window")
    if var_5138_count > max(0, fn_5003_total(var_5118_spec) - var_5136_start):
        raise ValueError("Source window exceeds generator domain")
    var_5148_records = []
    for var_5145_line, var_5135_record in zip(var_5144_body, fn_5005_generate(var_5118_spec, var_5136_start, var_5138_count), strict=True):
        if var_5145_line != fn_5015_line(var_5135_record):
            raise ValueError("Record checksum, length, metadata, escaping or ordinal disagrees with source specification")
        var_5148_records.append(var_5135_record)
    return {"spec": var_5118_spec, "namespace": fn_5002_namespace(var_5118_spec), "records": var_5148_records, "start": var_5136_start, "emitted_records": var_5138_count, "expected_total": fn_5003_total(var_5118_spec), "truncated": var_5147_expected["truncated"] == b"true"}
