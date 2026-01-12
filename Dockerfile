FROM python:3.14.2-alpine

ENV TZ=Europe/Stockholm

RUN pip install poetry

RUN apk --no-cache add build-base libpq libpq-dev py3-psycopg2 nginx

WORKDIR /app

COPY . .

RUN poetry install

RUN ln -s staticfiles static # It seems like it sometimes only looks in staticfiles/ and other times only in static/

EXPOSE 8000

ENTRYPOINT ["poetry", "run", "gunicorn", "cashflow.wsgi", "--bind=0.0.0.0:8000", "-t", "600", "--log-file", "-"]
