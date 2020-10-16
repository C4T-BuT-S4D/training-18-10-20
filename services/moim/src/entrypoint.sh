#!/bin/bash

/tmp/wait-for-it.sh db:5432

cd /var/www/html &&\
php artisan migrate --force &&\
chown -R www-data /storage &&\
for i in $(seq 1 $QUEUE_WORKERS);
do php artisan queue:work --sleep=1  &
done
apache2-foreground
