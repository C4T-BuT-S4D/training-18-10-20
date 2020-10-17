#!/usr/bin/env python3

import argparse
import json
import os
import random
import secrets
import string
import subprocess
import time
import traceback
import yaml
from concurrent.futures import ThreadPoolExecutor
from dockerfile_parse import DockerfileParser
from enum import Enum
from pathlib import Path
from threading import Lock, current_thread
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().absolute().parent
SERVICES_PATH = BASE_DIR / 'services'
CHECKERS_PATH = BASE_DIR / 'checkers'
MAX_THREADS = int(os.getenv('MAX_THREADS', default=os.cpu_count()))
RUNS = int(os.getenv('RUNS', default=10))
HOST = os.getenv('HOST', default='127.0.0.1')
OUT_LOCK = Lock()
DISABLE_LOG = False

DC_REQUIRED_OPTIONS = ['version', 'services']
DC_ALLOWED_OPTIONS = DC_REQUIRED_OPTIONS + ['volumes']

CONTAINER_REQUIRED_OPTIONS = ['restart']
CONTAINER_ALLOWED_OPTIONS = CONTAINER_REQUIRED_OPTIONS + \
    ['pids_limit', 'mem_limit', 'cpus', 'build', 'image', 'ports', 'environment', 'volumes', 'env_file',
        'depends_on', 'sysctls', 'privileged', 'security_opt']
SERVICE_REQUIRED_OPTIONS = ['pids_limit', 'mem_limit', 'cpus']
SERVICE_ALLOWED_OPTIONS = CONTAINER_ALLOWED_OPTIONS
DATABASES = ['redis', 'postgres', 'mysql', 'mariadb',
             'mongo', 'mssql', 'clickhouse', 'tarantool']
PROXIES = ['nginx', 'envoy']
CLEANERS = ['dedcleaner']

VALIDATE_DIRS = ['checkers', 'services', 'internal']


class ColorType(Enum):
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

    def __str__(self):
        return self.value


def generate_flag(name):
    alph = string.ascii_uppercase + string.digits
    return name[0].upper() + ''.join(random.choices(alph, k=30)) + '='


def colored_log(message: str, color: ColorType = ColorType.OKGREEN):
    print(f'{color}[{current_thread().name}]{ColorType.ENDC} {message}')


class BaseValidator:
    def _log(self, message: str, *, disable_log=False):
        with OUT_LOCK:
            if not DISABLE_LOG:
                colored_log(f'{self}: {message}')

    def _assert(self, cond, message):
        global DISABLE_LOG

        with OUT_LOCK:
            if not cond:
                if not DISABLE_LOG:
                    colored_log(f'{self}: {message}', color=ColorType.FAIL)
                DISABLE_LOG = True
                raise AssertionError

    def _warning(self, cond, message):
        global DISABLE_LOG

        with OUT_LOCK:
            if not cond:
                if not DISABLE_LOG:
                    colored_log(f'{self}: {message}', color=ColorType.WARNING)

    def _error(self, cond, message):
        global DISABLE_LOG

        with OUT_LOCK:
            if not cond:
                if not DISABLE_LOG:
                    colored_log(f'{self}: {message}', color=ColorType.FAIL)


