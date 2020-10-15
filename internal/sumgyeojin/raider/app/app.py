from flask import Flask, request, jsonify
from nsjail_pg.nsjail import NSJailCommand
from contextlib import closing
from secrets import token_hex
from pathlib import Path
import tempfile
import os
import time

BASE_DIR = Path(__file__).resolve().absolute().parent
RUNNER_PATH = BASE_DIR / 'runner'
RUNNER_CFG_PATH = BASE_DIR / 'nsjail_pg' / 'runner.cfg'
NASM_PATH = BASE_DIR / 'nasm'

TEAMS = 32
COOLDOWN = 15
TOKENS = set(map(x: x.strip(), open("/app/tokens", "r").readlines()))

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
        )
        res = cmd.run(output_limit=8192).stdout

    return jsonify({"result": res})

last_attack = {}

@app.route('/attack')
def attack():
    d = request.json
    if "bytecode" not in d or type(d["bytecode"]) != type(""):
        return jsonify({"error": "invalid bytecode field"})

    if "token" not in d or type(d["token"]) != type(""):
        return jsonify({"error": "invalid token field"})

    if "team" not in d or type(d["team"]) != type(0):
        return jsonify({"error": "invalid team field"})

    bytecode = d["bytecode"]
    token = d["token"]
    team = d["team"]

    if token not in TOKENS:
        return jsonify({"error": "invalid token"})

    if team < 0 or team >= TEAMS:
        return jsonify({"error": "invalid team"})

    if (token, team) in last_attack and last_attack[(token, team)] > time.time() - COOLDOWN:
        return jsonify({"error": "too fast"})

    if team not in flags:
        return jsonify({"error": "team has no flag"})

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
        )
        res = cmd.run(output_limit=8192).stdout

    last_attack[(token, team)] = time.time()
    return jsonify({"result": res})

if __name__ == "__main__":
    app.run(host="0.0.0.0")
