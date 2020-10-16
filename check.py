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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock, current_thread
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().absolute().parent
SERVICES_PATH = BASE_DIR / 'services'
CHECKERS_PATH = BASE_DIR / 'checkers'
MAX_THREADS = int(os.getenv('MAX_THREADS', default=16))
RUNS = int(os.getenv('RUNS', default=10))
HOST = os.getenv('HOST', default='127.0.0.1')
OUT_LOCK = Lock()


def generate_flag(name):
    alph = string.ascii_uppercase + string.digits
    return name[0].upper() + ''.join(random.choices(alph, k=30)) + '='


class BaseValidator:
    def _log(self, message: str):
        with OUT_LOCK:
            print(f'[{current_thread().name}] {str(self)}: {message}')

    def _assert(self, cond, message):
        if not cond:
            self._log(message)
            raise AssertionError


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

        self._assert(60 > self._timeout > 0, f'invalid timeout: {self._timeout}')

    def _run_command(self, command: List[str]) -> Tuple[str, str]:
        try:
            start = time.monotonic()
            p = subprocess.run(command, capture_output=True, check=False, timeout=self._timeout)
            end = time.monotonic()
        except subprocess.TimeoutExpired:
            self._log('command timeout expired')
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
            flag_id = self.put(flag=flag, flag_id=secrets.token_hex(16), vuln=vuln)
            flag_id = flag_id.strip()
            self.get(flag, flag_id, vuln)

    def __str__(self):
        return f'checker {self._name}'


class Service(BaseValidator):
    def __init__(self, name: str):
        self._name = name
        self._dc_path = SERVICES_PATH / self._name / 'docker-compose.yml'
        self._assert(self._dc_path.exists(), f'{self._dc_path.relative_to(BASE_DIR)} missing')

        self._checker = Checker(self._name)

    def _log(self, message: str):
        with OUT_LOCK:
            print(f'[{current_thread().name}] service {self._name}: {message}')

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
            executor.map(self._checker.run_all, range(1, RUNS + 1))

    def __str__(self):
        return f'service {self._name}'


def get_services() -> List[Service]:
    if os.getenv('SERVICE') == 'all':
        result = list(
            Service(service_path.name) for service_path in SERVICES_PATH.iterdir()
            if service_path.name[0] != '.' and service_path.is_dir()
        )
    else:
        result = [Service(os.environ['SERVICE'])]

    with OUT_LOCK:
        print('Got services:', ', '.join(map(str, result)))
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

    parsed = parser.parse_args()
    try:
        parsed.func(parsed)
    except AssertionError:
        exit(1)
    except Exception as e:
        tb = traceback.format_exc()
        print('Got exception:', e, tb)
        exit(1)
