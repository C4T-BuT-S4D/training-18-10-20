#!/bin/bash

/tmp/wait-for-it.sh db:5432

cd /var/www/html &&\
php artisan migrate --force &&\
chown -R www-data /storage &&\
php artisan queue:work --sleep=1 --max-jobs=40 &
apache2-foreground
