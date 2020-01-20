#!/bin/bash
#
# Configure RaceDB

DBCONFIG=/RaceDB/RaceDB/DatabaseConfig.py
TZCONFIG=/RaceDB/RaceDB/time_zone.py
DBCONFIGURED=/.db-configured

create_dbconf()
{
        cat > $DBCONFIG <<EOF
DatabaseConfig = {
        'ENGINE': '$DATABASE_ENGINE',
        'NAME': '$DATABASE_NAME',
EOF
    if [ "$DATABASE_TYPE" != "sqlite" ]; then
        if [ $DATABASE_PORT -eq 0 ]; then
            cat >> $DBCONFIG <<EOF2
        'USER': '$DATABASE_USER',
        'HOST': '$DATABASE_HOST',
EOF2
        else
            cat >> $DBCONFIG <<EOF3
        'USER': '$DATABASE_USER',
        'HOST': '$DATABASE_HOST',
        'PASSWORD': '$DATABASE_PASSWORD',
        'PORT': '$DATABASE_PORT',
EOF3
        fi
    fi
    echo '}'  >> $DBCONFIG
}

configure_database()
{
    if [ -z "$DATABASE_TYPE" ]; then
        DATABASE_TYPE=psql-local
    fi
    # Set some defaults
    if [ -z "$DATABASE_HOST" ]; then
        DATABASE_HOST=db
    fi
    if [ -z "$DATABASE_USER" ]; then
        DATABASE_USER=racedb
    fi
    if [ -z "$DATABASE_NAME" ]; then
        DATABASE_NAME=racedb
    fi

    case "$DATABASE_TYPE" in 
        mysql) DATABASE_ENGINE="django.db.backends.mysql"
            DATABASE_PORT="3306"
            echo "Configuring RaceDB for mysql"
            create_dbconf
            ;;
        mysql-local) DATABASE_ENGINE="django.db.backends.mysql"
            DATABASE_PORT="0"
            DATABASE_HOST="/var/run/mysqld/mysqld.sock"
            echo "Configuring RaceDB for mysql-local"
            create_dbconf
            ;;
        psql) DATABASE_ENGINE="django.db.backends.postgresql"
            DATABASE_PORT="5432"
            echo "Configuring RaceDB for psql"
            create_dbconf
            ;;
        psql-local) DATABASE_ENGINE="django.db.backends.postgresql"
            DATABASE_HOST="/var/run/postgresql"
            DATABASE_PORT="0"
            echo "Configuring RaceDB for psql-local"
            create_dbconf
            ;;
        sqlite) DATABASE_ENGINE="django.db.backends.sqlite3"
            DATABASE_NAME="/racedb-data/RaceDB.sqlite3"
            echo "Configuring RaceDB for SQLite"
            create_dbconf
            ;;
        *)
            echo "Unknown database selected. RaceDB will default to Sqlite!"
            ;;
    esac

    echo "TIME_ZONE=\"$TIME_ZONE\"" > $TZCONFIG
    echo "Configured!"
    touch $DBCONFIGURED
}

if [ -f $DBCONFIGURED ]; then
    echo "Database already configured."
else
    configure_database
fi
