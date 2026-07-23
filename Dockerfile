FROM oven/bun:1-alpine AS bun

WORKDIR /src
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend .
RUN bun run build


FROM python:3.14.6-alpine AS base

COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun

ENV TZ=Europe/Stockholm

# The poetry version on APK is outdated and does not work with our lockfile
# => install using pip
RUN apk --no-cache add build-base libpq libpq-dev py3-psycopg2 nginx supervisor && \
    pip install --no-cache-dir poetry==2.3.4 && \
    mkdir -p /var/log/supervisor

WORKDIR /app

COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry install --no-root
COPY backend .

EXPOSE 8000

CMD ["sh", "-c", "poetry run ./manage.py migrate && exec supervisord -c /etc/supervisord.conf -n"]



FROM base AS dev

COPY frontend/package.json frontend/bun.lock /app/frontend/
RUN cd /app/frontend && bun install --frozen-lockfile
COPY frontend /app/frontend

COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.dev.conf /etc/supervisord.conf


FROM base AS prod

COPY --from=bun /src/build /app/frontend

COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisord.conf
