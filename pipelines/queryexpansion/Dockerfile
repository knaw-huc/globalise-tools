FROM alpine:latest

RUN apk update && apk add cargo runit nginx sudo git && adduser -D user && mkdir -p /usr/src /etc/service/nginx /etc/service/kweepeer
RUN cargo install --root /usr --git https://github.com/knaw-huc/kweepeer kweepeer

COPY . /usr/src/

WORKDIR /usr/src/

RUN git clone https://github.com/knaw-huc/kweepeer-frontend &&\
    mv etc/kweepeer.run.sh /etc/service/kweepeer/run &&\
    mv etc/nginx.run.sh /etc/service/nginx/run &&\
    mv etc/nginx.conf /etc/nginx/http.d/default.conf &&\
    apk del git

EXPOSE 80

ENTRYPOINT ["runsvdir","-P","/etc/service"]
