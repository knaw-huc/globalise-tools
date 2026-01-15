FROM alpine:3.22

RUN apk update &&\
    apk add build-base bash python3 python3-dev linux-headers py3-psutil py3-pip py3-wheel poetry git &&\
    mkdir -p /work

COPY globalise_tools/ /work/globalise_tools/
COPY scripts/ /work/scripts/
COPY remote/ /work/remote/
COPY poetry.lock poetry_scripts.py pyproject.toml README.md /work/

RUN cd /work && pip install --break-system-packages .

VOLUME /data
WORKDIR /data

ENTRYPOINT ["/bin/bash"]
