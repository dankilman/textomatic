import subprocess

from textomatic.exceptions import ProcessException


def run_jq(text, args):
    final_args = ["jq", "-c", args or "."]
    text = bytes(text, encoding="utf-8") if text else None
    try:
        return subprocess.check_output(
            final_args,
            stderr=subprocess.STDOUT,
            input=text,
        ).decode()
    except subprocess.CalledProcessError as e:
        raise ProcessException(e.stdout.decode())
