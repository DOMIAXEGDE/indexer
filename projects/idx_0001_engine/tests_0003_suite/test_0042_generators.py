"""Bounded independent and native differential tests for generator compatibility."""

import itertools as mod_6000_itertools
import pathlib as mod_6001_pathlib
import shutil as mod_6002_shutil
import subprocess as mod_6003_subprocess
import tempfile as mod_6004_tempfile
import unittest as mod_6005_unittest

from pkg_0002_engine import mod_0012_generators as mod_6006_generators


class cls_6007_GeneratorTests(mod_6005_unittest.TestCase):
    """Verify ordinals, byte semantics, identities, and strict source ingestion."""

    def test_6008_cartesian_independent(var_6010_self):
        """Compare direct random access with a separately enumerated byte product."""
        for var_6011_alphabet in ("original", "safe", "digits", "lower"):
            var_6012_spec = {"source_kind": "configure_1", "alphabet_name": var_6011_alphabet, "width": 2}
            var_6013_expected = mod_6000_itertools.islice(mod_6000_itertools.product(mod_6006_generators.const_5105_alphabets[var_6011_alphabet], repeat=2), 57, 78)
            var_6010_self.assertEqual([bytes(var_6014_pair) for var_6014_pair in var_6013_expected], [var_6015_record["payload_bytes"] for var_6015_record in mod_6006_generators.fn_5005_generate(var_6012_spec, 57, 21)])

    def test_6009_decimal_leading_zeros(var_6010_self):
        """Keep padded decimal payloads separate from numeric ordinal identity."""
        var_6012_spec = {"source_kind": "configure_2"}
        var_6010_self.assertEqual(mod_6006_generators.fn_5003_total(var_6012_spec), 10**7)
        var_6010_self.assertEqual(mod_6006_generators.fn_5004_record(var_6012_spec, 7)["payload_bytes"], b"0000007")
        var_6010_self.assertEqual(len(list(mod_6006_generators.fn_5005_generate(var_6012_spec))), 10000)

    def test_6016_large_ordinal_and_window(var_6010_self):
        """Resolve a 96-bit generator ordinal without traversing earlier records."""
        var_6012_spec = {"source_kind": "configure_1", "width": 16}
        var_6017_total = mod_6006_generators.fn_5003_total(var_6012_spec)
        var_6010_self.assertEqual(var_6017_total, 2**96)
        var_6010_self.assertEqual(mod_6006_generators.fn_5004_record(var_6012_spec, var_6017_total - 1)["payload_bytes"], b"\n" * 16)
        var_6010_self.assertEqual(len(list(mod_6006_generators.fn_5005_generate(var_6012_spec, var_6017_total - 2))), 2)
        for var_6018_start in (var_6017_total, var_6017_total + 8):
            var_6010_self.assertEqual(mod_6006_generators.fn_5007_import(mod_6006_generators.fn_5006_export(var_6012_spec, var_6018_start))["records"], [])

    def test_6019_byte_flows_and_duplicates(var_6010_self):
        """UTF-8 input becomes a byte alphabet; reverse does not reverse codepoints."""
        var_6012_spec = {"source_kind": "configure_3", "input_value": "é", "input_width": 2, "flow_type": "reverse", "prefix": "[", "suffix": "]", "separator": "|"}
        var_6015_record = mod_6006_generators.fn_5004_record(var_6012_spec, 0)
        var_6010_self.assertEqual(var_6015_record["payload_bytes"], b"\xa9\xc3")
        var_6010_self.assertEqual(var_6015_record["rendered_bytes"], b"[\xa9\xc3]")
        var_6010_self.assertEqual(var_6015_record["byte_length"], 2)
        var_6012_spec.update({"flow_type": "cartesian", "input_value": "aa"})
        var_6020_records = list(mod_6006_generators.fn_5005_generate(var_6012_spec))
        var_6010_self.assertEqual([var_6015_record["ordinal"] for var_6015_record in var_6020_records], [0, 1, 2, 3])
        var_6010_self.assertEqual([var_6015_record["payload_bytes"] for var_6015_record in var_6020_records], [b"aa"] * 4)
        var_6012_spec.update({"flow_type": "repeat", "input_width": 3})
        var_6010_self.assertEqual(len(list(mod_6006_generators.fn_5005_generate(var_6012_spec))), 3)
        var_6012_spec["flow_type"] = "literal"
        var_6010_self.assertEqual(mod_6006_generators.fn_5003_total(var_6012_spec), 1)

    def test_6021_namespace_and_validation(var_6010_self):
        """Only immutable source semantics affect identity; invalid inputs fail."""
        var_6012_spec = {"source_kind": "configure_1", "width": 2, "alphabet_name": "LOWER"}
        var_6022_namespace = mod_6006_generators.fn_5002_namespace(var_6012_spec)
        var_6010_self.assertEqual(var_6022_namespace, mod_6006_generators.fn_5002_namespace(dict(var_6012_spec, start=11, limit=30, output_target="elsewhere")))
        var_6010_self.assertNotEqual(var_6022_namespace, mod_6006_generators.fn_5002_namespace(dict(var_6012_spec, width=3)))
        for var_6023_invalid in ({"width": 0}, {"width": True}, {"width": "4"}, {"alphabet_name": "missing"}, {"source_kind": "other"}, {"source_kind": []}, {1: "invalid-key"}, {"typo": 3}, {"source_kind": "configure_3", "input_value": "", "flow_type": "cartesian"}):
            with var_6010_self.assertRaises(ValueError):
                mod_6006_generators.fn_5001_spec(var_6023_invalid)
        for var_6024_ordinal in (-1, True, 26**2):
            with var_6010_self.assertRaises(ValueError):
                mod_6006_generators.fn_5004_record(var_6012_spec, var_6024_ordinal)

    def test_6025_escaping_and_checksum(var_6010_self):
        """Verify published FNV basis and every special byte escape boundary."""
        var_6010_self.assertEqual(mod_6006_generators.fn_5013_checksum(b""), "cbf29ce484222325")
        var_6010_self.assertEqual(mod_6006_generators.fn_5013_checksum(b"hello"), "a430d84680aabd0b")
        var_6010_self.assertEqual(mod_6006_generators.fn_5012_escape(b"\\\n\r\t\x00\x1f \x7f\x80"), b"\\\\\\n\\r\\t\\x00\\x1F \\x7F\x80")
        var_6012_spec = {"source_kind": "configure_3", "flow_type": "literal", "input_value": "A\x00\x1f\t\r\n\\\x7fZ", "prefix": "P"}
        var_6026_data = mod_6006_generators.fn_5006_export(var_6012_spec)
        var_6010_self.assertEqual(mod_6006_generators.fn_5007_import(var_6026_data, var_6012_spec)["records"][0]["payload_bytes"], var_6012_spec["input_value"].encode())

    def test_6027_roundtrip_and_crlf(var_6010_self):
        """Import complete windows and source-compatible Windows text framing."""
        for var_6012_spec in ({"source_kind": "configure_1", "width": 2}, {"source_kind": "configure_2", "width": 2}, {"source_kind": "configure_3", "input_value": "ab", "input_width": 4}):
            var_6026_data = mod_6006_generators.fn_5006_export(var_6012_spec, 12, 8)
            var_6028_result = mod_6006_generators.fn_5007_import(var_6026_data, var_6012_spec if var_6012_spec["source_kind"] == "configure_3" else None)
            var_6010_self.assertEqual(var_6028_result["records"], list(mod_6006_generators.fn_5005_generate(var_6012_spec, 12, 8)))
            var_6010_self.assertEqual(var_6028_result, mod_6006_generators.fn_5007_import(var_6026_data.replace(b"\n", b"\r\n"), var_6012_spec))
        var_6026_data = mod_6006_generators.fn_5006_export({"source_kind": "configure_3"}, 0, 0)
        with var_6010_self.assertRaisesRegex(ValueError, "explicit source"):
            mod_6006_generators.fn_5007_import(var_6026_data)
        with var_6010_self.assertRaisesRegex(ValueError, "explicit input_value"):
            mod_6006_generators.fn_5007_import(var_6026_data, {"source_kind": "configure_3"})
        with var_6010_self.assertRaisesRegex(ValueError, "individually"):
            mod_6006_generators.fn_5007_import(var_6026_data + var_6026_data, {"source_kind": "configure_3"})

    def test_6029_reject_corruption(var_6010_self):
        """Reject tampered totals, checksums, ordering, metadata, and framing."""
        var_6026_data = mod_6006_generators.fn_5006_export({"source_kind": "configure_2", "width": 2}, 3, 3)
        var_6030_lines = var_6026_data.splitlines(keepends=True)
        var_6031_variants = [
            var_6026_data[:-1], var_6026_data + b"\n", var_6026_data + var_6030_lines[-1],
            var_6026_data.replace(b"expected_total=100", b"expected_total=99"),
            var_6026_data.replace(b"truncated=true", b"truncated=false"),
            var_6026_data.replace(b"emitted_records=3", b"emitted_records=4"),
            var_6026_data.replace(b"width=2", b"width=02"),
            var_6026_data.replace(b"# width=2\n", b"# width=2\n# width=2\n"),
            var_6026_data.replace(b"# width=2\n", b"# unknown=2\n# width=2\n"),
            var_6026_data.replace(b"record\t3\t", b"record\t4\t"),
            var_6026_data.replace(b"\t03\n", b"\t04\n"),
            var_6026_data.replace(b"numeric_object_handle\t2", b"numeric_object_handle\t3"),
            b"".join(var_6030_lines[:-2] + [var_6030_lines[-1], var_6030_lines[-2]]),
        ]
        for var_6032_variant in var_6031_variants:
            with var_6010_self.subTest(data=var_6032_variant):
                with var_6010_self.assertRaises(ValueError):
                    mod_6006_generators.fn_5007_import(var_6032_variant)


