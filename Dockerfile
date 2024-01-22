FROM python:3.6.15-alpine

RUN pip install pipenv

RUN apk --no-cache add gcc libc-dev libffi-dev zlib-dev jpeg-dev py3-psycopg2 postgresql14-dev

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pipenv --python 3.6 install

COPY . .

RUN ln -s staticfiles static # It seems like it sometimes only looks in staticfiles/ and other times only in static/

EXPOSE 8000

CMD ["pipenv", "run", "gunicorn", "cashflow.wsgi", "--bind=0.0.0.0:8000", "-t", "600", "--log-file", "-"]