class Checker(BaseValidator):
    def __init__(self, name: str):
        self._name = name
        self._exe_path = CHECKERS_PATH / self._name / 'checker.py'
        self._assert(
            os.access(self._exe_path, os.X_OK),
            f'{self._exe_path.relative_to(BASE_DIR)} must be executable',
        )
        self._timeout = 3
        self._get_info()

    def _get_info(self):
        self._log('running info action')
        cmd = [str(self._exe_path), 'info', HOST]
        out, _ = self._run_command(cmd)
        info = json.loads(out)
        self._log(f'got info: {info}')

        self._vulns = int(info['vulns'])
        self._timeout = int(info['timeout'])
        self._attack_data = bool(info['attack_data'])

        self._assert(60 > self._timeout > 0,
                     f'invalid timeout: {self._timeout}')

    def _run_command(self, command: List[str]) -> Tuple[str, str]:
        try:
            start = time.monotonic()
            p = subprocess.run(command, capture_output=True,
                               check=False, timeout=self._timeout)
            end = time.monotonic()
        except subprocess.TimeoutExpired:
            self._assert(False, 'command timeout expired')
            raise

        elapsed = end - start
        out = p.stdout.decode()
        err = p.stderr.decode()

        out_s = out.rstrip('\n')
        err_s = err.rstrip('\n')
        self._log(f'time: {elapsed:.2f}s\nstdout:\n{out_s}\nstderr:\n{err_s}')
        self._assert(p.returncode == 101, f'bad return code: {p.returncode}')

        return out, err

    def check(self):
        self._log('running CHECK')
        cmd = [str(self._exe_path), 'check', HOST]
        self._run_command(cmd)

    def put(self, flag: str, flag_id: str, vuln: int):
        self._log(f'running PUT, flag={flag} flag_id={flag_id} vuln={vuln}')
        cmd = [str(self._exe_path), 'put', HOST, flag_id, flag, str(vuln)]
        out, err = self._run_command(cmd)

        self._assert(out, 'stdout is empty')

        new_flag_id = err
        self._assert(new_flag_id, 'returned flag_id is empty')

        if self._attack_data:
            self._assert(flag not in out, 'flag is leaked in public data')

        return new_flag_id

    def get(self, flag: str, flag_id: str, vuln: int):
        self._log(f'running GET, flag={flag} flag_id={flag_id} vuln={vuln}')
        cmd = [str(self._exe_path), 'get', HOST, flag_id, flag, str(vuln)]
        self._run_command(cmd)

    def run_all(self, step: int):
        self._log(f'running all actions (run {step} of {RUNS})')
        self.check()

        for vuln in range(1, self._vulns + 1):
            flag = generate_flag(self._name)
            flag_id = self.put(
                flag=flag, flag_id=secrets.token_hex(16), vuln=vuln)
            flag_id = flag_id.strip()
            self.get(flag, flag_id, vuln)

    def __str__(self):
        return f'checker {self._name}'


