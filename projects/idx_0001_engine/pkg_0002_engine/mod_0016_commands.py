"""One JSON command dispatcher for Python callers, CLI, REPL, and the PHP bridge."""
import argparse as mod_1401_argparse
import json as mod_1402_json
import os as mod_1403_os
import pathlib as mod_1404_pathlib
import sys as mod_1405_sys
import sqlite3 as mod_1448_sqlite
from .mod_0010_types import type_0105_error, type_0112_pointer, fn_0118_pointer, fn_0121_wire, fn_0125_unwire
from .mod_0011_algebra import type_3000_domain, fn_3002_encode, fn_3003_decode, fn_3004_evaluate, fn_3005_laws
from .mod_0012_generators import fn_5001_spec, fn_5003_total, fn_5004_record, fn_5005_generate, fn_5006_export, fn_5007_import
from .mod_0013_catalogues import fn_7001_sync, fn_7002_check, fn_7003_load
from .mod_0014_storage import type_1010_engine, fn_1008_load
from .mod_0015_reports import fn_1215_request, fn_1222_activate, fn_1231_render, fn_1262_catalogue_lock

const_1406_root = mod_1404_pathlib.Path(mod_1403_os.environ.get('INDEXER_PROJECT', mod_1404_pathlib.Path(__file__).resolve().parent.parent))
const_1407_commands = ('health', 'namespace', 'register', 'alias', 'history', 'resolve', 'encode', 'decode', 'evaluate', 'laws', 'generate', 'export', 'import', 'inventory', 'catalogue', 'catalogue_check', 'catalogue_sync', 'report', 'report_request', 'report_activate')


