"""Independent command, transport, and declarative report integration checks."""

import json as mod_6100_json
import os as mod_6101_os
import pathlib as mod_6102_pathlib
import shutil as mod_6103_shutil
import subprocess as mod_6104_subprocess
import sys as mod_6105_sys
import tempfile as mod_6106_tempfile
import unittest as mod_6107_unittest
import http.client as mod_6183_http
import socket as mod_6184_socket
import time as mod_6185_time

from pkg_0002_engine import mod_0010_types as mod_6108_types
from pkg_0002_engine import mod_0013_catalogues as mod_6109_catalogues
from pkg_0002_engine import mod_0016_commands as mod_6110_commands


const_6111_root = mod_6102_pathlib.Path(__file__).resolve().parents[1]


class cls_6112_InterfaceTests(mod_6107_unittest.TestCase):
    """Exercise public commands through native Python and process boundaries."""

    def setUp(var_6113_self):
        """Allocate an isolated persistent database for each integration scenario."""
        var_6113_self.var_6114_temp = mod_6106_tempfile.TemporaryDirectory(prefix="idx_6114_interfaces_")
        var_6113_self.addCleanup(var_6113_self.var_6114_temp.cleanup)
        var_6113_self.var_6115_database = str(mod_6102_pathlib.Path(var_6113_self.var_6114_temp.name) / "data_6115_test.sqlite3")

    def fn_6116_dispatch(var_6113_self, var_6117_request: dict) -> dict:
        """Dispatch one native request against the scenario's persistent database."""
        return mod_6110_commands.fn_1408_dispatch(var_6117_request, var_6113_self.var_6115_database)

    def fn_6118_cli(var_6113_self, var_6119_request: object) -> tuple:
        """Invoke the module JSON transport and preserve its wire-level result."""
        var_6120_process = mod_6104_subprocess.run([mod_6105_sys.executable, "-m", "pkg_0002_engine", "--database", var_6113_self.var_6115_database, "--json-stdin"], input=mod_6100_json.dumps(mod_6108_types.fn_0121_wire(var_6119_request)), capture_output=True, text=True, encoding="utf-8", cwd=const_6111_root, timeout=30)
        var_6113_self.assertEqual(var_6120_process.stderr, "")
        return var_6120_process.returncode, mod_6100_json.loads(var_6120_process.stdout)

    def test_6121_native_registration_alias_and_context(var_6113_self):
        """Register data, create numeric text aliases, and retain error distinctions."""
        var_6122_first = var_6113_self.fn_6116_dispatch({"command": "register", "payload": {"message": "first"}})["result"]
        var_6123_second = var_6113_self.fn_6116_dispatch({"command": "register", "payload": {"message": "second"}})["result"]
        var_6124_alias = var_6113_self.fn_6116_dispatch({"command": "alias", "name": "1", "target": var_6123_second})
        var_6113_self.assertEqual(var_6124_alias["status"], "ok")
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": "1"})["result"]["target"], {"message": "second"})
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": 1, "kind": "record", "namespace": var_6122_first["namespace"]})["result"]["target"], {"message": "first"})
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "alias", "name": "1", "target": var_6122_first})["status"], "revision_conflict")
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": 1})["status"], "malformed_pointer")
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": "absent"})["status"], "missing_target")
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": dict(var_6122_first, kind="generator")})["status"], "namespace_mismatch")

    def test_6125_generate_export_import_and_resolution(var_6113_self):
        """Generator namespaces and imported archives preserve ordinal and byte data."""
        var_6126_spec = {"source_kind": "configure_3", "input_value": "aa", "input_width": 2, "prefix": "[", "suffix": "]"}
        var_6127_generated = var_6113_self.fn_6116_dispatch({"command": "generate", "specification": var_6126_spec, "start": 1, "limit": 2})
        var_6113_self.assertEqual(var_6127_generated["status"], "ok")
        var_6128_result = var_6127_generated["result"]
        var_6113_self.assertEqual([var_6129_record["ordinal"] for var_6129_record in var_6128_result["records"]], [1, 2])
        var_6113_self.assertEqual([var_6129_record["rendered_bytes"] for var_6129_record in var_6128_result["records"]], [b"[aa]", b"[aa]"])
        var_6130_resolved = var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": 2, "kind": "generator", "namespace": var_6128_result["namespace"]})
        var_6113_self.assertEqual(var_6130_resolved["result"]["target"], var_6128_result["records"][1])
        var_6131_export = var_6113_self.fn_6116_dispatch({"command": "export", "specification": var_6126_spec, "start": 1, "limit": 2})
        var_6132_imported = var_6113_self.fn_6116_dispatch({"command": "import", "data": var_6131_export["result"]["data"], "specification": var_6126_spec})
        var_6113_self.assertEqual(var_6132_imported["status"], "ok")
        var_6133_archive = var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": var_6132_imported["result"]["archive"]})["result"]["target"]
        var_6113_self.assertEqual(var_6133_archive["import"]["records"], var_6128_result["records"])
        var_6113_self.assertEqual(var_6133_archive["source_namespace"], var_6128_result["namespace"])
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": 4, "kind": "generator", "namespace": var_6128_result["namespace"]})["status"], "missing_target")

    def test_6134_huge_algebra_cli_wire(var_6113_self):
        """An integer far beyond JavaScript precision remains a typed decimal string."""
        var_6135_huge = 10**90 + 123456789
        var_6136_code, var_6137_wire = var_6113_self.fn_6118_cli({"command": "encode", "alphabet": ["single"], "configuration": [var_6135_huge]})
        var_6113_self.assertEqual(var_6136_code, 0)
        var_6113_self.assertEqual(var_6137_wire["result"]["pointer"]["id"], {"type": "integer", "value": str(var_6135_huge)})
        var_6138_pointer = mod_6108_types.fn_0125_unwire(var_6137_wire)["result"]["pointer"]
        var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": var_6138_pointer})["result"]["target"], (var_6135_huge,))
        var_6136_code, var_6137_wire = var_6113_self.fn_6118_cli({"command": "evaluate", "alphabet": ["single"], "operation": "add", "left": var_6138_pointer, "right": 1})
        var_6113_self.assertEqual(var_6136_code, 0)
        var_6139_native = mod_6108_types.fn_0125_unwire(var_6137_wire)
        var_6113_self.assertEqual(var_6139_native["result"]["outcome"]["id"], var_6135_huge + 1)

    def test_6140_cli_native_and_byte_roundtrip(var_6113_self):
        """Library and CLI agree over persistent state and base64 binary imports."""
        var_6113_self.assertEqual(var_6113_self.fn_6118_cli({"command": "health"})[1], mod_6108_types.fn_0121_wire(var_6113_self.fn_6116_dispatch({"command": "health"})))
        var_6126_spec = {"source_kind": "configure_3", "flow_type": "reverse", "input_value": "é", "input_width": 1}
        var_6136_code, var_6137_wire = var_6113_self.fn_6118_cli({"command": "export", "specification": var_6126_spec})
        var_6113_self.assertEqual(var_6136_code, 0)
        var_6113_self.assertEqual(var_6137_wire["result"]["data"]["encoding"], "base64")
        var_6141_data = mod_6108_types.fn_0125_unwire(var_6137_wire)["result"]["data"]
        var_6136_code, var_6137_wire = var_6113_self.fn_6118_cli({"command": "import", "data": var_6141_data, "specification": var_6126_spec})
        var_6113_self.assertEqual(var_6136_code, 0)
        var_6138_pointer = mod_6108_types.fn_0125_unwire(var_6137_wire)["result"]["archive"]
        var_6133_archive = var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": var_6138_pointer})["result"]["target"]
        var_6113_self.assertEqual(var_6133_archive["import"]["records"][0]["payload_bytes"], b"\xa9\xc3")

    def test_6142_cli_malformed_and_repl(var_6113_self):
        """Malformed messages stay structured, and a REPL continues after an error."""
        for var_6117_request in ([], {}, {"command": "unknown"}, {"command": "register"}, {"command": "decode", "alphabet": [], "id": 0}, {"command": "resolve", "pointer": {"bad": "shape"}}, {"command": "generate", "specification": {}, "limit": -1}):
            var_6136_code, var_6137_wire = var_6113_self.fn_6118_cli(var_6117_request)
            var_6113_self.assertEqual(var_6136_code, 2)
            var_6113_self.assertIn(var_6137_wire["status"], ("invalid_input", "malformed_pointer"))
            var_6113_self.assertIsNone(var_6137_wire["outcome"])
        var_6120_process = mod_6104_subprocess.run([mod_6105_sys.executable, "-m", "pkg_0002_engine", "--database", var_6113_self.var_6115_database, "--repl"], input=':help\n{bad json\n{"command":"health"}\n:quit\n', capture_output=True, text=True, encoding="utf-8", cwd=const_6111_root, timeout=30)
        var_6113_self.assertEqual(var_6120_process.returncode, 0)
        var_6113_self.assertEqual(var_6120_process.stderr, "")
        var_6143_responses = [mod_6100_json.loads(var_6144_line[var_6144_line.index("{"):]) for var_6144_line in var_6120_process.stdout.splitlines() if '"status"' in var_6144_line]
        var_6113_self.assertEqual([var_6145_response["status"] for var_6145_response in var_6143_responses], ["invalid_input", "ok"])

    def test_6146_php_bridge(var_6113_self):
        """Lint PHP and confirm the fixed stdin bridge uses the same engine result."""
        var_6147_php = mod_6103_shutil.which("php")
        var_6148_bridge = const_6111_root / "x3.php"
        if not var_6147_php or not var_6148_bridge.is_file():
            var_6113_self.skipTest("PHP runtime and completed x3.php required")
        var_6120_process = mod_6104_subprocess.run([var_6147_php, "-l", str(var_6148_bridge)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        var_6113_self.assertEqual(var_6120_process.returncode, 0, var_6120_process.stdout + var_6120_process.stderr)
        var_6149_environment = dict(mod_6101_os.environ, INDEXER_PYTHON=mod_6105_sys.executable, INDEXER_DATABASE=var_6113_self.var_6115_database)
        for var_6117_request in ({"command": "health"}, {"command": "encode", "alphabet": ["single"], "configuration": [10**70]}, {"command": "generate", "specification": {"source_kind": "configure_2"}, "start": 7, "limit": 1}):
            var_6120_process = mod_6104_subprocess.run([var_6147_php, str(var_6148_bridge)], input=mod_6100_json.dumps(mod_6108_types.fn_0121_wire(var_6117_request)), capture_output=True, text=True, encoding="utf-8", cwd=const_6111_root, env=var_6149_environment, timeout=30)
            var_6113_self.assertEqual(var_6120_process.returncode, 0, var_6120_process.stderr)
            var_6113_self.assertEqual(mod_6100_json.loads(var_6120_process.stdout), mod_6108_types.fn_0121_wire(var_6113_self.fn_6116_dispatch(var_6117_request)))

    def test_6186_php_http(var_6113_self):
        """Serve loopback HTML/JSON temporarily and enforce origin/host boundaries."""
        var_6147_php = mod_6103_shutil.which("php")
        var_6148_bridge = const_6111_root / "x3.php"
        if not var_6147_php or not var_6148_bridge.is_file():
            var_6113_self.skipTest("PHP runtime and completed x3.php required")
        with mod_6184_socket.socket() as var_6187_socket:
            var_6187_socket.bind(("127.0.0.1", 0))
            var_6188_port = var_6187_socket.getsockname()[1]
        var_6149_environment = dict(mod_6101_os.environ, INDEXER_PYTHON=mod_6105_sys.executable, INDEXER_DATABASE=var_6113_self.var_6115_database)
        var_6189_process = mod_6104_subprocess.Popen([var_6147_php, "-S", f"127.0.0.1:{var_6188_port}", str(var_6148_bridge)], cwd=const_6111_root, env=var_6149_environment, stdout=mod_6104_subprocess.PIPE, stderr=mod_6104_subprocess.PIPE, creationflags=getattr(mod_6104_subprocess, "CREATE_NO_WINDOW", 0))
        try:
            for var_6190_attempt in range(60):
                try:
                    with mod_6184_socket.create_connection(("127.0.0.1", var_6188_port), timeout=0.1):
                        break
                except OSError:
                    mod_6185_time.sleep(0.05)
            else:
                var_6113_self.fail("PHP loopback server did not become ready")
            var_6191_connection = mod_6183_http.HTTPConnection("127.0.0.1", var_6188_port, timeout=20)
            try:
                var_6191_connection.request("GET", "/")
                var_6192_response = var_6191_connection.getresponse()
                var_6113_self.assertEqual(var_6192_response.status, 200)
                var_6113_self.assertIn(b"Pointer resolution engine", var_6192_response.read())
                var_6191_connection.request("GET", "/?api=1&command=health")
                var_6192_response = var_6191_connection.getresponse()
                var_6113_self.assertEqual(var_6192_response.status, 200)
                var_6113_self.assertEqual(mod_6100_json.loads(var_6192_response.read()), mod_6108_types.fn_0121_wire(var_6113_self.fn_6116_dispatch({"command": "health"})))
                var_6117_request = {"command": "register", "payload": {"number": {"type": "integer", "value": str(10**100)}}}
                var_6191_connection.request("POST", "/?api=1", mod_6100_json.dumps(var_6117_request), {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{var_6188_port}"})
                var_6192_response = var_6191_connection.getresponse()
                var_6113_self.assertEqual(var_6192_response.status, 200)
                var_6138_pointer = mod_6108_types.fn_0125_unwire(mod_6100_json.loads(var_6192_response.read()))["result"]
                var_6113_self.assertEqual(var_6113_self.fn_6116_dispatch({"command": "resolve", "pointer": var_6138_pointer})["result"]["target"], {"number": 10**100})
                for var_6193_headers in ({"Content-Type": "application/json", "Origin": "http://elsewhere.invalid"}, {"Content-Type": "application/json", "Host": "elsewhere.invalid"}):
                    var_6191_connection.request("POST", "/?api=1", '{"command":"health"}', var_6193_headers)
                    var_6192_response = var_6191_connection.getresponse()
                    var_6113_self.assertEqual(var_6192_response.status, 403)
                    var_6192_response.read()
            finally:
                var_6191_connection.close()
        finally:
            var_6189_process.terminate()
            try:
                var_6189_process.communicate(timeout=10)
            except mod_6104_subprocess.TimeoutExpired:
                var_6189_process.kill()
                var_6189_process.communicate(timeout=10)


class cls_6160_ReportTests(mod_6107_unittest.TestCase):
    """Activate reports in a disposable project copy and inspect typed evidence."""

    @classmethod
    def setUpClass(var_6161_cls):
        """Create an isolated catalogue copy so the real project is never changed."""
        var_6161_cls.var_6162_temp = mod_6106_tempfile.TemporaryDirectory(prefix="idx_6162_reports_")
        var_6161_cls.addClassCleanup(var_6161_cls.var_6162_temp.cleanup)
        var_6161_cls.var_6163_root = mod_6102_pathlib.Path(var_6161_cls.var_6162_temp.name) / "idx_0001_engine"
        mod_6103_shutil.copytree(const_6111_root, var_6161_cls.var_6163_root, ignore=mod_6103_shutil.ignore_patterns("__pycache__", "*.pyc", "runtime_0007_state", "*.sqlite3", "*.sqlite3-wal", "*.sqlite3-shm", "*.egg-info", "build", "dist"))
        var_6164_sync = mod_6109_catalogues.fn_7001_sync(var_6161_cls.var_6163_root)
        if not var_6164_sync.get("ok"):
            raise AssertionError("Copied project catalogue failed synchronization: " + repr(var_6164_sync))

    def setUp(var_6113_self):
        """Separate report request registries while reusing the disposable catalogue."""
        var_6113_self.var_6165_database_temp = mod_6106_tempfile.TemporaryDirectory(prefix="idx_6165_reportsdb_")
        var_6113_self.addCleanup(var_6113_self.var_6165_database_temp.cleanup)
        var_6113_self.var_6166_database = str(mod_6102_pathlib.Path(var_6113_self.var_6165_database_temp.name) / "data_6166_reports.sqlite3")

    def fn_6167_report_command(var_6113_self, var_6117_request: dict) -> dict:
        """Route a report scenario into its isolated database and catalogue copy."""
        return mod_6110_commands.fn_1408_dispatch(var_6117_request, var_6113_self.var_6166_database, var_6113_self.var_6163_root)

    def test_6168_builtin_reports(var_6113_self):
        """Inventory and dependency expose typed rows and verifiable source coverage."""
        var_6122_first = var_6113_self.fn_6167_report_command({"command": "register", "payload": {"number": 10**80}})["result"]
        var_6169_inventory = var_6113_self.fn_6167_report_command({"command": "report", "name": "inventory"})
        var_6113_self.assertEqual(var_6169_inventory["status"], "ok", var_6169_inventory)
        var_6128_result = var_6169_inventory["result"]
        var_6113_self.assertEqual(var_6128_result["type"], "list")
        var_6113_self.assertEqual(var_6128_result["element_type"]["type"], "list")
        var_6113_self.assertEqual(var_6128_result["items"][0][1], {"role": "cell", "type": "integer", "value": str(var_6122_first["id"])})
        var_6113_self.assertEqual(var_6128_result["items"][0][3]["value"]["number"], 10**80)
        var_6113_self.assertEqual(mod_6108_types.fn_0121_wire(var_6128_result)["items"][0][3]["value"]["number"], {"type": "integer", "value": str(10**80)})
        var_6170_dependency = var_6113_self.fn_6167_report_command({"command": "report", "name": "dependency", "limit": 3})
        var_6113_self.assertEqual(var_6170_dependency["status"], "ok", var_6170_dependency)
        var_6113_self.assertEqual(len(var_6170_dependency["result"]["items"]), 3)
        var_6113_self.assertGreater(var_6170_dependency["result"]["coverage"]["source_total"], 3)
        var_6113_self.assertFalse(var_6170_dependency["result"]["coverage"]["source_complete"])
        var_6113_self.assertEqual(len(var_6170_dependency["result"]["provenance"]["catalogue_sha256"]), 64)

    def test_6171_report_activation_and_validation(var_6113_self):
        """A validated filter/group report updates catalogues and becomes executable."""
        for var_6172_value in ("a", "b", "c"):
            var_6122_first = var_6113_self.fn_6167_report_command({"command": "register", "payload": {"value": var_6172_value}})["result"]
        var_6113_self.fn_6167_report_command({"command": "register", "payload": var_6122_first, "reference": True})
        var_6173_before = (var_6113_self.var_6163_root / "x2.json").read_bytes()
        var_6174_requested = var_6113_self.fn_6167_report_command({"command": "report_request", "definition": {"name": "json_counts", "source": "inventory", "columns": ["record_type", "id"], "filters": [{"field": "record_type", "op": "eq", "value": "json"}], "group_by": ["record_type"]}})
        var_6113_self.assertEqual(var_6174_requested["result"]["status"], "validated")
        var_6175_activated = var_6113_self.fn_6167_report_command({"command": "report_activate", "request_id": var_6174_requested["result"]["request_id"]})
        var_6113_self.assertEqual(var_6175_activated["status"], "ok", var_6175_activated)
        var_6113_self.assertEqual(var_6175_activated["result"]["status"], "active")
        var_6176_after = (var_6113_self.var_6163_root / "x2.json").read_bytes()
        var_6113_self.assertNotEqual(var_6173_before, var_6176_after)
        var_6113_self.assertIn(var_6175_activated["result"]["catalogue_entity"].encode(), var_6176_after)
        var_6177_rendered = var_6113_self.fn_6167_report_command({"command": "report", "name": "json_counts"})
        var_6113_self.assertEqual(var_6177_rendered["result"]["items"], [[{"role": "cell", "type": "string", "value": "json"}, {"role": "cell", "type": "integer", "value": "3"}]])
        var_6113_self.assertTrue(mod_6109_catalogues.fn_7002_check(var_6113_self.var_6163_root)["ok"])
        var_6178_invalid = var_6113_self.fn_6167_report_command({"command": "report_request", "definition": {"name": "bad_report", "source": "inventory", "columns": ["not_a_field"]}})
        var_6113_self.assertEqual(var_6178_invalid["result"]["status"], "invalid")
        var_6113_self.assertEqual(var_6113_self.fn_6167_report_command({"command": "report_activate", "request_id": var_6178_invalid["result"]["request_id"]})["status"], "invalid_report")

    def test_6179_evidence_reports(var_6113_self):
        """Resolution and algebra reports label caller evidence and preserve outcomes."""
        var_6122_first = var_6113_self.fn_6167_report_command({"command": "register", "payload": "evidence"})["result"]
        var_6130_resolved = var_6113_self.fn_6167_report_command({"command": "resolve", "pointer": var_6122_first})["result"]
        var_6180_resolution_report = var_6113_self.fn_6167_report_command({"command": "report", "name": "resolution", "evidence": var_6130_resolved})
        var_6113_self.assertEqual(var_6180_resolution_report["status"], "ok")
        var_6113_self.assertEqual(len(var_6180_resolution_report["result"]["items"]), len(var_6130_resolved["trace"]))
        var_6181_algebra = var_6113_self.fn_6167_report_command({"command": "evaluate", "alphabet": ["single"], "operation": "add", "left": 3, "right": 4})["result"]
        var_6182_algebra_report = var_6113_self.fn_6167_report_command({"command": "report", "name": "algebra", "evidence": var_6181_algebra})
        var_6113_self.assertEqual(var_6182_algebra_report["status"], "ok", var_6182_algebra_report)
        var_6113_self.assertEqual(var_6182_algebra_report["result"]["provenance"]["evidence_origin"], "caller_supplied")
        var_6113_self.assertEqual(var_6113_self.fn_6167_report_command({"command": "report", "name": "resolution"})["status"], "invalid_input")


if __name__ == "__main__":
    mod_6107_unittest.main()
