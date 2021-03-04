FROM python:3.8

WORKDIR /root/challengeutils
COPY ./ ./
RUN pip install .
