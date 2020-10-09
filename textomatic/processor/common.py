import subprocess

from textomatic.exceptions import ProcessException


def run_jq(text, args):
    final_args = ["jq", "-c"]
    if args:
        final_args.append(args)
    try:
        return subprocess.check_output(
            final_args,
            stderr=subprocess.STDOUT,
            input=bytes(text, encoding="utf-8"),
        ).decode()
    except subprocess.CalledProcessError as e:
        raise ProcessException(e.stdout.decode())
