#!/bin/bash

OSNAME=$(uname -s)
PYTHONVER=python3.8
ENVDIR=env
if [ "$OSNAME" == "Darwin" ]; then
	PYTHONVER="python3.8"
fi
if [ "$OSNAME" == "Linux" ]; then
	PYTHONVER="python3.8"
fi

checkEnvActive() {
	if [ -z "$VIRTUAL_ENV" -a -d $ENVDIR ]; then
        . $ENVDIR/bin/activate
        echo "Virtual env ($VIRTUAL_ENV) activated"
    elif [ -n "$VIRTUAL_ENV" ]; then
        echo "Using existing environment ($VIRTUAL_ENV)"
    else
        echo "Python environment not active. Aborting..."
        exit 1
    fi
}

getVersion() {
	if [ ! -f "helptxt/version.py" ]; then
		echo "No version file in helptxt/version.py. Aborting..."
		exit 1
	fi
	. helptxt/version.py
	VERSION=$version
	export VERSION
}

cleanup() {
	echo "Cleaning up everything..."
	rm -rf __pycache__
	rm -rf release
}

compileCode() {
    checkEnvActive
	echo "Compiling code"
	python3 -mcompileall -l . core RaceDB
	if [ $? -ne 0 ];then
		echo "Compile failed. Aborting..."
		exit 1
	fi
}

packagecode()
{
    checkEnvActive
    python3 package.py -a -d release
    if [ $? -ne 0 ]; then
        echo "Packaging failed"
        exit 1
    fi
}

envSetup() {
	if [ ! -f requirements.txt ]; then
		echo "Script must be run in same main directory with requirements.txt. Aborting..."
		exit 1
	fi
	if [ -z "$VIRTUAL_ENV" ]; then
		if [ -d $ENVDIR ]; then
			echo "Activating virtual env ($ENVDIR) ..."
			. env/bin/activate
		else
			echo "Creating virtual env in $ENVDIR..."
			$PYTHONVER -mpip install virtualenv
            if [ $? -ne 0 ];then
                echo "Virtual env setup failed. Aborting..."
                exit 1
            fi
			$PYTHONVER -mvirtualenv $ENVDIR -p $PYTHONVER
            if [ $? -ne 0 ];then
                echo "Virtual env setup failed. Aborting..."
                exit 1
            fi
			. env/bin/activate
		fi
	else
		echo "Already using $VIRTUAL_ENV"
	fi
	pip3 install -r requirements.txt
    if [ $? -ne 0 ];then
        echo "Pip requirememnts install failed. Aborting..."
        exit 1
    fi
}

updateversion() {
	if [ -n "$GITHUB_REF" ]; then
		echo "GITHUB_REF=$GITHUB_REF"
        getVersion
        # development build
        GIT_TYPE=$(echo $GITHUB_REF | awk -F '/' '{print $2'})
        GIT_TAG=$(echo $GITHUB_REF | awk -F '/' '{print $3'})
        SHORTSHA=$(echo $GITHUB_SHA | cut -c 1-7)
        VERSION=$(echo $VERSION | awk -F - '{print $1}')
        if [ "$GIT_TYPE" == "heads" -a "$GIT_TAG" == "master" ]; then
            echo "Refusing to build an untagged master build. Release builds on a tag only!"
            exit 1
        fi
        if [ "$GIT_TYPE" == "heads" -a "$GIT_TAG" == "dev" ]; then
            APPVERNAME="version=\"$VERSION-beta-$SHORTSHA\""
            VERSION="$VERSION-beta-$SHORTSHA"
        fi
        if [ "$GIT_TYPE" == "tags" ]; then
            VERNO=$(echo $GIT_TAG | awk -F '-' '{print $1}')
            REFDATE=$(echo $GIT_TAG | awk -F '-' '{print $2}')
            MAJOR=$(echo $VERNO | awk -F '.' '{print $1}')
            MINOR=$(echo $VERNO | awk -F '.' '{print $2}')
            RELEASE=$(echo $VERNO | awk -F '.' '{print $3}')
            if [ "$MAJOR" != "v3" -o -z "$MINOR" -o -z "$RELEASE" -o -z "$REFDATE" ]; then
                echo "Invalid tag format. Must be v3.0.3-20200101010101. Refusing to build!"
                exit 1
            fi
            APPVERNAME="version=\"$VERSION-$REFDATE\""
            VERSION="$GIT_TAG"
        fi
        if [ -z "$APPVERNAME" ]; then
            echo "APPVERNAME is empty! [$APPVERNAME] Aborting..."
            exit 1
        fi
        echo "RaceDB version is now $VERSION"
        echo "New version.py: [$APPVERNAME] - [helptxt/version.py]"
        echo "$APPVERNAME" > helptxt/version.py
	else
		echo "Running a local build"
	fi

}

checkbeta() {
    getVersion
    grep beta > /dev/null <<VER
$VERSION
VER
    if [ $? -eq 0 ]; then
        ISBETA=1
    else
        ISBETA=0
    fi
}

checkprivate() {
    getVersion
    grep private > /dev/null <<VER
$VERSION
VER
    if [ $? -eq 0 ]; then
        ISPRIVATE=1
    else
        ISPRIVATE=0
    fi
}

getdockertags()
{
    checkbeta
    checkprivate
    . .dockerdef
    if [ $ISBETA -eq 1 ]
    then
        export LATESTTAG=beta
    elif [ $ISPRIVATE -eq 1 ]; then
        export LATESTTAG=private
    else
        export LATESTTAG=latest
    fi
    export TAG=$VERSION
    export IMAGE
    echo "Docker will use the following for a build:"
    echo "TAG=$TAG"
    echo "IMAGE=$IMAGE"
    echo "LATESTTAG=$LATESTTAG"
}

