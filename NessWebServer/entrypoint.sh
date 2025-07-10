#!/bin/sh

# Last changed 04/04/2020
# Andre F. K. Iwers

python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate

gunicorn -c gunicorn.conf NessWebServer.wsgi

exec "$@"
