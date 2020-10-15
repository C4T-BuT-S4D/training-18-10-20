FROM ubuntu:20.04

RUN apt-get update && apt-get upgrade -yyq

ADD --chown=root ./market /marketd/market

WORKDIR /marketd

CMD "./market"
