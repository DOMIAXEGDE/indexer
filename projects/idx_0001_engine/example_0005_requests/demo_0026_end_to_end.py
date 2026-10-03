"""Run a persistent, repeatable record-to-algebra-to-report demonstration."""
import json as mod_1901_json
import pathlib as mod_1902_pathlib
import sys as mod_1903_sys

var_1904_root = mod_1902_pathlib.Path(__file__).resolve().parent.parent
mod_1903_sys.path.insert(0, str(var_1904_root))
from pkg_0002_engine.mod_0010_types import fn_0121_wire
from pkg_0002_engine.mod_0016_commands import fn_1408_dispatch


def fn_1905_demo():
    """Register records, update a versioned alias, resolve a reference, and export reports."""
    var_1906_database = var_1904_root / 'runtime_0007_state' / 'demo_0029_store.sqlite3'

    def fn_1907_call(var_1908_request):
        """Require successful shared-dispatcher behavior for every demonstration step."""
        var_1909_response = fn_1408_dispatch(var_1908_request, str(var_1906_database), var_1904_root)
        if var_1909_response['status'] != 'ok':
            raise RuntimeError(mod_1901_json.dumps(fn_0121_wire(var_1909_response)))
        return var_1909_response['result']

    var_1910_alphabet = ['neutral', 'toggle']
    var_1911_tensor = [[[1, 0], [0, 1]], [[0, 1], [1, 0]]]
    var_1912_encoded = fn_1907_call({'command': 'encode', 'alphabet': var_1910_alphabet, 'configuration': [1, 1]})
    var_1913_record = fn_1907_call({'command': 'register', 'payload': {'label': 'mixed configuration', 'configuration_pointer': var_1912_encoded['pointer']}})
    var_1914_history = fn_1907_call({'command': 'history', 'name': 'demo_mixed'})
    var_1915_alias = fn_1907_call({'command': 'alias', 'name': 'demo_mixed', 'target': var_1913_record, 'expected_revision': var_1914_history[-1]['revision'] if var_1914_history else 0})
    var_1916_reference = fn_1907_call({'command': 'register', 'reference': True, 'payload': {'alias': 'demo_mixed', 'namespace': var_1913_record['namespace']}})
    var_1917_resolution = fn_1907_call({'command': 'resolve', 'pointer': var_1916_reference})
    var_1918_integer_resolution = fn_1907_call({'command': 'resolve', 'pointer': var_1913_record['id'], 'namespace': var_1913_record['namespace'], 'kind': 'record'})
    if var_1917_resolution['target'] != var_1918_integer_resolution['target']:
        raise AssertionError('Text/reference and integer resolution disagree.')
    var_1919_algebra = fn_1907_call({'command': 'evaluate', 'alphabet': var_1910_alphabet, 'operation': 'divide_right', 'left': 4, 'right': 4, 'composition': var_1911_tensor})
    if set(var_1919_algebra['outcome']['ids']) != {1, 2}:
        raise AssertionError('Manuscript division fixture failed.')
    var_1920_export = fn_1907_call({'command': 'export', 'specification': {'source_kind': 'configure_2', 'width': 7}, 'start': 7, 'limit': 4})
    var_1921_import = fn_1907_call({'command': 'import', 'data': var_1920_export['data']})
    var_1922_report = {
        'record': var_1913_record, 'alias': var_1915_alias, 'import': var_1921_import,
        'inventory': fn_1907_call({'command': 'report', 'name': 'inventory'}),
        'resolution': fn_1907_call({'command': 'report', 'name': 'resolution', 'evidence': var_1917_resolution}),
        'algebra': fn_1907_call({'command': 'report', 'name': 'algebra', 'evidence': var_1919_algebra}),
    }
    var_1923_output = var_1904_root / 'runtime_0007_state' / 'demo_0028_report.json'
    var_1923_output.write_text(mod_1901_json.dumps(fn_0121_wire(var_1922_report), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Resolved the same record by reference, text alias, and integer ID.')
    print('Exact neutral-toggle division returned IDs {1, 2}.')
    print('Imported four byte-verified C++ compatible decimal records.')
    print('Typed reports: ' + str(var_1923_output))


if __name__ == '__main__':
    fn_1905_demo()
