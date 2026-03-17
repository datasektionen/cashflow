FROM python:3.14.3-alpine AS prod

ENV TZ=Europe/Stockholm

RUN apk --no-cache add build-base libpq libpq-dev py3-psycopg2 poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

RUN ln -s staticfiles static # It seems like it sometimes only looks in staticfiles/ and other times only in static/

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "cashflow.wsgi", "--bind=0.0.0.0:8000", "-t", "600", "--log-file", "-"]

FROM prod AS dev

RUN apk --no-cache add nginx
