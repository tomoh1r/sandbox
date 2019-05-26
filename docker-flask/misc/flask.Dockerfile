#
# flask Dockerfile
#

FROM python:3.7.0-stretch

WORKDIR /usr/src/app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
