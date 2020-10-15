from flask import Flask, request
from nsjail_pg.nsjail import NSJailCommand
from contextlib import closing
from secrets import token_hex
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().absolute().parent
RUNNER_PATH = BASE_DIR / 'runner'

app = Flask(__name__)

@app.route('/6c04c574b7fa315f9ad8_checker_create_file', methods=["POST"])
def checker_create_file():
    d = request.json
    filename = d["filename"]
    bytecode = d["bytecode"]

    with tempfile.TemporaryDirectory() as dirname:
        cmd = NSJailCommand(
            cmd=['/runner', bytecode],
            config='./runner.cfg',
            other=[
                '--bindmount', f"{dirname}:/jail",
                '--bindmount', f"{RUNNER_PATH}:/runner",
                '--bindmount', "./nasm:/usr/bin/nasm"
            ],
        )
        res = cmd.run(output_limit=8192)
        print(res)
        with open(f"{dirname}/{filename}", "r") as f:
            print(f.read())

if __name__ == "__main__":
    app.run()