class Service(BaseValidator):
    def __init__(self, name: str):
        self._name = name
        self._path = SERVICES_PATH / self._name
        self._dc_path = self._path / 'docker-compose.yml'
        self._assert(self._dc_path.exists(),
                     f'{self._dc_path.relative_to(BASE_DIR)} missing')

        self._checker = Checker(self._name)

    @property
    def name(self):
        return self._name

    def _run_dc(self, *args):
        cmd = ['docker-compose', '-f', str(self._dc_path)] + list(args)
        subprocess.run(cmd, check=True)

    def up(self):
        self._log('starting')
        self._run_dc('up', '--build', '-d')

    def logs(self):
        self._log('printing logs')
        self._run_dc('logs', '--tail', '2000')

    def down(self):
        self._log('stopping')
        self._run_dc('down', '-v')

    def validate_checker(self):
        self._log('validating checker')

        cnt_threads = max(1, min(MAX_THREADS, RUNS // 10))
        self._log(f'starting {cnt_threads} checker threads')
        with ThreadPoolExecutor(max_workers=cnt_threads, thread_name_prefix='Executor') as executor:
            for _ in executor.map(self._checker.run_all, range(1, RUNS + 1)):
                pass

    def __str__(self):
        return f'service {self._name}'


class StructureValidator(BaseValidator):
    def __init__(self, d: Path, service: Service):
        self.d = d
        self._was_error = False
        self._service = service

    def _error(self, cond, message):
        if not cond:
            self._was_error = True
            super()._error(cond, message)

    def validate(self):
        for d in VALIDATE_DIRS:
            self.validate_dir(self.d / d / self._service.name)
        return not self._was_error

    def validate_dir(self, d: Path = None):
        if not d.exists():
            return
        for f in d.iterdir():
            if f.is_file():
                self.validate_file(f)
            elif f.name[0] != '.':
                self.validate_dir(f)

    def validate_file(self, f: Path):
        path = f.relative_to(BASE_DIR)
        self._error(f.suffix != '.yaml', f'file {path} has .yaml extension')

        if f.name == 'docker-compose.yml':
            with open(f, "r") as file:
                dc = yaml.safe_load(file)

            for opt in DC_REQUIRED_OPTIONS:
                self._error(opt in dc, f'required option {opt} not in {path}')

            self._error(dc['version'] == '2.4',
                        f'version is not 2.4 in {path}')

            for opt in dc:
                self._error(opt in DC_ALLOWED_OPTIONS,
                            f'option {opt} in {path} is not allowed')

            for container in dc['services']:
                for opt in CONTAINER_REQUIRED_OPTIONS:
                    self._error(
                        opt in dc['services'][container], f'required option {opt} not in {path} for container {container}')

                for opt in dc['services'][container]:
                    self._error(opt in CONTAINER_ALLOWED_OPTIONS,
                                f'option {opt} in {path} is not allowed for container {container}')

                if 'image' in container and 'build' in container:
                    self._error(False, f'both image and build options in {path} for container {container}')
                    continue

                if 'image' in dc['services'][container]:
                    image = dc['services'][container]['image']
                else:
                    build = dc['services'][container]['build']
                    if type(build) == str:
                        dockerfile = f.parent / build / 'Dockerfile'
                    else:
                        context = build['context']
                        if 'dockerfile' in build:
                            dockerfile = f.parent / context / build['dockerfile']
                        else:
                            dockerfile = f.parent / context / 'Dockerfile'

                    dfp = DockerfileParser()
                    with open(dockerfile, 'r') as file:
                        dfp.content = file.read()
                    image = dfp.baseimage

                is_service = True
                for not_service in DATABASES + PROXIES + CLEANERS:
                    if not_service in image:
                        is_service = False

                if is_service:
                    for opt in SERVICE_REQUIRED_OPTIONS:
                        self._warning(
                            opt in dc['services'][container], f'required option {opt} not in {path} for service {container}')

                    for opt in dc['services'][container]:
                        self._warning(opt in SERVICE_ALLOWED_OPTIONS,
                                    f'option {opt} in {path} is not allowed for service {container}')

        elif f.name == '.gitkeep':
            self._error(False, f'{path} found, should be named .keep')

    def __str__(self):
        return f'structure validator'


def get_services() -> List[Service]:
    if os.getenv('SERVICE') == 'all':
        result = list(
            Service(service_path.name) for service_path in SERVICES_PATH.iterdir()
            if service_path.name[0] != '.' and service_path.is_dir()
        )
    else:
        result = [Service(os.environ['SERVICE'])]

    with OUT_LOCK:
        colored_log('Got services:', ', '.join(map(str, result)))
    return result


def list_services(_args):
    get_services()


def start_services(_args):
    for service in get_services():
        service.up()


def stop_services(_args):
    for service in get_services():
        service.down()


def logs_services(_args):
    for service in get_services():
        service.logs()


def validate_checkers(_args):
    for service in get_services():
        service.validate_checker()


def validate_structure(_args):
    was_error = False
    for service in get_services():
        validator = StructureValidator(BASE_DIR, service)
        if not validator.validate():
            was_error = True

    if was_error:
        with OUT_LOCK:
            colored_log(f'structure validator: failed', color=ColorType.FAIL)
            raise AssertionError


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Validate checkers for A&D. '
                    'Host & number of runs are passed with HOST and RUNS env vars'
    )
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser(
        'list',
        help='List services to test',
    )
    list_parser.set_defaults(func=list_services)

    up_parser = subparsers.add_parser(
        'up',
        help='Start services',
    )
    up_parser.set_defaults(func=start_services)

    down_parser = subparsers.add_parser(
        'down',
        help='Stop services',
    )
    down_parser.set_defaults(func=stop_services)

    logs_parser = subparsers.add_parser(
        'logs',
        help='Print logs for services',
    )
    logs_parser.set_defaults(func=logs_services)

    check_parser = subparsers.add_parser(
        'check',
        help='Run checkers validation',
    )
    check_parser.set_defaults(func=validate_checkers)

    validate_parser = subparsers.add_parser(
        'validate',
        help='Run structure validation',
    )
    validate_parser.set_defaults(func=validate_structure)

    parsed = parser.parse_args()
    try:
        parsed.func(parsed)
    except AssertionError:
        exit(1)
    except Exception as e:
        tb = traceback.format_exc()
        print('Got exception:', e, tb)
        exit(1)
