"""SQLite append-only records, revisioned aliases, and snapshot pointer resolution.

Records and alias revisions persist as immutable rows. Namespaces describe the
address model; configuration ranks and generator ordinals need no materialization.
"""
from __future__ import annotations

import contextlib as mod_1001_contextlib
import json as mod_1002_json
import pathlib as mod_1003_pathlib
import sqlite3 as mod_1004_sqlite
import uuid as mod_1005_uuid
from .mod_0010_types import type_0105_error, type_0112_pointer, fn_0118_pointer, fn_0121_wire, fn_0125_unwire, fn_0129_decimal, fn_0134_integer
from .mod_0011_algebra import type_3000_domain, fn_3003_decode
from .mod_0012_generators import fn_5001_spec, fn_5002_namespace, fn_5003_total, fn_5004_record


def fn_1006_dump(var_1007_value):
    """Canonical storage JSON retains integers and bytes without PHP coercion."""
    return mod_1002_json.dumps(fn_0121_wire(var_1007_value), sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def fn_1008_load(var_1009_text):
    """Recover typed storage JSON."""
    return fn_0125_unwire(mod_1002_json.loads(var_1009_text))


class type_1010_engine:
    """Context-managed local engine; all writes are transactional and IDs permanent."""
    def __init__(var_1011_self, var_1012_path):
        var_1011_self.attr_1013_path = str(var_1012_path)
        if var_1011_self.attr_1013_path != ':memory:':
            mod_1003_pathlib.Path(var_1012_path).parent.mkdir(parents=True, exist_ok=True)
        var_1011_self.attr_1014_connection = mod_1004_sqlite.connect(var_1011_self.attr_1013_path, isolation_level=None, timeout=10)
        var_1011_self.attr_1014_connection.row_factory = mod_1004_sqlite.Row
        var_1011_self.attr_1014_connection.execute('PRAGMA foreign_keys=ON')
        var_1015_version = var_1011_self.attr_1014_connection.execute('PRAGMA user_version').fetchone()[0]
        if var_1015_version not in (0, 1):
            var_1011_self.attr_1014_connection.close()
            raise type_0105_error('schema_version', 'Database version is unsupported; migrate a backup explicitly.')
        var_1011_self.attr_1014_connection.executescript('''
            CREATE TABLE IF NOT EXISTS namespace_1016_models(namespace TEXT PRIMARY KEY, kind TEXT NOT NULL, specification TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS record_1017_values(namespace TEXT NOT NULL REFERENCES namespace_1016_models(namespace), id TEXT NOT NULL, record_type TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(namespace,id));
            CREATE TABLE IF NOT EXISTS alias_1018_revisions(namespace TEXT NOT NULL, name TEXT NOT NULL, revision INTEGER NOT NULL, target TEXT NOT NULL, PRIMARY KEY(namespace,name,revision));
            CREATE TABLE IF NOT EXISTS meta_1019_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS request_1020_reports(id INTEGER PRIMARY KEY AUTOINCREMENT, definition TEXT NOT NULL,status TEXT NOT NULL,diagnostic TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS skill_1021_reports(name TEXT PRIMARY KEY,definition TEXT NOT NULL,catalogue_digest TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS guard_1022_record_update BEFORE UPDATE ON record_1017_values BEGIN SELECT RAISE(ABORT,'immutable record'); END;
            CREATE TRIGGER IF NOT EXISTS guard_1023_record_delete BEFORE DELETE ON record_1017_values BEGIN SELECT RAISE(ABORT,'immutable record'); END;
            CREATE TRIGGER IF NOT EXISTS guard_1024_alias_update BEFORE UPDATE ON alias_1018_revisions BEGIN SELECT RAISE(ABORT,'immutable alias revision'); END;
            CREATE TRIGGER IF NOT EXISTS guard_1025_alias_delete BEFORE DELETE ON alias_1018_revisions BEGIN SELECT RAISE(ABORT,'immutable alias revision'); END;
            PRAGMA user_version=1;
        ''')
        with var_1011_self.fn_1026_transaction(True):
            var_1011_self.attr_1014_connection.execute('INSERT OR IGNORE INTO meta_1019_settings VALUES (?,?)', ('default_namespace', 'r' + mod_1005_uuid.uuid4().hex))
            var_1011_self.attr_1027_namespace = var_1011_self.attr_1014_connection.execute('SELECT value FROM meta_1019_settings WHERE key=?', ('default_namespace',)).fetchone()[0]
            var_1011_self.fn_1028_namespace('record', {}, var_1011_self.attr_1027_namespace)

    def __enter__(var_1011_self):
        return var_1011_self

    def __exit__(var_1011_self, *var_1029_exception):
        var_1011_self.attr_1014_connection.close()

    @mod_1001_contextlib.contextmanager
    def fn_1026_transaction(var_1011_self, var_1030_write=False):
        """Hold a consistent snapshot or serialize an append-only update."""
        var_1031_nested = var_1011_self.attr_1014_connection.in_transaction
        if not var_1031_nested:
            var_1011_self.attr_1014_connection.execute('BEGIN IMMEDIATE' if var_1030_write else 'BEGIN')
        try:
            yield
            if not var_1031_nested:
                var_1011_self.attr_1014_connection.commit()
        except BaseException:
            if not var_1031_nested:
                var_1011_self.attr_1014_connection.rollback()
            raise

    def fn_1028_namespace(var_1011_self, var_1032_kind, var_1033_specification, var_1034_namespace=None):
        """Register an immutable address specification, independent of materialized rows."""
        if var_1032_kind == 'configuration':
            var_1035_domain = type_3000_domain(var_1033_specification['alphabet'])
            var_1034_namespace = var_1035_domain.attr_3001_namespace
            var_1033_specification = {'alphabet': list(var_1035_domain.attr_3006_alphabet), 'domain': 'natural', 'order': 'cardinality_then_lex'}
        elif var_1032_kind == 'generator':
            var_1033_specification = fn_5001_spec(var_1033_specification)
            var_1034_namespace = fn_5002_namespace(var_1033_specification)
        elif var_1032_kind == 'record':
            var_1034_namespace = var_1034_namespace or var_1011_self.attr_1027_namespace
            var_1033_specification = {}
        else:
            raise type_0105_error('invalid_input', 'Unsupported namespace kind.')
        type_0112_pointer(var_1032_kind, var_1034_namespace, 0)
        with var_1011_self.fn_1026_transaction(True):
            var_1036_existing = var_1011_self.attr_1014_connection.execute('SELECT kind,specification FROM namespace_1016_models WHERE namespace=?', (var_1034_namespace,)).fetchone()
            var_1037_spec_json = fn_1006_dump(var_1033_specification)
            if var_1036_existing and (var_1036_existing['kind'] != var_1032_kind or var_1036_existing['specification'] != var_1037_spec_json):
                raise type_0105_error('namespace_mismatch', 'An existing namespace cannot change meaning.')
            var_1011_self.attr_1014_connection.execute('INSERT OR IGNORE INTO namespace_1016_models VALUES (?,?,?)', (var_1034_namespace, var_1032_kind, var_1037_spec_json))
        return {'kind': var_1032_kind, 'namespace': var_1034_namespace, 'specification': var_1033_specification}

    def fn_1038_register(var_1011_self, var_1039_payload, var_1040_namespace=None, var_1041_reference=False):
        """Append a payload or an explicit pointer/alias reference and return its stable ID."""
        var_1040_namespace = var_1040_namespace or var_1011_self.attr_1027_namespace
        if type(var_1041_reference) is not bool:
            raise type_0105_error('invalid_input', 'reference must be a boolean.')
        if var_1041_reference:
            if isinstance(var_1039_payload, dict) and set(var_1039_payload) == {'alias', 'namespace'}:
                if not isinstance(var_1039_payload['alias'], str) or not var_1039_payload['alias']:
                    raise type_0105_error('malformed_pointer', 'Reference alias must be nonempty text.')
                type_0112_pointer('record', var_1039_payload['namespace'], 0)
            else:
                var_1039_payload = fn_0118_pointer(var_1039_payload).fn_0117_dict()
        var_1042_payload_json = fn_1006_dump(var_1039_payload)
        with var_1011_self.fn_1026_transaction(True):
            var_1011_self.fn_1028_namespace('record', {}, var_1040_namespace)
            var_1043_counter_key = 'next_id:' + var_1040_namespace
            var_1044_counter_row = var_1011_self.attr_1014_connection.execute('SELECT value FROM meta_1019_settings WHERE key=?', (var_1043_counter_key,)).fetchone()
            var_1045_identifier = fn_0134_integer(var_1044_counter_row[0]) if var_1044_counter_row else 1
            var_1011_self.attr_1014_connection.execute('INSERT INTO record_1017_values VALUES (?,?,?,?)', (var_1040_namespace, fn_0129_decimal(var_1045_identifier), 'reference' if var_1041_reference else 'json', var_1042_payload_json))
            var_1011_self.attr_1014_connection.execute('INSERT OR REPLACE INTO meta_1019_settings VALUES (?,?)', (var_1043_counter_key, fn_0129_decimal(var_1045_identifier + 1)))
        return type_0112_pointer('record', var_1040_namespace, var_1045_identifier)

    def fn_1046_alias(var_1011_self, var_1047_name, var_1048_target, var_1049_expected_revision=0, var_1050_namespace=None):
        """Append an alias revision only if the caller observed the current revision."""
        var_1050_namespace = var_1050_namespace or var_1011_self.attr_1027_namespace
        if not isinstance(var_1047_name, str) or not var_1047_name or var_1047_name.startswith('idx:'):
            raise type_0105_error('invalid_input', 'Alias must be nonempty exact text outside the reserved idx: prefix.')
        if type(var_1049_expected_revision) is not int or var_1049_expected_revision < 0:
            raise type_0105_error('invalid_input', 'Expected revision must be a nonnegative integer.')
        var_1051_pointer = fn_0118_pointer(var_1048_target)
        type_0112_pointer('record', var_1050_namespace, 0)
        with var_1011_self.fn_1026_transaction(True):
            var_1011_self.fn_1052_direct(var_1051_pointer)
            var_1053_row = var_1011_self.attr_1014_connection.execute('SELECT MAX(revision) FROM alias_1018_revisions WHERE namespace=? AND name=?', (var_1050_namespace, var_1047_name)).fetchone()
            var_1054_revision = var_1053_row[0] or 0
            if var_1054_revision != var_1049_expected_revision:
                raise type_0105_error('revision_conflict', 'Alias was changed since the expected revision.', {'actual_revision': var_1054_revision})
            var_1011_self.attr_1014_connection.execute('INSERT INTO alias_1018_revisions VALUES (?,?,?,?)', (var_1050_namespace, var_1047_name, var_1054_revision + 1, fn_1006_dump(var_1051_pointer)))
        return {'alias': var_1047_name, 'namespace': var_1050_namespace, 'revision': var_1054_revision + 1, 'target': var_1051_pointer.fn_0117_dict()}

    def fn_1052_direct(var_1011_self, var_1055_pointer):
        """Read one target without following its reference, preserving all address kinds."""
        var_1056_model = var_1011_self.attr_1014_connection.execute('SELECT kind,specification FROM namespace_1016_models WHERE namespace=?', (var_1055_pointer.attr_0114_namespace,)).fetchone()
        if not var_1056_model:
            raise type_0105_error('missing_target', 'Namespace is not registered.')
        if var_1056_model['kind'] != var_1055_pointer.attr_0113_kind:
            raise type_0105_error('namespace_mismatch', 'Pointer kind disagrees with its namespace.')
        var_1057_spec = fn_1008_load(var_1056_model['specification'])
        if var_1055_pointer.attr_0113_kind == 'configuration':
            return {'record_type': 'configuration', 'payload': fn_3003_decode(type_3000_domain(var_1057_spec['alphabet']), var_1055_pointer.attr_0115_id)}
        if var_1055_pointer.attr_0113_kind == 'generator':
            if var_1055_pointer.attr_0115_id >= fn_5003_total(var_1057_spec):
                raise type_0105_error('missing_target', 'Generator ordinal is outside its domain.')
            return {'record_type': 'generator', 'payload': fn_5004_record(var_1057_spec, var_1055_pointer.attr_0115_id)}
        var_1058_row = var_1011_self.attr_1014_connection.execute('SELECT record_type,payload FROM record_1017_values WHERE namespace=? AND id=?', (var_1055_pointer.attr_0114_namespace, fn_0129_decimal(var_1055_pointer.attr_0115_id))).fetchone()
        if not var_1058_row:
            raise type_0105_error('missing_target', 'Record ID does not exist.')
        return {'record_type': var_1058_row['record_type'], 'payload': fn_1008_load(var_1058_row['payload'])}

    def fn_1059_resolve(var_1011_self, var_1060_value, var_1061_namespace=None, var_1062_kind=None, var_1063_max_hops=64):
        """Follow explicit references in one snapshot, recording aliases and every target."""
        if type(var_1063_max_hops) is not int or not 1 <= var_1063_max_hops <= 10000:
            raise type_0105_error('invalid_input', 'max_hops must be between 1 and 10000.')
        var_1064_trace = []
        var_1065_seen = set()
        var_1066_current = var_1060_value
        var_1067_context = var_1061_namespace or var_1011_self.attr_1027_namespace
        with var_1011_self.fn_1026_transaction():
            for var_1068_hop in range(var_1063_max_hops):
                if isinstance(var_1066_current, dict) and set(var_1066_current) == {'alias', 'namespace'}:
                    var_1067_context = var_1066_current['namespace']
                    var_1066_current = var_1066_current['alias']
                if isinstance(var_1066_current, str) and not var_1066_current.startswith('idx:'):
                    var_1069_alias_key = ('alias', var_1067_context, var_1066_current)
                    if var_1069_alias_key in var_1065_seen:
                        raise type_0105_error('cycle', 'Alias/reference cycle detected.', var_1064_trace)
                    var_1065_seen.add(var_1069_alias_key)
                    var_1070_alias_row = var_1011_self.attr_1014_connection.execute('SELECT revision,target FROM alias_1018_revisions WHERE namespace=? AND name=? ORDER BY revision DESC LIMIT 1', (var_1067_context, var_1066_current)).fetchone()
                    if not var_1070_alias_row:
                        raise type_0105_error('missing_target', 'Text alias does not exist.', var_1064_trace)
                    var_1064_trace.append({'alias': var_1066_current, 'namespace': var_1067_context, 'revision': var_1070_alias_row['revision']})
                    var_1066_current = fn_1008_load(var_1070_alias_row['target'])
                if type(var_1066_current) is int:
                    if not var_1061_namespace or not var_1062_kind:
                        raise type_0105_error('malformed_pointer', 'Integer resolution requires explicit namespace and kind.')
                    var_1071_pointer = type_0112_pointer(var_1062_kind, var_1061_namespace, var_1066_current)
                else:
                    var_1071_pointer = fn_0118_pointer(var_1066_current)
                if var_1068_hop == 0 and ((var_1061_namespace and var_1071_pointer.attr_0114_namespace != var_1061_namespace and (not isinstance(var_1060_value, str) or var_1060_value.startswith('idx:'))) or (var_1062_kind and var_1071_pointer.attr_0113_kind != var_1062_kind)):
                    raise type_0105_error('namespace_mismatch', 'Explicit resolution context does not match pointer.')
                var_1072_key = str(var_1071_pointer)
                if var_1072_key in var_1065_seen:
                    raise type_0105_error('cycle', 'Pointer/reference cycle detected.', var_1064_trace)
                var_1065_seen.add(var_1072_key)
                var_1073_target = var_1011_self.fn_1052_direct(var_1071_pointer)
                var_1064_trace.append({'pointer': var_1071_pointer.fn_0117_dict(), 'record_type': var_1073_target['record_type']})
                if var_1073_target['record_type'] != 'reference':
                    return {'pointer': var_1071_pointer.fn_0117_dict(), 'target': var_1073_target['payload'], 'target_type': var_1073_target['record_type'], 'trace': var_1064_trace}
                var_1066_current = var_1073_target['payload']
            raise type_0105_error('resource_limit', 'Reference chain exceeded max_hops.', var_1064_trace)

    def fn_1074_history(var_1011_self, var_1075_alias, var_1076_namespace=None):
        """Return immutable alias history in revision order."""
        var_1076_namespace = var_1076_namespace or var_1011_self.attr_1027_namespace
        return [{'revision': var_1077_row['revision'], 'target': fn_1008_load(var_1077_row['target'])} for var_1077_row in var_1011_self.attr_1014_connection.execute('SELECT revision,target FROM alias_1018_revisions WHERE namespace=? AND name=? ORDER BY revision', (var_1076_namespace, var_1075_alias))]

    def fn_1078_inventory(var_1011_self, var_1079_limit=1000):
        """Expose a bounded, deterministic record inventory for typed reports."""
        if type(var_1079_limit) is not int or not 0 <= var_1079_limit <= 100000:
            raise type_0105_error('invalid_input', 'Inventory limit must be 0..100000.')
        return [{'namespace': var_1080_row['namespace'], 'id': fn_0134_integer(var_1080_row['id']), 'record_type': var_1080_row['record_type'], 'payload': fn_1008_load(var_1080_row['payload'])} for var_1080_row in var_1011_self.attr_1014_connection.execute('SELECT * FROM record_1017_values ORDER BY namespace,length(id),id LIMIT ?', (var_1079_limit,))]
