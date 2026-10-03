"""Declarative reports produce typed lists of lists from engine evidence.

No report definition contains executable Python, PHP, SQL, or shell text.
Catalogue synchronization supplies inspectable provenance for activated reports.
"""
import hashlib as mod_1201_hashlib
import json as mod_1202_json
import re as mod_1203_re
import contextlib as mod_1260_contextlib
import os as mod_1261_os
from .mod_0010_types import type_0105_error, fn_0121_wire, fn_0129_decimal
from .mod_0014_storage import fn_1006_dump, fn_1008_load
from .mod_0013_catalogues import fn_7001_sync, fn_7003_load

const_1204_columns = {
    'inventory': {'namespace': 'string', 'id': 'integer', 'record_type': 'string', 'payload': 'json'},
    'dependency': {'relation': 'string', 'source': 'string', 'target': 'string', 'description': 'string'},
    'resolution': {'step': 'integer', 'evidence': 'json'},
    'algebra': {'status': 'string', 'outcome': 'json'},
}


def fn_1205_validate(var_1206_definition):
    """Validate a finite report projection/filter/grouping without an execution language."""
    if not isinstance(var_1206_definition, dict) or set(var_1206_definition) - {'name', 'source', 'columns', 'filters', 'group_by'}:
        raise type_0105_error('invalid_report', 'Report definition has unknown fields.')
    var_1207_name = var_1206_definition.get('name')
    var_1208_source = var_1206_definition.get('source')
    if not isinstance(var_1207_name, str) or not mod_1203_re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', var_1207_name):
        raise type_0105_error('invalid_report', 'Report name must be 1..64 ASCII letters, digits, or underscores, starting with a letter.')
    if not isinstance(var_1208_source, str) or var_1208_source not in const_1204_columns:
        raise type_0105_error('invalid_report', 'Unknown report source.')
    var_1209_columns = var_1206_definition.get('columns', list(const_1204_columns[var_1208_source]))
    var_1210_groups = var_1206_definition.get('group_by', [])
    var_1211_filters = var_1206_definition.get('filters', [])
    for var_1212_fields in (var_1209_columns, var_1210_groups):
        if not isinstance(var_1212_fields, list) or any(not isinstance(var_1213_field, str) or var_1213_field not in const_1204_columns[var_1208_source] for var_1213_field in var_1212_fields) or len(set(var_1212_fields)) != len(var_1212_fields):
            raise type_0105_error('invalid_report', 'Projection/group fields must be unique source columns.')
    if not var_1209_columns or not isinstance(var_1211_filters, list) or len(var_1211_filters) > 32:
        raise type_0105_error('invalid_report', 'Report needs columns and at most 32 filters.')
    for var_1214_filter in var_1211_filters:
        if not isinstance(var_1214_filter, dict) or set(var_1214_filter) != {'field', 'op', 'value'} or not isinstance(var_1214_filter['field'], str) or var_1214_filter['field'] not in const_1204_columns[var_1208_source] or var_1214_filter['op'] not in ('eq', 'ne', 'contains'):
            raise type_0105_error('invalid_report', 'Filters require a known field, eq/ne/contains operation, and value.')
    return {'name': var_1207_name, 'source': var_1208_source, 'columns': var_1209_columns, 'filters': var_1211_filters, 'group_by': var_1210_groups}


def fn_1215_request(var_1216_engine, var_1217_definition):
    """Persist both valid and invalid report requests with explicit validation status."""
    try:
        var_1217_definition = fn_1205_validate(var_1217_definition)
        var_1218_status, var_1219_diagnostic = 'validated', ''
    except type_0105_error as var_1220_error:
        var_1218_status, var_1219_diagnostic = 'invalid', str(var_1220_error)
    with var_1216_engine.fn_1026_transaction(True):
        var_1221_cursor = var_1216_engine.attr_1014_connection.execute('INSERT INTO request_1020_reports(definition,status,diagnostic) VALUES (?,?,?)', (fn_1006_dump(var_1217_definition), var_1218_status, var_1219_diagnostic))
    return {'request_id': var_1221_cursor.lastrowid, 'status': var_1218_status, 'diagnostic': var_1219_diagnostic}


