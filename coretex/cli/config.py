import click


@click.command()
@click.option("--user", is_flag = True, help = "Configure user credentials")
@click.option("--node", is_flag = True, help = "Configure node")
def config(user: bool, node: bool) -> None:
    if not (user ^ node):
        raise click.UsageError("Please use either --user or --node")

    if user:
        click.echo("USER INITIATED")

    if node:
        click.echo("NODE BUILDING")
