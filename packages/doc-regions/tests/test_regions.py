import json
import subprocess
import sys

import pytest

from doc_regions.regions import check, update


CODE = 'import sources; cog.out(sources.render("source.txt"))'


def region(code=CODE, output='fresh\n'):
    return f'<!-- [[[cog {code} ]]] -->\n{output}<!-- [[[end]]] -->\n'


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / 'root'
    root.mkdir()
    generators = tmp_path / 'generators'
    generators.mkdir()
    (generators / 'sources.py').write_text(
        'from pathlib import Path\n'
        'def render(source):\n'
        '    return Path(source).read_text()\n'
    )
    (root / 'source.txt').write_text('fresh\n')
    (root / 'doc.md').write_text('# Title\n\nBefore.\n\n' + region() + '\nAfter.\n')
    return root, ['doc.md'], 'sources', generators


def test_current_region_is_read_only_and_root_relative(workspace, unchanged):
    with unchanged(workspace[0].parent):
        assert check(*workspace) == []


@pytest.mark.parametrize('separator', ['\u2028', '\x0b', '\x0c', '\x1c', '\x1d', '\x1e', '\x85'])
def test_cog_marker_line_counts_only_lf_breaks(workspace, separator, unchanged):
    root = workspace[0]
    (root / 'doc.md').write_text(
        f'Paragraph{separator}continues.\n<!-- [[[end]]] -->\n')
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems[0]['line'] == 2


def test_stale_has_cog_diff_line_and_update_command(workspace, unchanged):
    root = workspace[0]
    (root / 'source.txt').write_text('new\n')
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems
    assert problems[0]['document'] == 'doc.md'
    assert problems[0]['line'] == 5
    assert '-fresh' in problems[0]['message']
    assert '+new' in problems[0]['message']
    assert 'deno task doc-regions:update' in problems[0]['message']


def test_stale_names_caller_supplied_update_command(workspace, unchanged):
    root = workspace[0]
    (root / 'source.txt').write_text('new\n')
    with unchanged(root.parent):
        problems = check(*workspace, fix_command='wiki-consistency update')
    assert problems
    assert 'Run wiki-consistency update' in problems[0]['message']


@pytest.mark.parametrize('text, message', [
    (region().replace('<!-- [[[end]]] -->\n', ''), 'unclosed'),
    ('<!-- [[[end]]] -->\n', 'end'),
    (region(output=region()), 'nested'),
    (region('print("bad")'), 'shape'),
    (region('import sources; cog.out(sources.unknown("source.txt"))'), 'unknown'),
    (region('import sources; cog.out(sources.render(source="source.txt"))'), 'shape'),
    (region('import sources; cog.out(sources.render("missing.txt"))'), 'missing.txt'),
    (region('import sources; cog.out(sources.render("../outside.txt"))'), 'root-relative'),
    (region('import sources; cog.out(sources._private("source.txt"))'), 'shape'),
    (region('import sources as other; cog.out(sources.render("source.txt"))'), 'shape'),
    ('`' + region().splitlines()[0] + '`\n', 'malformed'),
])
def test_bad_region_names_document_and_line(workspace, text, message, unchanged):
    root = workspace[0]
    (root / 'doc.md').write_text(text)
    with unchanged(root.parent):
        problems = check(*workspace)
    assert any(message in p['message'] for p in problems), problems
    assert all(p['document'] == 'doc.md' and p['line'] >= 1 for p in problems)


@pytest.mark.parametrize('text, broken', [
    ('[missing](missing.md)\n', True),
    ('# Title\n\n[missing](#no-heading)\n', True),
    ('# Title\n\n[valid](#title)\n', False),
    ('[external](https://does-not-exist.invalid/foo)\n', False),
])
def test_lychee_offline_links(workspace, text, broken, unchanged):
    root = workspace[0]
    (root / 'doc.md').write_text(text)
    with unchanged(root.parent):
        problems = check(*workspace)
    assert bool(problems) == broken
    if broken:
        assert 'missing' in str(problems) or 'no-heading' in str(problems)


