FROM python:3.10.8

WORKDIR /codegen
RUN git clone https://github.com/OpenNaja/cobra-tools.git && \
    git clone https://github.com/Candoran2/new-pyffi && \
    mv ./new-pyffi/formats/nif ./cobra-tools/source/formats && \
    mv ./new-pyffi/spells ./cobra-tools/source && \
    mv ./new-pyffi/utils ./cobra-tools/utils

WORKDIR cobra-tools
RUN python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install -r requirements.txt

ADD generate.sh .
CMD ["./generate.sh"]
