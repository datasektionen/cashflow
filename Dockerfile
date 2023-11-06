FROM python:3.6-alpine3.15

WORKDIR /app

RUN apk add --no-cache postgresql12-dev postgresql12-plpython3 gcc musl-dev

RUN pip install pipenv==2022.4.8

COPY Pipfile Pipfile.lock .

RUN pipenv install

COPY . .

EXPOSE 8000

CMD sh -c "pipenv run ./manage.py migrate && pipenv run ./manage.py runserver 0.0.0.0:8000"
