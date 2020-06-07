FROM python:3.8-slim-buster
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./data ./data
COPY ./icon.png .

COPY ./beginner ./beginner

CMD ["python3", "-u", "-m", "beginner"]
