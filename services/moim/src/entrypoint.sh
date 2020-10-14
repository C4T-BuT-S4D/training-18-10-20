#!/bin/bash

/tmp/wait-for-it.sh db:5432

cd /var/www/html &&\
php artisan migrate --force &&\
chown -R www-data /storage &&\
apache2-foreground
