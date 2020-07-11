FROM python:3.8-slim-buster
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

RUN mkdir -p /usr/src/app/tmp
ENV TMPDIR /usr/src/app/tmp

COPY ./data ./data
COPY ./production.yaml .

COPY ./beginner ./beginner

CMD ["poetry", "run", "python", "-u", "-m", "beginner"]
