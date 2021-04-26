"""Makefile-like"""
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence

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


def info(msg: str) -> None:
    typer.echo(f"{ECHO_PREFIX}{msg}")


def error(msg: str) -> None:
    typer.secho(f"{ECHO_PREFIX}ERROR: {msg}", fg="red")


def run_command(cmd: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    info(f"Running command: {shlex.join(cmd)}")
    proc = subprocess.run(cmd, check=False)
    if check:
        proc.check_returncode()
    return proc


cli = typer.Typer()


@cli.command()
def lint() -> None:
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
    run_command(["isort"] + PYTHON_SOURCES)
    run_command(["black"] + PYTHON_SOURCES)


if __name__ == "__main__":
    cli(prog_name="make")
