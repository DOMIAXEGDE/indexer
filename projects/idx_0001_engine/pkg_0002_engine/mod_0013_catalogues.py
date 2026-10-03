"""Describe owned declarations and their wiring in the indexer's three catalogues.

The catalogue is a reproducible static map, not an interpreter of attached text.
Documentation identifiers are content-addressed names and never runtime pointers.
"""

from __future__ import annotations

import ast as mod_7004_ast
import hashlib as mod_7005_hashlib
import json as mod_7006_json
import os as mod_7007_os
from pathlib import Path as cls_7008_Path
import re as mod_7009_re
import shutil as mod_7010_shutil
import subprocess as mod_7011_subprocess
import tempfile as mod_7012_tempfile
import tomllib as mod_7013_tomllib


var_7014_pattern = mod_7009_re.compile(r"^[A-Za-z][A-Za-z0-9]*_([0-9]+)_[A-Za-z][A-Za-z0-9_]*$")
var_7015_exempt_files = {"x0.txt", "x1.txt", "x2.json", "x3.php", "x4.md", "pyproject.toml", "README.md", "LICENSE", ".gitignore", "__init__.py", "__main__.py"}
var_7016_exempt_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", ".idea", ".vscode"}
var_7017_policy = [
    "x0.txt through x4.md are the mandated indexer contract filenames.",
    "Python __dunder__ names, self/cls receiver parameters, AST visit_Node callbacks, unittest lifecycle overrides, and packaging files pyproject.toml, README.md, LICENSE, .gitignore, __init__.py and __main__.py are exempt from numbered naming; future imports are compiler directives.",
    "The unchanged contents of ref_0004_sources are provenance, not owned declarations.",
    "External library attributes, language builtin names and PHP superglobals are not owned declarations.",
    "Caches, environments, build outputs, hidden editor state, runtime_0007_state contents, *.egg-info, SQLite database/WAL/SHM files, and generated catalogue staging/lock files are excluded.",
    "Existing ancestors outside the project root and user supplied JSON keys/report column labels are outside owned naming scope.",
]


def fn_7018_id(var_7019_category: str, var_7020_identity: str) -> str:
    """Create a stable documentation ID independent of runtime integer addresses."""
    return "c_" + mod_7005_hashlib.sha256((var_7019_category + ":" + var_7020_identity).encode()).hexdigest()[:24]


def fn_7021_protocol(var_7022_name: str) -> bool:
    """Recognize Python's documented protocol spelling, including future imports."""
    return (var_7022_name.startswith("__") and var_7022_name.endswith("__")) or var_7022_name in {"annotations", "setUp", "tearDown", "setUpClass", "tearDownClass", "runTest", "defaultTestResult"} or (var_7022_name.startswith("visit_") and isinstance(getattr(mod_7004_ast, var_7022_name[6:], None), type))


def fn_7023_description(var_7024_name: str, var_7025_form: str, var_7026_doc: str | None = None) -> str:
    """Prefer semantic documentation and otherwise explain the named binding's role."""
    if var_7026_doc and var_7026_doc.strip():
        return " ".join(var_7026_doc.strip().split())
    var_7027_words = mod_7009_re.sub(r"^[A-Za-z][A-Za-z0-9]*_[0-9]+_", "", var_7024_name).replace("_", " ")
    return f"{var_7025_form.capitalize()} for {var_7027_words}; source locations and wiring identify its owners and uses."


def fn_7028_included(var_7029_path: cls_7008_Path, var_7030_root: cls_7008_Path) -> bool:
    """Exclude generated runtime state and preserved source contents from inspection."""
    var_7031_parts = var_7029_path.relative_to(var_7030_root).parts
    if any(var_7032_part in var_7016_exempt_dirs or var_7032_part.endswith(".egg-info") for var_7032_part in var_7031_parts):
        return False
    if "ref_0004_sources" in var_7031_parts[:-1] or "runtime_0007_state" in var_7031_parts[:-1]:
        return False
    if var_7029_path.name.startswith(".idx-catalogue-"):
        return False
    return var_7029_path.suffix.lower() not in {".pyc", ".pyo", ".sqlite", ".sqlite3", ".db"} and not var_7029_path.name.endswith(("-wal", "-shm"))


class cls_7033_Collector:
    """Collect named entities and static edges while retaining every occurrence."""

    def __init__(self, var_7034_root: cls_7008_Path):
        self.var_7035_root = var_7034_root
        self.var_7036_entities: dict[str, dict] = {}
        self.var_7037_edges: dict[str, dict] = {}
        self.var_7038_errors: list[str] = []
        self.var_7039_numbers: dict[int, str] = {}
        self.var_7040_files: dict[str, str] = {}

    def fn_7041_name(self, var_7042_name: str, var_7043_exempt: bool = False):
        """Check numbered ownership and reject integer reuse by distinct names."""
        if var_7043_exempt or fn_7021_protocol(var_7042_name):
            return
        var_7044_match = var_7014_pattern.fullmatch(var_7042_name)
        if not var_7044_match:
            self.var_7038_errors.append(f"Naming violation: {var_7042_name!r} must be <prefix>_<integer-id>_<suffix>.")
            return
        var_7045_number = int(var_7044_match.group(1))
        if var_7045_number in self.var_7039_numbers and self.var_7039_numbers[var_7045_number] != var_7042_name:
            self.var_7038_errors.append(f"Integer documentation number {var_7045_number} is reused by {self.var_7039_numbers[var_7045_number]!r} and {var_7042_name!r}.")
        self.var_7039_numbers[var_7045_number] = var_7042_name

    def fn_7046_entity(self, var_7047_category: str, var_7048_identity: str, var_7049_name: str, var_7050_form: str, var_7051_location: dict, var_7052_doc: str | None = None, var_7053_exempt: bool = False) -> str:
        """Register an entity or append another location of an existing named symbol."""
        var_7054_id = fn_7018_id(var_7047_category, var_7048_identity)
        self.fn_7041_name(var_7049_name, var_7053_exempt)
        if var_7054_id not in self.var_7036_entities:
            self.var_7036_entities[var_7054_id] = {"id": var_7054_id, "name": var_7049_name, "form": var_7050_form, "description": fn_7023_description(var_7049_name, var_7050_form, var_7052_doc), "origin": "source", "active": True, "locations": []}
        if var_7051_location not in self.var_7036_entities[var_7054_id]["locations"]:
            self.var_7036_entities[var_7054_id]["locations"].append(var_7051_location)
        if var_7052_doc:
            self.var_7036_entities[var_7054_id]["description"] = fn_7023_description(var_7049_name, var_7050_form, var_7052_doc)
        return var_7054_id

    def fn_7055_edge(self, var_7056_source: str, var_7057_target: str, var_7058_relation: str, var_7059_location: dict | None = None, var_7060_description: str | None = None):
        """Register a directed relationship with reproducible identity and locations."""
        var_7061_id = fn_7018_id("edge", f"{var_7056_source}:{var_7058_relation}:{var_7057_target}")
        if var_7061_id not in self.var_7037_edges:
            self.var_7037_edges[var_7061_id] = {"id": var_7061_id, "source": var_7056_source, "target": var_7057_target, "relation": var_7058_relation, "description": var_7060_description or f"{var_7058_relation.capitalize()} relationship; source occurrences give the concrete connection.", "origin": "source", "locations": []}
        if var_7059_location and var_7059_location not in self.var_7037_edges[var_7061_id]["locations"]:
            self.var_7037_edges[var_7061_id]["locations"].append(var_7059_location)


