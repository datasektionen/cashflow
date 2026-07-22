#!/bin/sh

poetry run ./manage.py migrate
poetry run gunicorn cashflow.wsgi --bind=0.0.0.0:$PORT -t 600 --log-file - &

nginx -g 'daemon off;' &

wait -n
exit $?

# This scripts starts both python and nginx. If one exits, it kills the other
# one and exits, stopping the container (which could then be restarted)
