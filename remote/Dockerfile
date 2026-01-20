FROM alpine:3.22

RUN apk update &&\
    apk add build-base bash python3 python3-dev linux-headers \
            py3-psutil py3-pip py3-wheel poetry git expect openssh \
            openssh-client sshpass zip &&\
    mkdir -p /work

COPY globalise_tools/ /work/globalise_tools/
COPY scripts/ /work/scripts/
COPY remote/ /work/remote/
COPY poetry.lock poetry_scripts.py pyproject.toml README.md /work/
COPY remote/Makefile /work/Makefile
COPY data/typesystem.xml /work/typesystem.xml
COPY data/inventory2timespan.json /work/inventory2timespan.json

RUN cd /work && \
    cp remote/scripts/* scripts/ && \
    mkdir ~/.ssh && \
    echo "[hucdrive.huc.knaw.nl]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC8jtrMZ9tf1YcVtA1+JgYh709ifmXKwuRQER31cUNtaIjGuqP7KElcnms548c8Lnh7fyzE/72gOGex54rWCnnsCgN84gt4tA3GAURmdwospaXV3hKa73n9zmxIuSMw12mzxtVlFo2CnsXWYsaoh9gw80RF2V52Q3lEwLrJq7DKIm6KWMTys+h+5sZFSAnEDaAmVDv4669SPNwJuLAbJufi2R4VDtPiFWDGFbch6EKUGs0oS6LQzD9XYYU9E/62bmGAQdqQ5HgBA4OVN2YtBDz4kL/VSICH7Wzl89b0ReIh3X/rYuJbnqwIEZCrD4kLskiee3HGNCZDcCNZLjv/2o5jkWZQ6cvyCVtCrMIckX+3Ysplyd5tb/NY5GIo/e0GWmLaO7bYNmHo2GV60Iu6wDLVXD0B+90cYKd58CZb7T3iDA3m0UtII03S/yr5UFmSd/nCz8nEprygxiKxqtuYO4gQ2t6XyFu2YWXYoeBcN2pyZGdpo4BKwYXnoJ2Tfq5drLxPbv0fwiUKROyEF4cCLTo9iNFfFbO6quGDh4boeGsDvzNFcE+QyOKDEq97pxPjKoJ9QsNCmJ5YF+e1V6aOMHCxSZEknHK0E85nU6dFSVJKVgUjHCbTvbsOz/X02e1Htbpgxbka0hdXJIpGiQr4aOXjirzNsEbPTK26bksC65oHaQ==" > ~/.ssh/known_hosts

VOLUME /data
WORKDIR /work

ENTRYPOINT ["/bin/bash"]
