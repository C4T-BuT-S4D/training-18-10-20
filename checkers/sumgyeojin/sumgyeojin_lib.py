import requests
import os
from checklib import *

PORT = 9090
RAIDER = "http://127.0.0.1:5000"

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

    def get_vm(self, s, vmid, status=Status.MUMBLE):
        r = s.get(f"{self.url}/{vmid}")

        d = self.c.get_json(r, "Can't get vm", status=status)
        self.c.assert_in("result", d, "Can't get vm", status=status)
        self.c.assert_eq(type(vmid), type(""), "Invalid response on vm get", status=status)

        return d["result"]

    def run_write_to_file(self, s, bc, filename, string, status=Status.MUMBLE):
        r = s.post(f"{RAIDER}/6c04c574b7fa315f9ad8_checker_write_file", json={
            "filename": filename,
            "bytecode": bc
        })

        d = self.c.get_json(r, "Can't run vm", status=status)
        self.c.assert_in("result", d, "Can't run vm", status=status)
        self.c.assert_eq(d["result"], string, "Invalid vm result", status=status)

    def run_read_from_file(self, s, bc, filename, string, status=Status.MUMBLE):
        r = s.post(f"{RAIDER}/6c04c574b7fa315f9ad8_checker_read_file", json={
            "filename": filename,
            "bytecode": bc,
            "string": string
        })

        d = self.c.get_json(r, "Can't run vm", status=status)
        self.c.assert_in("result", d, "Can't run vm", status=status)
        self.c.assert_eq(d["result"], string, "Invalid vm result", status=status)
