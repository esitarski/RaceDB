#!/bin/bash
# Graceful exit
trap 'exit 0' SIGTERM

#
# Rename this file to zdontstart.sh to prevent container from starting normally
# This allows changes to be made to made to the container using bash
echo "Sleeping to prevent container from starting..."
while [ "1" == "1" ]
do
    sleep 60
done

