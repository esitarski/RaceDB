# RaceDB-Container

## Welcome to RaceDB

RaceDB is a database system for for Cross Manager. It allows registration of riders via web browser, and allows the timing person to refer to the race data in RaceDB from Cross Manager.

## Installation

There are two method to get RaceDB working
    - The hard way using lots of command line "code" as per the original install instructions (Install-Readme.txt) from the source code
    - The easy way using Docker and the RaceDB-Container

If you are a seasoned RaceDB enthusist or a seasoned python programmer, feel free to run though the old install instructions. Otherwise, go download and install Docker ([http://www.docker.com]). Docker Desktop is available for Mac and Windows and Docker Community edition is available for Linux. Once Docker is installed, the installation procedure is straight forward.

## Why Use the Docker Container?

Docker is a lightweight virtual machine environment. Unlike VMware, Docker does not virtual the entire machine, but only parts of the operating system needed to spin up a container. As such, it is more effiencent. Further, we have packaged all the software require to run RaceDB inside the container. This is no need to install Python, PostgreSQL, or do any database configuraion or to update Python, PostgreSQL, etc. as you might normally do. This container takes care of that for you. By default, the we also spin up PostgreSQL in another container without any work required from you. We use PostgreSQL for the database for best performance. This is all done for you when you start the container set for the first time.

Upgrades are a matter of pulling the latest container image. This is a one command affair. Once the latest container is pulled, you just start it as usual. Any updates are taken care of for you. See Updating below.

About the only con is the Docker on Linux is a pain to setup the first time. However, on MacOSX and Windows Docker Desktop is a simple application to use. Docker also starts the containers by default when the system is start, so you no longer have to start it manually.

## Default Port

While racedb installed from source uses port 8000 [http://localhost:8000], the container has been setup to use the standard http port, port 80, for convenience. If you have a non-standard setup (run a local web server on the same machine as racedb), you will need to change this port number. To do so, do the following:

- edit the docker-compose.yml file
- find the line "80:8000"
- change it to "8000:8000" to map it to port 8000.

Additionally, but changing the mapping, you can set the port to anything you want.

## Running the Container (Windows)

The RaceDB container comes preconfigured for the most used options. However, if you use a RFID reader at registration to "burn" tags, you will want to add the IP number of your reader to the racedb.env file using the setup tool. The setup tool is a Windows UI application that allows the user to edit settings, install, run, and update the container. There is no need to use the commnad line.

Steps:

- Make sure Docker Desktop for Windows is installed and running. On machines will 4G of ram, it may is necessary to adjust the docker settings to allocate less memory to Docker.
  
- Unzip the release file into a directory (ie. C:\RaceDB (Windows)). The actual container is not supplied, but download when you first start it. The files in the zip allow for easy management of the container.

- Run the RaceDBController.exe file. On Windows, this is the file to use to control RaceDB. (If you run RaceDBController.exe from the command line, you MUST run it from the directory where it is located, or it will fail to install the container.)

- If you have RFID tag reader for registration or wish to change the TimeZone, select the File->Preferences menu item. Set the appropriate items, and click Save. This will update the racedb.env file used by Docker.

- For this step, you will require internet access. Select File->Update. Click the update button. This will start the process of downloading and installing the container. This can take 1-10mins depending on the internet connection speed. The dialog will display the progress. When it is complete, click the close button.

- Now the container is installed, you can start it. Hit the Start button. After a few seconds, the "Start Command Send" box will appear, and the RaceDB Controller will indicate RaceDB is running.

- Now, wait about two mins point your webbrowser to [http://localhost]. This delay is required to allow the database container to start. From another computer on the network, use the IP number of your computer. For example, [http://192.168.30.23].  The first time RaceDB starts it will initialize the database and setup the default configuration, which can, depending on the speed of your system, take up to two minutes.

- The default admin login is super and the password is super. Be sure to use the [http://localhost/admin] page to change the password!

We recommend configuring Docker to start with your system. If you do so, RaceDB will automatically start with Docker starts. Additionally, you can use the Docker control panel to control RaceDB.

The RaceDB Controller has other funcitonality available to the user to assist in things like troubleshooting. The File->Logs menu item display the Docker logs for the container setup including the RaceDB log as it starts and runs. This is good place to check if something isn't working. File->Run Bash opens a Unix shell prompt inside the container.

Additionally, you can import/export the database to json with the import/export menu options. See below for additional information importing/exporting the database.

## Running the Container (Mac/Linux)

The RaceDB container comes preconfigured for the most used options. However, if you use a RFID reader at registration to "burn" tags, you will want to add the IP number of your reader to the racedb.env file (see below). For Mac/Linux users, you are expected to be able to use the UNIX command line (bash prompt).

Steps:

- Install Docker Desktop for Mac or the Docker _community edition_ for Linux. On Linux, you must also install docker-compose. This is where things can get tricky on Linux. You must install the latest version from the Docker website and not use the one provided by your Linux distribution or weird things will happen. You have been warned. A recent version of docker-compose from the docker website is required to run this container. You can find the instructions here: [https://docs.docker.com/install/linux/docker-ce/ubuntu/]. You must be able to run the docker help container before proceeding with these instructions.

- Untar the release file into a directory (ie. $HOME/RaceDB)

- If you have RFID tag reader for registration or wish to change the TimeZone used by RaceDB, open the racedb.env file with a text editor, and set RFID_READER_HOST and TIMEZONE respectively. This configuration file is each time the container is started. You can stop the container, change these settings, and restart it to get the new settings if so required.

- For this step, you require internet access. From the terminal prompt run: "bash racedb.sh run" from the racedb container directory to start the container. The first time this command run, docker will download the container images from the internet and then spin up the containers, configure the database and racedb, and start racedb. The container download can take 1-10 mins depending on the speed of your internet connection. The download only happens the first time. Any other time you start the container, it will start from disk.

- Now, wait about two mins point your webbrowser to [http://localhost]. This delay is required to allow the database container to start. From another computer on the network, use the IP number of your computer. For example, [http://192.168.30.23].  The first time RaceDB starts it will initialize the database and setup the default configuration, which can, depending on the speed of your system, take up to two minutes.

- The default admin login is super and the password is super. Be sure to use the [http://localhost/admin] page to change the password!

We recommend configuring Docker to start with your system. If you do so, RaceDB will automatically start with Docker starts. Additionally, you can use the Docker control panel to control RaceDB.

## Commands Available (Linux/Mac)

The racedb.sh command line tool supports the follow commands:

Commands:
| Command | Description |
|---------|-------------|
| run | start the racedb container |
| stop | stop the racedb container |
| restart | stop and restart the racedb container |
| bash | run bash shell in running container |
| ps  | list running containers |
| manage | run manage.py in running container (passes additional args to manage) |
| logs | show the racedb container log |
| flogs | show the racedb container log and display continuously |
| export | export database to racedb-data |
| import {filename} | database database from racedb-data/{filename} |

On Windows, most above commands are encapsulated in the UI with the expection of the manage command.

## Data Directory and Automatic Backups

When the container is started, it will create a racedb-data directory in the same directory as the docker-compose.yml file. This directory is where data is exchanged from inside the container. You will also find the racedb log file that is created as racedb is running. By default, when the container is started, the container will save the current database to the racedb-data/backups directory, effectively backing up the database. The output is a json file suitable to restore the database using the manage.py command. You should check the contents of the directory randomly and clean up the files. Files are compressed with gzip to save space.

You can disable automatic backups by creating an empty file named ".nobackup" in the racedb-data directory.

### Upgrading from a Non-Container RaceDB

By default, the old installation of RaceDB will configure itself to use the Sqlite database driver and it will create a file RaceDB.sqlite3 in the RaceDB directory. If you were using the older non-containerized RaceDB, to migrate your old data into the containerized version, simple copy your RaceDB.sqlite3 file into the racedb-data directory. When the container is started with "./racedb.sh run" (Linux/Mac) or RaceDBController.exe (Windows), it will detect the existance of the file, and import the data into the database. Please keep this in mind, this is a destructive import and any existing data will be removed. This import will only happen once as the RaceDB.sqlite3 is renamed once the import is finished.

IMPORTANT: The import happens _after_ the database is backed up (as above).

## Auto Importing Data

The container is setup to look for the racedb-import.json in the racedb-data directory. If this file is detected, it will be imported into the database with the manage.py command. This is a destructive import. The import will only happen once as the file is renamed when the import has completed.

IMPORTANT: The import happens _after_ the database is backed up (as above).

## Manually importing/exporting data

The racedb.sh and the Windows controller UI both support manually exporting data. For Windows, use the Backup menu to select Export or Import. For the import, the selected file will be copied to the racedb-data directory and imported. For export, the racedb-export-{datecode}.json will be created.

Similarly, for Linux/MacOSX, running 'bash raced.sh import filename' will copy the file to the racedb-data directory, and run manage.py in the running container to import the data. The "bash racedb.sh export" will export the data to the racedb-data directory as racedb-export-{datecode}.json.

## Updating RaceDB

From time to time, RaceDB will be updated to a newer version. Generally speaking, unless there is a new feature you need or a bug fixed, we recommended upgrading no more than 1-2/times per year. To update the container, making sure you have an internet connection, and run the following command. The container MUST be stopped for the upgrade to proceed. If there is no upgraded container, the command will succeed with a message suggesting you have the latest version.

On Linux/Mac
```bash
bash  racedb.sh update
```

On Windows, use the RaceDBController.exe program, and select File->Update.

Once the command has complete, start the container as normal.

## Database Support

We have selected PostgresSQL as the database backend for RaceDB. While Sqlite, MySQL and Oracle are also supported, we have not tested these configrations.

By default, no configuration is required for PostgresSQL. The database is run passwordless as the PostgreSQL socket is exposed to RaceDB. PostgreSQL TCP port is disabled and not available outside the container for security reasons. An external database can be used which will be useful for cloud deployment. The docker-compose-extdb.yml gives an example of how to run the container with an external database. In this case, database configuration is stored in the racedb.sh file.

## Building the container

The container is self contained. Building the container requires either MacOSX or Linux. We do not support building the container on Windows. Building the container may be necessary for cloud deployment as cloud systems typically require a private docker repo.

Run "./racedb.sh build" to build the container. This will replace the container pulled from the Docker repo. This is only for users that understand how to use docker. The container uses scripts from docker-entrypoint-init.d to container the database setup, migrate data from an old RaceDB, configure racedb, and start it up. The 99-zdontstart.sh is used to stop the container from exiting on error. Additionally, renaming 99-zdontstart.sh to start will 00-zdontstart.sh will stop the startup scripts from running. This is useful for debugging an problem.

## Support

The first place to get support is in the CrossMgr Google Group [https://groups.google.com/forum/#!forum/crossmgrsoftware]. If you cannot get help there, please use the issue tab on Github to report problems to the maintainer or to get help. Do not email Ed directly, as he did not create the containers and will not be able to assist you.

