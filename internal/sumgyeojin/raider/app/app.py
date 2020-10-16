import os
import tempfile
import time
from pathlib import Path

from flask import Flask, request, jsonify

from nsjail_pg.nsjail import NSJailCommand

BASE_DIR = Path(__file__).resolve().absolute().parent
RUNNER_PATH = BASE_DIR / 'runner'
RUNNER_CFG_PATH = BASE_DIR / 'nsjail_pg' / 'runner.cfg'
NASM_PATH = BASE_DIR / 'nasm'
TOKENS_PATH = BASE_DIR / 'tokens.txt'

TEAMS = 32
COOLDOWN = 15
TOKENS = set(token.split(':')[1] for token in TOKENS_PATH.read_text().split('\n') if token)

app = Flask(__name__)

flags = {}


@app.route('/6c04c574b7fa315f9ad8_checker_write_file', methods=["POST"])
def checker_write_file():
    d = request.json
    filename = d["filename"]
    bytecode = d["bytecode"]
    team = d["team"]

    with tempfile.TemporaryDirectory() as dirname:
        os.chmod(dirname, 0o777)
        cmd = NSJailCommand(
            cmd=['/runner', bytecode],
            config=str(RUNNER_CFG_PATH),
            other=[
                '--bindmount', f"{dirname}:/jail",
                '--bindmount', f"{RUNNER_PATH}:/runner",
            ],
            logger=app.logger,
        )
        cmd.run(output_limit=8192)
        with open(f"{dirname}/{filename}", "r") as f:
            s = f.read()

    flags[team] = (s, filename)

    return jsonify({"result": s})


@app.route('/6c04c574b7fa315f9ad8_checker_read_file', methods=["POST"])
def checker_read_file():
    d = request.json
    filename = d["filename"]
    bytecode = d["bytecode"]
    string = d["string"]

    with tempfile.TemporaryDirectory() as dirname:
        os.chmod(dirname, 0o777)
        with open(f"{dirname}/{filename}", "w") as f:
            f.write(string)
        cmd = NSJailCommand(
            cmd=['/runner', bytecode],
            config=str(RUNNER_CFG_PATH),
            other=[
                '--bindmount', f"{dirname}:/jail",
                '--bindmount', f"{RUNNER_PATH}:/runner",
            ],
            logger=app.logger,
        )
        res = cmd.run(output_limit=8192).stdout

    return jsonify({"result": res})


last_attack = {}


@app.route('/attack')
def attack():
    d = request.json
    if "bytecode" not in d or not isinstance(d["bytecode"], str):
        return jsonify({"error": "invalid bytecode field"}), 400

    if "token" not in d or not isinstance(d["token"], str):
        return jsonify({"error": "invalid token field"}), 400

    if "team" not in d or not isinstance(d["team"], int):
        return jsonify({"error": "invalid team field"}), 400

    bytecode = d["bytecode"]
    token = d["token"]
    team = d["team"]

    if token not in TOKENS:
        return jsonify({"error": "invalid token"}), 403

    if team < 0 or team >= TEAMS:
        return jsonify({"error": "invalid team"}), 400

    if team not in flags:
        return jsonify({"error": "team has no flag"}), 400

    # FIXME: low-probability race condition here
    # threading.Lock won't help with gunicorn workers (LWP, not threads), need to use e.g. redis
    if (token, team) in last_attack and last_attack[(token, team)] > time.time() - COOLDOWN:
        return jsonify({"error": "too fast"}), 429
    last_attack[(token, team)] = time.time()

    flag, filename = flags[team]

    with tempfile.TemporaryDirectory() as dirname:
        os.chmod(dirname, 0o777)
        with open(f"{dirname}/{filename}", "w") as f:
            f.write(flag)
        cmd = NSJailCommand(
            cmd=['/runner', bytecode],
            config=str(RUNNER_CFG_PATH),
            other=[
                '--bindmount', f"{dirname}:/jail",
                '--bindmount', f"{RUNNER_PATH}:/runner",
            ],
            logger=app.logger,
        )
        res = cmd.run(output_limit=8192).stdout

    return jsonify({"result": res})


if __name__ == "__main__":
    app.run(host="0.0.0.0")
