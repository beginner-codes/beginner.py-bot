FROM python:3.8-slim-buster
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt