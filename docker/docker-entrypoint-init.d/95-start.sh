#!/bin/bash
#
# Start up RaceDB
#
export sqlite3_database_fname=/racedb-data/racedb.db3
export PYTHONPATH=/RaceDB
export RACEDBLOGFILE=/racedb-data/RaceDB-log.txt

# Graceful exit
trap 'echo "Shutdown called"; exit 0' SIGTERM

cd /RaceDB
ARGS=""
if [ -n "$RFID_READER_HOST" ];then
    ARGS="--rfid_reader --rfid_reader_host $RFID_READER_HOST"
fi
if [ -n "$RFID_TRANSMIT_POWER" ];then
    ARGS="$ARGS --rfid_transmit_power $RFID_TRANSMIT_POWER"
fi
if [ -n "$USE_HUB" ];then
    ARGS="$ARGS --hub"
fi
if [ -n "$LLRP_SERVER_HOST" ];then
    ARGS="$ARGS --host $LLRP_SERVER_HOST"
fi

if [ -n "$ARGS" ]; then
    echo "Starting RaceDB with args:"
    echo "Args: $ARGS"
fi

# Try to start it forever in case there is a database issue
while true
do
    /RaceDB/manage.py launch --no_browser $ARGS
    if [ $? -eq 0 ]; then
        if [ -f /.dontstart ]; then
            echo "Skipping restart..."
            exit
        fi
        break
    fi
    echo "Unable to Start RaceDB. Pausing..."
    sleep 10
done

