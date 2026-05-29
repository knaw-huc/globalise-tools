FROM alpine:3.22

RUN apk update &&\
    apk add build-base bash python3 python3-dev linux-headers \
            py3-psutil py3-pip py3-wheel poetry git expect openssh \
            openssh-client sshpass zip curl
RUN adduser -D -s /bin/bash -u 5100 globalise
RUN mkdir -p /work
RUN chown globalise /work

USER globalise
WORKDIR /work

COPY globalise_tools/ /work/globalise_tools/
COPY scripts/ /work/scripts/
COPY remote/ /work/remote/
COPY poetry_scripts.py pyproject.toml README.md /work/
COPY remote/Makefile /work/Makefile
COPY remote/scripts/* /work/scripts/
COPY data/typesystem.xml /work/typesystem.xml
COPY data/document_data.json /work/document_data.json
COPY data/inventory2timespan.json /work/inventory2timespan.json
COPY data/globalise-documents.json /work/data/globalise-documents.json

RUN cd /work && \
    mkdir ~/.ssh && \
    echo "[hucdrive.huc.knaw.nl]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC1sGLWtNSX6xv93Mjk1FDmduItTbcDvPoleba1q8aQawInU1oPIWkUSvnHFV2WzJEWtVleEcYcT16IyRvVMYsLma/lb95+VTXwGO21nzPZBs7fPM7Gs71mlNwNNtUot1E0U9pVM9vfzG4UtDuOY7y6X00fgflLlcRm/0J7IKS5RuR4eVNnX6uxUdsv+b7jDJN6I6i7lJgo3gdx48HGsLYPMB+VqpQRnT4QVkXd9gHyyjHwgrtMw7xPfHckouAmWVitYG+5TASvw2PxtZTRxeOw04qvr0Qpunn3Lq9+R7Y7oBdzJOu7xSGMZX957EE+Nkxrp4olUigfEAHGeCSw1/MDf3/8DX9EWQST0XZ1eidvu1pqIcxzQfid6NgPiwil5oiYr0RQ1iAJ3twtdWdhS/6EMvc9+pZngCNIDUc1ayOxjIOFADDYstEG7vMV1JmvG21nf6nnJYr0ZfIwHm68mPM2hez6Ge9WiUqe5wt1EQ/pH24D3/VxEnfCN1ukclI0pLnw/oCrIywQy5/1suYT/Nozw9v/cBcXwVXwjiGCL3HaxJz4YhXRCdlF/VBdYR7H12LPiQkBE1uSgpJFPbjQ9W9bV/PbiFuX59PxxH7U5oXJzS+gr3pp1CRkC4MxfSueY1r3jLwSjXABgCcRlnKbW2thIRVIw3BYdsutcmidFfktxw==" > ~/.ssh/known_hosts &&\
    poetry install && \
    echo "alias l='ls -lF'" >> ~/.bashrc && \
    echo "alias h='history|grep'" >> ~/.bashrc && \
    echo "echo \"Hello, globalise\"" >> ~/.bash_profile


VOLUME /data

ENTRYPOINT ["/bin/bash"]
