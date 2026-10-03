"""Verify catalogue identity, source coverage, retained documentation and PHP tokens."""

from pathlib import Path as cls_8001_Path
import json as mod_8002_json
import shutil as mod_8003_shutil
import tempfile as mod_8004_tempfile
import tomllib as mod_8005_tomllib
import unittest as mod_8006_unittest

from pkg_0002_engine import mod_0013_catalogues as mod_8007_catalogues


class cls_8010_CatalogueTests(mod_8006_unittest.TestCase):
    """Exercise catalogues in isolated numbered projects with independent fixtures."""

    def setUp(self):
        self.var_8011_temporary = mod_8004_tempfile.TemporaryDirectory()
        self.var_8012_root = cls_8001_Path(self.var_8011_temporary.name) / "idx_8900_fixture"
        self.var_8012_root.mkdir()
        self.var_8013_source = self.var_8012_root / "mod_8901_fixture.py"
        self.var_8013_source.write_text('"""A catalogue fixture with an explicit semantic purpose."""\n\ndef fn_8902_double(var_8903_value):\n    """Double the supplied value."""\n    return var_8903_value * 2\n', encoding="utf-8")

    def tearDown(self):
        self.var_8011_temporary.cleanup()

    def fn_8014_sync(self, var_8015_additions=None):
        """Require a successful synchronization before testing a subsequent change."""
        var_8016_result = mod_8007_catalogues.fn_7001_sync(self.var_8012_root, var_8015_additions)
        self.assertTrue(var_8016_result["ok"], var_8016_result.get("errors"))
        return var_8016_result

    def test_8101_bootstrap_and_stability(self):
        self.fn_8014_sync()
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])
        var_8017_before = {var_8018_name: (self.var_8012_root / var_8018_name).read_bytes() for var_8018_name in ("x0.txt", "x1.txt", "x2.json")}
        self.fn_8014_sync()
        self.assertEqual(var_8017_before, {var_8018_name: (self.var_8012_root / var_8018_name).read_bytes() for var_8018_name in var_8017_before})
        var_8019_json = mod_8007_catalogues.fn_7003_load(self.var_8012_root)
        self.assertEqual(var_8019_json["schema_version"], 1)
        self.assertIn("recursive", var_8019_json)
        self.assertTrue(any(var_8020_edge["relation"] == "inputs" for var_8020_edge in var_8019_json["wiring"]))
        self.assertTrue(any(var_8020_edge["relation"] == "outputs" for var_8020_edge in var_8019_json["wiring"]))

    def test_8102_stale_source(self):
        self.fn_8014_sync()
        self.var_8013_source.write_text(self.var_8013_source.read_text(encoding="utf-8") + "\nvar_8904_extra = 3\n", encoding="utf-8")
        var_8021_checked = mod_8007_catalogues.fn_7002_check(self.var_8012_root)
        self.assertFalse(var_8021_checked["ok"])
        self.assertTrue(any("Undocumented declaration" in var_8022_error for var_8022_error in var_8021_checked["errors"]))
        self.fn_8014_sync()
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])

    def test_8103_naming_and_duplicate_numbers(self):
        self.var_8013_source.write_text("bad_name = 1\nvar_8903_first = 2\nvar_8903_second = 3\n", encoding="utf-8")
        var_8016_result = mod_8007_catalogues.fn_7001_sync(self.var_8012_root)
        self.assertFalse(var_8016_result["ok"])
        self.assertTrue(any("Naming violation" in var_8022_error for var_8022_error in var_8016_result["errors"]))
        self.assertTrue(any("reused" in var_8022_error or "Duplicate documentation" in var_8022_error for var_8022_error in var_8016_result["errors"]))
        self.assertFalse((self.var_8012_root / "x0.txt").exists())

    def test_8104_description_edits_are_retained(self):
        self.fn_8014_sync()
        var_8023_forms_path = self.var_8012_root / "x0.txt"
        var_8023_forms_path.write_text(var_8023_forms_path.read_text(encoding="utf-8").replace("Double the supplied value.", "Maintainer description: exact multiplication by two."), encoding="utf-8")
        self.assertFalse(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])
        self.fn_8014_sync()
        self.assertIn("Maintainer description: exact multiplication by two.", var_8023_forms_path.read_text(encoding="utf-8"))
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])

    def test_8105_manual_wiring_and_cycle_references(self):
        self.fn_8014_sync()
        var_8024_wiring_path = self.var_8012_root / "x1.txt"
        var_8025_function_id = mod_8007_catalogues.fn_7018_id("symbol", "fn_8902_double")
        var_8026_root_id = mod_8007_catalogues.fn_7018_id("path", ".")
        with var_8024_wiring_path.open("a", encoding="utf-8") as var_8027_stream:
            var_8027_stream.write(f'\n[[edges]]\nid = "manual-cycle"\nsource = "{var_8025_function_id}"\ntarget = "{var_8026_root_id}"\nrelation = "contains"\ndescription = "Fixture cycle for recursive graph validation."\norigin = "manual"\nlocations = []\n')
        self.fn_8014_sync()
        self.assertIn("manual-cycle", var_8024_wiring_path.read_text(encoding="utf-8"))
        self.assertIn('"$ref"', (self.var_8012_root / "x2.json").read_text(encoding="utf-8"))
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])

    def test_8106_missing_endpoint_rejects_sync(self):
        self.fn_8014_sync()
        var_8024_wiring_path = self.var_8012_root / "x1.txt"
        with var_8024_wiring_path.open("a", encoding="utf-8") as var_8027_stream:
            var_8027_stream.write('\n[[edges]]\nid = "broken"\nsource = "missing-a"\ntarget = "missing-b"\nrelation = "reads"\ndescription = "Deliberately invalid fixture."\n')
        var_8016_result = mod_8007_catalogues.fn_7001_sync(self.var_8012_root)
        self.assertFalse(var_8016_result["ok"])
        self.assertTrue(any("Missing wiring endpoint" in var_8022_error for var_8022_error in var_8016_result["errors"]))

    def test_8107_report_registration(self):
        self.fn_8014_sync([{"name": "report_8904_totals", "description": "Select and group stored records by namespace.", "definition": {"source": "inventory", "columns": ["namespace"]}, "wiring": [{"relation": "calls", "target": "fn_8902_double", "description": "Fixture report uses the doubling transformation."}]}])
        var_8019_json = mod_8007_catalogues.fn_7003_load(self.var_8012_root)
        var_8028_report = next(var_8029_entity for var_8029_entity in var_8019_json["entities"] if var_8029_entity["name"] == "report_8904_totals")
        self.assertEqual(var_8028_report["origin"], "report")
        self.assertEqual(var_8028_report["definition"]["source"], "inventory")
        self.fn_8014_sync()
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])
        self.assertTrue(any(var_8029_entity["id"] == var_8028_report["id"] and var_8029_entity["active"] for var_8029_entity in mod_8007_catalogues.fn_7003_load(self.var_8012_root)["entities"]))

    @mod_8006_unittest.skipUnless(mod_8003_shutil.which("php"), "PHP tokenizer is required")
    def test_8108_php_token_coverage(self):
        (self.var_8012_root / "x3.php").write_text("<?php\n/** Add one integer. */\nfunction fn_8904_increment($var_8905_number) { return $var_8905_number + 1; }\n$var_8906_result = fn_8904_increment(4);\n?><title>Indexer · précision · 数学</title>", encoding="utf-8")
        self.fn_8014_sync()
        var_8019_json = mod_8007_catalogues.fn_7003_load(self.var_8012_root)
        var_8030_names = {var_8029_entity["name"] for var_8029_entity in var_8019_json["entities"]}
        self.assertTrue({"fn_8904_increment", "var_8905_number", "var_8906_result"} <= var_8030_names)
        var_8034_function = mod_8007_catalogues.fn_7018_id("symbol", "fn_8904_increment")
        self.assertTrue(any(var_8020_edge["source"] == var_8034_function and var_8020_edge["relation"] == "inputs" for var_8020_edge in var_8019_json["wiring"]))
        self.assertTrue(any(var_8020_edge["source"] == var_8034_function and var_8020_edge["relation"] == "outputs" for var_8020_edge in var_8019_json["wiring"]))
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])
        (self.var_8012_root / "x3.php").write_text("<?php $bad = 1;", encoding="utf-8")
        self.assertFalse(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])

    def test_8109_exceptions_and_lambda_bindings(self):
        (self.var_8012_root / "ref_0004_sources").mkdir()
        (self.var_8012_root / "ref_0004_sources" / "1.c").write_text("int unnumbered_reference;", encoding="utf-8")
        (self.var_8012_root / "runtime_0007_state").mkdir()
        (self.var_8012_root / "runtime_0007_state" / "output.json").write_text("{}", encoding="utf-8")
        self.var_8013_source.write_text('from __future__ import annotations\nvar_8904_transform = lambda var_8905_input: var_8905_input * 2\n', encoding="utf-8")
        self.fn_8014_sync()
        self.assertTrue(any(var_8029_entity["name"] == "var_8905_input" and var_8029_entity["form"] == "lambda parameter" for var_8029_entity in mod_8007_catalogues.fn_7003_load(self.var_8012_root)["entities"]))

    def test_8110_blank_documentation_is_rejected(self):
        self.fn_8014_sync()
        var_8023_forms_path = self.var_8012_root / "x0.txt"
        var_8023_forms_path.write_text(var_8023_forms_path.read_text(encoding="utf-8").replace("Double the supplied value.", ""), encoding="utf-8")
        var_8016_result = mod_8007_catalogues.fn_7001_sync(self.var_8012_root)
        self.assertFalse(var_8016_result["ok"])
        self.assertTrue(any("Unresolved description" in var_8022_error for var_8022_error in var_8016_result["errors"]))

    def test_8111_duplicate_entity_and_stale_json(self):
        self.fn_8014_sync()
        var_8031_json_path = self.var_8012_root / "x2.json"
        var_8019_json = mod_8002_json.loads(var_8031_json_path.read_text(encoding="utf-8"))
        var_8019_json["catalogue_digest"] = "wrong"
        var_8031_json_path.write_text(mod_8002_json.dumps(var_8019_json), encoding="utf-8")
        self.assertFalse(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])
        self.fn_8014_sync()
        var_8023_forms_path = self.var_8012_root / "x0.txt"
        var_8032_forms = mod_8005_tomllib.loads(var_8023_forms_path.read_text(encoding="utf-8"))
        var_8032_forms["entities"].append(var_8032_forms["entities"][0])
        var_8023_forms_path.write_text(mod_8007_catalogues.fn_7164_toml(var_8032_forms, "entities"), encoding="utf-8")
        self.assertFalse(mod_8007_catalogues.fn_7001_sync(self.var_8012_root)["ok"])

    def test_8112_retired_entities_keep_descriptions(self):
        self.fn_8014_sync()
        self.var_8013_source.write_text('"""The fixture no longer defines a doubling operation."""\n', encoding="utf-8")
        self.fn_8014_sync()
        var_8033_retired = next(var_8029_entity for var_8029_entity in mod_8007_catalogues.fn_7003_load(self.var_8012_root)["entities"] if var_8029_entity["name"] == "fn_8902_double")
        self.assertFalse(var_8033_retired["active"])
        self.assertEqual(var_8033_retired["description"], "Double the supplied value.")
        self.assertTrue(mod_8007_catalogues.fn_7002_check(self.var_8012_root)["ok"])


if __name__ == "__main__":
    mod_8006_unittest.main()
