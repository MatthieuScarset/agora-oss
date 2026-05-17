"""Minimal agent runner stub.

This is a non-functional scaffold used for development and testing.
It locates agent folders under the repository `agents/` directory and
provides a simple `AgentRunner` class with a no-op `run` method.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import typer

AGENTS_ROOT = Path(__file__).resolve().parents[2] / "agents"


def list_agents() -> Dict[str, Path]:
    """Return a mapping of agent-name -> path for available agents.

    This is intentionally simple: it lists directories under `agents/`.
    """
    agents: Dict[str, Path] = {}
    if not AGENTS_ROOT.exists():
        return agents
    for p in AGENTS_ROOT.iterdir():
        if p.is_dir():
            agents[p.name] = p
    return agents


class AgentRunner:
    """Stub runner that would execute a named agent.

    Use `run` to invoke the agent. Current implementation is a placeholder
    that validates the agent exists and returns a minimal result dict.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.path = list_agents().get(name)
        if not self.path:
            raise ValueError(f"Unknown agent: {name}")

    def run(self, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Run the agent with an optional payload.

        This stub does not perform any real computation.
        """
        # In a real runner this is where we'd load the prompt/instructions,
        # instantiate models, call tools, and persist outputs.
        return {
            "agent": self.name,
            "path": str(self.path),
            "status": "stubbed",
            "payload": payload,
        }


# Typer CLI app (preferred for agent CLIs per agents/.instructions.md)
app = typer.Typer(help="Agent runner CLI")


@app.command("list")
def cli_list() -> None:
    """List available agents."""
    agents = list_agents()
    print(json.dumps({k: str(v) for k, v in agents.items()}, indent=2))


@app.command("run")
def cli_run(name: str, extra_args: List[str] = typer.Argument(None)) -> None:
    """Run a named agent (stub).

    Example: `agora-agent-runner run <agent-name> -- --dry`
    """
    payload = {"args": extra_args} if extra_args else None
    runner = AgentRunner(name)
    result = runner.run(payload)
    print(json.dumps(result, indent=2))


@app.callback(invoke_without_command=True)
def main_cli(
    ctx: typer.Context,
    name: str | None = None,
    extra_args: List[str] = typer.Argument(
        None, help="Extra arguments passed to the agent"
    ),
) -> None:
    """Compatibility callback: allow `agora-agent-runner <agent-name>`.

    If no `name` is provided, list agents. If `name` is provided and no
    subcommand was invoked, run the agent directly.
    """
    if ctx.invoked_subcommand is None:
        if name is None:
            cli_list()
        else:
            cli_run(name, extra_args)


def main(argv: list[str] | None = None) -> int:
    """Simple CLI entrypoint for the agent runner.

    Usage:
      - no args: prints available agents
      - <agent-name> [args...]: runs the named agent (stub) with optional args
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        agents = list_agents()
        print(json.dumps({k: str(v) for k, v in agents.items()}, indent=2))
        return 0

    name = argv[0]
    payload = {"args": argv[1:]} if len(argv) > 1 else None
    runner = AgentRunner(name)
    result = runner.run(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