def fn_1408_dispatch(var_1409_request, var_1410_database=None, var_1411_root=None):
    """Execute one structured request, returning operational errors as distinct results.

The native Python API uses integers/bytes directly. Only the CLI transport applies
reserved wire tags. Database and project locations are host parameters, not fields
accepted from browser request data.
"""
    var_1411_root = mod_1404_pathlib.Path(var_1411_root or const_1406_root).resolve()
    var_1410_database = var_1410_database or mod_1403_os.environ.get('INDEXER_DATABASE') or str(var_1411_root / 'runtime_0007_state' / 'data_0022_store.sqlite3')
    try:
        if not isinstance(var_1409_request, dict):
            raise type_0105_error('invalid_input', 'A request must be a JSON object.')
        var_1412_command = var_1409_request.get('command')
        if var_1412_command not in const_1407_commands:
            raise type_0105_error('invalid_input', 'Unknown command.', {'commands': const_1407_commands})
        if var_1412_command == 'catalogue_check':
            var_1413_result = fn_7002_check(var_1411_root)
            return {'status': 'ok' if var_1413_result.get('ok') else 'catalogue_invalid', 'result': var_1413_result}
        if var_1412_command == 'catalogue_sync':
            with fn_1262_catalogue_lock(var_1411_root):
                var_1413_result = fn_7001_sync(var_1411_root)
            return {'status': 'ok' if var_1413_result.get('ok', var_1413_result.get('status') == 'ok') else 'catalogue_invalid', 'result': var_1413_result}
        if var_1412_command == 'catalogue':
            return {'status': 'ok', 'result': fn_7003_load(var_1411_root)}
        with type_1010_engine(var_1410_database) as var_1414_engine:
            if var_1412_command == 'health':
                var_1413_result = {'schema_version': 1, 'record_namespace': var_1414_engine.attr_1027_namespace, 'commands': const_1407_commands}
            elif var_1412_command == 'namespace':
                var_1413_result = var_1414_engine.fn_1028_namespace(var_1409_request['kind'], var_1409_request.get('specification', {}), var_1409_request.get('namespace'))
            elif var_1412_command == 'register':
                var_1413_result = var_1414_engine.fn_1038_register(var_1409_request['payload'], var_1409_request.get('namespace'), var_1409_request.get('reference', False)).fn_0117_dict()
            elif var_1412_command == 'alias':
                var_1413_result = var_1414_engine.fn_1046_alias(var_1409_request['name'], var_1409_request['target'], var_1409_request.get('expected_revision', 0), var_1409_request.get('namespace'))
            elif var_1412_command == 'history':
                var_1413_result = var_1414_engine.fn_1074_history(var_1409_request['name'], var_1409_request.get('namespace'))
            elif var_1412_command == 'resolve':
                var_1413_result = var_1414_engine.fn_1059_resolve(var_1409_request['pointer'], var_1409_request.get('namespace'), var_1409_request.get('kind'), var_1409_request.get('max_hops', 64))
            elif var_1412_command in ('encode', 'decode', 'evaluate', 'laws'):
                var_1415_alphabet = var_1409_request.get('alphabet')
                if var_1415_alphabet is None:
                    var_1416_row = var_1414_engine.attr_1014_connection.execute('SELECT specification FROM namespace_1016_models WHERE namespace=? AND kind=?', (var_1409_request.get('namespace'), 'configuration')).fetchone()
                    if not var_1416_row:
                        raise type_0105_error('missing_target', 'Supply an alphabet or a registered configuration namespace.')
                    var_1415_alphabet = fn_1008_load(var_1416_row[0])['alphabet']
                var_1417_domain = type_3000_domain(var_1415_alphabet)
                if var_1409_request.get('namespace', var_1417_domain.attr_3001_namespace) != var_1417_domain.attr_3001_namespace:
                    raise type_0105_error('namespace_mismatch', 'Alphabet and namespace disagree.')
                var_1414_engine.fn_1028_namespace('configuration', {'alphabet': var_1415_alphabet})
                if var_1412_command == 'encode':
                    var_1418_id = fn_3002_encode(var_1417_domain, var_1409_request['configuration'])
                    var_1413_result = {'pointer': type_0112_pointer('configuration', var_1417_domain.attr_3001_namespace, var_1418_id).fn_0117_dict(), 'configuration': var_1409_request['configuration']}
                elif var_1412_command == 'decode':
                    var_1413_result = {'namespace': var_1417_domain.attr_3001_namespace, 'id': var_1409_request['id'], 'configuration': fn_3003_decode(var_1417_domain, var_1409_request['id'])}
                elif var_1412_command == 'laws':
                    var_1413_result = fn_3005_laws(var_1417_domain, var_1409_request['composition'], var_1409_request.get('max_steps', 500000))
                else:
                    var_1419_left = fn_1420_operand(var_1417_domain, var_1409_request['left'])
                    var_1421_right = fn_1420_operand(var_1417_domain, var_1409_request['right'])
                    var_1413_result = fn_3004_evaluate(var_1417_domain, var_1409_request['operation'], var_1419_left, var_1421_right, var_1409_request.get('composition'), var_1409_request.get('max_steps', 500000), var_1409_request.get('max_solutions', 10000))
            elif var_1412_command in ('generate', 'export'):
                var_1422_spec = fn_5001_spec(var_1409_request['specification'])
                var_1423_namespace = var_1414_engine.fn_1028_namespace('generator', var_1422_spec)['namespace']
                var_1424_start = var_1409_request.get('start', 0)
                var_1425_limit = var_1409_request.get('limit', 10000)
                if type(var_1425_limit) is not int or not 0 <= var_1425_limit <= 1000000:
                    raise type_0105_error('invalid_input', 'Explicit export limit must be 0..1000000; use windows for larger exports.')
                if type(var_1424_start) is not int or var_1424_start < 0:
                    raise type_0105_error('invalid_input', 'start must be a nonnegative integer.')
                var_1449_count = min(var_1425_limit, max(0, fn_5003_total(var_1422_spec) - var_1424_start))
                if var_1449_count:
                    var_1451_sample = fn_5004_record(var_1422_spec, var_1424_start)
                    var_1452_estimate = var_1449_count * (1024 + 2 * len(mod_1402_json.dumps(fn_0121_wire(var_1451_sample), ensure_ascii=True).encode('utf-8')))
                    if var_1452_estimate > 67108864:
                        raise type_0105_error('resource_limit', 'Estimated response exceeds 64 MiB. Request a smaller window or use the native lazy generator.', {'estimated_bytes': var_1452_estimate, 'budget_bytes': 67108864})
                var_1413_result = {'namespace': var_1423_namespace, 'expected_total': fn_5003_total(var_1422_spec), 'start': var_1424_start, 'limit': var_1425_limit}
                if var_1412_command == 'export':
                    var_1413_result['data'] = fn_5006_export(var_1422_spec, var_1424_start, var_1425_limit)
                else:
                    var_1413_result['records'] = list(fn_5005_generate(var_1422_spec, var_1424_start, var_1425_limit))
            elif var_1412_command == 'import':
                var_1426_import = fn_5007_import(var_1409_request['data'], var_1409_request.get('specification'))
                with var_1414_engine.fn_1026_transaction(True):
                    var_1414_engine.fn_1028_namespace('generator', var_1426_import['spec'])
                    var_1427_archive = var_1414_engine.fn_1038_register({'source_namespace': var_1426_import['namespace'], 'import': var_1426_import})
                var_1413_result = {'archive': var_1427_archive.fn_0117_dict(), 'namespace': var_1426_import['namespace'], 'emitted_records': var_1426_import['emitted_records'], 'start': var_1426_import['start']}
            elif var_1412_command == 'inventory':
                var_1413_result = var_1414_engine.fn_1078_inventory(var_1409_request.get('limit', 1000))
            elif var_1412_command == 'report_request':
                var_1413_result = fn_1215_request(var_1414_engine, var_1409_request['definition'])
            elif var_1412_command == 'report_activate':
                var_1413_result = fn_1222_activate(var_1414_engine, var_1411_root, var_1409_request['request_id'])
            else:
                var_1413_result = fn_1231_render(var_1414_engine, var_1411_root, var_1409_request.get('name', 'inventory'), var_1409_request.get('evidence'), var_1409_request.get('limit', 1000))
            return {'status': var_1413_result.get('status', 'ok') if isinstance(var_1413_result, dict) and var_1413_result.get('status') == 'resource_limit' else 'ok', 'result': var_1413_result}
    except type_0105_error as var_1428_error:
        return {'status': var_1428_error.attr_0110_code, 'error': str(var_1428_error), 'details': var_1428_error.attr_0111_details, 'outcome': None}
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as var_1428_error:
        return {'status': 'invalid_input', 'error': str(var_1428_error), 'outcome': None}
    except OSError as var_1428_error:
        return {'status': 'io_error', 'error': str(var_1428_error), 'outcome': None}
    except mod_1448_sqlite.Error as var_1428_error:
        return {'status': 'database_error', 'error': str(var_1428_error), 'outcome': None}


