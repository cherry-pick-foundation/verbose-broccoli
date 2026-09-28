import pytest

from doc_regions.config import load


def write_config(root, **overrides):
    fields = dict(targets=['wiki/**/*.md'], report_only=['AGENTS.md'],
                  generators='sources', generator_path='scripts')
    fields.update(overrides)
    config = root / 'regions.toml'
    config.write_text('\n'.join(f'{key} = {value!r}' for key, value in fields.items()
                                if value is not None))
    return config


def test_resolves_sorted_globs_against_root(tmp_path, unchanged):
    (tmp_path / 'wiki/sub').mkdir(parents=True)
    for name in ['wiki/z.md', 'wiki/sub/a.md', 'AGENTS.md']:
        (tmp_path / name).write_text('text')
    write_config(tmp_path)
    with unchanged(tmp_path):
        result = load('regions.toml', tmp_path)
    assert result == dict(targets=['wiki/sub/a.md', 'wiki/z.md'],
                          report_only=['AGENTS.md'], generators='sources',
                          generator_path=tmp_path / 'scripts', evidence_exclude=[])


def test_accepts_evidence_exclude_globs(tmp_path):
    (tmp_path / 'wiki').mkdir()
    (tmp_path / 'wiki/doc.md').touch()
    (tmp_path / 'AGENTS.md').touch()
    patterns = ['**/*.lock', 'specs/**']
    config = write_config(tmp_path, evidence_exclude=patterns)
    assert load(config, tmp_path)['evidence_exclude'] == patterns


@pytest.mark.parametrize('value', [
    '**/*.lock', [1], ['/absolute/*.lock'], ['../outside/**'], [''],
])
def test_rejects_invalid_evidence_exclude(tmp_path, value):
    (tmp_path / 'wiki').mkdir()
    (tmp_path / 'wiki/doc.md').touch()
    (tmp_path / 'AGENTS.md').touch()
    config = write_config(tmp_path, evidence_exclude=value)
    with pytest.raises(ValueError, match='evidence_exclude'):
        load(config, tmp_path)


def test_absolute_generator_path_outside_root(tmp_path):
    (tmp_path / 'AGENTS.md').touch()
    config = write_config(tmp_path, targets=[], generator_path=str(tmp_path.parent))
    assert load(config, tmp_path)['generator_path'] == tmp_path.parent


@pytest.mark.parametrize('overrides, message', [
    ({'targets': ['missing/**/*.md']}, 'missing/'),
    ({'targets': ['AGENTS.md']}, 'AGENTS.md'),
    ({'generators': None}, 'generators'),
    ({'targets': 'AGENTS.md'}, 'targets'),
    ({'targets': ['../outside.md']}, '../outside.md'),
    ({'targets': ['/absolute.md']}, '/absolute.md'),
])
def test_rejects_invalid_configuration(tmp_path, overrides, message, unchanged):
    (tmp_path / 'AGENTS.md').touch()
    config = write_config(tmp_path, **overrides)
    with unchanged(tmp_path), pytest.raises(ValueError, match=message):
        load(config, tmp_path)


@pytest.mark.parametrize('field', ['targets', 'report_only', 'generators', 'generator_path'])
def test_missing_required_field_names_field(tmp_path, field):
    (tmp_path / 'AGENTS.md').touch()
    config = write_config(tmp_path, **{field: None})
    with pytest.raises(ValueError, match=field):
        load(config, tmp_path)
