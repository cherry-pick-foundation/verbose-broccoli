import ast
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest

from doc_regions.requests import classify_requests, prepare, verify_requests


FIXTURES = Path(__file__).parent / 'fixtures'
SCHEMAS = {name: json.loads((FIXTURES / f'{name}_input_schema.json').read_text())
           for name in ('backfire_verify', 'backfire_classify')}


def valid(requests):
    for request in requests:
        jsonschema.validate(request['arguments'], SCHEMAS[request['tool']])


def units(count):
    return [dict(id=f'doc.md:{i+1}-{i+1}', text=f'Claim {i}\n') for i in range(count)]


def test_schema_fixtures_copy_backfire_verbatim():
    root = Path(__file__).resolve().parents[2]
    for name, schema in SCHEMAS.items():
        tree = ast.parse((root / 'backfire/src/backfire/tools' / f'{name.removeprefix("backfire_")}.py').read_text())
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'INPUT_SCHEMA' for t in node.targets))
        assert schema == ast.literal_eval(assignment.value)


@pytest.mark.parametrize('evidence_count', [1, 2, 10, 249])
def test_verify_limits_and_lossless_order(evidence_count):
    source = units(451)
    evidence = [dict(id=f'e{i}', text='Evidence\n') for i in range(evidence_count)]
    requests = verify_requests([(source, evidence)])
    valid(requests)
    assert [i for r in requests for i in r['units']] == [u['id'] for u in source]
    assert [c for r in requests for c in r['arguments']['claims']] == [u['text'] for u in source]
    for request in requests:
        count = len(request['arguments']['claims'])
        assert count * (3 if evidence_count == 1 else evidence_count + 4) <= 672
        assert request['arguments']['evidence'] == evidence


def test_verify_groups_keep_input_order_and_evidence():
    first, second = units(2), [dict(id='another:1-1', text='other')]
    a, b = [dict(id='original', text='  untouched\n')], [dict(id='other', text='second')]
    requests = verify_requests([(first, a), (second, b)])
    valid(requests)
    assert [r['units'] for r in requests] == [[u['id'] for u in first], ['another:1-1']]
    assert [r['arguments']['evidence'] for r in requests] == [a, b]


@pytest.mark.parametrize('evidence, limit', [([], '1'),
    ([dict(id=str(i), text='e') for i in range(250)], '249')])
def test_bad_evidence_fails_without_dropping(evidence, limit):
    with pytest.raises(ValueError, match=limit):
        verify_requests([(units(1), evidence)])


def test_classify_batches_and_preserves_long_text():
    source = units(129)
    source[0]['text'] = 'x' * 4000
    requests = classify_requests(source, 'docs/example.md')
    valid(requests)
    assert [len(r['units']) for r in requests] == [64, 64, 1]
    assert [item for r in requests for item in r['arguments']['items']] == source
    assert all(r['arguments']['purpose'] == 'docs/example.md' for r in requests)
    assert [c['id'] for c in requests[0]['arguments']['classes']] == ['mechanical_candidate', 'agent_region']


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, text=True, capture_output=True,
                          check=True).stdout


