FROM python:3.7

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app

WORKDIR /app

COPY requiments.txt /app/

RUN pip install -r requiments.txt

COPY . /app/
