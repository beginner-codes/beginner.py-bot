FROM zzmmrmn/beginner-py-bot-base:20200614
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

COPY ./data ./data
COPY ./icon.png .

COPY ./beginner ./beginner

CMD ["python3", "-u", "-m", "beginner"]
