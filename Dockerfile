FROM python:3.6

WORKDIR /root/challengeutils
COPY ./ ./
RUN pip install .
