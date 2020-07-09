FROM zzmmrmn/beginner-py-bot-base:20200709
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

RUN mkdir -p /usr/src/app/tmp
ENV TMPDIR /usr/src/app/tmp

COPY ./data ./data
COPY ./icon.png .
COPY ./production.yaml .

COPY ./beginner ./beginner

CMD ["python3", "-u", "-m", "beginner"]
