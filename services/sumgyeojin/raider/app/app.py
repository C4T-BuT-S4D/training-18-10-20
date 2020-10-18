import json
import logging
import os
import tempfile
from pathlib import Path

import redis
from flask import Flask, request, jsonify

from nsjail_pg.nsjail import NSJailCommand

BASE_DIR = Path(__file__).resolve().absolute().parent
RUNNER_PATH = BASE_DIR / 'runner'
RUNNER_CFG_PATH = BASE_DIR / 'nsjail_pg' / 'runner.cfg'
NASM_PATH = BASE_DIR / 'nasm'
TOKENS_PATH = BASE_DIR / 'tokens.txt'

COOLDOWN = 3
TOKENS = set(token.split(':')[1] for token in TOKENS_PATH.read_text().split('\n') if token)
TEAMS = len(TOKENS)

app = Flask(__name__)

R = redis.Redis(host='redis', port=6379, db=0)

@app.route('/attack', methods=["POST"])
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

    with R.pipeline(transaction=False) as pipeline:
        pipeline.exists(team)
        pipeline.set(f'attack:rl:{team}:{token}', 1, ex=COOLDOWN, nx=True)
        exists, set_success = pipeline.execute()

        if not exists:
            return jsonify({"error": "team has no flag"}), 400

        if not set_success:
            return jsonify({"error": "too fast"}), 429

        data = pipeline.get(team).execute()[0]
        flag, filename = json.loads(data)

    app.logger.info(f"{token} is attacking {team} with flag {flag}")

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
    app.run(host="0.0.0.0", debug=True)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
