# GitHub Setup for Builds

Github workflows are incorporated into the build system for RaceDB. The build runs the compile.sh on Linux to create the zip/tar for the racedb code (distributable) and builds the docker container.

All development work is done on the dev branch. Large changes should be incorporated into a feature branch and merged back into dev. The master branch is reserved for releases. Checkins to the dev branch cause an automatic build into the a Developemnt Release on the development tag. The build automatically generates the tag and replaces the contents of the previous build each time so that there is only one development build. To make a release, one must be on the dev branch and run the "bash compile.sh -r" command. For windows, the build workflow generates the docker container zip only. Actually building the code is only supported on Mac and Linux systems (or Windows System for Linux on Windows).

## Docker Hub

To use the workflow system requires a Docker Hub account. This involves creating a hub account and a project for the racedb container.

To create the project on Docker Hub:
-	Go to hub.docker.com and create an account if you haven’t already
-	Go to https://hub.docker.com/repository/create and create a project called “racedb”
   -	Name: racedb
   - 	Description: RaceDB container (or whatever)
   -	Type: public

The setup above will allow my GitHub to push container to your docker project. The next step is to modify the .dockerdef file.

There are two types of containers:
- beta - built from the development tag
- latest - built from the master branch.

The tar/zip for the container automatically updates the docker-compose.yml file as part of the build process.

## .dockerdef File

The .dockerdef file gives the tag name and version to the container. By default, it is set to the maintainer of RaceDB. For your own personal build, you must edit the .dockerdef file and change the maintainer's tag to your own.

For example:
export IMAGE="mbuckaway/racedb"
export TAG="v3.0.31-private"

mbuckaway is the username on Docker Hub and racedb is the name of the container.

## Secrets

In order to publish to Docker Hub, the workflow must know your username and password on Docker Hub. These are not stored in the workflow file for security reasons. You must create a set of secrets in github for the workflow to reference.

To do so, do the following:

- head over to https://github.com/username/RaceDB/settings/secrets where username is your github username. This is the settings page for your racedb repo.
- add two new settings:
   - HUB_USER - set to your username on Docker Hub
   - HUB_PASSWD - set to your password on Docker Hub

Your password is encrypted and stored in github. It is accessible from the workflow from the {{ secret.HUB_PASSWD }} variable.

## Done!

With the above, you are done and automatic builds will occur on your repo. Check the releases tab on your repo to see the releases. Check Docker Hub for your container builds.

