FROM python:3.7

WORKDIR /usr/app

ADD ./requirements.txt ./

RUN pip install -r requirements.txt

COPY ./ ./

ENV FLASK_APP=run

ENV FLASK_PORT=5000

CMD flask run --host 0.0.0.0
