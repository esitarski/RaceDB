#!/bin/bash

#
# Script to build the release zip

. .wharf
if [ -f RaceBB-Container-Unix.zip ]; then
    rm -f RaceBB-Container-Unix.zip
fi
zip RaceBB-Container-Unix.zip README.md dbconfig.env.tmpl docker-compose*.yml racedb.env racedb.sh