class cls_7062_PythonVisitor(mod_7004_ast.NodeVisitor):
    """Inspect Python bindings, arguments, attribute writes and executable data flow."""

    def __init__(self, var_7063_collector: cls_7033_Collector, var_7064_file: str, var_7065_file_id: str):
        self.var_7066_collector = var_7063_collector
        self.var_7067_file = var_7064_file
        self.var_7068_scope = [var_7065_file_id]
        self.var_7069_locals: set[str] = set()
        self.var_7070_pending: list[tuple] = []

    def fn_7071_location(self, var_7072_node: mod_7004_ast.AST, var_7073_role: str) -> dict:
        """Record reproducible one-based source positions for each occurrence."""
        return {"file": self.var_7067_file, "line": getattr(var_7072_node, "lineno", 1), "column": getattr(var_7072_node, "col_offset", 0) + 1, "role": var_7073_role}

    def fn_7074_binding(self, var_7075_name: str, var_7076_node: mod_7004_ast.AST, var_7077_form: str, var_7078_doc: str | None = None) -> str:
        """Connect an owned binding with its enclosing function, class, or file."""
        var_7079_location = self.fn_7071_location(var_7076_node, "declaration")
        var_7080_id = self.var_7066_collector.fn_7046_entity("symbol", var_7075_name, var_7075_name, var_7077_form, var_7079_location, var_7078_doc, var_7075_name in {"self", "cls"})
        self.var_7066_collector.fn_7055_edge(self.var_7068_scope[-1], var_7080_id, "contains", var_7079_location)
        self.var_7069_locals.add(var_7075_name)
        return var_7080_id

    def visit_FunctionDef(self, var_7081_node):
        """Describe a function, its interface and references in its body."""
        var_7082_id = self.fn_7074_binding(var_7081_node.name, var_7081_node, "function", mod_7004_ast.get_docstring(var_7081_node))
        for var_7083_decorator in var_7081_node.decorator_list:
            self.visit(var_7083_decorator)
        self.var_7068_scope.append(var_7082_id)
        for var_7084_arg in [*var_7081_node.args.posonlyargs, *var_7081_node.args.args, *var_7081_node.args.kwonlyargs, *([var_7081_node.args.vararg] if var_7081_node.args.vararg else []), *([var_7081_node.args.kwarg] if var_7081_node.args.kwarg else [])]:
            var_7085_arg_id = self.fn_7074_binding(var_7084_arg.arg, var_7084_arg, "parameter")
            self.var_7066_collector.fn_7055_edge(var_7082_id, var_7085_arg_id, "inputs", self.fn_7071_location(var_7084_arg, "input"))
        for var_7086_default in [*var_7081_node.args.defaults, *[var_7087_value for var_7087_value in var_7081_node.args.kw_defaults if var_7087_value is not None]]:
            self.visit(var_7086_default)
        if var_7081_node.returns:
            self.visit(var_7081_node.returns)
        for var_7088_statement in var_7081_node.body:
            self.visit(var_7088_statement)
        self.var_7068_scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, var_7089_node):
        """Describe a class and connect its methods and class attributes."""
        var_7090_id = self.fn_7074_binding(var_7089_node.name, var_7089_node, "class", mod_7004_ast.get_docstring(var_7089_node))
        for var_7091_base in var_7089_node.bases:
            self.visit(var_7091_base)
        self.var_7068_scope.append(var_7090_id)
        for var_7092_statement in var_7089_node.body:
            self.visit(var_7092_statement)
        self.var_7068_scope.pop()

    def visit_Name(self, var_7093_node):
        """Record assigned bindings and resolve read references after collection."""
        if isinstance(var_7093_node.ctx, mod_7004_ast.Store):
            self.fn_7074_binding(var_7093_node.id, var_7093_node, "variable")
        elif isinstance(var_7093_node.ctx, mod_7004_ast.Load):
            self.var_7070_pending.append((self.var_7068_scope[-1], var_7093_node.id, "reads", self.fn_7071_location(var_7093_node, "read")))

    def visit_Attribute(self, var_7094_node):
        """Include owned attributes but do not claim names belonging to libraries."""
        if isinstance(var_7094_node.ctx, mod_7004_ast.Store) and (var_7014_pattern.fullmatch(var_7094_node.attr) or isinstance(var_7094_node.value, mod_7004_ast.Name) and var_7094_node.value.id in {"self", "cls"}):
            self.fn_7074_binding(var_7094_node.attr, var_7094_node, "attribute")
        elif var_7014_pattern.fullmatch(var_7094_node.attr):
            self.var_7070_pending.append((self.var_7068_scope[-1], var_7094_node.attr, "reads", self.fn_7071_location(var_7094_node, "attribute read")))
        self.visit(var_7094_node.value)

    def visit_Import(self, var_7095_node):
        """Document the exact library imported by each alias."""
        for var_7096_alias in var_7095_node.names:
            self.fn_7074_binding(var_7096_alias.asname or var_7096_alias.name.split(".")[0], var_7095_node, "import alias", f"Alias for imported module {var_7096_alias.name}.")

    def visit_ImportFrom(self, var_7097_node):
        """Document explicit imported symbols, rejecting uninspectable wildcard imports."""
        if var_7097_node.module == "__future__":
            return
        for var_7098_alias in var_7097_node.names:
            if var_7098_alias.name == "*":
                self.var_7066_collector.var_7038_errors.append(f"Wildcard imports prevent catalogue coverage at {self.var_7067_file}:{var_7097_node.lineno}.")
            else:
                self.fn_7074_binding(var_7098_alias.asname or var_7098_alias.name, var_7097_node, "import alias", f"Alias for {var_7097_node.module or 'relative module'}.{var_7098_alias.name}.")

    def visit_Call(self, var_7099_node):
        """Connect call sites to owned functions and recognized persistence interfaces."""
        var_7100_name = var_7099_node.func.id if isinstance(var_7099_node.func, mod_7004_ast.Name) else var_7099_node.func.attr if isinstance(var_7099_node.func, mod_7004_ast.Attribute) else None
        if var_7100_name:
            self.var_7070_pending.append((self.var_7068_scope[-1], var_7100_name, "calls", self.fn_7071_location(var_7099_node, "call")))
        if isinstance(var_7099_node.func, mod_7004_ast.Attribute) and var_7100_name in {"execute", "executemany", "commit", "rollback", "connect", "write_text", "write_bytes", "replace"}:
            for var_7101_receiver in mod_7004_ast.walk(var_7099_node.func.value):
                if isinstance(var_7101_receiver, mod_7004_ast.Name):
                    self.var_7070_pending.append((self.var_7068_scope[-1], var_7101_receiver.id, "persistence", self.fn_7071_location(var_7099_node, "persistence")))
        self.generic_visit(var_7099_node)

    def visit_Return(self, var_7102_node):
        """Connect returned expressions to named values and constructors they use."""
        if var_7102_node.value:
            for var_7103_value in mod_7004_ast.walk(var_7102_node.value):
                if isinstance(var_7103_value, mod_7004_ast.Name):
                    self.var_7070_pending.append((self.var_7068_scope[-1], var_7103_value.id, "outputs", self.fn_7071_location(var_7103_value, "output")))
            self.visit(var_7102_node.value)

    def visit_ExceptHandler(self, var_7104_node):
        """Include exception target bindings, which are strings in the Python AST."""
        if var_7104_node.name:
            self.fn_7074_binding(var_7104_node.name, var_7104_node, "exception")
        self.generic_visit(var_7104_node)

    def visit_MatchAs(self, var_7105_node):
        """Include structural pattern matching bindings."""
        if var_7105_node.name:
            self.fn_7074_binding(var_7105_node.name, var_7105_node, "pattern binding")
        self.generic_visit(var_7105_node)

    def visit_MatchStar(self, var_7106_node):
        """Include starred structural pattern matching bindings."""
        if var_7106_node.name:
            self.fn_7074_binding(var_7106_node.name, var_7106_node, "pattern binding")

    def visit_MatchMapping(self, var_7107_node):
        """Include mapping-rest structural pattern matching bindings."""
        if var_7107_node.rest:
            self.fn_7074_binding(var_7107_node.rest, var_7107_node, "pattern binding")
        self.generic_visit(var_7107_node)

    def visit_Lambda(self, var_7277_node):
        """Document anonymous function parameters in their enclosing source scope."""
        for var_7278_arg in [*var_7277_node.args.posonlyargs, *var_7277_node.args.args, *var_7277_node.args.kwonlyargs, *([var_7277_node.args.vararg] if var_7277_node.args.vararg else []), *([var_7277_node.args.kwarg] if var_7277_node.args.kwarg else [])]:
            self.fn_7074_binding(var_7278_arg.arg, var_7278_arg, "lambda parameter")
        self.generic_visit(var_7277_node)

    def fn_7279_assignment(self, var_7280_targets, var_7281_value):
        """Connect values assigned into named variables and owned attributes."""
        if var_7281_value is None:
            return
        for var_7282_target in var_7280_targets:
            for var_7283_node in mod_7004_ast.walk(var_7282_target):
                var_7284_name = var_7283_node.id if isinstance(var_7283_node, mod_7004_ast.Name) and isinstance(var_7283_node.ctx, mod_7004_ast.Store) else var_7283_node.attr if isinstance(var_7283_node, mod_7004_ast.Attribute) and isinstance(var_7283_node.ctx, mod_7004_ast.Store) and var_7014_pattern.fullmatch(var_7283_node.attr) else None
                if var_7284_name:
                    for var_7285_value_node in mod_7004_ast.walk(var_7281_value):
                        if isinstance(var_7285_value_node, mod_7004_ast.Name):
                            self.var_7070_pending.append((fn_7018_id("symbol", var_7284_name), var_7285_value_node.id, "assigned_from", self.fn_7071_location(var_7285_value_node, "assignment input")))

    def visit_Assign(self, var_7286_node):
        """Track assignment dependencies as well as bindings and expression reads."""
        self.fn_7279_assignment(var_7286_node.targets, var_7286_node.value)
        self.generic_visit(var_7286_node)

    def visit_AnnAssign(self, var_7287_node):
        """Track typed assignments, including fields declared without a value."""
        self.fn_7279_assignment([var_7287_node.target], var_7287_node.value)
        self.generic_visit(var_7287_node)

    def visit_AugAssign(self, var_7288_node):
        """Track augmented assignment dependencies."""
        self.fn_7279_assignment([var_7288_node.target], var_7288_node.value)
        self.generic_visit(var_7288_node)


