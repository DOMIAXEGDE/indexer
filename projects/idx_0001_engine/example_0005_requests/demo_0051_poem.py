"""Run and persist a four-operation poem example through the shared dispatcher."""
import json as mod_2000_json
import pathlib as mod_2001_pathlib
import sys as mod_2002_sys

var_2003_root = mod_2001_pathlib.Path(__file__).resolve().parent.parent
mod_2002_sys.path.insert(0, str(var_2003_root))
from pkg_0002_engine.mod_0010_types import fn_0121_wire
from pkg_0002_engine.mod_0016_commands import fn_1408_dispatch


def fn_2004_poem():
    """Check the configured algebra chain, save its poem record, and export evidence.

    The JSON describes this example, not a new engine command. Each step becomes
    an ordinary evaluate request; the full requests and responses are exported.
    Repeated runs append immutable records and advance the poem's versioned alias.
    """
    var_2005_config = mod_2000_json.loads((var_2003_root / 'example_0005_requests' / 'config_0050_poem.json').read_text(encoding='utf-8'))
    var_2006_database = var_2003_root / 'runtime_0007_state' / 'poem_0054_store.sqlite3'
    var_2007_alphabet = var_2005_config['domain']['alphabet']
    var_2008_tensor = var_2005_config['composition']
    var_2009_evidence = []

    def fn_2010_call(var_2011_request):
        """Preserve every dispatcher response and stop on operational failure."""
        var_2012_response = fn_1408_dispatch(var_2011_request, str(var_2006_database), var_2003_root)
        var_2009_evidence.append({'request': var_2011_request, 'response': var_2012_response})
        if var_2012_response['status'] != 'ok':
            raise RuntimeError(mod_2000_json.dumps(fn_0121_wire(var_2012_response)))
        return var_2012_response['result']

    def fn_2013_evaluate(var_2014_operation, var_2015_left, var_2016_right):
        """Apply explicit line bindings and the declared tensor through the engine."""
        return fn_2010_call({'command': 'evaluate', 'alphabet': var_2007_alphabet,
                            'composition': var_2008_tensor, 'operation': var_2014_operation,
                            'left': var_2015_left, 'right': var_2016_right})

    def fn_2017_render(var_2018_configuration):
        """Apply the external reading order without treating order as multiset state."""
        return '\n'.join(var_2007_alphabet[var_2019_index]
                         for var_2019_index in var_2005_config['interpretation']['reading_order']
                         for var_2020_occurrence in range(var_2018_configuration[var_2019_index]))

    if (var_2005_config['schema_version'] != 1
            or var_2005_config['domain']['kind'] != 'natural'
            or var_2005_config['domain']['coefficient_domain'] != 'N0^4'
            or var_2005_config['domain']['equality'] != 'coordinatewise'
            or var_2005_config['domain']['order'] != 'cardinality-then-ascending-lexicographic'
            or len(var_2007_alphabet) != 4
            or sorted(var_2005_config['interpretation']['reading_order']) != [0, 1, 2, 3]):
        raise ValueError('This example requires four natural line counts and one reading position per line.')
    if [var_2022_step['operation'] for var_2022_step in var_2005_config['steps']] != ['add', 'subtract', 'multiply', 'divide_right']:
        raise ValueError('The example must demonstrate all four operations in order.')
    var_2021_laws = fn_2010_call({'command': 'laws', 'alphabet': var_2007_alphabet, 'composition': var_2008_tensor})
    if (var_2021_laws['laws']['classification'] != 'commutative_unital_semiring'
            or var_2021_laws['laws']['identity']['configuration'] != var_2005_config['interpretation']['multiplicative_identity']):
        raise AssertionError('The composition laws or declared identity did not validate.')

    var_2023_steps = []
    var_2024_previous = None
    for var_2022_step in var_2005_config['steps']:
        if var_2024_previous is not None and var_2022_step['left'] != var_2024_previous:
            raise AssertionError('The next step must consume the preceding result.')
        var_2025_result = fn_2013_evaluate(var_2022_step['operation'], var_2022_step['left'], var_2022_step['right'])
        var_2026_outcome = var_2025_result['outcome']
        if var_2022_step['operation'] == 'divide_right':
            if (var_2026_outcome['kind'] != 'solutions' or not var_2026_outcome['finite']
                    or var_2026_outcome['configurations'] != var_2022_step['expected_configurations']
                    or len(var_2026_outcome['configurations']) != 1):
                raise AssertionError('Expected the complete singleton quotient set for this example.')
            var_2024_previous = var_2026_outcome['configurations'][0]
            var_2027_reconstruction = fn_2013_evaluate('multiply', var_2024_previous, var_2022_step['right'])
            if var_2027_reconstruction['outcome']['configuration'] != var_2022_step['left']:
                raise AssertionError('Quotient times divisor did not reconstruct the dividend.')
        else:
            if (var_2026_outcome['kind'] != 'value'
                    or var_2026_outcome['configuration'] != var_2022_step['expected_configuration']):
                raise AssertionError('An operation did not produce its declared configuration.')
            var_2024_previous = var_2026_outcome['configuration']
            if var_2022_step['operation'] == 'subtract':
                var_2027_reconstruction = fn_2013_evaluate('add', var_2024_previous, var_2022_step['right'])
                if var_2027_reconstruction['outcome']['configuration'] != var_2022_step['left']:
                    raise AssertionError('Residual plus removed line did not reconstruct the draft.')
        var_2028_encoded = fn_2010_call({'command': 'encode', 'alphabet': var_2007_alphabet, 'configuration': var_2024_previous})
        var_2029_decoded = fn_2010_call({'command': 'decode', 'alphabet': var_2007_alphabet, 'id': var_2028_encoded['pointer']['id']})
        if list(var_2029_decoded['configuration']) != var_2024_previous:
            raise AssertionError('Canonical encode/decode round trip failed.')
        var_2023_steps.append({'step': var_2022_step, 'result': var_2025_result,
                               'configuration_pointer': var_2028_encoded['pointer'],
                               'rendered_text': fn_2017_render(var_2024_previous),
                               'typed_report': fn_2010_call({'command': 'report', 'name': 'algebra', 'evidence': var_2025_result})})

    if var_2024_previous != var_2005_config['expected_final_configuration'] or var_2024_previous != [1, 1, 1, 1]:
        raise AssertionError('The final poem must contain exactly one occurrence of each line.')
    var_2030_text = var_2005_config['title'] + '\n\n' + fn_2017_render(var_2024_previous) + '\n'
    var_2031_payload = {'kind': 'poem_example', 'configuration': var_2005_config,
                        'final_configuration_pointer': var_2028_encoded['pointer'], 'text': var_2030_text}
    var_2032_record = fn_2010_call({'command': 'register', 'payload': var_2031_payload})
    var_2033_history = fn_2010_call({'command': 'history', 'name': 'poem_after_the_rain'})
    var_2034_alias = fn_2010_call({'command': 'alias', 'name': 'poem_after_the_rain', 'target': var_2032_record,
                                  'expected_revision': var_2033_history[-1]['revision'] if var_2033_history else 0})
    var_2035_resolved = fn_2010_call({'command': 'resolve', 'pointer': 'poem_after_the_rain'})
    if var_2035_resolved['target'] != var_2031_payload:
        raise AssertionError('The persistent alias did not resolve to the saved poem.')
    var_2036_report = {
        'configuration': var_2005_config, 'laws': var_2021_laws, 'steps': var_2023_steps,
        'poem_record': var_2032_record, 'alias': var_2034_alias, 'resolution': var_2035_resolved,
        'verification': {'status': 'passed', 'requirements': var_2005_config['requirements'],
                         'scope': 'Declared line-count arithmetic, complete singleton quotient, reconstruction, indexing and persistent resolution.',
                         'semantic_scope': 'Exact line occurrences under the declared rendering rule; no certification of literary meaning or quality.'},
        'dispatcher_evidence': var_2009_evidence,
    }
    var_2037_report_path = var_2003_root / 'runtime_0007_state' / 'poem_0053_report.json'
    var_2038_text_path = var_2003_root / 'runtime_0007_state' / 'poem_0055_text.txt'
    var_2037_report_path.write_text(mod_2000_json.dumps(fn_0121_wire(var_2036_report), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    var_2038_text_path.write_text(var_2030_text, encoding='utf-8')
    print(var_2030_text)
    for var_2039_summary in var_2023_steps:
        print(var_2039_summary['step']['operation'] + ': ' + mod_2000_json.dumps(var_2039_summary['result']['outcome']))
    print('All example checks passed; poem alias: poem_after_the_rain')
    print('Database: ' + str(var_2006_database))
    print('Evidence: ' + str(var_2037_report_path))


if __name__ == '__main__':
    fn_2004_poem()
