"""Check named-source Cog regions and local links."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from doc_regions.config import files


START = re.compile(r'\s*<!-- \[\[\[cog (.+?) \]\]\] -->\s*')
END = re.compile(r'\s*<!-- \[\[\[end\]\]\] -->\s*')


def problem(document, line, message):
    return dict(document=document, line=line, message=message)


def _split_lf_lines(text):
    parts = text.split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def scan(document, text):
    """Return zero-based, end-exclusive region spans and marker problems."""
    spans, problems = [], []
    opened = None
    for index, line in enumerate(_split_lf_lines(text)):
        if '[[[cog' in line:
            match = START.fullmatch(line)
            if not match:
                problems.append(problem(document, index + 1, 'malformed Cog start marker'))
            if opened is not None:
                problems.append(problem(document, index + 1, 'nested Cog region'))
            else:
                opened = (index, match[1] if match else '')
        elif '[[[end' in line:
            if not END.fullmatch(line):
                problems.append(problem(document, index + 1, 'malformed Cog end marker'))
            if opened is None:
                problems.append(problem(document, index + 1, 'end marker without start'))
            else:
                spans.append(dict(start=opened[0], end=index + 1, code=opened[1]))
                opened = None
        elif ']]]' in line:
            problems.append(problem(document, index + 1, 'malformed Cog marker'))
    if opened is not None:
        problems.append(problem(document, opened[0] + 1, 'unclosed Cog region'))
    return spans, problems


def shape(code, module):
    """Return a region's generator name and literal source arguments."""
    try:
        statements = ast.parse(code).body
    except SyntaxError:
        statements = []
    if len(statements) == 2 and isinstance(statements[0], ast.Import):
        imports = statements[0].names
        output = statements[1]
        if (len(imports) == 1 and imports[0].name == module and imports[0].asname is None
                and isinstance(output, ast.Expr) and isinstance(output.value, ast.Call)):
            call = output.value
            if (isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.attr == 'out' and call.func.value.id == 'cog'
                    and len(call.args) == 1 and not call.keywords
                    and isinstance(call.args[0], ast.Call)):
                generator = call.args[0]
                name = generator.func.attr if isinstance(generator.func, ast.Attribute) else ''
                owner = ast.unparse(generator.func.value) if isinstance(generator.func, ast.Attribute) else ''
                if (owner == module and name and not name.startswith('_') and generator.args
                        and not generator.keywords
                        and all(isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                                for arg in generator.args)):
                    return name, [arg.value for arg in generator.args]
    raise ValueError('region code does not match the allowed shape')


def generator_names(root, generator_path, module):
    code = ('import importlib, inspect, json, sys; '
            'sys.path.insert(0, sys.argv[1]); '
            'm = importlib.import_module(sys.argv[2]); '
            'print(json.dumps([n for n, f in inspect.getmembers(m, inspect.isfunction) '
            'if not n.startswith("_")]))')
    result = subprocess.run([sys.executable, '-B', '-c', code, str(generator_path), module],
                            cwd=root, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'cannot load generator module')
    return json.loads(result.stdout)


def validate(root, targets, generators, generator_path):
    problems, documents, functions = [], {}, None
    for document in targets:
        try:
            files(root, document)
            text = (root / document).read_bytes().decode('utf-8')
        except (OSError, ValueError, UnicodeError) as error:
            problems.append(problem(document, 1, str(error)))
            continue
        spans, errors = scan(document, text)
        problems.extend(errors)
        documents[document] = spans
        for span in spans:
            try:
                function, sources = shape(span['code'], generators)
                for source in sources:
                    files(root, source)
                if functions is None:
                    functions = generator_names(root, generator_path, generators)
                if function not in functions:
                    raise ValueError(f'unknown generator function: {generators}.{function}')
            except (OSError, ValueError) as error:
                problems.append(problem(document, span['start'] + 1, str(error)))
    return documents, problems


def run(root, arguments):
    return subprocess.run(arguments, cwd=root, text=True, capture_output=True)


def cog(root, document, generator_path, update):
    options = ['-r'] if update else [
        '--check', '--diff', '--check-fail-msg=Run deno task doc-regions:update']
    return run(root, [sys.executable, '-B', '-m', 'cogapp', *options,
                      '-I', str(generator_path), document])


def changed_regions(diff, spans):
    changed, line = set(), None
    for text in diff.split('\n'):
        match = re.match(r'^@@ -(\d+)', text)
        if match:
            line = int(match[1]) - 1
        elif line is not None and text.startswith('-'):
            changed.update(span['start'] + 1 for span in spans
                           if span['start'] <= line < span['end'])
            line += 1
        elif line is not None and text.startswith('+'):
            changed.update(span['start'] + 1 for span in spans
                           if span['start'] <= line < span['end'])
        elif line is not None and text.startswith(' '):
            line += 1
    return sorted(changed) or [span['start'] + 1 for span in spans[:1]]


def replace_outputs(document, original, updated, spans):
    old_lines = _split_lf_lines(original.decode('utf-8'))
    new_lines = _split_lf_lines(updated.decode('utf-8'))
    new_spans, errors = scan(document, updated.decode('utf-8'))
    if errors or len(new_spans) != len(spans):
        raise ValueError('Cog output changed the region markers')
    for old, new in reversed(list(zip(spans, new_spans))):
        old_lines[old['start'] + 1:old['end'] - 1] = new_lines[new['start'] + 1:new['end'] - 1]
    return ''.join(old_lines).encode('utf-8')


def process(root, targets, generators, generator_path, updating=False):
    root = Path(root).resolve()
    generator_path = Path(generator_path)
    if not generator_path.is_absolute():
        generator_path = root / generator_path
    generator_path = generator_path.resolve()
    documents, problems = validate(root, targets, generators, generator_path)
    if problems:
        return problems
    for document, spans in documents.items():
        if spans:
            path = root / document
            original = path.read_bytes() if updating else None
            result = cog(root, document, generator_path, updating)
            if result.returncode:
                message = (result.stdout + result.stderr).strip()
                problems.extend(problem(document, line, message)
                                for line in changed_regions(message, spans))
                if updating and path.read_bytes() != original:
                    path.write_bytes(original)
            elif updating:
                try:
                    merged = replace_outputs(document, original, path.read_bytes(), spans)
                except (UnicodeError, ValueError) as error:
                    path.write_bytes(original)
                    problems.append(problem(document, spans[0]['start'] + 1, str(error)))
                else:
                    if merged != path.read_bytes():
                        path.write_bytes(merged)
        if not updating:
            result = run(root, ['lychee', '--offline', '--include-fragments', '--no-progress',
                                '--config', os.devnull, '--format', 'json', '--', document])
            if result.returncode:
                try:
                    failures = [failure for entries in json.loads(result.stdout)['error_map'].values()
                                for failure in entries]
                except (ValueError, KeyError, TypeError):
                    failures = []
                if failures:
                    problems.extend(problem(
                        document, (failure.get('span') or {}).get('line', 1),
                        f"{failure.get('url', '')}: {failure.get('status', {}).get('text', 'link failed')}")
                        for failure in failures)
                else:
                    problems.append(problem(document, 1, (result.stdout + result.stderr).strip()))
    return problems


def check(root, targets, generators, generator_path):
    return process(root, targets, generators, generator_path)


def update(root, targets, generators, generator_path):
    return process(root, targets, generators, generator_path, updating=True)
