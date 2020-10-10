import os
import pty
import select
import signal
import sys
import time

import pyte


def run():
    screen = pyte.Screen(80, 24)
    stream = pyte.ByteStream(screen)
    p_pid, master_fd = pty.fork()
    python = sys.executable
    args = [python, "-m", "textomatic.main"]
    if p_pid == 0:
        os.execvpe(python, args, {})
    start = time.time()
    while True:
        rlist, *_ = select.select([master_fd], [], [], 1)
        if time.time() - start > 1:
            break
        if rlist:
            data = os.read(master_fd, 1024)
            if not data:
                break
            stream.feed(data)
    os.kill(p_pid, signal.SIGTERM)
    return screen.display


def test_sanity():
    output = run()
    assert output[0].startswith("INPUT")
    assert output[-1].startswith(">")
