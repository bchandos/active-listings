FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV ACTIVE_LISTINGS_ENV=production

RUN useradd -s /bin/bash www

RUN mkdir -p /var/log/uswgi

RUN chown -R www:www /var/log/uwsgi

CMD [ "uwsgi", "/usr/src/app/uwsgi.ini" ]