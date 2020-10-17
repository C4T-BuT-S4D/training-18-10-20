### There are two exploits for this service doing the same thing:

#### exploit_smart.py

This exploit uses a PHP microservice as a XSS webhook and a storage for team keys.

To use this exploit you need to deploy in on some public IP or internal network IP(eg vulnbox).

After it, you need to specify this IP in docker-compose enviroment and exploit.

#### sploit_via_render.py

This exploit uses and XSS to leak key and extract it from PDF file.

To run it you should have a php interpreter installed to generate 'haval160,4' hash.