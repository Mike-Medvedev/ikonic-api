"""Defines CLI commands that are exposed in pyproject.toml and built into binaries in venv. Executable from CLI."""

import subprocess


def formatter() -> None:
    """Run Ruff formatter in current directory."""
    args = ["uv", "run", "ruff", "format", "."]
    subprocess.run(args, check=False)  # noqa: S603


def lint() -> None:
    """Run Ruff linter in current directory."""
    args = ["uv", "run", "ruff", "check", "."]
    subprocess.run(args, check=False)  # noqa: S603
