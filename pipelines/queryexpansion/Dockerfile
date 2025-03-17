FROM alpine:latest

RUN apk update && apk add cargo && mkdir -p /usr/src
RUN cargo install --root /usr --git https://github.com/knaw-huc/kweepeer kweepeer

COPY . /usr/src/

EXPOSE 8080
WORKDIR /usr/src/

ENTRYPOINT ["/usr/bin/kweepeer","--config","all.config.toml"]
