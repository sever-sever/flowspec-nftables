
# podman build -t exabgp-noautostart ./
# docker build -t exabgp-noautostart ./

FROM python:3-slim-buster

RUN apt update && apt -y dist-upgrade
RUN apt -q -y install python3-exabgp nano procps nftables sudo
RUN rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN mkdir /etc/exabgp
