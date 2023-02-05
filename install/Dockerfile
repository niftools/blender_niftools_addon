FROM python:3.10.8

ARG cobra_commit=117d0983848468747dd3c7ab0699b230347b1db5
ARG pyffi_commit=4b18387137a4e73386f020fff66d033354ab2186
ARG nifxml_commit=89d03ffe69254ef4b3b58b0a22ec2ff9820b2e63

WORKDIR /codegen
RUN git clone https://github.com/OpenNaja/cobra-tools.git && cd cobra-tools && git reset --hard $cobra_commit && cd .. && \
    git clone https://github.com/Candoran2/new-pyffi && cd new-pyffi && git reset --hard $pyffi_commit && cd .. && \
    mv ./new-pyffi/formats/nif ./cobra-tools/source/formats && \
    mv ./new-pyffi/spells ./cobra-tools/source && \
    mv ./new-pyffi/utils ./cobra-tools/utils && \
    git clone https://github.com/niftools/nifxml.git && cd nifxml && git reset --hard $nifxml_commit && cd .. && \
    mv ./nifxml/nif.xml ./cobra-tools/source/formats/nif

WORKDIR cobra-tools
RUN python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install -r requirements.txt

ADD generate.sh .
CMD ["./generate.sh"]
