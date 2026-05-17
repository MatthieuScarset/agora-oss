"""Minimal agent runner stub.

This is a non-functional scaffold used for development and testing.
It locates agent folders under the repository `agents/` directory and
provides a simple `AgentRunner` class with a no-op `run` method.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

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


if __name__ == "__main__":
    # Quick smoke test when run directly
    print("Available agents:", list_agents())
