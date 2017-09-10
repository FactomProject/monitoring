FROM python:2.7

RUN mkdir -p /srv

RUN mkdir -p /srv
WORKDIR /srv
ENV PYTHONPATH "."

COPY requirements.txt ./requirements.txt

RUN pip --no-cache-dir install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

# If you want debug output
ENV DEBUG 1
CMD ["/usr/local/bin/python", "-u", "/srv/factomd_monitoring_exporter.py"]
