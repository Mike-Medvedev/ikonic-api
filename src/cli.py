import subprocess


def format():
    args = ["uv", "run", "ruff", "format", "."]
    subprocess.run(args)


def lint():
    args = ["uv", "run", "ruff", "check", "."]
    subprocess.run(args)
