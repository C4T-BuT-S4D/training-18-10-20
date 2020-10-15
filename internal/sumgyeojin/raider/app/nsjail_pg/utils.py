import platform
import shlex
from contextlib import closing
from multiprocessing import Process, Pipe

import base64
import math
import os
import resource
import time
from multiprocessing.connection import Connection
from pathlib import Path
from typing import List, Optional

from .serializers import CommandStats

STANDARD_FDS = {0, 1, 2}


def _close_all_fds(exclude=None):
    if exclude is None:
        exclude = STANDARD_FDS

    fds = list(map(lambda path: int(path.name), Path('/proc/self/fd').iterdir()))

    for fd in fds:
        if fd in exclude:
            continue
        try:
            os.close(fd)
        except OSError:
            pass


def _fast_run_command_target(command: List[str], w: Connection, stdin: Optional[int] = None,
                             stdout: Optional[int] = None,
                             stderr: Optional[int] = None) -> None:
    """Low-level command invoker with low overhead.

        Writes the CommandResult instance to the provided connection w.
        Uses pure os wrappers around libc commands, so it's pretty fast.
    """

    # this function is to be run in a dedicated process anyway, so we can overwrite
    # current process' fds for more accurate child execution time measurement
    if stdin is not None:
        os.dup2(stdin, 0, inheritable=True)

    if stdout is not None:
        os.dup2(stdout, 1, inheritable=True)

    if stderr is not None:
        os.dup2(stderr, 2, inheritable=True)

    _close_all_fds(STANDARD_FDS | {w.fileno()})

    pid = os.fork()
    if pid == 0:  # in child
        os.close(w.fileno())
        os.execvp(command[0], command)
        os._exit(1)  # this should never happen (unless execvp fails)

    opts = os.WUNTRACED
    start_time = time.monotonic()
    _, status = os.waitpid(pid, opts)
    end_time = time.monotonic()

    rusage = resource.getrusage(resource.RUSAGE_CHILDREN)

    real_time = end_time - start_time
    cpu_time = rusage.ru_utime + rusage.ru_stime
    max_memory = rusage.ru_maxrss

    # mac os shows result in bytes, normal OSes -- in kilobytes
    if platform.platform() != 'darwin':
        max_memory *= 1024

    if os.WIFSIGNALED(status):
        code = 128 + os.WTERMSIG(status)
    else:
        code = os.WEXITSTATUS(status)

    result = CommandStats(
        return_code=code,
        real_time=math.ceil(real_time * 1000),
        cpu_time=math.ceil(cpu_time * 1000),
        max_memory=math.ceil(max_memory),
    )

    w.send(result)


def run_command_fast(command: List[str], *, stdin: Optional[int] = None, stdout: Optional[int] = None,
                     stderr: Optional[int] = None) -> CommandStats:
    """This is the wrapper that created another Process for resource measurement.

        The reason is the specific of rusage linux structure which contains maximum rss
        (allocated memory), so we need a different parent process for each child invocation.

        WARNING: works only on UNIX systems.
    """
    str_command = ' '.join(shlex.quote(x) for x in command)

    r, w = Pipe(duplex=False)

    with closing(r), closing(w):
        p = Process(
            target=_fast_run_command_target,
            kwargs={
                'command': command,
                'stdin': stdin,
                'stdout': stdout,
                'stderr': stderr,
                'w': w,
            }
        )
        p.start()
        w.close()
        p.join()
        result: CommandStats = r.recv()

    return result


def force_printable(data: bytes) -> str:
    try:
        return data.decode()
    except UnicodeDecodeError:
        return base64.b64encode(data).decode()