@pytest.mark.parametrize('target, broken', [
    ('existing file.txt', False),
    ('existing doc.md#existing-heading', False),
    ('missing file.txt', True),
    ('existing doc.md#missing-heading', True),
    ('/missing-root-relative.md', True),
])
def test_lychee_absolute_local_links(workspace, target, broken, unchanged):
    root = workspace[0]
    outside = root.parent / 'linked files'
    outside.mkdir()
    (outside / 'existing file.txt').write_text('exists\n')
    (outside / 'existing doc.md').write_text('# Existing heading\n')
    target = target if target.startswith('/') else outside / target
    (root / 'doc.md').write_text(f'[text](<{target}>)\n')
    with unchanged(root.parent):
        problems = check(*workspace)
    assert bool(problems) == broken


def test_update_changes_only_output_and_is_idempotent(workspace):
    root = workspace[0]
    original = (root / 'doc.md').read_bytes()
    (root / 'source.txt').write_text('changed\n')
    assert update(*workspace) == []
    updated = (root / 'doc.md').read_bytes()
    assert updated == original.replace(b'fresh\n', b'changed\n')
    assert update(*workspace) == []
    assert (root / 'doc.md').read_bytes() == updated


def test_update_validates_all_targets_before_writing(workspace, unchanged):
    root, targets, module, generators = workspace
    (root / 'source.txt').write_text('changed\n')
    (root / 'bad.md').write_text(region('print("bad")'))
    with unchanged(root.parent):
        assert update(root, targets + ['bad.md'], module, generators)


def test_missing_target(workspace, unchanged):
    root, _, module, generators = workspace
    with unchanged(root.parent):
        problems = check(root, ['missing.md'], module, generators)
    assert problems[0]['document'] == 'missing.md'


def test_indented_region_in_list(workspace, unchanged):
    root = workspace[0]
    (root / 'doc.md').write_text('- Item\n\n' + ''.join('  ' + line for line in region().splitlines(True)))
    with unchanged(root.parent):
        assert check(*workspace) == []


def test_link_problem_reports_actual_line(workspace, unchanged):
    root = workspace[0]
    (root / 'doc.md').write_text('# Title\n\nParagraph.\n\n[bad](missing.md)\n')
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems[0]['line'] == 5


def test_stale_second_region_reports_its_line(workspace, unchanged):
    root = workspace[0]
    (root / 'doc.md').write_text(region() + '\nParagraph.\n\n' + region(output='stale\n'))
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems[0]['line'] == 7


def test_check_checks_target_links_without_regions_and_ignores_report_only(tmp_path, unchanged):
    root = tmp_path / 'root'
    root.mkdir()
    (root / 'target.md').write_text('[local](local.md)\n')
    (root / 'local.md').write_text('# Local\n')
    (root / 'AGENTS.md').write_text('[missing](absent.md)\n')
    (root / 'regions.toml').write_text(
        'targets = ["target.md"]\nreport_only = ["AGENTS.md"]\n'
        'generators = "sources"\ngenerator_path = "scripts"\n')
    with unchanged(root):
        result = subprocess.run([sys.executable, '-B', '-m', 'doc_regions',
                                 'check', 'regions.toml'], cwd=root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'problems': []}


def test_update_preserves_crlf_agent_bytes(workspace):
    root = workspace[0]
    original = ('Before.\r\n\r\n' + region().replace('\n', '\r\n') + '\r\nAfter.').encode()
    (root / 'doc.md').write_bytes(original)
    (root / 'source.txt').write_text('changed\n')
    assert update(*workspace) == []
    updated = (root / 'doc.md').read_bytes()
    assert updated.startswith(b'Before.\r\n\r\n')
    assert updated.endswith(b'\r\nAfter.')
    assert update(*workspace) == []
    assert (root / 'doc.md').read_bytes() == updated
