FROM python:3.8.0
MAINTAINER Zech Zimmerman "hi@zech.codes"

WORKDIR /usr/src/app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./beginner ./beginner
COPY ./icon.png .

CMD ["python3", "-u", "-m", "beginner"]
