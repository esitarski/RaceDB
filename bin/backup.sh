#!/usr/bin/env bash

cd ~/Projects/RaceDB

# Make backup and media directories if they don't exist.
mkdir -p backups
mkdir -p media

# Activate RaceDB python environment.
. env/bin/activate

# Get the date once and reuse for all filenames.
date_str=`date +%Y-%m-%d-%H-%M-%S`

fname_data=RaceDB-$date_str.json.gz
echo "Writing data backup:" $fname_data
python3 manage.py dumpdata -e contenttypes -e auth.Permission -o backups/$fname_data

fname_media=RaceDB-$date_str-media.tar.gz
echo "Writing media backup:" $fname_media
tar -czf backups/$fname_media media

echo "Clean up backup files older than 30 days."
find backups/* -mtime +30 -exec rm {} \;
