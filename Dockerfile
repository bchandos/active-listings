FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV ACTIVE_LISTINGS_ENV=production

RUN useradd -s /bin/bash www

CMD [ "uwsgi", "/usr/src/app/uwsgi.ini" ]