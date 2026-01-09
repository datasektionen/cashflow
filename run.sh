#!/bin/sh

poetry run ./manage.py migrate
poetry run gunicorn cashflow.wsgi --bind=0.0.0.0:8000 -t 600 --log-file - &

# nginx -g 'daemon off;' &
#
wait
exit $?

# This scripts starts both python and nginx. If one exits, it kills the other
# one and exits, stopping the container (which could then be restarted)
