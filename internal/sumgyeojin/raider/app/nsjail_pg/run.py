from nsjail import NSJailCommand
from pathlib import Path
import os

if __name__ == '__main__':
    os.makedirs('/tmp/jail', exist_ok=True)

    p = Path('/tmp/jail')
    p.mkdir(exist_ok=True)
    p /= 'flag.txt'
    p.write_text('flag')
    p.chmod(0o666)

    with open('/tmp/jail/flag.txt', 'w') as f:
        f.write('flag\n')

    # read-write mount
    cmd = NSJailCommand(
        cmd=['/bin/bash', '-c', 'echo new_flag > /jail/flag.txt'],
        config='./runner.cfg',
        other=[
            '--bindmount', "/tmp/jail:/jail",
        ],
    )
    res = cmd.run(output_limit=8192)
    print(res)

    # read-only mount
    cmd = NSJailCommand(
        cmd=['/bin/cat', '/jail/flag.txt'],
        config='./runner.cfg',
        other=[
            '--bindmount', "/tmp/jail:/jail",
        ],
    )
    res = cmd.run(output_limit=8192)
    print(res)
