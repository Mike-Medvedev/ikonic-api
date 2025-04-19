import subprocess


def formatter():
    args = ["uv", "run", "ruff", "format", "."]
    subprocess.run(args, check=False)  # noqa: S603


def lint():
    args = ["uv", "run", "ruff", "check", "."]
    subprocess.run(args, check=False)  # noqa: S603
