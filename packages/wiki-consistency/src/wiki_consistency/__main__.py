"""Run the offline Wiki consistency commands."""

import argparse
import json
import os
import subprocess
import sys

from wiki_consistency import evidence, search
from wiki_consistency.instance import instance_path, roots
from wiki_consistency.lint import check, update
from wiki_consistency.requests import prepare, revisions_for_scope


def _wiki_id(value):
    if value in ("", ".", "..") or "/" in value or "\0" in value:
        raise argparse.ArgumentTypeError("wiki must be a single folder name")
    return value


def _positive_int(value):
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _parser():
    parser = argparse.ArgumentParser(prog="wiki-consistency")
    parser.add_argument("--wiki", dest="wiki_id", type=_wiki_id, default="work")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "update"):
        command = commands.add_parser(name)
        command.add_argument("--wiki", dest="wiki_id", type=_wiki_id,
                             default=argparse.SUPPRESS)
    convert = commands.add_parser("convert")
    convert.add_argument("--wiki", dest="wiki_id", type=_wiki_id,
                         default=argparse.SUPPRESS)
    convert.add_argument("--scope", choices=("changed", "lint"), default="changed")
    index = commands.add_parser("index")
    index.add_argument("--wiki", dest="wiki_id", type=_wiki_id,
                       default=argparse.SUPPRESS)
    prepare_command = commands.add_parser("prepare")
    prepare_command.add_argument("--wiki", dest="wiki_id", type=_wiki_id,
                                 default=argparse.SUPPRESS)
    prepare_command.add_argument("--scope", choices=("changed", "lint"), required=True)
    prepare_command.add_argument("--max-evidence-chars", type=_positive_int, default=40000)
    prepare_command.add_argument("--candidates", type=_positive_int, default=3)
    return parser


def main(argv=None):
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        instance = instance_path(args.wiki_id, os.environ)
        if args.command == "check":
            result = check(instance)
        elif args.command == "update":
            result = update(instance)
        else:
            cache = roots(os.environ)["cache"]
            if args.command == "convert":
                result = evidence.convert(
                    instance, args.wiki_id, cache, revisions_for_scope(instance, args.scope)
                )
            elif args.command == "index":
                result = search.index(instance, args.wiki_id, cache, download=True)
            else:
                result = prepare(
                    instance, args.wiki_id, cache, scope=args.scope,
                    max_evidence_chars=args.max_evidence_chars, candidates=args.candidates,
                )
    except (OSError, ValueError, LookupError, subprocess.SubprocessError) as error:
        print(f"wiki:1: {error}", file=sys.stderr)
        return 1
    if result.get("problems"):
        for problem in result["problems"]:
            print(f"{problem['document']}:{problem['line']}: {problem['message']}",
                  file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
