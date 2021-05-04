#!/bin/bash
#
# Script to import old version of RaceDB data from Sqlite database
#

SQLITEDATA=/racedb-data/RaceDB.sqlite3
JSONIMPORTDATA=/racedb-data/racedb-import.json

if [ -f $SQLITEDATA ];
then
    export PYTHONPATH=/RaceDB
    export sqlite3_database_fname=$SQLITEDATA
    cd /RaceDB
    python3 ./SqliteToDB.py $SQLITEDATA
    mv $SQLITEDATA ${SQLITEDATA}.bak
    echo "Imported database from $SQLITEDATA file"
else
    echo "No SQLITE data to import from $SQLITEDATA"
fi

if [ -f $JSONIMPORTDATA ];
then
    export PYTHONPATH=/RaceDB
    cd /RaceDB
    #python3 ./manage.py flush 
    python3 ./manage.py loaddata $JSONIMPORTDATA
    mv $JSONIMPORTDATA ${JSONIMPORTDATA}.bak
    echo "Imported database from $JSONIMPORTDATA file"
else
    echo "No JSON data to import from $JSONIMPORTDATA"
fi