@pytest.fixture
def repository(tmp_path):
    git(tmp_path, 'init', '-b', 'develop')
    git(tmp_path, 'config', 'user.name', 'Test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    (tmp_path / 'doc.md').write_text('# Title\n\nKept line\nold line.\n')
    (tmp_path / 'AGENTS.md').write_text('# Rules\n\nKeep the files.\n')
    (tmp_path / 'config.toml').write_text('targets = ["doc.md"]\nreport_only = ["AGENTS.md"]\n'
                                         'generators = "sources"\ngenerator_path = "scripts"\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'base')
    git(tmp_path, 'switch', '-c', 'feature')
    (tmp_path / 'doc.md').write_text('# Title\n\nKept line\nnew line.\n\nAdded paragraph.\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'feature')
    (tmp_path / 'doc.md').write_text((tmp_path / 'doc.md').read_text() + '\nWorking tree addition.\n')
    return tmp_path


def test_prepare_root_diff_schema_determinism_and_read_only(repository, unchanged):
    with unchanged(repository):
        first = prepare(repository, 'config.toml', base='develop', max_evidence_chars=80)
        second = prepare(repository, 'config.toml', base='develop', max_evidence_chars=80)
    assert first == second
    assert first['base'].strip() == git(repository, 'rev-parse', 'develop').strip()
    assert [(u['document'], u['first_line']) for u in first['units']] == sorted(
        (u['document'], u['first_line']) for u in first['units'])
    assert all(u['report_only'] == (u['document'] == 'AGENTS.md') for u in first['units'])
    assert [u['added'] for u in first['units'] if u['document'] == 'doc.md'] == [False, False, True, True]
    valid(first['requests'])
    verify = [r for r in first['requests'] if r['tool'] == 'backfire_verify']
    classify = [r for r in first['requests'] if r['tool'] == 'backfire_classify']
    assert [i for r in verify for i in r['units']] == [u['id'] for u in first['units']]
    assert [i for r in classify for i in r['units']] == [u['id'] for u in first['units'] if u['added']]
    evidence = verify[0]['arguments']['evidence']
    assert evidence[0]['id'] == 'doc.md#1'
    assert evidence[1]['id'] == 'doc.md#2'
    assert all(len(e['text']) <= 80 for e in evidence)
    assert ''.join(e['text'] for e in evidence) == git(repository, 'diff', first['base'], '--', 'doc.md')
    assert 'Working tree addition.' in ''.join(e['text'] for e in evidence)


def test_prepare_new_file_and_empty_diff(repository, unchanged):
    (repository / 'new.md').write_text('# New\n\nNew body.\n')
    (repository / 'config.toml').write_text('targets = ["doc.md", "new.md"]\nreport_only = []\n'
                                          'generators = "sources"\ngenerator_path = "scripts"\n')
    with unchanged(repository):
        result = prepare(repository, 'config.toml', base='develop', max_evidence_chars=20000)
    valid(result['requests'])
    assert all(u['added'] for u in result['units'] if u['document'] == 'new.md')
    git(repository, 'add', '.')
    git(repository, 'commit', '-m', 'all')
    with unchanged(repository):
        result = prepare(repository, 'config.toml', base='HEAD', max_evidence_chars=20000)
    assert result['units']
    assert result['requests'] == []


def test_prepare_rejects_more_than_249_evidence_items(repository, unchanged):
    (repository / 'doc.md').write_text('# Title\n\n' + 'x' * 500 + '\n')
    with unchanged(repository), pytest.raises(ValueError, match='249'):
        prepare(repository, 'config.toml', base='develop', max_evidence_chars=1)


def cli(root, *args):
    return subprocess.run([sys.executable, '-B', '-m', 'doc_regions', *args], cwd=root,
                          text=True, capture_output=True)


def test_cli_prepare_deterministic_json(repository, unchanged):
    with unchanged(repository):
        first = cli(repository, 'prepare', 'config.toml', '--base', 'develop', '--max-evidence-chars', '20000')
        second = cli(repository, 'prepare', 'config.toml', '--base', 'develop', '--max-evidence-chars', '20000')
    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    valid(json.loads(first.stdout)['requests'])


@pytest.mark.parametrize('args', [[], ['--base', 'develop'], ['--base', 'develop', '--max-evidence-chars', '0']])
def test_cli_invalid_arguments(repository, args, unchanged):
    with unchanged(repository):
        result = cli(repository, 'prepare', 'config.toml', *args)
    assert result.returncode == 2
    assert result.stderr
    assert not result.stdout


def test_cli_check_update_and_failures(repository, unchanged):
    with unchanged(repository):
        result = cli(repository, 'check', 'config.toml')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'problems': []}
    assert json.loads(cli(repository, 'update', 'config.toml').stdout) == {'problems': []}
    (repository / 'doc.md').write_text('[bad](missing.md)\n')
    with unchanged(repository):
        result = cli(repository, 'check', 'config.toml')
    assert result.returncode == 1
    assert 'doc.md' in result.stderr and 'missing.md' in result.stderr
    assert not result.stdout


def test_cli_accepts_deno_task_separator(repository, unchanged):
    with unchanged(repository):
        result = cli(repository, 'prepare', 'config.toml', '--', '--base', 'develop',
                     '--max-evidence-chars', '20000')
    assert result.returncode == 0, result.stderr
    valid(json.loads(result.stdout)['requests'])
