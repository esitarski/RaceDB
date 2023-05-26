#!/usr/bin/env bash

if [$# -ne 1]; then
	echo "restore.sh <django-data-file.json.gz>"
	exit -1
fi

fname=$1

if [ ! -f "$fname" ]; then
	echo "restore file does not exist:" "$fname"
	exit -1
fi

cd ~/Projects/RaceDB

# Activate RaceDB python environment.
. env/bin/activate

python3 manage.py reset_db
python3 manage.py loaddata "$fname"
