FROM alpine:3.22

RUN apk update &&\
    apk add build-base bash python3 python3-dev linux-headers py3-psutil py3-pip py3-wheel poetry cargo git &&\
    cargo install --root /usr/ lingua-cli &&\  
    cargo install --root /usr/ lexmatch &&\  
    mkdir -p /usr/src

COPY . /usr/src

RUN cd /usr/src && pip install --break-system-packages .

VOLUME /data
WORKDIR /data

ENTRYPOINT ["/bin/sh"]
