"""Makefile-like"""
import os
import shutil
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import typer

REPO_DIR = Path(__file__).parent
PYTHON_SOURCES = [
    str(p)
    for p in (
        Path(__file__),
        REPO_DIR / "source" / "conf.py",
        REPO_DIR / "lib" / "papyrus",
    )
]
ECHO_PREFIX = "[make] "
PYTHON = sys.executable

# Sphinx options
SPHINX_SOURCE_DIR = "source"
SPHINX_BUILD_DIR = "build"
SPHINX_OPTS = ["-W", "--keep-going", "-T"]


def info(msg: str) -> None:
    typer.echo(f"{ECHO_PREFIX}{msg}")


def error(msg: str) -> None:
    typer.secho(f"{ECHO_PREFIX}ERROR: {msg}", fg="red")


def run_command(
    cmd: Sequence[str],
    *,
    check: bool = True,
    env: Optional[Dict[str, str]] = None,
    cwd: Path = REPO_DIR,
) -> subprocess.CompletedProcess[bytes]:
    info(f"Running command: {shlex.join(cmd)}")
    env = {**os.environ, **(env or {})}
    proc = subprocess.run(cmd, check=False, env=env, cwd=cwd)
    if check and proc.returncode != 0:
        error(f"Command returned non-zero exit status {proc.returncode}.")
        sys.exit(1)
    return proc


cli = typer.Typer()


@cli.command()
def edit() -> None:
    """Launch Visual Studio Code."""
    code_exe = shutil.which("code")
    if not code_exe:
        error("Could not find 'code' in PATH.")
        sys.exit(1)
    env = {"PYTHON": PYTHON}  # for "python.pythonPath" in .vscode/settings.json
    run_command([code_exe, str(REPO_DIR)], env=env)


@cli.command()
def lint() -> None:
    """Run linters."""
    failed: List[str] = []
    for cmd in (
        ["isort", "--check"] + PYTHON_SOURCES,
        ["black", "--check"] + PYTHON_SOURCES,
        ["pylint"] + PYTHON_SOURCES,
        ["mypy"] + PYTHON_SOURCES,
    ):
        name = cmd[0]
        proc = run_command(cmd, check=False)
        if proc.returncode != 0:
            failed.append(name)

    if failed:
        error(f"Linter(s) failed: {failed}")
        sys.exit(1)


@cli.command()
def format() -> None:  # pylint: disable=redefined-builtin
    """Run auto-formatters."""
    run_command(["isort"] + PYTHON_SOURCES)
    run_command(["black"] + PYTHON_SOURCES)


@cli.command()
def build() -> None:
    """Build blog content."""
    run_command(
        [
            "sphinx-build",
            SPHINX_SOURCE_DIR,
            SPHINX_BUILD_DIR,
            "-j",
            "auto",
        ]
        + SPHINX_OPTS
    )


if __name__ == "__main__":
    cli(prog_name="make")
