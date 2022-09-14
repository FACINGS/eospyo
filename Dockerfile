FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install curl wget -y

RUN wget https://github.com/AntelopeIO/leap/releases/download/v3.1.0/leap-3.1.0-ubuntu22.04-x86_64.deb
RUN apt install ./leap-3.1.0-ubuntu22.04-x86_64.deb -y
