FROM python:3.13-alpine3.21
LABEL maintainer="videv1410@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /vol/web/media

RUN adduser \
        --disabled-password \
        --no-create-home \
        django-user

RUN chown -R django-user:django-user /vol/
RUN chmod -R 755 /vol/web/

USER django-user
