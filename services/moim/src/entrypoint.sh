#!/bin/bash

/tmp/wait-for-it.sh db:5432

cd /var/www/html
php artisan migrate
apache2-foreground
