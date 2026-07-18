FROM oven/bun:1-alpine AS bun

WORKDIR /src
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend .
RUN bun run build


FROM python:3.14.3-alpine AS prod


COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun
COPY --from=bun /src/build /app/frontend

ENV TZ=Europe/Stockholm

# The poetry version on APK is outdated and does not work with our lockfile
# => install using pip
RUN apk --no-cache add build-base libpq libpq-dev py3-psycopg2 && \
    pip install --no-cache-dir poetry==2.3.4

# We need supervisor to run both the backend and frontend in the same process
RUN apk --no-cache add supervisor
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisord.conf

WORKDIR /app

COPY backend/pyproject.toml backend/poetry.lock ./

RUN poetry install --no-root

COPY backend .

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "cashflow.wsgi", "--bind=0.0.0.0:8000", "-t", "600", "--log-file", "-"]

FROM prod AS dev

RUN apk --no-cache add nginx
COPY nginx.conf /etc/nginx/nginx.conf

CMD ["sh", "-c", "poetry run ./manage.py migrate && exec supervisord -c /etc/supervisord.conf -n"]
