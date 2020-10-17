FROM ubuntu:20.04

RUN apt-get update && apt-get upgrade -yyq
RUN apt-get install socat build-essential -yyq

ADD --chown=root ./sijang /sijang

WORKDIR /

CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork,keepalive", "EXEC:./sijang"]

