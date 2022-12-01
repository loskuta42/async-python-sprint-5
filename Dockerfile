FROM python:3.9.7-slim

COPY . /code

WORKDIR /code

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