def fn_7108_php(var_7109_path: cls_7008_Path, var_7110_collector: cls_7033_Collector, var_7111_file_id: str):
    """Use PHP's tokenizer to inspect variables, declarations and function calls."""
    var_7112_php = mod_7010_shutil.which("php")
    if not var_7112_php:
        var_7110_collector.var_7038_errors.append("PHP token inspection requires the php executable on PATH.")
        return
    var_7113_program = 'foreach(token_get_all(stream_get_contents(STDIN)) as $var_7990_token){if(is_array($var_7990_token)){echo json_encode([token_name($var_7990_token[0]),$var_7990_token[1],$var_7990_token[2]]),"\\n";}else{echo json_encode(["CHAR",$var_7990_token,0]),"\\n";}}'
    try:
        var_7114_process = mod_7011_subprocess.run([var_7112_php, "-r", var_7113_program], input=var_7109_path.read_text(encoding="utf-8"), text=True, encoding="utf-8", capture_output=True, timeout=30, check=True)
        var_7115_tokens = [mod_7006_json.loads(var_7116_line) for var_7116_line in var_7114_process.stdout.splitlines()]
    except (OSError, ValueError, mod_7011_subprocess.SubprocessError) as var_7117_error:
        var_7110_collector.var_7038_errors.append(f"PHP token inspection failed: {var_7117_error}.")
        return
    var_7118_relative = var_7109_path.relative_to(var_7110_collector.var_7035_root).as_posix()
    var_7119_pending = None
    var_7120_comment = None
    var_7121_php_globals = {"GLOBALS", "_SERVER", "_GET", "_POST", "_FILES", "_COOKIE", "_SESSION", "_REQUEST", "_ENV", "this", "argc", "argv"}
    for var_7122_index, (var_7123_kind, var_7124_text, var_7125_line) in enumerate(var_7115_tokens):
        if var_7123_kind == "T_DOC_COMMENT":
            var_7120_comment = mod_7009_re.sub(r"[/\*]", "", var_7124_text).strip()
        if var_7123_kind in {"T_FUNCTION", "T_CLASS", "T_INTERFACE", "T_TRAIT", "T_CONST"}:
            var_7119_pending = var_7123_kind
        elif var_7123_kind == "T_STRING" and var_7119_pending:
            var_7126_id = var_7110_collector.fn_7046_entity("symbol", var_7124_text, var_7124_text, "PHP " + var_7119_pending[2:].lower(), {"file": var_7118_relative, "line": var_7125_line, "column": 1, "role": "declaration"}, var_7120_comment)
            var_7110_collector.fn_7055_edge(var_7111_file_id, var_7126_id, "contains")
            var_7119_pending = None
            var_7120_comment = None
        elif var_7123_kind == "T_VARIABLE" and var_7124_text[1:] not in var_7121_php_globals:
            var_7127_location = {"file": var_7118_relative, "line": var_7125_line, "column": 1, "role": "variable occurrence"}
            var_7128_id = var_7110_collector.fn_7046_entity("symbol", var_7124_text[1:], var_7124_text[1:], "PHP variable", var_7127_location)
            var_7110_collector.fn_7055_edge(var_7111_file_id, var_7128_id, "contains", var_7127_location)
        elif var_7123_kind == "CHAR" and var_7124_text in {"(", ";"}:
            var_7119_pending = None
    var_7290_depth = 0
    var_7291_scopes = [(var_7111_file_id, 0)]
    var_7292_function_name = False
    var_7293_function_id = None
    var_7294_returning = False
    var_7295_persisting = False
    for var_7129_index, (var_7130_kind, var_7131_text, var_7132_line) in enumerate(var_7115_tokens):
        if var_7130_kind == "T_FUNCTION":
            var_7292_function_name = True
            continue
        if var_7130_kind == "T_STRING" and var_7292_function_name:
            var_7293_function_id = fn_7018_id("symbol", var_7131_text)
            var_7292_function_name = False
            continue
        if var_7130_kind == "CHAR":
            if var_7131_text == "(":
                var_7292_function_name = False
            elif var_7131_text == "{":
                var_7290_depth += 1
                if var_7293_function_id:
                    var_7291_scopes.append((var_7293_function_id, var_7290_depth))
                    var_7293_function_id = None
            elif var_7131_text == "}":
                if len(var_7291_scopes) > 1 and var_7291_scopes[-1][1] == var_7290_depth:
                    var_7291_scopes.pop()
                var_7290_depth -= 1
            elif var_7131_text == ";":
                var_7294_returning = False
                var_7295_persisting = False
                var_7293_function_id = None
        elif var_7130_kind == "T_RETURN":
            var_7294_returning = True
        elif var_7130_kind == "T_VARIABLE" and var_7131_text[1:] not in var_7121_php_globals:
            var_7296_variable_id = fn_7018_id("symbol", var_7131_text[1:])
            var_7297_location = {"file": var_7118_relative, "line": var_7132_line, "column": 1, "role": "PHP data flow"}
            var_7110_collector.fn_7055_edge(var_7293_function_id or var_7291_scopes[-1][0], var_7296_variable_id, "inputs" if var_7293_function_id else "reads", var_7297_location)
            if var_7294_returning:
                var_7110_collector.fn_7055_edge(var_7291_scopes[-1][0], var_7296_variable_id, "outputs", var_7297_location)
            if var_7295_persisting:
                var_7110_collector.fn_7055_edge(var_7291_scopes[-1][0], var_7296_variable_id, "persistence", var_7297_location)
        elif var_7130_kind == "T_STRING":
            if var_7131_text in {"proc_open", "fwrite", "file_put_contents", "fopen", "session_start"}:
                var_7295_persisting = True
            if fn_7018_id("symbol", var_7131_text) in var_7110_collector.var_7036_entities:
                var_7133_next = next((var_7134_token for var_7134_token in var_7115_tokens[var_7129_index + 1:] if var_7134_token[0] not in {"T_WHITESPACE", "T_COMMENT", "T_DOC_COMMENT"}), None)
                if var_7133_next and var_7133_next[1] == "(":
                    var_7110_collector.fn_7055_edge(var_7291_scopes[-1][0], fn_7018_id("symbol", var_7131_text), "calls", {"file": var_7118_relative, "line": var_7132_line, "column": 1, "role": "PHP call"})


