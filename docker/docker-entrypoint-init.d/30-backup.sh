#!/bin/bash
#
# Script to import old version of RaceDB data from Sqlite database
#

NOBACKUP=/racedb-data/.nobackup
DATE=`date +%Y%m%d-%H%M%S`
BACKUPDIR=/racedb-data/backups
JSONEXPORTDATA="${BACKUPDIR}/racedb-backup-${DATE}.json"

if [ ! -f $NOBACKUP ];
then
    if [ ! -d $BACKUPDIR ]; then
        mkdir -p $BACKUPDIR
    fi
    echo "Backing up database to "
    export PYTHONPATH=/RaceDB
    cd /RaceDB
    python3 ./manage.py dumpdata core --indent 2 --output $JSONEXPORTDATA
else
    echo "============================="
    echo "Backups currently turned off!"
    echo "============================="
fi


