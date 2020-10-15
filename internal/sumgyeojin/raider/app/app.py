from flask import Flask, request, jsonify
from nsjail_pg.nsjail import NSJailCommand
from contextlib import closing
from secrets import token_hex
import tempfile
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().absolute().parent
RUNNER_PATH = BASE_DIR / 'runner'
RUNNER_CFG_PATH = BASE_DIR / 'nsjail_pg' / 'runner.cfg'
NASM_PATH = BASE_DIR / 'nasm'

app = Flask(__name__)

@app.route('/6c04c574b7fa315f9ad8_checker_write_file', methods=["POST"])
def checker_read_file():
    d = request.json
    filename = d["filename"]
    bytecode = d["bytecode"]

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

    return jsonify({"result": s})

@app.route('/6c04c574b7fa315f9ad8_checker_read_file', methods=["POST"])
def checker_write_file():
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

if __name__ == "__main__":
    app.run(host="0.0.0.0")