class cls_6040_NativeTests(mod_6005_unittest.TestCase):
    """Compile preserved references and compare small outputs byte for byte."""

    @classmethod
    def setUpClass(var_6041_cls):
        """Locate source fixtures and compilers, building only inside a temp dir."""
        var_6042_root = mod_6001_pathlib.Path(__file__).resolve().parents[1]
        var_6041_cls.var_6043_source = var_6042_root / "ref_0004_sources"
        if not (var_6041_cls.var_6043_source / "4.cpp").is_file():
            var_6041_cls.var_6043_source = mod_6001_pathlib.Path(r"C:\Users\dacoo\OneDrive\2026\LanguageV1\Language\omicron")
        var_6041_cls.var_6044_cxx = mod_6002_shutil.which("g++") or mod_6002_shutil.which("clang++")
        var_6041_cls.var_6045_cc = mod_6002_shutil.which("gcc") or mod_6002_shutil.which("clang")
        if not var_6041_cls.var_6044_cxx or not var_6041_cls.var_6045_cc or not (var_6041_cls.var_6043_source / "4.cpp").is_file():
            raise mod_6005_unittest.SkipTest("Native differential tests require gcc/g++ or clang and preserved reference sources")
        var_6041_cls.var_6046_temporary = mod_6004_tempfile.TemporaryDirectory(prefix="idx_6046_native_")
        var_6041_cls.addClassCleanup(var_6041_cls.var_6046_temporary.cleanup)
        var_6041_cls.var_6047_directory = mod_6001_pathlib.Path(var_6041_cls.var_6046_temporary.name)
        for var_6048_number in (4, 5, 6):
            mod_6003_subprocess.run([var_6041_cls.var_6044_cxx, "-std=c++17", "-O1", str(var_6041_cls.var_6043_source / f"{var_6048_number}.cpp"), "-o", str(var_6041_cls.var_6047_directory / f"bin_{var_6048_number}_source.exe")], check=True, capture_output=True, timeout=90)

    def fn_6049_native(var_6010_self, var_6048_number: int, var_6050_flags: list) -> bytes:
        """Run a precompiled source with explicit bounded execution and binary sink."""
        var_6051_target = var_6010_self.var_6047_directory / "data_6051_native.txt"
        var_6052_option = "--output-target" if var_6048_number == 6 else "--output"
        mod_6003_subprocess.run([str(var_6010_self.var_6047_directory / f"bin_{var_6048_number}_source.exe"), "--execute", "--overwrite", var_6052_option, str(var_6051_target)] + var_6050_flags, check=True, capture_output=True, timeout=15)
        return var_6051_target.read_bytes()

    def test_6053_cpp_alphabets(var_6010_self):
        """Match each profile including whitespace-containing original records."""
        for var_6011_alphabet in ("original", "safe", "digits", "lower"):
            var_6012_spec = {"source_kind": "configure_1", "width": 2, "alphabet_name": var_6011_alphabet}
            var_6026_data = var_6010_self.fn_6049_native(4, ["--width", "2", "--alphabet", var_6011_alphabet, "--start", "57", "--limit", "15"])
            var_6010_self.assertEqual(var_6026_data, mod_6006_generators.fn_5006_export(var_6012_spec, 57, 15))
            var_6010_self.assertEqual(mod_6006_generators.fn_5007_import(var_6026_data)["namespace"], mod_6006_generators.fn_5002_namespace(var_6012_spec))

    def test_6054_cpp_decimal(var_6010_self):
        """Match default width seven and leading-zero decimal handles."""
        var_6026_data = var_6010_self.fn_6049_native(5, ["--start", "7", "--limit", "11"])
        var_6010_self.assertEqual(var_6026_data, mod_6006_generators.fn_5006_export({"source_kind": "configure_2"}, 7, 11))

    def test_6055_cpp_flows(var_6010_self):
        """Match Cartesian, literal, repeat, reverse, escapes, and duplicate inputs."""
        for var_6056_flow in ("cartesian", "literal", "repeat", "reverse"):
            var_6012_spec = {"source_kind": "configure_3", "input_value": "a\\\n\t\rZ", "input_width": 2, "flow_type": var_6056_flow, "prefix": "<", "suffix": ">", "separator": "|"}
            var_6026_data = var_6010_self.fn_6049_native(6, ["--input-value", "a\\\\\\n\\t\\rZ", "--input-width", "2", "--flow-type", var_6056_flow, "--prefix", "<", "--suffix", ">", "--separator", "|", "--limit", "20"])
            var_6010_self.assertEqual(var_6026_data, mod_6006_generators.fn_5006_export(var_6012_spec, 0, 20))
            var_6010_self.assertEqual(mod_6006_generators.fn_5007_import(var_6026_data, var_6012_spec)["records"], list(mod_6006_generators.fn_5005_generate(var_6012_spec, 0, 20)))
        var_6012_spec = {"source_kind": "configure_3", "input_value": "aa", "input_width": 2}
        var_6010_self.assertEqual(var_6010_self.fn_6049_native(6, ["--input-value", "aa", "--input-width", "2", "--limit", "4"]), mod_6006_generators.fn_5006_export(var_6012_spec))

    def test_6057_cpp_utf8_bytes(var_6010_self):
        """Pass UTF-8 through a file to avoid Windows argv code-page conversions."""
        var_6058_config = var_6010_self.var_6047_directory / "data_6058_utf8.txt"
        var_6051_target = var_6010_self.var_6047_directory / "data_6059_utf8_result.txt"
        for var_6056_flow in ("cartesian", "reverse"):
            var_6058_config.write_text("object_name=x33\ninput_value=é\ninput_width=2\nflow_type=" + var_6056_flow + "\noutput_target=" + str(var_6051_target) + "\nend\n", encoding="utf-8")
            mod_6003_subprocess.run([str(var_6010_self.var_6047_directory / "bin_6_source.exe"), "--execute", "--overwrite", "--config", str(var_6058_config), "--limit", "4"], check=True, capture_output=True, timeout=15)
            var_6010_self.assertEqual(var_6051_target.read_bytes(), mod_6006_generators.fn_5006_export({"source_kind": "configure_3", "input_value": "é", "input_width": 2, "flow_type": var_6056_flow}))

    def test_6060_legacy_small_harnesses(var_6010_self):
        """Call legacy generators at safe width one via renamed-main harnesses."""
        for var_6048_number in (1, 2):
            var_6061_harness = var_6010_self.var_6047_directory / f"src_6061_harness{var_6048_number}.c"
            var_6062_program = var_6010_self.var_6047_directory / f"bin_6062_harness{var_6048_number}.exe"
            var_6051_target = var_6010_self.var_6047_directory / f"data_6063_legacy{var_6048_number}.bin"
            var_6064_include = (var_6010_self.var_6043_source / f"{var_6048_number}.c").as_posix()
            var_6065_code = '#define main fn_6066_reference_main\n#include "' + var_6064_include + '"\n#undef main\nint main(int var_6067_argc, char** var_6068_argv) {\nFILE* var_6069_file = fopen(var_6068_argv[1], "wb");\nif (!var_6069_file) return 2;\n'
            if var_6048_number == 1:
                var_6065_code += "OutputSink var_6070_sink = {var_6069_file, file_sink_write, file_sink_write_char};\nint var_6071_result = generate_permutations(1, &var_6070_sink);\n"
                var_6012_spec = {"source_kind": "configure_1", "width": 1}
            else:
                var_6065_code += "x3 var_6070_sink = {var_6069_file, x23, x25};\nint var_6071_result = x15(1, &var_6070_sink);\n"
                var_6012_spec = {"source_kind": "configure_2", "width": 1}
            var_6065_code += "fclose(var_6069_file); return var_6071_result ? 0 : 1; }\n"
            var_6061_harness.write_text(var_6065_code, encoding="utf-8")
            mod_6003_subprocess.run([var_6010_self.var_6045_cc, "-std=c11", str(var_6061_harness), "-o", str(var_6062_program)], check=True, capture_output=True, timeout=60)
            mod_6003_subprocess.run([str(var_6062_program), str(var_6051_target)], check=True, capture_output=True, timeout=15)
            var_6010_self.assertEqual(var_6051_target.read_bytes(), b"".join(var_6015_record["rendered_bytes"] + b"\n" for var_6015_record in mod_6006_generators.fn_5005_generate(var_6012_spec)))

    def test_6072_legacy_configurator(var_6010_self):
        """Compare all legacy configurable flows using a small, explicit alphabet."""
        var_6062_program = var_6010_self.var_6047_directory / "bin_6073_configurator.exe"
        mod_6003_subprocess.run([var_6010_self.var_6045_cc, "-std=c11", str(var_6010_self.var_6043_source / "3.c"), "-o", str(var_6062_program)], check=True, capture_output=True, timeout=60)
        var_6051_target = var_6010_self.var_6047_directory / "data_6074_configurator.txt"
        for var_6056_flow in ("cartesian", "literal", "repeat", "reverse"):
            mod_6003_subprocess.run([str(var_6062_program), "--input-value", "01", "--input-width", "2", "--flow-type", var_6056_flow, "--prefix", "<", "--suffix", ">", "--separator", "|", "--output-target", str(var_6051_target)], check=True, capture_output=True, timeout=15)
            var_6012_spec = {"source_kind": "configure_3", "input_value": "01", "input_width": 2, "flow_type": var_6056_flow, "prefix": "<", "suffix": ">", "separator": "|"}
            var_6010_self.assertEqual(var_6051_target.read_bytes(), b"".join(var_6015_record["rendered_bytes"] + b"|" for var_6015_record in mod_6006_generators.fn_5005_generate(var_6012_spec)))


if __name__ == "__main__":
    mod_6005_unittest.main()
