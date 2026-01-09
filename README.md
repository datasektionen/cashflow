# Cashflow 2.0
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fdatasektionen%2Fcashflow%2Frefs%2Fheads%2Fmaster%2Fpyproject.toml&style=flat-square&logoSize=auto)

Django project to manage receipts and reimbursements at Datasektionen.

## Developing locally

### Docker (recommended)
There is a provided Docker compose file; this will run all necessary services for development, including
a PostgreSQL instance and a mock authentication system.
To build and start all services to run in the background:

```console
$ docker compose up --watch --build -d
```

The app will now be available on `http://localhost:8000`.


### Poetry

The [psycopg2](https://pypi.org/project/psycopg2/) library requires an external PostgreSQL installation.
Install it using your package manager of choice. You will also need to create a `.env` file with the required environment variables (see below).

Cashflow has moved from Pipenv to Poetry for dependency management. Depending on your system you can: install it globally using
`pip install poetry` or install it using your package manager.

To setup and run the application:

```console
$ poetry install
$ poetry run ./manage.py migrate
$ poetry run ./manage.py runserver
```

The app will be available on `http://localhost:8000`. The server will restart on file changes.

### Getting data from production

1. Get a database dump: `ssh hermes dokku postgres:export cashflow > cashflow.sql`
2. Shove it into a local database: `pg_restore -h localhost -U cashflow -d cashflow --no-owner < cashflow.sql`
3. Copy files from s3 to local: `aws s3 cp --recursive s3://dsekt-cashflow-2/media/ media/` (warning: you need a fair bit of free disk space for this. todo: how does one easily download only new files?)

## Environment variables

The following environment variables are required to run the project:

| Variable             | Description                          | Default                        |
| -------------------- | ------------------------------------ | ------------------------------ |
| DATABASE_URL         | PostgreSQL server url                | ---                            |
| DEBUG                | Django debug mode. Set to True when developing locally. Never set to True in production.                     | False                          |
| SECRET_KEY           | Django encryption key                | ---                            |
| LOGIN_KEY            | Login API key for KTH authentication | ---                            |
| HIVE_SECRET          | Hive API Token secret                | ---                            |
| S3_BUCKET_NAME       | Amazon AWS s3 bucket name            | ---                            |
| S3_ACCESS_KEY_ID     | Amazon AWS IAM access key id         | ---                            |
| S3_SECRET_ACCESS_KEY | Amazon AWS IAM secret access key     | ---                            |
| S3_USE_SIGV4         | If Frankfurt, set to False           | True                           |
| S3_HOST              | Url to s3 server                     | s3.eu-central-1.amazonaws.com  |
| SPAM_API_KEY         | API key for the spam mail system     | ---                            |
| SPAM_URL             | URL to spam service                  | https://spam.datasektionen.se  |
| HIVE_URL             | URL to Hive service                  | https://hive.datasektionen.se  |
| LOGIN_API_URL        | URL to login service api             | https://login.datasektionen.se |
| LOGIN_FRONTEND_URL   | URL to login service frontend        | https://login.datasektionen.se |
| SEND_EMAILS          | If False, does not send emails       | True                           |
| RFINGER_API_URL      | URL to rfinger api                   | https://rfinger.datasektionen.se |
| RFINGER_API_KEY      | API key for rfinger                  | ---                            |

(The variables beginning with `S3` are not used if `DEBUG` is true. Files are
instead stored at `./media/`)

They can be put in an .env-file in root. They will be loaded automatically by `pipenv`.

Check out [.env.example](.env.example) for an example.

## Protip
The default max upload size in nginx is 1 MB. To allow larger file uploads, set the max size of file uploads to for example 100 MB.

```bash
echo "client_max_body_size 100M;" > /home/dokku/cashflow/nginx.conf.d/max_size.conf
```
