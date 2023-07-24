#!/bin/bash
#
# Initialize or Update the RaceDB Database
# 
# Migrate runs each time in case there is a software update
# initdata only runs once

export PYTHONPATH=/RaceDB
# Make sure the sqlitedb gets started on the data volume in case something screws up
export sqlite3_database_fname=/racedb-data/racedb.db3
chmod 755 /RaceDB/manage.py

# Create the media/uploads directory if it does not already exist.
mkdir -p /RaceDB/media/uploads

racedb=$(psql -U "$DATABASE_NAME" -tAc "select 1 from information_schema.tables WHERE table_name='core_systeminfo'")

if [ "$racedb" != "1" ]; then
    echo "Initializing/Updating RaceDB Database..."
    /RaceDB/manage.py migrate
    /RaceDB/manage.py init_data

    if [ -n "$RACEDBDEMO" ]; then
        /RaceDB/manage.py init_demo
    fi
else
    echo "Database already initialized."
fi
