FROM php:7.3-apache

RUN apt update && apt install -y git zip unzip libpq-dev \
    build-essential chrpath libssl-dev libxft-dev \
    && docker-php-ext-install -j$(nproc) pgsql \
    && docker-php-ext-install -j$(nproc) pdo_pgsql

# Runtime dependencies
RUN apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        bzip2 \
        libfontconfig \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV OPENSSL_CONF=/opt/openssl.cnf

RUN a2enmod rewrite

COPY composer.json /var/www/html
COPY composer.lock /var/www/html

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
COPY --from=wernight/phantomjs:latest /usr/local/bin/phantomjs /usr/bin/phantomjs

WORKDIR /var/www/html

RUN composer global require hirak/prestissimo

RUN composer install

COPY --chown=www-data:www-data . /var/www/html/

RUN chown -R www-data /var/www/html

ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

RUN echo "TOKEN_KEY=$(head -c 25 /dev/urandom | base64)" >> /var/www/html/.env

COPY entrypoint.sh /tmp/run.sh
COPY wait-for-it.sh /tmp/wait-for-it.sh

ENTRYPOINT ["/tmp/run.sh"]


