Please read the following text carefully.

You are given 3 parts: the server, client and raider.

You can patch server and do everything you want with it.

Client is being used by checkers, so you can't change it. Source code and binary is given for your convenience.

In this task you have to attack checkers and not players.

Attack server (raider) is available on 10.10.10.137. Part of source code is given for your convenience.

Checker logic:

1) submit bytecode that writes flag to /jail/flag_<random>
2) submit bytecode that reads flag from /jail/flag_<random>

To get last flag you can submit your bytecode, token and team that you want to attack on http://10.10.10.137:5000/attack that will attempt to read that /jail/flag_<random> file.
Stdout of your program will be send back to you so you can read flag.

For more information consider reading raider/app/app.py

