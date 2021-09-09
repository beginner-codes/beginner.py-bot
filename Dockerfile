FROM zzmmrmn/beginner-py-bot-base:20210902.1
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

RUN mkdir -p /usr/src/app/tmp
ENV TMPDIR /usr/src/app/tmp

COPY ./data ./data
COPY ./production.yaml .

COPY ./beginner ./beginner

CMD ["poetry", "run", "python", "-u", "-m", "beginner"]
