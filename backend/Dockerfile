FROM python:3.14.3-alpine AS prod

ENV TZ=Europe/Stockholm

# The poetry version on APK is outdated and does not work with our lockfile
# => install using pip
RUN apk --no-cache add build-base libpq libpq-dev py3-psycopg2 && \
    pip install --no-cache-dir poetry==2.3.4

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "cashflow.wsgi", "--bind=0.0.0.0:8000", "-t", "600", "--log-file", "-"]

FROM prod AS dev

RUN apk --no-cache add nginx
