#!/bin/sh

mkdir -p /var/log/gunicorn
mkdir -p /app/static-files
mkdir -p /app/media-files

python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate

python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME:-admin}"
email = "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
password = "${DJANGO_SUPERUSER_PASSWORD:-admin123}"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
EOF

daphne -b 0.0.0.0 -p 8000 --access-log /var/log/gunicorn/daphne-access.log NessWebServer.asgi:application

exec "$@"
