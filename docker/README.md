# RaceDB-Container

## Welcome to RaceDB

RaceDB is a database system for for Cross Manager. It allows registration of riders via web browser, and allows the timing person to refer to the race data in RaceDB from Cross Manager.

## Installation

There are two method to get RaceDB working
    - The hard way using lots of command line "code" as per the original install instructions (Install-Readme.txt) from the Cross Manager website.
    - The easy way using Docker and the RaceDB-Container

If you are a seasoned RaceDB enthusist or a seasoned python programmer, feel free to run though the old install instructions. Otherwise, go download and install Docker ([http://www.docker.com]). Docker Desktop is available for Mac and Windows and Docker Community edition is available for Linux. Once Docker is installed, the installation procedure is straight forward.

## Why Use the Docker Container?

Docker is a lightweight virtual machine environment. Unlike VMware, Docker does not virtual the entire machine, but only parts of the operating system needed to spin up a container. As such, it is more effiencent. Further, we have packaged all the software require to run RaceDB inside the container. This is no need to install Python, Mysql, or do any database configuraion or to update Python, Mysql, etc. as you might normally do. This container takes care of that for you. By default, the we also spin up MySQL in another container without any work required from you. We use Mysql for the database for best performance. This is all done for you when you start the container for the first time.

Upgrades are a matter of pulling the latest container image. This is a one command affair. Once the latest container is pulled, you just start it as usual. Any updates are taken care of for you. See Updating below.

## Running the Container (Windows)

The RaceDB container comes preconfigured for the most used options. However, if you use a RFID reader at registration to "burn" tags, you will want to add the IP number of your reader to the racedb.env file using the setup tool. The setup tool is a Windows UI application that allows the user to edit settings, install, run, and update the container.

Steps:

- Make sure Docker Desktop for Windows is installed and running. On machines will 4G of ram, it may is necessary to adjust the docker settings to allocate less memory to Docker.
  
- Unzip the release file into a directory (ie. C:\RaceDB (Windows))

- Run the RaceDBController.exe file. On Windows, this is the file to use to control RaceDB. (If you run RaceDBController.exe from the command line, you MUST run it from the directory where it is located, it will fail to install the container.)

- If you have RFID tag reader for registration or wish to change the TimeZone, select the File->Preferences menu item. Set the appropriate items, and click Save. This will update the racedb.env file used by Docker.

- For this step, you will require internet access. Select File->Update. Click the update button. This will start the process of downloading and installing the container. This can take 1-10mins depending on the internet connection speed. The dialog will display the progress. When it is complete, click the close button.

- Now the container is installed, you can start it. Hit the Start button. After a few seconds, the "Start Command Send" box will appear, and the RaceDB Controller will indicate RaceDB is running.

- Now, wait about two mins point your webbrowser to [http://localhost:8000]. From another computer on the network, use the IP number of your computer. For example, [http://192.168.30.23].  The first time RaceDB starts it will initialize the database and setup the default configuration, which can, depending on the speed of your system, take up to two minutes.

- The default admin login is super and the password is super. Be sure to use the [http://localhost:8000/admin] page to change the password!

We recommend configuring Docker to start with your system. If you do so, RaceDB will automatically start with Docker starts. Additionally, you can use the Docker control panel to control RaceDB.

The RaceDB Controller has other funcitonality available to the user to assist in things like troubleshooting. The File->Logs menu item display the Docker logs for the container setup including the RaceDB log as it starts and runs. This is good place to check if something isn't working. File->Run Bash opens a Unix shell prompt inside the container.

## Running the Container (Mac/Linux)

The RaceDB container comes preconfigured for the most used options. However, if you use a RFID reader at registration to "burn" tags, you will want to add the IP number of your reader to the racedb.env file (see below). For Mac/Linux users, you are expected to be able to use the UNIX command line (bash prompt).

Steps:

- Install Docker Desktop for Mac or the Docker community edition for Linux. On Linux, you must also install docker-compose. It is highly recommanded to install the latest version from the Docker website and not use the one provided by your Linux distribution. A recent version of docker-compose is required to run this container.

- Untar the release file into a directory (ie. $HOME/RaceDB)

- If you have RFID tag reader for registration or wish to change the TimeZone used by RaceDB, open the racedb.env file with a text editor, and set RFID_READER_HOST and TIMEZONE respectively. This configuration file is each time the container is started. You can stop the container, change these settings, and restart it to get the new settings if so required.

- For this step, you require internet access. From the terminal prompt run: "bash racedb.sh run" from the racedb container directory to start the container. The first time this command run, docker will download the container images from the internet and then spin up the containers, configure the database and racedb, and start racedb. The container download can take 1-10 mins depending on the speed of your internet connection. The download only happens the first time. Any other time you start the container, it will start from disk.

- Now, wait about two mins point your webbrowser to [http://localhost:8000]. From another computer on the network, use the IP number of your computer. For example, [http://192.168.30.23].  The first time RaceDB starts it will initialize the database and setup the default configuration, which can, depending on the speed of your system, take up to two minutes.

- The default admin login is super and the password is super. Be sure to use the [http://localhost:8000/admin] page to change the password!

We recommend configuring Docker to start with your system. If you do so, RaceDB will automatically start with Docker starts. Additionally, you can use the Docker control panel to control RaceDB.

## Commands Available (Linux/Mac)

The racedb.sh command line tool supports the follow commands:

run - start the racedb container
stop - stop the racedb container
restart - stop and restart the container
bash - run bash shell in running container
manage - run manage.py in running container (passes additional args to manage)
logs - show the racedb container log
update - update the RaceDB and MySQL containers from the current versions

To run the development version of the container, pass -d as the first parameter and any command. This will start phpmyadmin on [http://localhost:8080] and allow for database administration. You will need the Mysql root password from dbconfig.env to use phpmyadmin.

On Windows, most above commands are encapsulated in the UI with the expection of the manage command.

## Updating RaceDB

From time to time, RaceDB will be updated to a newer version. Generally speaking, unless there is a new feature you need or a bug fixed, we recommended upgrading no more than 1-2/times per year. To update the container, making sure you have an internet connection, and run the following command. The container MUST be stopped for the upgrade to proceed. If there is no upgraded container, the command will succeed with a message suggesting you have the latest version.

On Linux/Mac
```bash
bash  racedb.sh update
```

On Windows, use the RaceDBController.exe program, and select File->Update.

Once the command has complete, start the container as normal.

## Database Support

We have selected MySQL as the database backend for RaceDB. While Sqlite, Postgress and Oracle are also supported, we have not tested these configrations.

The Mysql configuration is stored in the dbconfig.env file that is created when the container is first started. The passwords in this file may be required to administrate the database. This file is auto-created the first time the RaceDBController.exe (Windows) or racedb.sh (Linux/Mac) commands are run. It is important to never remove this file; otherwise, the database passwords will be lost. While the containers will continue to function, you will require some Unix command line and docker knownledge to get the passwords back.

## Upgrading from a Non-Container RaceDB

By default, the old installation of RaceDB will configure itself to use the Sqlite database driver and it will create a file RaceDB.sqlite3 in the RaceDB directory. If you were using the older non-containerized RaceDB, to migrate your old data into the containerized version, simple copy your RaceDB.sqlite3 file into the same directory as the docker-compose.yml file. When the container is started with "./racedb.sh run" (Linux/Mac) or RaceDBController.exe (Windows), it will detect the existance of the file, and mount it inside the container. The startup scripts in the container will detect this file, and import the data into the MySQL database. Please keep this in mind, this is a destructive import and any existing data will be removed. This import will only happen once. We recommend removing the RaceDB.sqlite3 file from the directory after the import has been completed.

## Using the Development Version

The developer version of the container set can be enabled with the -d option to racedb.sh. This is only offically supported on Linux and MacOSX. This changes the docker compose file to the dev version which mounts the docker-entrypoint-init.d and RaceDB directories outside the container. It will further install the phpmyadmin container to enable database administraton. This is intended for development only and the full source tree from git will be required.

## Building the container

THe container is self contained. Building the container requires either MacOSX or Linux. We do not support building the container on Windows. Run "./racedb.sh build" to build the container. This will replace the container pulled from the Docker repo. This is only for users that understand how to use docker. The container uses scripts from docker-entrypoint-init.d to container the database setup, migrate data from an old RaceDB, configure racedb, and start it up. The 99-zdontstart.sh is used to stop the container from exiting on error. Additionally, renaming 99-zdontstart.sh to start will 00-zdontstart.sh will stop the startup scripts from running. This is useful for debugging an problem.

## Support

Please use the issue tab on Github to report problems to the maintainer.