def fn_1222_activate(var_1223_engine, var_1224_root, var_1225_request_id):
    """Activate a validated request only after its catalogue changes pass validation."""
    if type(var_1225_request_id) is not int or var_1225_request_id <= 0:
        raise type_0105_error('invalid_report', 'request_id must be a positive integer.')
    with fn_1262_catalogue_lock(var_1224_root), var_1223_engine.fn_1026_transaction(True):
        var_1226_row = var_1223_engine.attr_1014_connection.execute('SELECT * FROM request_1020_reports WHERE id=?', (var_1225_request_id,)).fetchone()
        if not var_1226_row or var_1226_row['status'] not in ('validated', 'active'):
            raise type_0105_error('invalid_report', 'Only validated report requests can be activated.')
        var_1227_definition = fn_1205_validate(fn_1008_load(var_1226_row['definition']))
        var_1271_identity = var_1223_engine.attr_1027_namespace + ':' + str(var_1225_request_id)
        var_1263_entities = fn_7003_load(var_1224_root)['entities']
        var_1272_reserved = next((var_1266_entity['name'] for var_1266_entity in var_1263_entities if isinstance(var_1266_entity.get('definition'), dict) and var_1266_entity['definition'].get('request_identity') == var_1271_identity), None)
        if var_1272_reserved:
            var_1228_catalogue_name = var_1272_reserved
        elif var_1226_row['status'] == 'active':
            var_1228_catalogue_name = mod_1202_json.loads(var_1226_row['diagnostic'])['catalogue_entity']
        else:
            var_1264_numbers = [int(var_1265_match.group(1)) for var_1266_entity in var_1263_entities if (var_1265_match := mod_1203_re.fullmatch(r'[A-Za-z][A-Za-z0-9]*_([0-9]+)_.+', var_1266_entity['name']))]
            var_1228_catalogue_name = f"report_{max([9999] + var_1264_numbers) + 1}_{var_1227_definition['name']}"
        var_1229_result = fn_7001_sync(var_1224_root, [{'name': var_1228_catalogue_name, 'form': 'report', 'description': 'Declarative ' + var_1227_definition['source'] + ' report: ' + fn_1006_dump(var_1227_definition), 'definition': {'request_identity': var_1271_identity, 'report_json': fn_1006_dump(var_1227_definition)}, 'wiring': [{'relation': 'calls', 'target': 'fn_1231_render', 'description': 'Renders validated source columns as typed nested lists.'}]}])
        if not var_1229_result.get('ok', var_1229_result.get('status') == 'ok'):
            raise type_0105_error('catalogue_invalid', 'Report activation requires a valid catalogue.', var_1229_result)
        var_1230_digest = mod_1201_hashlib.sha256((var_1224_root / 'x2.json').read_bytes()).hexdigest()
        var_1223_engine.attr_1014_connection.execute('INSERT OR REPLACE INTO skill_1021_reports VALUES (?,?,?)', (var_1227_definition['name'], fn_1006_dump(var_1227_definition), var_1230_digest))
        var_1223_engine.attr_1014_connection.execute('UPDATE request_1020_reports SET status=?,diagnostic=? WHERE id=?', ('active', mod_1202_json.dumps({'catalogue_entity': var_1228_catalogue_name}), var_1225_request_id))
    return {'status': 'active', 'name': var_1227_definition['name'], 'request_id': var_1225_request_id, 'catalogue_entity': var_1228_catalogue_name, 'catalogue_digest': var_1230_digest}


