#!/bin/bash
#set -x

build() {
    if [ ! -f ".dockerdef" ]; then
        echo "ERROR: Command must be run from same directory as the .dockerdef file."
        exit 1
    fi
    . .dockerdef
    if [ "$TAG" == "beta" ]; then
      docker build -t $IMAGE:$TAG -f Dockerfile.beta .
    else
      docker build -t $IMAGE:$TAG .
    fi
}

rebuild() {
    if [ ! -f ".dockerdef" ]; then
        echo "ERROR: Command must be run from same directory as the $.dockerdef file."
        exit 1
    fi
    . .dockerdef

    if [ "$TAG" == "beta" ]; then
      docker build -t $IMAGE:$TAG -f Dockerfile.beta --no-cache .
    else
      docker build -t $IMAGE:$TAG --no-cache .
    fi
}

cleanall() {
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

        RACEDBIMAGES=$(docker image list | grep racedb-mysql | awk '{print $3}')
        for image in $RACEDBIMAGES
        do
            echo "Removing image: $image"
            docker image rm -f $image
        done

        VOLUMES=$(docker volume list | grep racedb-container | awk '{print $2}')
        for volume in $VOLUMES
        do
            echo "Removing RaceDB volume: $volume"
            docker volume rm $volume
        done

        if [ -f RaceDB.sqlite3 ]; then
            echo "Removed old RaceDB.sqlite3"
            rm -f RaceDB.sqlite3
        fi
    else
        echo "Clean cancelled"
    fi
}

usage() {
    echo "Commands:"
    echo "build - build the racedb container"
    echo "rebuild - build the racedb container and ignore the local cache"
    echo "clean - trash all racedb containers and volumes (DESTRUCTIVE)"
}
CMD=$1
case $CMD in
    "clean") cleanall
        ;;
    "build") build
        ;;
    "rebuild") build
        ;;
    "help") usage
        ;;
    *) build
       ;;
esac


        
