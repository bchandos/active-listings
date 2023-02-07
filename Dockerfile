FROM python:3

WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uwsgi", "/usr/src/app/uwsgi.ini" ]