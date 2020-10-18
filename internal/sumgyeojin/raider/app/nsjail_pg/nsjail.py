import os
import tempfile
import typing
from contextlib import closing
from pathlib import Path
from typing import List, Optional, IO

from .serializers import RunResult
from .utils import run_command_fast, force_printable

CommandFile = typing.Union[int, Path, None]


class NSJailCommand:
    def __init__(self, cmd: List[str], config: Optional[str] = None, *, logger, other: Optional[List[str]] = None):
        self.cmd = cmd
        self.config = config
        self.other = other
        self.logger = logger

    def _create_command(self, log_file: str):
        result = ['nsjail', '--log', log_file]

        if self.config is not None:
            result += ['--config', self.config]

        if self.other is not None:
            result += self.other

        result.append('--')
        result += self.cmd

        return result

    def run(self, stdin: Optional[int] = None,
            stdout: CommandFile = None, stderr: CommandFile = None,
            output_limit: int = 1024) -> RunResult:

        _stdout: Optional[int] = None
        _stdout_f: Optional[IO] = None
        if isinstance(stdout, Path):
            _stdout_f = stdout.open(mode='wb')
            _stdout = _stdout_f.fileno()
        elif stdout is not None:  # IO instance
            _stdout = stdout
        else:
            _stdout_f = tempfile.NamedTemporaryFile()
            stdout = Path(_stdout_f.name)
            _stdout = _stdout_f.fileno()

        _stderr: Optional[int] = None
        _stderr_f: Optional[IO] = None
        if isinstance(stderr, Path):
            _stderr_f = stderr.open(mode='wb')
            _stderr = _stderr_f.fileno()
        elif stderr is not None:  # IO instance
            _stderr = stderr
        else:
            _stderr_f = tempfile.NamedTemporaryFile()
            stderr = Path(_stderr_f.name)
            _stderr = _stderr_f.fileno()

        jail_logfile = tempfile.NamedTemporaryFile(delete=True)

        command = self._create_command(log_file=jail_logfile.name)
        log_cmd = str(command)[:128]

        self.logger.info(f'Running command {log_cmd} with stdin={stdin} stdout={stdout} stderr={stderr}')
        stats = run_command_fast(command, stdin=stdin, stdout=_stdout, stderr=_stderr)

        stdout_content = b''
        stderr_content = b''

        if isinstance(stdout, Path):
            with stdout.open(mode='rb') as f:
                stdout_content = f.read(output_limit)

            if output_limit != -1 and stdout.stat().st_size > output_limit:
                stdout_content += b' <truncated>'

            _stdout_f.close()  # this will remove file if initial stdout was None

        if isinstance(stderr, Path):
            with stderr.open(mode='rb') as f:
                if output_limit != -1 and stderr.stat().st_size > output_limit:
                    f.seek(-output_limit, os.SEEK_END)
                    stderr_content = b'<truncated> '

                stderr_content += f.read(output_limit)

            _stderr_f.close()  # this will remove file if initial stderr was None

        with closing(jail_logfile):
            with open(jail_logfile.name, 'rb') as f:
                jail_log_content = f.read()

        result = RunResult(
            stats=stats,
            stdout=force_printable(stdout_content),
            stderr=force_printable(stderr_content),
            run_log=force_printable(jail_log_content),
        )

        self.logger.info(f'Command {log_cmd} result: {result}')

        return result
