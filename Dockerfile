FROM python:3.7.4
MAINTAINER Zech Zimmerman "hi@zech.codes"
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY beginner/cogs cogs
COPY beginner/beginner.py beginner.py
COPY icon.png icon.png

CMD ["python3", "beginner.py"]
