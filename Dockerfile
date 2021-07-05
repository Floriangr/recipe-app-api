FROM python:3.7-alpine
MAINTAINER floriangr

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt
