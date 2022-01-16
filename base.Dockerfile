FROM python:3.10-slim-buster
MAINTAINER Zech Zimmerman "hi@zech.codes"

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean

WORKDIR /usr/src/app

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry run pip install --upgrade pip
RUN poetry install
