import click
from .config import config

@click.group()
def main() -> None:
    pass

main.add_command(config)
