# Cashflow 2.0
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fdatasektionen%2Fcashflow%2Frefs%2Fheads%2Fmaster%2Fpyproject.toml&style=flat-square&logoSize=auto)

Django project to manage receipts and reimbursements at Datasektionen.

## Developing locally

### Docker
There is a provided Docker compose file; this will run all necessary services for development, including
a PostgreSQL instance, a mock authentication system, an s3 mock as well as a mail system.
> [!NOTE]
> By default, the compose stack will use a Dockerfile meant for development only. This Dockerfile also runs an Nginx server to proxy the mock authentication.

To build and start the application in the background:

```console
$ docker compose up --watch --build
```

The app will now be available on `http://localhost:8000`.
Sent emails will be available on `http://localhost:8080`.

If you make any model changes, you will need to generate new migration files. This is easiest to do outside the docker container, but you can run the command and copy the migrations from the container:

```console
$ docker exec -it cashflow-app-1 poetry run ./manage.py makemigrations
$ docker cp cashflow-app-1:/app/expenses/migrations/ ./expenses/
```

### Poetry

The [psycopg2](https://pypi.org/project/psycopg2/) library requires an external PostgreSQL installation.
Install it using your package manager of choice. You will also need provide the required environment variables, using your method of choice.

Cashflow uses Poetry for dependency management. Depending on your system you can install it globally using
`pip install poetry` or install it using your package manager.


> [!TIP]
> To manage Python several versions, you can use a tool like [pyenv](https://github.com/pyenv/pyenv).
> Poetry will automatically find and use the correct Python version if it is installed.

To install all dependencies, perform the database migration, and run the application:

```console
$ poetry install
$ poetry run ./manage.py migrate
$ poetry run ./manage.py runserver
```

The app will be available on `http://localhost:8000`. The server will restart on file changes.

If you make any model changes, you will need to generate new migration files:

```console
$ poetry run ./manage.py makemigrations
```

You will then need to perform a database migration:
```poetry
$ poetry run ./manage.py migrate
```
## Environment variables

The following environment variables are required to run the project:

| Variable             | Description                          | Default                        |
| -------------------- | ------------------------------------ | ------------------------------ |
| DEBUG                | Django debug mode. Set to True when developing locally. Never set to True in production.                     | False                          |
| DJANGO_LOG_LEVEL     | Which types of logs to get           | INFO                           |
| DATABASE_URL         | PostgreSQL server url                | ---                            |
| SECRET_KEY           | Django encryption key                | ---                            |
| OIDC_PROVIDER        | URL to sso (with /op)                | ---                            |
| OIDC_ID              | ID used when authentication to oidc  | ---                            |
| OIDC_SECRET          | Secret used when authentication to oidc  | ---                            |
| REDIRECT_URL         | Return point after successful login  | ---                            |
| HIVE_URL             | URL to Hive service                  | https://hive.datasektionen.se  |
| HIVE_SECRET          | Hive API Token secret                | ---                            |
| SPAM_URL             | URL to spam service                  | https://spam.datasektionen.se  |
| SPAM_API_KEY         | API key for the spam mail system     | ---                            |
| RFINGER_API_URL      | URL to rfinger api                   | https://rfinger.datasektionen.se |
| RFINGER_API_KEY      | API key for rfinger                  | ---                            |
| S3_ACCESS_KEY_ID     | Amazon AWS IAM access key id         | ---                            |
| S3_SECRET_ACCESS_KEY | Amazon AWS IAM secret access key     | ---                            |
| S3_USE_SIGV4         | If Frankfurt, set to False           | True                           |
| S3_HOST              | Url to s3 server                     | None                           |
| S3_BUCKET_NAME       | Amazon AWS s3 bucket name            | calypso                        |
