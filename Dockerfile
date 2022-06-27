
# podman build -t exabgp-noautostart ./
# docker build -t exabgp-noautostart ./

FROM python:3-slim-buster

RUN apt-get -qy update && apt-get -qy dist-upgrade
RUN apt-get -qy install python3-exabgp nano procps nftables ssh
RUN rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN python3 -m pip install --upgrade pip && pip3 install -U netmiko

RUN mkdir /etc/exabgp
