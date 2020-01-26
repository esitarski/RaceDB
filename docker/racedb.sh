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
    $DOCKERCMD racedb /RaceDB/manage.py $@
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
    echo "Updating RaceDB and MySQL containers (if available)"
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
    $DOCKERCMD exec racedb python3 /RaceDB/manage.py flush
    $DOCKERCMD exec racedb python3 /RaceDB/manage.py loaddata /racedb-data/${filename}
}

exportdata()
{
    filename=$1
    if [ -z "$filename" ]; then
        DATE=$(date +%Y%m%d-%H%M%S)
        filename="racedb-export-${DATE}.json"
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
    $DOCKERCMD exec racedb python3 /RaceDB/manage.py dumpdata core --indent 2 --output /racedb-data/${filename}
    echo "Export saved to racedb-data/${filename}..."
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
    *) echo "Unknown command."
       usage
       ;;
esac


        
