FROM python:3.7

WORKDIR /root/challengeutils
COPY ./ ./
RUN pip install .
