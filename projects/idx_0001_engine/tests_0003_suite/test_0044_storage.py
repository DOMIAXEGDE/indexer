"""Storage, pointer isolation, snapshot, and lossless transport acceptance tests."""

import json as mod_4501_json
import pathlib as mod_4502_pathlib
import sqlite3 as mod_4503_sqlite
import tempfile as mod_4504_tempfile
import unittest as mod_4505_unittest
from unittest import mock as mod_4506_mock

from pkg_0002_engine.mod_0010_types import (
    type_0105_error, type_0112_pointer, fn_0118_pointer, fn_0121_wire, fn_0125_unwire,
)
from pkg_0002_engine.mod_0014_storage import type_1010_engine
from pkg_0002_engine.mod_0015_reports import fn_1215_request, fn_1222_activate
from pkg_0002_engine.mod_0016_commands import fn_1408_dispatch, fn_1432_json


class type_4500_storage_tests(mod_4505_unittest.TestCase):
    """Exercise permanent IDs and concurrent reads against real SQLite files."""

    def setUp(arg_4507_self):
        arg_4507_self.attr_4508_directory = mod_4504_tempfile.TemporaryDirectory()
        arg_4507_self.addCleanup(arg_4507_self.attr_4508_directory.cleanup)
        arg_4507_self.attr_4509_path = mod_4502_pathlib.Path(arg_4507_self.attr_4508_directory.name) / "db_4510_test.sqlite"

    def test_4511_restart_and_immutable_binding(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4513_first = var_4512_engine.fn_1038_register({"message": "first", "number": 10**100})
            var_4514_second = var_4512_engine.fn_1038_register({"message": "changed"})
            var_4515_namespace = var_4512_engine.attr_1027_namespace
            var_4512_engine.fn_1046_alias("current", var_4513_first)
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            arg_4507_self.assertEqual(var_4512_engine.attr_1027_namespace, var_4515_namespace)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4513_first)["target"],
                                      {"message": "first", "number": 10**100})
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve("current")["pointer"], var_4513_first.fn_0117_dict())
            var_4516_third = var_4512_engine.fn_1038_register({"message": "changed"})
            arg_4507_self.assertNotEqual(var_4514_second, var_4516_third)
            arg_4507_self.assertGreater(var_4516_third.attr_0115_id, var_4514_second.attr_0115_id)

    def test_4517_sql_guards(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4513_first = var_4512_engine.fn_1038_register({"stable": True})
            var_4512_engine.fn_1046_alias("stable", var_4513_first)
            for var_4518_sql in (
                    "UPDATE record_1017_values SET payload='null'",
                    "DELETE FROM record_1017_values",
                    "UPDATE alias_1018_revisions SET revision=9",
                    "DELETE FROM alias_1018_revisions"):
                with arg_4507_self.assertRaises(mod_4503_sqlite.IntegrityError):
                    var_4512_engine.attr_1014_connection.execute(var_4518_sql)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve("stable")["target"], {"stable": True})

    def test_4519_alias_conflicts_and_history(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4513_first = var_4512_engine.fn_1038_register("first")
            var_4514_second = var_4512_engine.fn_1038_register("second")
            var_4520_initial = var_4512_engine.fn_1046_alias("name", var_4513_first)
            arg_4507_self.assertEqual(var_4520_initial["revision"], 1)
            var_4521_update = var_4512_engine.fn_1046_alias("name", var_4514_second, 1)
            arg_4507_self.assertEqual(var_4521_update["revision"], 2)
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1046_alias("name", var_4513_first, 1)
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "revision_conflict")
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0111_details, {"actual_revision": 2})
            arg_4507_self.assertEqual(var_4512_engine.fn_1074_history("name"), [
                {"revision": 1, "target": var_4513_first.fn_0117_dict()},
                {"revision": 2, "target": var_4514_second.fn_0117_dict()}])
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve("name")["target"], "second")

    def test_4523_numeric_alias_and_explicit_integer(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4513_first = var_4512_engine.fn_1038_register("integer target")
            var_4514_second = var_4512_engine.fn_1038_register("numeric alias target")
            var_4512_engine.fn_1046_alias(str(var_4513_first.attr_0115_id), var_4514_second)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(str(var_4513_first.attr_0115_id))["target"], "numeric alias target")
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4513_first.attr_0115_id,
                var_4513_first.attr_0114_namespace, "record")["target"], "integer target")
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(str(var_4513_first))["target"], "integer target")
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1059_resolve(var_4513_first.attr_0115_id)
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "malformed_pointer")

    def test_4524_virtual_namespaces_are_distinct(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4525_configuration = var_4512_engine.fn_1028_namespace("configuration", {"alphabet": ["neutral", "toggle"]})
            var_4526_generator = var_4512_engine.fn_1028_namespace("generator", {"source_kind": "configure_2", "width": 2})
            var_4527_config_pointer = type_0112_pointer("configuration", var_4525_configuration["namespace"], 4)
            var_4528_gen_pointer = type_0112_pointer("generator", var_4526_generator["namespace"], 4)
            arg_4507_self.assertNotEqual(var_4527_config_pointer.attr_0114_namespace, var_4528_gen_pointer.attr_0114_namespace)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4527_config_pointer)["target"], (1, 1))
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4528_gen_pointer)["target"]["payload_bytes"], b"04")
            arg_4507_self.assertEqual(var_4512_engine.fn_1078_inventory(), [])
            var_4512_engine.fn_1046_alias("configuration", var_4527_config_pointer)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve("configuration")["target_type"], "configuration")
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1059_resolve(type_0112_pointer("record", var_4525_configuration["namespace"], 4))
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "namespace_mismatch")
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1028_namespace("record", {}, var_4525_configuration["namespace"])
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "namespace_mismatch")

    def test_4529_namespace_context_mismatches(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4513_first = var_4512_engine.fn_1038_register("payload", "namespace_a")
            var_4512_engine.fn_1038_register("other", "namespace_b")
            for var_4530_pointer in (var_4513_first, var_4513_first.fn_0117_dict(), str(var_4513_first)):
                with arg_4507_self.subTest(var_4530_pointer=var_4530_pointer):
                    with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                        var_4512_engine.fn_1059_resolve(var_4530_pointer, "namespace_b")
                    arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "namespace_mismatch")
            var_4512_engine.fn_1046_alias("cross", var_4513_first, 0, "namespace_b")
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve("cross", "namespace_b")["target"], "payload")

    def test_4531_alias_cycle_and_direct_cycle(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4532_reference = var_4512_engine.fn_1038_register({"alias": "loop", "namespace": var_4512_engine.attr_1027_namespace}, None, True)
            var_4512_engine.fn_1046_alias("loop", var_4532_reference)
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1059_resolve("loop")
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "cycle")
            arg_4507_self.assertGreaterEqual(len(var_4522_error.exception.attr_0111_details), 2)
        with type_1010_engine(":memory:") as var_4512_engine:
            var_4530_pointer = type_0112_pointer("record", var_4512_engine.attr_1027_namespace, 1)
            arg_4507_self.assertEqual(var_4512_engine.fn_1038_register(var_4530_pointer, None, True), var_4530_pointer)
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1059_resolve(var_4530_pointer)
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "cycle")

    def test_4533_missing_targets(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4526_generator = var_4512_engine.fn_1028_namespace("generator", {"source_kind": "configure_2", "width": 1})
            for var_4530_pointer in (
                    "missing alias", type_0112_pointer("record", var_4512_engine.attr_1027_namespace, 999),
                    type_0112_pointer("record", "unknown", 1),
                    type_0112_pointer("generator", var_4526_generator["namespace"], 10)):
                with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                    var_4512_engine.fn_1059_resolve(var_4530_pointer)
                arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "missing_target")

    def test_4534_hop_budget_and_trace(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4530_pointer = var_4512_engine.fn_1038_register("terminal")
            for var_4535_index in range(63):
                var_4530_pointer = var_4512_engine.fn_1038_register(var_4530_pointer, None, True)
            var_4536_result = var_4512_engine.fn_1059_resolve(var_4530_pointer)
            arg_4507_self.assertEqual(len(var_4536_result["trace"]), 64)
            arg_4507_self.assertEqual(var_4536_result["target"], "terminal")
            var_4530_pointer = var_4512_engine.fn_1038_register(var_4530_pointer, None, True)
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                var_4512_engine.fn_1059_resolve(var_4530_pointer)
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "resource_limit")
            arg_4507_self.assertEqual(len(var_4522_error.exception.attr_0111_details), 64)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4530_pointer, None, None, 65)["target"], "terminal")

    def test_4537_consistent_snapshot_across_alias_update(arg_4507_self):
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4538_reader:
            var_4538_reader.attr_1014_connection.execute("PRAGMA journal_mode=WAL")
            var_4513_first = var_4538_reader.fn_1038_register("old")
            var_4514_second = var_4538_reader.fn_1038_register("new")
            var_4538_reader.fn_1046_alias("secondary", var_4513_first)
            var_4532_reference = var_4538_reader.fn_1038_register({"alias": "secondary", "namespace": var_4538_reader.attr_1027_namespace}, None, True)
            var_4538_reader.fn_1046_alias("start", var_4532_reference)
            with type_1010_engine(arg_4507_self.attr_4509_path) as var_4539_writer:
                var_4540_original = var_4538_reader.fn_1052_direct
                var_4541_changes = []

                def fn_4542_intercept(arg_4543_pointer):
                    """Commit another connection's alias update after the snapshot starts."""
                    var_4544_target = var_4540_original(arg_4543_pointer)
                    if arg_4543_pointer == var_4532_reference and not var_4541_changes:
                        var_4541_changes.append(var_4539_writer.fn_1046_alias("secondary", var_4514_second, 1))
                    return var_4544_target

                with mod_4506_mock.patch.object(var_4538_reader, "fn_1052_direct", side_effect=fn_4542_intercept):
                    var_4536_result = var_4538_reader.fn_1059_resolve("start")
                arg_4507_self.assertEqual(var_4536_result["target"], "old")
                arg_4507_self.assertEqual(var_4536_result["trace"][2]["revision"], 1)
                arg_4507_self.assertEqual(var_4538_reader.fn_1059_resolve("start")["target"], "new")
                arg_4507_self.assertEqual(var_4541_changes[0]["revision"], 2)

    def test_4545_large_wire_and_binary_roundtrip(arg_4507_self):
        var_4546_payload = {"id": 10**250 + 17, "negative": -(10**250), "bytes": bytes(range(256)),
                            "nested": [0, True, False, None, "0012", {"id": 2**128}]}
        var_4547_wire = fn_0121_wire(var_4546_payload)
        arg_4507_self.assertEqual(var_4547_wire["id"]["type"], "integer")
        arg_4507_self.assertEqual(var_4547_wire["id"]["value"], str(10**250 + 17))
        arg_4507_self.assertIs(var_4547_wire["nested"][1], True)
        arg_4507_self.assertEqual(fn_0125_unwire(mod_4501_json.loads(mod_4501_json.dumps(var_4547_wire))), var_4546_payload)
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4530_pointer = var_4512_engine.fn_1038_register(var_4546_payload)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4530_pointer)["target"], var_4546_payload)

    def test_4548_reserved_tag_shapes_remain_json_objects(arg_4507_self):
        for var_4546_payload in (
                {"type": "integer", "value": "7"},
                {"type": "bytes", "encoding": "base64", "value": "YQ=="},
                {"nested": [{"type": "integer", "value": "7"}]}):
            arg_4507_self.assertEqual(fn_0125_unwire(fn_0121_wire(var_4546_payload)), var_4546_payload)
            with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
                var_4530_pointer = var_4512_engine.fn_1038_register(var_4546_payload)
                arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4530_pointer)["target"], var_4546_payload)

    def test_4549_malformed_pointer_and_wire_tags(arg_4507_self):
        for var_4550_invalid in (True, -1, {"kind": "record", "namespace": "a", "id": True},
                "idx:record:a:01", "idx:record:a:-1", "idx:unknown:a:1", "idx:record::1"):
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                fn_0118_pointer(var_4550_invalid)
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "malformed_pointer")
        for var_4550_invalid in ("01", "-0", "+1", "1.5", "", True, 1):
            with arg_4507_self.assertRaises(type_0105_error) as var_4522_error:
                fn_0125_unwire({"type": "integer", "value": var_4550_invalid})
            arg_4507_self.assertEqual(var_4522_error.exception.attr_0110_code, "invalid_input")

    def test_4551_unrestricted_decimal_digit_roundtrip(arg_4507_self):
        var_4552_huge = 10**4999 + 17
        var_4546_payload = {"id": var_4552_huge, "negative": -var_4552_huge}
        var_4547_wire = fn_0121_wire(var_4546_payload)
        arg_4507_self.assertEqual(len(var_4547_wire["id"]["value"]), 5000)
        arg_4507_self.assertEqual(fn_0125_unwire(mod_4501_json.loads(mod_4501_json.dumps(var_4547_wire))), var_4546_payload)
        var_4530_pointer = type_0112_pointer("configuration", "large_integer_test", var_4552_huge)
        arg_4507_self.assertEqual(fn_0118_pointer(str(var_4530_pointer)), var_4530_pointer)
        with type_1010_engine(arg_4507_self.attr_4509_path) as var_4512_engine:
            var_4530_pointer = var_4512_engine.fn_1038_register(var_4546_payload)
            arg_4507_self.assertEqual(var_4512_engine.fn_1059_resolve(var_4530_pointer)["target"], var_4546_payload)

    def test_4553_invalid_report_shapes_are_retained(arg_4507_self):
        with type_1010_engine(":memory:") as var_4512_engine:
            for var_4554_definition in (
                    {"name": "bad", "source": []},
                    {"name": "bad", "source": "inventory", "filters": [{"field": [], "op": "eq", "value": 1}]},
                    {"name": "bad", "source": "inventory", "columns": [None]},
                    {"name": "bad", "source": "inventory", "filters": None}):
                var_4536_result = fn_1215_request(var_4512_engine, var_4554_definition)
                arg_4507_self.assertEqual(var_4536_result["status"], "invalid")
                arg_4507_self.assertTrue(var_4536_result["diagnostic"])
            arg_4507_self.assertEqual(var_4512_engine.attr_1014_connection.execute(
                "SELECT count(*) FROM request_1020_reports WHERE status='invalid'").fetchone()[0], 4)

    def test_4555_report_evidence_matches_declared_types(arg_4507_self):
        with mod_4506_mock.patch("pkg_0002_engine.mod_0015_reports.fn_7003_load", return_value={"wiring": []}), mod_4506_mock.patch("pathlib.Path.read_bytes", return_value=b"{}"):
            for var_4556_request in (
                    {"command": "report", "name": "algebra", "evidence": {"status": ["not a string"], "outcome": None}},
                    {"command": "report", "name": "algebra", "evidence": {"status": None, "outcome": None}},
                    {"command": "report", "name": "resolution", "evidence": {"trace": "abc"}},
                    {"command": "report", "name": "resolution", "evidence": {"trace": ["not a mapping"]}}):
                var_4536_result = fn_1408_dispatch(var_4556_request, ":memory:")
                arg_4507_self.assertEqual(var_4536_result["status"], "invalid_input")
                arg_4507_self.assertIsNone(var_4536_result["outcome"])
            var_4536_result = fn_1408_dispatch({"command": "report", "name": "algebra",
                "evidence": {"status": "ok", "outcome": {"kind": "value", "id": 0}}}, ":memory:")
            arg_4507_self.assertEqual(var_4536_result["status"], "ok")
            arg_4507_self.assertEqual(var_4536_result["result"]["items"][0][0], {"role": "cell", "type": "string", "value": "ok"})

    def test_4557_nonfinite_json_stays_operational_error(arg_4507_self):
        for var_4558_constant in ("NaN", "Infinity", "-Infinity"):
            var_4559_text = '{"command":"report","name":"algebra","evidence":{"status":' + var_4558_constant + ',"outcome":null}}'
            var_4536_result = mod_4501_json.loads(fn_1432_json(var_4559_text, ":memory:"))
            arg_4507_self.assertEqual(var_4536_result["status"], "invalid_input")
            arg_4507_self.assertIsNone(var_4536_result["outcome"])

    def test_4560_generation_byte_budget_precedes_materialization(arg_4507_self):
        with mod_4506_mock.patch("pkg_0002_engine.mod_0016_commands.fn_5005_generate", side_effect=AssertionError("must not materialize oversized request")), mod_4506_mock.patch("pkg_0002_engine.mod_0016_commands.fn_5006_export", side_effect=AssertionError("must not export oversized request")):
            for var_4561_spec in (
                    {"source_kind": "configure_3", "input_value": "x" * 4096, "input_width": 1000000, "flow_type": "repeat"},
                    {"source_kind": "configure_3", "input_value": "x", "input_width": 10000, "flow_type": "repeat", "object_name": "z" * 1048576}):
                for var_4562_command in ("generate", "export"):
                    var_4536_result = fn_1408_dispatch({"command": var_4562_command,
                        "specification": var_4561_spec, "limit": 1000000}, ":memory:")
                    arg_4507_self.assertEqual(var_4536_result["status"], "resource_limit")
                    arg_4507_self.assertIsNone(var_4536_result.get("outcome"))

    def test_4563_sqlite_errors_are_operational(arg_4507_self):
        var_4536_result = fn_1408_dispatch({"command": "history", "name": {}}, ":memory:")
        arg_4507_self.assertEqual(var_4536_result["status"], "database_error")
        arg_4507_self.assertIsNone(var_4536_result["outcome"])
        var_4536_result = fn_1408_dispatch({"command": "health"}, arg_4507_self.attr_4508_directory.name)
        arg_4507_self.assertEqual(var_4536_result["status"], "database_error")

    def test_4564_report_retry_after_database_failure_reuses_identity(arg_4507_self):
        var_4565_catalogue = {"entities": []}

        def fn_4566_publish(arg_4567_root, arg_4568_additions):
            """Model successful catalogue publication without modifying the project."""
            for var_4569_addition in arg_4568_additions:
                if not any(var_4570_entity["name"] == var_4569_addition["name"] for var_4570_entity in var_4565_catalogue["entities"]):
                    var_4565_catalogue["entities"].append(dict(var_4569_addition))
            return {"ok": True}

        with type_1010_engine(":memory:") as var_4512_engine:
            var_4536_result = fn_1215_request(var_4512_engine, {"name": "retry", "source": "inventory"})
            var_4571_request_id = var_4536_result["request_id"]
            var_4512_engine.attr_1014_connection.execute(
                "CREATE TRIGGER fail_4572_publish BEFORE INSERT ON skill_1021_reports BEGIN SELECT RAISE(ABORT,'simulated registry failure'); END")
            with mod_4506_mock.patch("pkg_0002_engine.mod_0015_reports.fn_7003_load", return_value=var_4565_catalogue), mod_4506_mock.patch("pkg_0002_engine.mod_0015_reports.fn_7001_sync", side_effect=fn_4566_publish), mod_4506_mock.patch("pathlib.Path.read_bytes", return_value=b"{}"):
                with arg_4507_self.assertRaises(mod_4503_sqlite.IntegrityError):
                    fn_1222_activate(var_4512_engine, arg_4507_self.attr_4509_path.parent, var_4571_request_id)
                arg_4507_self.assertEqual(len(var_4565_catalogue["entities"]), 1)
                var_4573_name = var_4565_catalogue["entities"][0]["name"]
                var_4512_engine.attr_1014_connection.execute("DROP TRIGGER fail_4572_publish")
                var_4536_result = fn_1222_activate(var_4512_engine, arg_4507_self.attr_4509_path.parent, var_4571_request_id)
                arg_4507_self.assertEqual(var_4536_result["catalogue_entity"], var_4573_name)
                arg_4507_self.assertEqual(len(var_4565_catalogue["entities"]), 1)
                arg_4507_self.assertIn("definition", var_4565_catalogue["entities"][0])


if __name__ == "__main__":
    mod_4505_unittest.main()
