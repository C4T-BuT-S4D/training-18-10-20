import requests
import os
from checklib import *
from nsjail_pg.nsjail import NSJailCommand

PORT = 9090

class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker):
        self.c = checker
        self.port = PORT

    def create_vm(self, s, vm):
        r = s.post(self.url, json={
            "bytecode": vm
        })

        d = self.c.get_json(r, "Can't create vm")
        self.c.assert_in("result", d, "Can't create vm")

        vmid = d["result"]
        self.c.assert_eq(type(vmid), type(""), "Invalid response on vm creation")

        return vmid

    def get_vm(self, s, vmid):
        r = s.get(f"{self.url}/{vmid}")

        d = self.c.get_json(r, "Can't get vm")
        self.c.assert_in("result", d, "Can't get vm")

        bc = d["result"]
        self.c.assert_eq(type(vmid), type(""), "Invalid response on vm get")

        return bc

    def run_write_to_file(self, bc, filename, string):
        path = f"/tmp{filename}"
        with open(path, "w") as f:
            f.write(string)

        cmd = NSJailCommand(
            cmd=['/runner', bc],
            config='./runner.cfg',
            other=[
                '--bindmount', f"{path}:{filename}",
                '--bindmount', "./runner:/runner"
            ],
        )

        res = cmd.run(output_limit=8192)
        print(res)

        os.remove(path)
