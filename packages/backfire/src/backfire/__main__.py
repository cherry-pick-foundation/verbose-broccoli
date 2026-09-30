"""Start the PyModel server with Backfire's selected provider."""

import argparse
import logging
import os
import sys

import anyio
from jev_judge_mcp import server as pymodel
from jev_judge_mcp import tools as model_tools

from backfire import noul
from backfire import providers


def main() -> None:
    """Run PyModel's stdio server and cleanly exit its worker process."""
    parser = argparse.ArgumentParser(prog="backfire")
    parser.add_argument("command", choices=("serve-mcp",))
    parser.add_argument("--education", action="store_true")
    parser.add_argument("--profile", help="use only this profile of the order")
    args = parser.parse_args()
    pymodel.require_posix()
    settings = pymodel.load_settings()
    if args.education:
        settings = settings.model_copy(update={"jev_judge_mcp_cache": False})
    pymodel.ensure_secrets_redactable(settings)
    pymodel.ensure_http_access_control(settings)
    pymodel.ensure_http_port_free(settings)
    pymodel.configure_logging(settings.log_level, settings.secret_values())
    runtime = model_tools.Runtime(
        settings,
        provider_factory=providers.provider_factory(
            education=args.education, profile=args.profile
        ),
    )
    instance = pymodel.JevMCPServer(
        toolset=model_tools.Toolset(runtime, (*model_tools.TOOLS, noul.NOUL)),
        log_level=settings.log_level,
    )
    logging.getLogger(__name__).info(
        "identity %s %s", instance.name, instance.version
    )
    pymodel.freeze_startup_heap()
    anyio.run(pymodel.serve, instance, settings)
    logging.shutdown()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
