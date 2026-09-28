"""Run the offline Wiki consistency commands."""

import argparse
import json
import os
import subprocess
import sys

from wiki_consistency.instance import instance_path
from wiki_consistency.lint import check, update


def _wiki_id(value):
    if value in ("", ".", "..") or "/" in value or "\0" in value:
        raise argparse.ArgumentTypeError("wiki must be a single folder name")
    return value


def _parser():
    parser = argparse.ArgumentParser(prog="wiki-consistency")
    parser.add_argument("--wiki", dest="wiki_id", type=_wiki_id, default="default")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "update"):
        command = commands.add_parser(name)
        command.add_argument("--wiki", dest="wiki_id", type=_wiki_id,
                             default=argparse.SUPPRESS)
    return parser


def main(argv=None):
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        instance = instance_path(args.wiki_id, os.environ)
        result = check(instance) if args.command == "check" else update(instance)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"wiki:1: {error}", file=sys.stderr)
        return 1
    if result["problems"]:
        for problem in result["problems"]:
            print(f"{problem['document']}:{problem['line']}: {problem['message']}",
                  file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
