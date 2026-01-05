FROM python:3.6.15

ENV TZ=Europe/Stockholm

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY . .

RUN ln -s staticfiles static # It seems like it sometimes only looks in staticfiles/ and other times only in static/

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "cashflow.wsgi", "--bind=0.0.0.0:8000", "-t", "600", "--log-file", "-"]
