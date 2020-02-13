#!/bin/bash
# Graceful exit
trap 'exit 0' SIGTERM

if [ $TESTING -eq 1 ]; then
    #
    # Rename this file to zdontstart.sh to prevent container from starting normally
    # This allows changes to be made to made to the container using bash
    echo "Sleeping to prevent container from starting..."
    while [ "1" == "1" ]
    do
        sleep 60
    done
else
    echo "TESTING not set. Exiting normally..."
fi