updatecompose() {
    getdockertags
    if [ $ISBETA -eq 1 ]; then
        sed -E "s/racedb:(private|beta|latest)/racedb\:beta/g" docker/docker-compose.yml > docker/docker-compose.yml.new
        echo "Updated docker-compose.yml for beta version"
    elif [ $ISPRIVATE -eq 1 ]; then
        sed -E "s/racedb:(private|beta|latest)/racedb\:private/g" docker/docker-compose.yml > docker/docker-compose.yml.new
        echo "docker-compose.yml set for private version"
    else
        sed -E "s/racedb:(private|beta|latest)/racedb\:latest/g" docker/docker-compose.yml > docker/docker-compose.yml.new
        echo "docker-compose.yml set for latest version (default)"
    fi
    mv docker/docker-compose.yml.new docker/docker-compose.yml
}

buildcontainer() {
    getdockertags
    if [ $ISPRIVATE -eq 1 ]; then
        echo "##################################################"
        echo "WARNING: BUILDING A PRIVATE BUILD OF THE CONTAINER"
        echo "##################################################"
        LATESTTAG="private"
    fi
    echo "Building version container: $IMAGE:$TAG"
    docker build --no-cache -t $IMAGE:$TAG .
    echo "Building latest container: $IMAGE:$LATESTTAG"
    docker build -t $IMAGE:$LATESTTAG .
}

pushcontainer() {
    getdockertags
    if [ $ISPRIVATE -eq 0 ]; then
        getdockertags
        echo "Pushing version container: $IMAGE:$TAG"
        docker push $IMAGE:$TAG
        echo "Pushing latest container: $IMAGE:$TAG"
        docker push $IMAGE:$LATESTTAG
    else
        echo "Refusing to push/publsh a private build!"
    fi
}

buildall() {
        checkEnvActive
        cleanup
        updateversion
    	echo "RaceDB Version is $VERSION"
        updatecompose
        compileCode
        packagecode
        buildcontainer
}

tagrepo() {
	CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD -- | head -1)
	if [ "$CURRENT_BRANCH" != "master" ]; then
		echo "Unable to tag $CURRENT_BRANCH branch for release. Releases are from master only!"
        exit 1
	fi
    echo "Crossmgr version will be updated by the auto-build system to match the tag"
	getVersion
	# Remove the -private from the version
	VERSIONNO=$(echo $VERSION | awk -F - '{print $1}')
	DATETIME=$(date +%Y%m%d%H%M%S)
	TAGNAME="v$VERSIONNO-$DATETIME"
	echo "Tagging with $TAGNAME"
	git tag $TAGNAME
	git push origin $TAGNAME
}

dorelease() {
	CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD -- | head -1)
	if [ "$CURRENT_BRANCH" != "dev" ]; then
		echo "Unable to do release on $CURRENT_BRANCH branch. You must be on dev branch to cut a release".
        exit 1
	fi
    if ! git diff-index --quiet HEAD --; then
        echo "$CURRENT_BRANCH has uncommited changed. Refusing to release. Commit your code."
        exit 1
    fi
    if [ x"$(git rev-parse $CURRENT_BRANCH)" != x"$(git rev-parse origin/$CURRENT_BRANCH)" ]; then
        echo "$CURRENT_BRANCH is not in sync with origin. Please push your changes."
        exit 1
    fi
	getVersion
	# Remove the -private from the version
	VERSIONNO=$(echo $VERSION | awk -F - '{print $1}')
	DATETIME=$(date +%Y%m%d%H%M%S)
	TAGNAME="v$VERSIONNO-$DATETIME"
	echo "Releasing with $TAGNAME"
    git checkout master
    git merge dev -m "Release $TAGNAME"
    git push
    echo "Code merged into master..."
	git tag $TAGNAME
	git push origin $TAGNAME
    echo "Code tagged with $TAGNAME for release"
    git checkout dev
    echo "Current branch set back to dev..."
}


doHelp() {
	cat <<EOF
$0 [ -hcCtaep: ]
 -h        - Help
 -E [env]  - Use Environment ($VIRTUAL_ENV)
 -p [pythonexe]  - Python version (Default $PYTHONVER)

 -S        - Setup environment
 -C        - Clean up everything
 -B        - Compile code
 -k        - Package application
 -c        - Build container
 -u        - Update docker-compose
 -b        - Build docker containers
 -P        - Push docker containers
 -A        - Build everything and package (except push containers)

 -T        - Tag for release
 -r        - do release

Running on: $OSNAME

To setup the build environment after a fresh checkout, use:
$0 -S

To build all the applications and package them, use:
$0 -a

EOF
	exit
}

gotarg=0
while getopts "hvCpSBPkUAzTrub" option
do
	gotarg=1
	case ${option} in
		h) doHelp
		;;
		v) 	getVersion
		;;
		C) 	cleanup
		;;
		p) PYTHONVER=$OPTIONARG
		   echo "Using Python: $PYTHONVER"
		;;
		S) envSetup
		;;
		B) compileCode
		;;
		k) packagecode
		;;
		U) updateversion
        ;;
        u) updatecompose
		;;
        b) buildcontainer
		;;
        P) pushcontainer
		;;
		A) buildall
		;;
		z) checkEnvActive
		;;
		T) tagrepo
		;;
		r) dorelease
		;;
		*) doHelp
		;;
	esac
done

if [ $gotarg -eq 0 ]; then
	echo "No arguments given"
	doHelp
	exit 1
fi

