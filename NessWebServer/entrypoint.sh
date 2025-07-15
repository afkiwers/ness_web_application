#!/bin/sh

python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate

gunicorn -c gunicorn.conf NessWebServer.wsgi

exec "$@"
