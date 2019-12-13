FROM python:3.8.0
MAINTAINER Zech Zimmerman "hi@zech.codes"
WORKDIR /usr/src/app

COPY zechcodes/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY zechcodes/zechcodes zechcodes

CMD ["hypercorn", "--bind", "0.0.0.0:8080", "--workers", "8", "zechcodes.app:app"]
