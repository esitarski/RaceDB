#!/bin/bash
#set -x

COMPOSEFILE=docker-compose.yml
DOCKERCMD="docker-compose -f $COMPOSEFILE"

checkconfig() {
    if [ ! -f $COMPOSEFILE ]; then
        echo "Please run this command from the same directory as the $COMPOSEFILE"
        exit 1
    fi
}

restart() {
    stop
    sleep 2
    run
}

run() {
    checkconfig
    echo "Starting RaceDB Container set..."
    $DOCKERCMD up -d
}

logs() {
    checkconfig
    $DOCKERCMD logs
}

flogs() {
    checkconfig
    $DOCKERCMD logs -f
}

bash() {
    checkconfig
    echo "You are now running commands inside the racedb container"
    echo
    $DOCKERCMD exec racedb /bin/bash
}

manage() {
    checkconfig
    $DOCKERCMD exec racedb /RaceDB/manage.py $@
}

stop() {
    echo "Stopping RaceDB Container set..."
    $DOCKERCMD stop
}

ps() {
    $DOCKERCMD ps
}

update() {
    stop
    echo "Updating RaceDB and PostgreSQL containers (if available)"
    $DOCKERCMD pull
}

build() {
    if [ ! -f "$COMPOSEFILE" ]; then
        echo "ERROR: Command must be run from same directory as the $COMPOSEFILE file."
        exit 1
    fi
    . .dockerdef
    docker build -t $IMAGE:$TAG .
}

rebuild() {
    if [ ! -f "$COMPOSEFILE" ]; then
        echo "ERROR: Command must be run from same directory as the $COMPOSEFILE file."
        exit 1
    fi
    . .dockerdef
    docker build -t $IMAGE:$TAG --no-cache .
}

cleanall() {
    if [ ! -f "$COMPOSEFILE" ]; then
        echo "ERROR: Command must be run from same directory as the $COMPOSEFILE file."
        exit 1
    fi
    echo -n "About to wipe all the RaceDB data and configuration!! Are you sure? THIS CANNOT BE UNDONE! (type YES): "
    read ENTRY
    if [ "$ENTRY" = "YES" ]; then
        stop
        
        RACEDBCONTAINERS=$(docker container list -a | grep racedb_app | awk '{ print $1 }')
        for container in $RACEDBCONTAINERS
        do
            echo "Removing container: $container"
            docker container rm -f $container
        done

        RACEDBIMAGES=$(docker image list | grep racedb | awk '{print $3}')
        for image in $RACEDBIMAGES
        do
            echo "Removing image: $image"
            docker image rm -f $image
        done

        VOLUMES=$(docker volume list | grep racedb | awk '{print $2}')
        for volume in $VOLUMES
        do
            echo "Removing RaceDB volume: $volume"
            docker volume rm $volume
        done

        NETWORKS=$(docker network list | grep racedb | awk '{print $2}')
        for network in $NETWORKS
        do
            echo "Removing RaceDB network: $network"
            docker network rm $network
        done

        if [ -f RaceDB.sqlite3 ]; then
            echo "Removed old RaceDB.sqlite3"
            rm -f RaceDB.sqlite3
        fi
    else
        echo "Clean cancelled"
    fi
}

importdata()
{
    filename=$1
    if [ ! -f "$COMPOSEFILE" ]; then
        echo "ERROR: Command must be run from same directory as the $COMPOSEFILE file."
        exit 1
    fi
    if [ !  -f "racedb-data/${filename}" ];then
        echo "racedb-data/${filename} does not exist"
        exit 1
    fi
    echo "Importing racedb-data/${filename}..."
    $DOCKERCMD exec racedb python3 /RaceDB/manage.py backup_restore /racedb-data/${filename}
}

exportdata()
{
    filename=$1
    if [ -z "$filename" ]; then
        DATE=$(date +%Y%m%d-%H%M%S)
        filename="racedb-export-${DATE}.json.gz"
    fi
    if [ ! -f "$COMPOSEFILE" ]; then
        echo "ERROR: Command must be run from same directory as the $COMPOSEFILE file."
        exit 1
    fi
    if [ -f "racedb-data/${filename}" ];then
        echo "racedb-data/${filename} already exists. Aborting..."
        exit 1
    fi
    echo "Exporting to racedb-data/${filename}..."
    $DOCKERCMD exec racedb python3 /RaceDB/manage.py backup_create /racedb-data/${filename}
    echo "Export saved to racedb-data/${filename}..."
}

reader() {
    READER=$1
    if [ -z "$READER" ]; then
        echo "You must specify the reader name or ip"
        exit 1
    fi
    if (echo "$READER" | grep -Eq "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"); then
        READER_IP=$READER
    elif (echo "$READER" | grep -Eq ".*\.local$"); then
        if [ "$(uname -s)" == "Darwin" ]; then
            READER_IP=$(ping -c 1 "$READER" | grep from | awk '{print $4}' | awk -F':' '{print $1}')
        else
            READER_IP=$(avahi-resolve -n "$READER" | awk '{print $2}')
        fi
    else
        READER_IP=$(host $READER | awk '{print $4}')
        if [ "$READER_IP" == "found:" ]; then
            echo "READER ip not found"
            exit 1
        fi
    fi
    if [ -z "$READER_IP" ];then
        echo "Error finding reader IP"
        exit 1
    fi
    echo "Reader IP is $READER_IP"
    grep -v RFID_READER_HOST racedb.env > racedb.env.tmp.$$
    echo "RFID_READER_HOST=$READER_IP" >> racedb.env.tmp.$$
    cp racedb.env racedb.env.bak
    mv racedb.env.tmp.$$ racedb.env
    echo "racedb.env updated"
}

usage() {
    echo "Commands:"
    echo "run - start the racedb container"
    echo "stop - stop the racedb container"
    echo "restart - stop and restart the racedb container"
    echo "bash - run bash shell in running container"
    echo "ps   - list running containers"
    echo "manage - run manage.py in running container (passes additional args to manage)"
    echo "logs - show the racedb container log"
    echo "flogs - show the racedb container log and display continuously"
    echo "export {filename} - export database to racedb-data/{filename} (filename is optional)"
    echo "import {filename} - database database from racedb-data/{filename}"
    echo "reader {ip or name} - updates racedb.env with the reader ip" 
    echo
    echo "Use a webbrowser to login to RaceDB: http://localhost"
    echo 
}
CMD=$1
shift
case $CMD in
    "dbconfig") checkconfig
        ;;
    "run" | "start") run
        ;;
    "restart") restart
        ;;
    "bash") bash
        ;;
    "update") update
        ;;
    "logs" | "log") logs
        ;;
    "flogs" | "flog") flogs
        ;;
    "stop") stop
        ;;
    "ps") ps
        ;;
    "manage") manage $@
        ;;
    "import") importdata $@
        ;;
    "export") exportdata $@
        ;;
    "clean") cleanall
        ;;
    "build") build
        ;;
    "rebuild") build
        ;;
    "reader") reader $@
        ;;
    *) echo "Unknown command."
       usage
       ;;
esac


        
