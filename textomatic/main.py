import sys

import click
from prompt_toolkit.patch_stdout import patch_stdout

from textomatic import context
from textomatic.app.builder import create_app, process_one


@click.command()
@click.argument("path", nargs=-1)
@click.option(
    "-c",
    "--command",
    default="",
    help="Start with an initial COMMAND",
)
@click.option(
    "-p",
    "--process-and-exit",
    is_flag=True,
    help="Run process on INPUT and COMMAND and exit without showing the UI",
)
@click.option(
    "-h",
    "--horizontal",
    is_flag=True,
    help="Start with a horizontal split between the INPUT and OUTPUT",
)
@click.option(
    "-m",
    "--manual",
    is_flag=True,
    help="Start with manual mode enabled. In manual mode, OUTPUT is only updated on demand",
)
@click.option(
    "-f",
    "--focus",
    type=click.Choice(["COMMAND", "INPUT", "OUTPUT", "c", "i", "o"]),
    help="Start the specified component focused",
)
def main(path, command, process_and_exit, horizontal, manual, focus):
    if len(path) > 1:
        raise click.ClickException("Only one path argument is supported")

    if process_and_exit and manual:
        raise click.ClickException("--manual with --process-and-exit makes no sense")

    ctx = context.get()

    path = path[0] if path else None
    if path or not sys.stdin.isatty():
        if path:
            with open(path) as f:
                text = f.read()
        else:
            text = sys.stdin.read()
            sys.stdin.close()
            sys.stdin = open(2)
        ctx.input_buffer.text = text

    ctx.live = not manual
    ctx.box_veritcal_orientation = not horizontal
    ctx.cmd_buffer.text = command

    if process_and_exit:
        ctx.non_interactive = True
        process_one()
    else:
        ctx.app = create_app(focus)
        with patch_stdout():
            ctx.app.run()

    if ctx.print_output_on_exit or ctx.non_interactive:
        print(ctx.output_buffer.text)


if __name__ == "__main__":
    main()
