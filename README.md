# Cashflow 2.0

Django project to manage receipts and reimbursements at Datasektionen.

## Setup

Install the packages in `requirements.txt`. You can then run the django-server with `manage.py runserver`.
Make sure you first set up a database, an S3 bucket and supply the correct environment variables as specified below.

TODO: Make sure the packages are up to date/throw out old stuff

## Run

The following environment variables are required to run the project:

| Variable              | Description                           | Default                       |
|-----------------------|---------------------------------------|-------------------------------|
| DB_URL                | PostgreSQL server url                 | ---                           |
| DEBUG                 | Django debug mode                     | False                         |
| SECRET_KEY            | Django encryption key                 | ---                           |
| LOGIN2_KEY            | Login2 API key for KTH authentication | ---                           |
| S3_BUCKET_NAME        | Amazon AWS s3 bucket name             | ---                           |
| S3_ACCESS_KEY_ID      | Amazon AWS IAM access key id          | ---                           |
| S3_SECRET_ACCESS_KEY  | Amazon AWS IAM secret access key      | ---                           |
| S3_USE_SIGV4          | If Frankfurt, set to False            | True                          |
| S3_HOST               | Url to s3 server                      | s3.eu-central-1.amazonaws.com |
| SPAM_API_KEY          | API key for the spam mail system      | ---                           |
