FROM nginx:latest

ADD nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/www/media /var/www/static && \
    chown -R nginx:nginx /var/www/media /var/www/static
