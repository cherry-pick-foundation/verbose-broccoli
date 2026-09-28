"""Command wrappers; the current directory is the document root."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from doc_regions.config import load
from doc_regions import regions
from doc_regions.requests import prepare


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # Deno task forwards its separator after the configured positional path.
    if len(argv) > 2 and argv[0] == 'prepare' and argv[2] == '--':
        del argv[2]
    parser = argparse.ArgumentParser(prog='doc-regions')
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('check', 'update', 'prepare', 'audit'):
        sub = commands.add_parser(command)
        sub.add_argument('config')
        if command == 'prepare':
            sub.add_argument('--base', required=True)
            sub.add_argument('--max-evidence-chars', required=True, type=positive)
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == 'prepare':
            result = prepare(root, args.config, base=args.base, max_evidence_chars=args.max_evidence_chars)
        else:
            config = load(args.config, root)
            if args.command == 'audit':
                from doc_regions.audit import audit
                result = audit(root, config['report_only'])
            else:
                problems = getattr(regions, args.command)(root, config['targets'], config['generators'],
                                                          config['generator_path'])
                if problems:
                    for p in problems:
                        print(f"{p['document']}:{p['line']}: {p['message']}", file=sys.stderr)
                    return 1
                result = dict(problems=[])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
