"""Load root-relative document and generator configuration."""

from pathlib import Path
import tomllib


def files(root, entry):
    """Expand a repository-relative path or glob into existing files."""
    path = Path(entry) if isinstance(entry, str) else None
    if path is None or not entry or path.is_absolute() or '..' in path.parts:
        raise ValueError(f'Expected a root-relative path or glob: {entry!r}')
    root = Path(root).resolve()
    matches = sorted((match for match in root.glob(entry) if match.is_file()),
                     key=lambda match: match.as_posix())
    if not matches:
        raise ValueError(f'No files match: {entry}')
    if any(not match.resolve().is_relative_to(root) for match in matches):
        raise ValueError(f'Path leaves root: {entry}')
    return matches


def load(config_path, root):
    root = Path(root).resolve()
    config_path = Path(config_path)
    path = config_path if config_path.is_absolute() else root / config_path
    with path.open('rb') as source:
        config = tomllib.load(source)

    for field in ('targets', 'report_only', 'generators', 'generator_path'):
        if field not in config:
            raise ValueError(f'Missing configuration field: {field}')
    for field in ('targets', 'report_only'):
        entries = config[field]
        if not isinstance(entries, list):
            raise ValueError(f'{field} must be a list')
        config[field] = sorted({
            match.relative_to(root).as_posix()
            for entry in entries for match in files(root, entry)
        })

    evidence_exclude = config.get('evidence_exclude', [])
    if not isinstance(evidence_exclude, list) or any(
        not isinstance(entry, str) or not entry or Path(entry).is_absolute()
        or '..' in Path(entry).parts for entry in evidence_exclude
    ):
        raise ValueError('evidence_exclude must be a list of root-relative glob strings')
    config['evidence_exclude'] = evidence_exclude

    overlap = sorted(set(config['targets']) & set(config['report_only']))
    if overlap:
        raise ValueError(f"Paths in targets and report_only: {', '.join(overlap)}")
    for field in ('generators', 'generator_path'):
        if not isinstance(config[field], str) or not config[field]:
            raise ValueError(f'{field} must be a nonempty string')
    generator_path = Path(config['generator_path'])
    config['generator_path'] = (generator_path if generator_path.is_absolute()
                                else root / generator_path).resolve()
    return config