def fn_1420_operand(var_1429_domain, var_1430_value):
    """Reject cross-namespace algebra operands instead of coercing their address."""
    if isinstance(var_1430_value, (dict, type_0112_pointer, str)):
        var_1431_pointer = fn_0118_pointer(var_1430_value)
        if var_1431_pointer.attr_0113_kind != 'configuration' or var_1431_pointer.attr_0114_namespace != var_1429_domain.attr_3001_namespace:
            raise type_0105_error('namespace_mismatch', 'Algebra operands must belong to the declared configuration namespace.')
        return var_1431_pointer.attr_0115_id
    return var_1430_value


def fn_1432_json(var_1433_text, var_1434_database=None):
    """Serve exactly one lossless wire request without tracebacks on malformed JSON."""
    try:
        if len(var_1433_text.encode('utf-8')) > 16777216:
            raise ValueError('Request exceeds 16 MiB.')
        var_1435_request = fn_0125_unwire(mod_1402_json.loads(var_1433_text, parse_constant=fn_1450_reject_constant))
        var_1436_response = fn_1408_dispatch(var_1435_request, var_1434_database)
        return mod_1402_json.dumps(fn_0121_wire(var_1436_response), ensure_ascii=True, allow_nan=False)
    except (ValueError, TypeError, RecursionError, type_0105_error) as var_1437_error:
        var_1436_response = {'status': 'invalid_input', 'error': str(var_1437_error), 'outcome': None}
    return mod_1402_json.dumps(fn_0121_wire(var_1436_response), ensure_ascii=True, allow_nan=False)


def fn_1450_reject_constant(var_1453_constant):
    """Reject non-JSON NaN/Infinity tokens at the transport boundary."""
    raise ValueError('Non-finite JSON number is not allowed: ' + var_1453_constant)


def fn_1438_main(var_1439_arguments=None):
    """Run JSON stdin, an individual command request, or the interactive JSON REPL."""
    var_1440_parser = mod_1401_argparse.ArgumentParser(description='Namespaced text and integer pointer engine. Integers/bytes use explicit lossless JSON tags in responses.')
    var_1440_parser.add_argument('--database', help='SQLite database path (default: project runtime state)')
    var_1440_parser.add_argument('--json-stdin', action='store_true', help='Read exactly one JSON command from stdin')
    var_1440_parser.add_argument('--request', help='Read one UTF-8 JSON command file')
    var_1440_parser.add_argument('--repl', action='store_true', help='Interactive JSON commands; :help and :quit are available')
    var_1440_parser.add_argument('command', nargs='?', choices=const_1407_commands)
    var_1440_parser.add_argument('--data', default='{}', help='JSON fields merged with the positional command')
    var_1441_options = var_1440_parser.parse_args(var_1439_arguments)
    if sum(bool(var_1442_mode) for var_1442_mode in (var_1441_options.json_stdin, var_1441_options.request, var_1441_options.repl, var_1441_options.command)) != 1:
        var_1440_parser.error('Select exactly one of --json-stdin, --request, --repl, or a command.')
    if var_1441_options.repl:
        print('Indexer JSON REPL. :help lists commands; :quit exits.')
        while True:
            try:
                var_1443_line = input('idx> ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if var_1443_line == ':quit':
                return 0
            if var_1443_line == ':help':
                print(', '.join(const_1407_commands))
            elif var_1443_line:
                print(fn_1432_json(var_1443_line, var_1441_options.database))
    try:
        if var_1441_options.json_stdin:
            var_1444_text = mod_1405_sys.stdin.read(16777217)
            if len(var_1444_text) > 16777216:
                raise ValueError('Request exceeds 16 MiB.')
        elif var_1441_options.request:
            var_1444_text = mod_1404_pathlib.Path(var_1441_options.request).read_text(encoding='utf-8')
        else:
            var_1445_request = mod_1402_json.loads(var_1441_options.data)
            var_1445_request['command'] = var_1441_options.command
            var_1444_text = mod_1402_json.dumps(var_1445_request)
        var_1446_response = fn_1432_json(var_1444_text, var_1441_options.database)
        print(var_1446_response)
        return 0 if mod_1402_json.loads(var_1446_response)['status'] == 'ok' else 2
    except (ValueError, OSError, TypeError) as var_1447_error:
        print(mod_1402_json.dumps({'status': 'invalid_input', 'error': str(var_1447_error), 'outcome': None}))
        return 2
