from pathlib import Path
from typing import Any
from coretex.networking import networkManager

import subprocess
import click


@click.group()
def main() -> None:
    pass


@main.command()
@click.option("--username", required = True, type = str)
@click.option("--password", required = True, type = str)
def login(username: str, password: str) -> None:
    response = networkManager.authenticate(username, password)
    if response.hasFailed():
        click.echo("Falied to authenticate")
    else:
        click.echo("Authentification successful")


@main.command(context_settings = dict(ignore_unknown_options = True, allow_extra_args = True))
@click.argument('args', nargs = -1, type = click.UNPROCESSED)
def run(args: Any) -> None:
    argsList = list(args)
    entryPoint = Path(argsList.pop(0))
    if entryPoint.exists():
        click.echo("Starting process")
        subprocess.run(["python", str(entryPoint)] + argsList)
    else:
        click.echo("File not found")