def fn_7135_scan(var_7136_root: cls_7008_Path) -> cls_7033_Collector:
    """Build an independent current-source inventory for generation and validation."""
    var_7137_collector = cls_7033_Collector(var_7136_root)
    var_7138_root_id = var_7137_collector.fn_7046_entity("path", ".", var_7136_root.name, "project", {"file": ".", "line": 1, "column": 1, "role": "project root"})
    var_7139_visitors: list[cls_7062_PythonVisitor] = []
    for var_7140_path in sorted(set(var_7136_root.rglob("*")) | {var_7136_root / "x0.txt", var_7136_root / "x1.txt", var_7136_root / "x2.json"}, key=lambda var_7141_item: var_7141_item.as_posix()):
        if not fn_7028_included(var_7140_path, var_7136_root):
            continue
        var_7142_relative = var_7140_path.relative_to(var_7136_root).as_posix()
        var_7143_name = var_7140_path.name if var_7140_path.is_dir() else var_7140_path.stem
        var_7144_exempt = var_7140_path.name in var_7015_exempt_files
        var_7145_id = var_7137_collector.fn_7046_entity("path", var_7142_relative, var_7143_name, "directory" if var_7140_path.is_dir() else "file", {"file": var_7142_relative, "line": 1, "column": 1, "role": "filesystem"}, var_7053_exempt=var_7144_exempt)
        var_7146_parent = var_7140_path.parent.relative_to(var_7136_root).as_posix()
        var_7137_collector.fn_7055_edge(var_7138_root_id if var_7146_parent == "." else fn_7018_id("path", var_7146_parent), var_7145_id, "contains")
        if var_7140_path.is_file() and var_7140_path.name not in {"x0.txt", "x1.txt", "x2.json"}:
            var_7137_collector.var_7040_files[var_7142_relative] = mod_7005_hashlib.sha256(var_7140_path.read_bytes()).hexdigest()
            if var_7140_path.suffix == ".py":
                try:
                    var_7147_tree = mod_7004_ast.parse(var_7140_path.read_text(encoding="utf-8-sig"), filename=var_7142_relative)
                    var_7148_visitor = cls_7062_PythonVisitor(var_7137_collector, var_7142_relative, var_7145_id)
                    var_7148_visitor.visit(var_7147_tree)
                    var_7139_visitors.append(var_7148_visitor)
                    var_7149_doc = mod_7004_ast.get_docstring(var_7147_tree)
                    if var_7149_doc:
                        var_7137_collector.var_7036_entities[var_7145_id]["description"] = fn_7023_description(var_7143_name, "module", var_7149_doc)
                except (SyntaxError, UnicodeError) as var_7150_error:
                    var_7137_collector.var_7038_errors.append(f"Python inspection failed for {var_7142_relative}: {var_7150_error}.")
            elif var_7140_path.suffix == ".php":
                fn_7108_php(var_7140_path, var_7137_collector, var_7145_id)
    for var_7151_visitor in var_7139_visitors:
        for var_7152_source, var_7153_name, var_7154_relation, var_7155_location in var_7151_visitor.var_7070_pending:
            var_7156_target = fn_7018_id("symbol", var_7153_name)
            if var_7156_target in var_7137_collector.var_7036_entities:
                var_7137_collector.fn_7055_edge(var_7152_source, var_7156_target, var_7154_relation, var_7155_location)
    return var_7137_collector


