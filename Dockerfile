FROM python:2.7

MAINTAINER Erik Ljungstrom

RUN apt-get update -y && \
    apt-get install -y libmemcached-dev supervisor && \
    rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /requirements.txt

RUN pip install -r requirements.txt

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
