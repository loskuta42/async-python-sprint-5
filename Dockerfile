FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

COPY ./migrations /code/migrations

COPY ./alembic.ini /code/alembic.ini

COPY ./.env /code/.env

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src