def fn_7157_digest(var_7158_value) -> str:
    """Hash normalized data so formatting changes do not alter semantic revisions."""
    return mod_7005_hashlib.sha256(mod_7006_json.dumps(var_7158_value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def fn_7159_toml_value(var_7160_value) -> str:
    """Render the catalogue's JSON-compatible values as valid TOML literals."""
    if isinstance(var_7160_value, str):
        return mod_7006_json.dumps(var_7160_value, ensure_ascii=False)
    if isinstance(var_7160_value, bool):
        return "true" if var_7160_value else "false"
    if isinstance(var_7160_value, (int, float)):
        return str(var_7160_value)
    if isinstance(var_7160_value, list):
        return "[" + ", ".join(fn_7159_toml_value(var_7161_item) for var_7161_item in var_7160_value) + "]"
    if isinstance(var_7160_value, dict):
        return "{ " + ", ".join(fn_7159_toml_value(var_7162_key) + " = " + fn_7159_toml_value(var_7163_value) for var_7162_key, var_7163_value in sorted(var_7160_value.items())) + " }"
    raise ValueError(f"Unsupported catalogue value: {type(var_7160_value).__name__}.")


def fn_7164_toml(var_7165_data: dict, var_7166_table: str) -> str:
    """Produce readable deterministic TOML with one table for each entity or edge."""
    var_7167_lines = ["# Indexer catalogue: semantic descriptions are retained by synchronization."]
    for var_7168_key, var_7169_value in sorted(var_7165_data.items()):
        if var_7168_key != var_7166_table:
            var_7167_lines.append(f"{var_7168_key} = {fn_7159_toml_value(var_7169_value)}")
    if not var_7165_data.get(var_7166_table):
        var_7167_lines.append(f"{var_7166_table} = []")
    for var_7170_row in var_7165_data.get(var_7166_table, []):
        var_7167_lines.extend(["", f"[[{var_7166_table}]]"])
        for var_7171_key, var_7172_value in var_7170_row.items():
            var_7167_lines.append(f"{var_7171_key} = {fn_7159_toml_value(var_7172_value)}")
    return "\n".join(var_7167_lines) + "\n"


def fn_7173_read(var_7174_path: cls_7008_Path, var_7175_table: str) -> dict:
    """Read TOML without interpreting comments or prose as executable instructions."""
    if not var_7174_path.exists():
        return {"schema_version": 1, var_7175_table: []}
    with var_7174_path.open("rb") as var_7176_stream:
        var_7177_data = mod_7013_tomllib.load(var_7176_stream)
    if var_7177_data.get("schema_version") != 1:
        raise ValueError(f"Unsupported catalogue schema in {var_7174_path.name}; expected 1.")
    if not isinstance(var_7177_data.get(var_7175_table), list):
        raise ValueError(f"Missing {var_7175_table} array in {var_7174_path.name}.")
    return var_7177_data


def fn_7178_recursive(var_7179_entities: list[dict], var_7180_edges: list[dict], var_7181_root: str) -> dict:
    """Expand containment once and represent cycles and shared targets as ID refs."""
    var_7182_lookup = {var_7183_entity["id"]: var_7183_entity for var_7183_entity in var_7179_entities}
    var_7184_outgoing: dict[str, list[dict]] = {}
    for var_7185_edge in var_7180_edges:
        var_7184_outgoing.setdefault(var_7185_edge["source"], []).append(var_7185_edge)
    var_7186_seen: set[str] = set()

    def fn_7187_expand(var_7188_id: str) -> dict:
        """Embed a contained entity's documented form and outgoing relationships."""
        if var_7188_id in var_7186_seen:
            return {"$ref": var_7188_id}
        var_7186_seen.add(var_7188_id)
        var_7189_node = {"entity": var_7182_lookup[var_7188_id], "relationships": []}
        for var_7190_edge in var_7184_outgoing.get(var_7188_id, []):
            var_7189_node["relationships"].append({"edge_id": var_7190_edge["id"], "relation": var_7190_edge["relation"], "description": var_7190_edge["description"], "target": fn_7187_expand(var_7190_edge["target"]) if var_7190_edge["relation"] == "contains" else {"$ref": var_7190_edge["target"]}})
        return var_7189_node

    var_7191_tree = {"root": fn_7187_expand(var_7181_root), "uncontained": []}
    for var_7192_id in sorted(var_7182_lookup):
        if var_7192_id not in var_7186_seen:
            var_7191_tree["uncontained"].append(fn_7187_expand(var_7192_id))
    return var_7191_tree


def fn_7193_render(var_7194_forms: dict, var_7195_wiring: dict) -> dict:
    """Recursively jsonify the exact normalized form and wiring catalogues."""
    return {"schema_version": 1, "source_digest": var_7194_forms.get("source_digest", ""), "catalogue_digest": fn_7157_digest([var_7194_forms, var_7195_wiring]), "policy": var_7194_forms.get("policy", []), "entities": var_7194_forms["entities"], "wiring": var_7195_wiring["edges"], "recursive": fn_7178_recursive(var_7194_forms["entities"], var_7195_wiring["edges"], fn_7018_id("path", "."))}


def fn_7196_validate(var_7197_forms: dict, var_7198_wiring: dict) -> list[str]:
    """Reject duplicate identities, blank descriptions and unresolved wire endpoints."""
    var_7199_errors: list[str] = []
    var_7200_ids: set[str] = set()
    var_7201_numbers: dict[int, str] = {}
    for var_7202_entity in var_7197_forms["entities"]:
        if not isinstance(var_7202_entity, dict) or not all(var_7203_key in var_7202_entity for var_7203_key in ("id", "name", "form", "description", "locations")):
            var_7199_errors.append("Malformed entity: require id, name, form, description and locations.")
            continue
        if var_7202_entity["id"] in var_7200_ids:
            var_7199_errors.append(f"Duplicate catalogue entity ID: {var_7202_entity['id']}.")
        var_7200_ids.add(var_7202_entity["id"])
        if not isinstance(var_7202_entity["description"], str) or var_7202_entity["description"].strip().lower() in {"", "todo", "tbd", "placeholder"}:
            var_7199_errors.append(f"Unresolved description for {var_7202_entity['name']}.")
        var_7204_match = var_7014_pattern.fullmatch(var_7202_entity["name"])
        if var_7204_match:
            var_7205_number = int(var_7204_match.group(1))
            if var_7205_number in var_7201_numbers and var_7201_numbers[var_7205_number] != var_7202_entity["name"]:
                var_7199_errors.append(f"Duplicate documentation number {var_7205_number}: {var_7201_numbers[var_7205_number]} and {var_7202_entity['name']}.")
            var_7201_numbers[var_7205_number] = var_7202_entity["name"]
    var_7206_edge_ids: set[str] = set()
    for var_7207_edge in var_7198_wiring["edges"]:
        if not isinstance(var_7207_edge, dict) or not all(var_7208_key in var_7207_edge for var_7208_key in ("id", "source", "target", "relation", "description")):
            var_7199_errors.append("Malformed edge: require id, source, target, relation and description.")
            continue
        if var_7207_edge["id"] in var_7206_edge_ids:
            var_7199_errors.append(f"Duplicate catalogue edge ID: {var_7207_edge['id']}.")
        var_7206_edge_ids.add(var_7207_edge["id"])
        if var_7207_edge["source"] not in var_7200_ids or var_7207_edge["target"] not in var_7200_ids:
            var_7199_errors.append(f"Missing wiring endpoint for {var_7207_edge['id']}: {var_7207_edge['source']} -> {var_7207_edge['target']}.")
        if not isinstance(var_7207_edge["description"], str) or not var_7207_edge["description"].strip():
            var_7199_errors.append(f"Unresolved wiring description for {var_7207_edge['id']}.")
    return var_7199_errors


def fn_7209_additions(var_7210_collector: cls_7033_Collector, var_7211_additions: list[dict] | None):
    """Attach declarative report definitions to the project documentation graph."""
    for var_7212_addition in var_7211_additions or []:
        if not isinstance(var_7212_addition, dict) or not all(var_7213_key in var_7212_addition for var_7213_key in ("name", "description")):
            raise ValueError("Report additions require name and description.")
        if not var_7212_addition["description"].strip():
            raise ValueError("Report additions require a nonempty semantic description.")
        var_7214_report = var_7210_collector.fn_7046_entity("report", var_7212_addition["name"], var_7212_addition["name"], var_7212_addition.get("form", "report"), {"file": "x0.txt", "line": 1, "column": 1, "role": "declarative report"}, var_7212_addition["description"])
        var_7210_collector.var_7036_entities[var_7214_report]["origin"] = "report"
        if "definition" in var_7212_addition:
            var_7210_collector.var_7036_entities[var_7214_report]["definition"] = var_7212_addition["definition"]
        var_7210_collector.fn_7055_edge(fn_7018_id("path", "."), var_7214_report, "contains", var_7060_description="The project registers this declarative report skill.")
        var_7215_names = {var_7216_entity["name"]: var_7216_entity["id"] for var_7216_entity in var_7210_collector.var_7036_entities.values()}
        for var_7217_wire in var_7212_addition.get("wiring", []):
            var_7218_target = var_7215_names.get(var_7217_wire["target"], var_7217_wire["target"])
            var_7210_collector.fn_7055_edge(var_7214_report, var_7218_target, var_7217_wire.get("relation", "reads"), var_7060_description=var_7217_wire.get("description", "Report definition reads the registered source entity."))
        for var_7219_edge in var_7210_collector.var_7037_edges.values():
            if var_7219_edge["source"] == var_7214_report or var_7219_edge["target"] == var_7214_report:
                var_7219_edge["origin"] = "report"


def fn_7220_write(var_7221_root: cls_7008_Path, var_7222_outputs: dict[str, str]):
    """Stage all three catalogues, replace them, and roll back on local I/O errors."""
    var_7223_old = {var_7224_name: (var_7221_root / var_7224_name).read_bytes() if (var_7221_root / var_7224_name).exists() else None for var_7224_name in var_7222_outputs}
    var_7225_staged: dict[str, cls_7008_Path] = {}
    try:
        for var_7226_name, var_7227_contents in var_7222_outputs.items():
            var_7228_fd, var_7229_path = mod_7012_tempfile.mkstemp(prefix=".idx-catalogue-", dir=var_7221_root)
            var_7225_staged[var_7226_name] = cls_7008_Path(var_7229_path)
            with mod_7007_os.fdopen(var_7228_fd, "w", encoding="utf-8", newline="\n") as var_7230_stream:
                var_7230_stream.write(var_7227_contents)
                var_7230_stream.flush()
                mod_7007_os.fsync(var_7230_stream.fileno())
        for var_7231_name, var_7232_staging in var_7225_staged.items():
            mod_7007_os.replace(var_7232_staging, var_7221_root / var_7231_name)
    except OSError:
        for var_7233_name, var_7234_contents in var_7223_old.items():
            if var_7234_contents is None:
                (var_7221_root / var_7233_name).unlink(missing_ok=True)
            else:
                (var_7221_root / var_7233_name).write_bytes(var_7234_contents)
        raise
    finally:
        for var_7235_staging in var_7225_staged.values():
            var_7235_staging.unlink(missing_ok=True)


def fn_7001_sync(var_7236_root, var_7237_additions=None) -> dict:
    """Synchronize x0/x1/x2, preserving descriptions and valid manual/report edges.

    ``additions`` is a list of {name, description, form?, definition?, wiring?}.
    Wiring rows contain target (entity name or ID), relation and description.
    Bootstrap descriptions come from code docstrings and explicit binding roles;
    blank existing documentation is rejected instead of silently overwritten.
    """
    var_7238_root = cls_7008_Path(var_7236_root).resolve()
    var_7239_lock = var_7238_root / ".idx-catalogue-lock"
    try:
        var_7240_lock_fd = mod_7007_os.open(var_7239_lock, mod_7007_os.O_CREAT | mod_7007_os.O_EXCL | mod_7007_os.O_WRONLY)
    except FileExistsError:
        return {"ok": False, "errors": ["Catalogue synchronization already has an exclusive lock; remove a stale lock only after verifying no writer is active."]}
    try:
        mod_7007_os.close(var_7240_lock_fd)
        var_7241_collector = fn_7135_scan(var_7238_root)
        var_7242_old_forms = fn_7173_read(var_7238_root / "x0.txt", "entities")
        var_7243_old_wiring = fn_7173_read(var_7238_root / "x1.txt", "edges")
        var_7244_old_errors = fn_7196_validate(var_7242_old_forms, var_7243_old_wiring)
        if var_7244_old_errors:
            return {"ok": False, "errors": var_7244_old_errors}
        for var_7245_entity in var_7242_old_forms["entities"]:
            var_7246_id = var_7245_entity["id"]
            if var_7246_id in var_7241_collector.var_7036_entities:
                var_7241_collector.var_7036_entities[var_7246_id] = {**var_7245_entity, **var_7241_collector.var_7036_entities[var_7246_id], "description": var_7245_entity["description"]}
            else:
                var_7241_collector.var_7036_entities[var_7246_id] = {**var_7245_entity, "active": var_7245_entity.get("origin") != "source"}
        for var_7247_edge in var_7243_old_wiring["edges"]:
            var_7248_id = var_7247_edge["id"]
            if var_7248_id in var_7241_collector.var_7037_edges:
                var_7241_collector.var_7037_edges[var_7248_id] = {**var_7247_edge, **var_7241_collector.var_7037_edges[var_7248_id], "description": var_7247_edge["description"]}
            elif var_7247_edge.get("origin") != "source":
                var_7241_collector.var_7037_edges[var_7248_id] = var_7247_edge
        fn_7209_additions(var_7241_collector, var_7237_additions)
        var_7249_digest = fn_7157_digest(var_7241_collector.var_7040_files)
        var_7250_forms = {**var_7242_old_forms, "schema_version": 1, "source_digest": var_7249_digest, "policy": var_7017_policy, "source_files": var_7241_collector.var_7040_files, "entities": sorted(var_7241_collector.var_7036_entities.values(), key=lambda var_7251_item: (var_7251_item["name"], var_7251_item["id"]))}
        var_7252_wiring = {**var_7243_old_wiring, "schema_version": 1, "source_digest": var_7249_digest, "edges": sorted(var_7241_collector.var_7037_edges.values(), key=lambda var_7253_item: (var_7253_item["source"], var_7253_item["relation"], var_7253_item["target"]))}
        var_7254_errors = sorted(set(var_7241_collector.var_7038_errors + fn_7196_validate(var_7250_forms, var_7252_wiring)))
        if var_7254_errors:
            return {"ok": False, "errors": var_7254_errors}
        var_7255_output = fn_7193_render(var_7250_forms, var_7252_wiring)
        fn_7220_write(var_7238_root, {"x0.txt": fn_7164_toml(var_7250_forms, "entities"), "x1.txt": fn_7164_toml(var_7252_wiring, "edges"), "x2.json": mod_7006_json.dumps(var_7255_output, sort_keys=True, indent=2, ensure_ascii=False) + "\n"})
        return {"ok": True, "errors": [], "source_digest": var_7249_digest, "catalogue_digest": var_7255_output["catalogue_digest"], "counts": {"entities": len(var_7250_forms["entities"]), "edges": len(var_7252_wiring["edges"]), "files": len(var_7241_collector.var_7040_files)}}
    except (OSError, ValueError, TypeError, KeyError) as var_7256_error:
        return {"ok": False, "errors": [str(var_7256_error)]}
    finally:
        var_7239_lock.unlink(missing_ok=True)


def fn_7002_check(var_7257_root) -> dict:
    """Check naming, documentation coverage, wiring and deterministic generated data."""
    var_7258_root = cls_7008_Path(var_7257_root).resolve()
    var_7259_collector = fn_7135_scan(var_7258_root)
    var_7260_errors = list(var_7259_collector.var_7038_errors)
    try:
        for var_7261_required in ("x0.txt", "x1.txt", "x2.json"):
            if not (var_7258_root / var_7261_required).is_file():
                var_7260_errors.append(f"Missing catalogue: {var_7261_required}.")
        var_7262_forms = fn_7173_read(var_7258_root / "x0.txt", "entities")
        var_7263_wiring = fn_7173_read(var_7258_root / "x1.txt", "edges")
        var_7260_errors.extend(fn_7196_validate(var_7262_forms, var_7263_wiring))
        var_7264_actual = {var_7265_entity["id"]: var_7265_entity for var_7265_entity in var_7262_forms["entities"]}
        for var_7266_id, var_7267_expected in var_7259_collector.var_7036_entities.items():
            if var_7266_id not in var_7264_actual:
                var_7260_errors.append(f"Undocumented declaration: {var_7267_expected['name']} ({var_7266_id}).")
            elif not var_7264_actual[var_7266_id].get("active", True) or var_7264_actual[var_7266_id].get("locations") != var_7267_expected["locations"]:
                var_7260_errors.append(f"Stale declaration locations: {var_7267_expected['name']}.")
        var_7268_edges = {var_7269_edge["id"]: var_7269_edge for var_7269_edge in var_7263_wiring["edges"]}
        for var_7270_id, var_7271_expected in var_7259_collector.var_7037_edges.items():
            if var_7270_id not in var_7268_edges:
                var_7260_errors.append(f"Missing generated wiring: {var_7270_id} ({var_7271_expected['relation']}).")
            elif var_7268_edges[var_7270_id].get("locations") != var_7271_expected["locations"]:
                var_7260_errors.append(f"Stale wiring locations: {var_7270_id}.")
        var_7272_digest = fn_7157_digest(var_7259_collector.var_7040_files)
        if var_7262_forms.get("source_digest") != var_7272_digest or var_7263_wiring.get("source_digest") != var_7272_digest or var_7262_forms.get("source_files") != var_7259_collector.var_7040_files:
            var_7260_errors.append("Stale source metadata: synchronize x0.txt, x1.txt and x2.json after code or documentation changes.")
        if not var_7260_errors:
            var_7273_generated = fn_7003_load(var_7258_root)
            if var_7273_generated != fn_7193_render(var_7262_forms, var_7263_wiring):
                var_7260_errors.append("Stale x2.json: generated metadata differs from x0.txt/x1.txt.")
        return {"ok": not var_7260_errors, "errors": sorted(set(var_7260_errors)), "counts": {"entities": len(var_7262_forms["entities"]), "edges": len(var_7263_wiring["edges"]), "files": len(var_7259_collector.var_7040_files)}}
    except (OSError, ValueError, TypeError, KeyError) as var_7274_error:
        return {"ok": False, "errors": sorted(set([*var_7260_errors, str(var_7274_error)]))}


def fn_7003_load(var_7275_root) -> dict:
    """Load x2 without executing its contents, rejecting unsupported schema versions."""
    var_7276_data = mod_7006_json.loads((cls_7008_Path(var_7275_root) / "x2.json").read_text(encoding="utf-8"))
    if var_7276_data.get("schema_version") != 1:
        raise ValueError("Unsupported x2.json schema; expected 1.")
    return var_7276_data
