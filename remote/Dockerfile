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
    echo "[hucdrive.huc.knaw.nl]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC1sGLWtNSX6xv93Mjk1FDmduItTbcDvPoleba1q8aQawInU1oPIWkUSvnHFV2WzJEWtVleEcYcT16IyRvVMYsLma/lb95+VTXwGO21nzPZBs7fPM7Gs71mlNwNNtUot1E0U9pVM9vfzG4UtDuOY7y6X00fgflLlcRm/0J7IKS5RuR4eVNnX6uxUdsv+b7jDJN6I6i7lJgo3gdx48HGsLYPMB+VqpQRnT4QVkXd9gHyyjHwgrtMw7xPfHckouAmWVitYG+5TASvw2PxtZTRxeOw04qvr0Qpunn3Lq9+R7Y7oBdzJOu7xSGMZX957EE+Nkxrp4olUigfEAHGeCSw1/MDf3/8DX9EWQST0XZ1eidvu1pqIcxzQfid6NgPiwil5oiYr0RQ1iAJ3twtdWdhS/6EMvc9+pZngCNIDUc1ayOxjIOFADDYstEG7vMV1JmvG21nf6nnJYr0ZfIwHm68mPM2hez6Ge9WiUqe5wt1EQ/pH24D3/VxEnfCN1ukclI0pLnw/oCrIywQy5/1suYT/Nozw9v/cBcXwVXwjiGCL3HaxJz4YhXRCdlF/VBdYR7H12LPiQkBE1uSgpJFPbjQ9W9bV/PbiFuX59PxxH7U5oXJzS+gr3pp1CRkC4MxfSueY1r3jLwSjXABgCcRlnKbW2thIRVIw3BYdsutcmidFfktxw==" > ~/.ssh/known_hosts

VOLUME /data
WORKDIR /work

ENTRYPOINT ["/bin/bash"]
