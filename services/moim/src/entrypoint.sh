#!/bin/bash

/tmp/wait-for-it.sh db:5432 &&\
cd /var/www/html &&\
php artisan migrate --force &&\
mkdir -p /storage/tickets &&\
mkdir -p /storage/templates &&\
chmod 777 /storage/tickets /storage/templates &&\
chown -R www-data /storage &&\
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
