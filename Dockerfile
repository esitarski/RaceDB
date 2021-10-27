FROM python:3.9-buster

RUN apt-get update \
  && apt-get install -y \
    vim.tiny \
    postgresql-client
# Add this back in when we figure out how to use host networking
#    avahi-daemon \

ENV sqlite3_database_fname=/racedb-data/RaceDB.sqlite3
ENV RACEDBLOGFILE=/racedb-data/RaceDB-log.txt
ENV TIME_ZONE=America/Toronto
ENV DATABASE_TYPE=psql-local
ENV POSTGRES_USER=postgres
ENV DATABASE_NAME=racedb
ENV DATABASE_USER=racedb
ENV TESTING=0

# Set out hostname for avahi
RUN echo "racedb.local" > /etc/hostname && \
    mkdir -p /RaceDB && \
    mkdir -p /docker-entrypoint-init.d/ && \
    useradd -m -s /bin/bash postgres && \
    useradd -m -s /bin/bash racedb

# Copy in our source code
COPY . /RaceDB/
WORKDIR /RaceDB

# We are left in the /RaceDB at this point by WORKDIR. Setup RaceDB
RUN rm -rf Dockerfile release test_data migrations_old env docker .git .vscode core/__pycache__  RaceDB/__pycache__ __pycache__ helptxt/__pycache__ .git* .dockerdef && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt && \
    python3 -m pip install PyMySQL mysqlclient psycopg2 && \
    cd helptxt && \
    python3 compile.py && \
    cd /RaceDB && \
    chmod 755 manage.py && \
    ./manage.py collectstatic -v 2 -c --no-input && \
    chown -R racedb.racedb /RaceDB/

ENV PYTHONPATH=/RaceDB
WORKDIR /

COPY docker/docker-entrypoint-init.d/* /docker-entrypoint-init.d/
COPY docker/build-files/entrypoint.sh /usr/sbin/entrypoint.sh

VOLUME [ "/racedb_data" ]
EXPOSE 8000

CMD ["/usr/sbin/entrypoint.sh"]