def fn_1231_render(var_1232_engine, var_1233_root, var_1234_name='inventory', var_1235_evidence=None, var_1236_limit=1000):
    """Render deterministic typed rows; coverage explicitly describes a bounded source."""
    if type(var_1236_limit) is not int or not 1 <= var_1236_limit <= 100000:
        raise type_0105_error('invalid_input', 'Report limit must be 1..100000.')
    var_1237_row = var_1232_engine.attr_1014_connection.execute('SELECT definition FROM skill_1021_reports WHERE name=?', (var_1234_name,)).fetchone()
    if var_1237_row:
        var_1238_definition = fn_1205_validate(fn_1008_load(var_1237_row[0]))
    elif var_1234_name in const_1204_columns:
        var_1238_definition = fn_1205_validate({'name': var_1234_name, 'source': var_1234_name})
    else:
        raise type_0105_error('missing_target', 'Report skill is not registered.')
    var_1239_source = var_1238_definition['source']
    var_1240_catalogue = fn_7003_load(var_1233_root)
    var_1241_digest = mod_1201_hashlib.sha256((var_1233_root / 'x2.json').read_bytes()).hexdigest()
    if var_1239_source == 'inventory':
        with var_1232_engine.fn_1026_transaction():
            var_1242_rows = var_1232_engine.fn_1078_inventory(var_1236_limit)
            var_1243_total = var_1232_engine.attr_1014_connection.execute('SELECT count(*) FROM record_1017_values').fetchone()[0]
    elif var_1239_source == 'dependency':
        var_1244_edges = var_1240_catalogue.get('wiring', [])
        var_1242_rows = [{'relation': var_1245_edge.get('relation', ''), 'source': var_1245_edge.get('source', ''), 'target': var_1245_edge.get('target', ''), 'description': var_1245_edge.get('description', '')} for var_1245_edge in var_1244_edges[:var_1236_limit]]
        var_1243_total = len(var_1244_edges)
    elif var_1239_source == 'resolution':
        if not isinstance(var_1235_evidence, dict) or not isinstance(var_1235_evidence.get('trace'), list) or any(not isinstance(var_1247_step, dict) for var_1247_step in var_1235_evidence.get('trace', [])):
            raise type_0105_error('invalid_input', 'Resolution report requires engine resolution evidence.')
        var_1242_rows = [{'step': var_1246_index, 'evidence': var_1247_step} for var_1246_index, var_1247_step in enumerate(var_1235_evidence['trace'][:var_1236_limit])]
        var_1243_total = len(var_1235_evidence['trace'])
    else:
        if not isinstance(var_1235_evidence, dict) or not isinstance(var_1235_evidence.get('status'), str) or 'outcome' not in var_1235_evidence:
            raise type_0105_error('invalid_input', 'Algebra report requires algebra evaluation evidence.')
        var_1242_rows = [{'status': var_1235_evidence['status'], 'outcome': var_1235_evidence['outcome']}]
        var_1243_total = 1
    for var_1248_filter in var_1238_definition['filters']:
        var_1242_rows = [var_1249_item for var_1249_item in var_1242_rows if fn_1250_match(var_1249_item[var_1248_filter['field']], var_1248_filter['op'], var_1248_filter['value'])]
    var_1251_fields = var_1238_definition['columns']
    var_1252_types = const_1204_columns[var_1239_source]
    if var_1238_definition['group_by']:
        var_1251_fields = var_1238_definition['group_by'] + ['count']
        var_1252_types = dict(var_1252_types, count='integer')
        var_1253_groups = {}
        for var_1249_item in var_1242_rows:
            var_1254_key = fn_1006_dump([var_1249_item[var_1255_field] for var_1255_field in var_1238_definition['group_by']])
            if var_1254_key not in var_1253_groups:
                var_1253_groups[var_1254_key] = {var_1255_field: var_1249_item[var_1255_field] for var_1255_field in var_1238_definition['group_by']}
                var_1253_groups[var_1254_key]['count'] = 0
            var_1253_groups[var_1254_key]['count'] += 1
        var_1242_rows = [var_1253_groups[var_1254_key] for var_1254_key in sorted(var_1253_groups)]
    return {
        'type': 'list', 'element_type': {'type': 'list', 'columns': [{'name': var_1255_field, 'type': var_1252_types[var_1255_field]} for var_1255_field in var_1251_fields]},
        'items': [[{'role': 'cell', 'type': var_1252_types[var_1255_field], 'value': fn_0129_decimal(var_1249_item[var_1255_field]) if var_1252_types[var_1255_field] == 'integer' else var_1249_item[var_1255_field]} for var_1255_field in var_1251_fields] for var_1249_item in var_1242_rows],
        'provenance': {'report': var_1234_name, 'source': var_1239_source, 'catalogue_sha256': var_1241_digest, 'evidence_origin': 'caller_supplied' if var_1239_source in ('resolution', 'algebra') else 'engine'},
        'coverage': {'limit': var_1236_limit, 'source_total': var_1243_total, 'source_complete': var_1243_total <= var_1236_limit, 'filter_scope': 'selected_source_window'},
    }


def fn_1250_match(var_1256_actual, var_1257_operator, var_1258_expected):
    """Apply one bounded equality or string containment predicate."""
    if var_1257_operator == 'eq':
        return type(var_1256_actual) is type(var_1258_expected) and var_1256_actual == var_1258_expected
    if var_1257_operator == 'ne':
        return not fn_1250_match(var_1256_actual, 'eq', var_1258_expected)
    return isinstance(var_1256_actual, str) and isinstance(var_1258_expected, str) and var_1258_expected in var_1256_actual


@mod_1260_contextlib.contextmanager
def fn_1262_catalogue_lock(var_1267_root):
    """Serialize catalogue publication across databases that share a project root."""
    var_1268_lock = var_1267_root / 'runtime_0007_state' / 'lock_0024_catalogue'
    var_1268_lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        var_1269_descriptor = mod_1261_os.open(var_1268_lock, mod_1261_os.O_CREAT | mod_1261_os.O_EXCL | mod_1261_os.O_WRONLY)
    except FileExistsError as var_1270_error:
        raise type_0105_error('catalogue_busy', 'Another catalogue writer is active. If a writer crashed, verify it stopped before removing the catalogue lock.') from var_1270_error
    try:
        mod_1261_os.write(var_1269_descriptor, str(mod_1261_os.getpid()).encode('ascii'))
        mod_1261_os.close(var_1269_descriptor)
        yield
    finally:
        var_1268_lock.unlink(missing_ok=True)
