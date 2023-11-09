![DevelopmentBuild](https://github.com/esitarski/RaceDB/workflows/DevelopmentBuild/badge.svg)
![ReleaseBuild](https://github.com/esitarski/RaceDB/workflows/ReleaseBuild/badge.svg)

# Welcome to RaceDB

RaceDB is a database system for for Cross Manager. It allows registration of riders via web browser, and allows the timing person to refer to the race data in RaceDB from Cross Manager.

## Installation

There are two method to get RaceDB working
- The hard way using lots of command line "code" as per the original install instructions (See OLD INSTALL METHOD below) from the source code
- The easy way using Docker and the RaceDB-Container

If you are a seasoned RaceDB enthusist or a seasoned python programmer, feel free to run though the old install instructions. Otherwise, go download and install Docker ([http://www.docker.com]). Docker Desktop is available for Mac and Windows and Docker Community edition is available for Linux. Once Docker is installed, the installation procedure is straight forward.

## Why Use the Docker Container?

Docker is a lightweight virtual machine environment. Unlike VMware, Docker does not virtual the entire machine, but only parts of the operating system needed to spin up a container. As such, it is more efficient. Further, we have packaged all the software require to run RaceDB inside the container. This is no need to install Python, PostgreSQL, or do any database configuraion or to update Python, PostgreSQL, etc. as you might normally do. This container takes care of that for you. By default, we also spin up PostgreSQL in another container without any work required from you. We use PostgreSQL for the database for best performance. This is all done for you when you start the container set for the first time.

Upgrades are a matter of pulling the latest container image. This is a one command affair. Once the latest container is pulled, you just start it as usual. Any updates are taken care of for you. See Updating below.

About the only con is the Docker on Linux is a pain to setup the first time. However, on MacOSX and Windows Docker Desktop is a simple application to use. Docker also starts the containers by default when the system is start, so you no longer have to start it manually.

## Default Port

While racedb installed from source uses port 8000 [http://localhost:8000/RaceDB], the container has been setup to use the standard http port, port 80, for convenience. If you have a non-standard setup (run a local web server on the same machine as racedb), you will need to change this port number. To do so, do the following:

- edit the docker-compose.yml file
- find the line "80:8000"
- change it to "8000:8000" to map it to port 8000.

Additionally, but changing the mapping, you can set the port to anything you want.

## Running the Container (Windows)

The RaceDB container comes preconfigured for the most used options. However, if you use a RFID reader at registration to "burn" tags, you will want to add the IP number of your reader to the racedb.env file using the setup tool. The setup tool is a Windows UI application that allows the user to edit settings, install, run, and update the container. There is no need to use the command line.

Steps:

- Make sure Docker Desktop for Windows is installed and running. On machines will 4G of ram, it may is necessary to adjust the docker settings to allocate less memory to Docker.
  
- Unzip the release file (RaceDB-Container-Windows.zip) into a directory (ie. C:\RaceDB (Windows)). The actual container is not supplied, but download when you first start it. The files in the zip allow for easy management of the container.

- Run the RaceDBController.exe file. On Windows, this is the file to use to control RaceDB. (If you run RaceDBController.exe from the command line, you MUST run it from the directory where it is located, or it will fail to install the container.)

- If you have RFID tag reader for registration or wish to change the TimeZone, select the File->Preferences menu item. Set the appropriate items, and click Save. This will update the racedb.env file used by Docker.

- For this step, you will require internet access. Select File->Update. Click the update button. This will start the process of downloading and installing the container. This can take 1-10mins depending on the internet connection speed. The dialog will display the progress. When it is complete, click the close button.

- Now the container is installed, you can start it. Hit the Start button. After a few seconds, the "Start Command Send" box will appear, and the RaceDB Controller will indicate RaceDB is running.

- Now, wait about two mins, and point your webbrowser to [http://localhost/RaceDB]. This delay is required to allow the database container to start. From another computer on the network, use the IP number of your computer. For example, [http://192.168.30.23/RaceDB].  The first time RaceDB starts it will initialize the database and setup the default configuration, which can, depending on the speed of your system, take up to two minutes.

- The default login is super and the password is super. Be sure to use the __python3 manage.py set_password super ???__ command to change the password!

We recommend configuring Docker to start with your system. If you do so, RaceDB will automatically start with Docker starts. Additionally, you can use the Docker control panel to control RaceDB.

The RaceDB Controller has other funcitonality available to the user to assist in things like troubleshooting. The File->Logs menu item display the Docker logs for the container setup including the RaceDB log as it starts and runs. This is good place to check if something isn't working. File->Run Bash opens a Unix shell prompt inside the container.

Additionally, you can import/export the database to json with the import/export menu options. See below for additional information importing/exporting the database.

## Running the Container (Mac/Linux)

The RaceDB container comes preconfigured for the most used options. However, if you use a RFID reader at registration to "burn" tags, you will want to add the IP number of your reader to the racedb.env file (see below). For Mac/Linux users, you are expected to be able to use the UNIX command line (bash prompt).

Steps:

- Install Docker Desktop for Mac or the Docker _community edition_ for Linux. On Linux, you must also install docker-compose. This is where things can get tricky on Linux. You must install the latest version from the Docker website and not use the one provided by your Linux distribution or weird things will happen. You have been warned. A recent version of docker-compose from the docker website is required to run this container. You can find the instructions here: [https://docs.docker.com/install/linux/docker-ce/ubuntu/]. You must be able to run the docker help container before proceeding with these instructions.

- Untar the release file into a directory (ie. $HOME/RaceDB)

- If you have RFID tag reader for registration, wish to change the TimeZone used by RaceDB, or the Date/Time format, open the racedb.env file with a text editor, and set RFID_READER_HOST, TIMEZONE, and DATETIME_FORMAT respectively. This configuration file is each time the container is started. You can stop the container, change these settings, and restart it to get the new settings if so required.

- For this step, you require internet access. From the terminal prompt run: "bash racedb.sh run" from the racedb container directory to start the container. The first time this command run, docker will download the container images from the internet and then spin up the containers, configure the database and racedb, and start racedb. The container download can take 1-10 mins depending on the speed of your internet connection. The download only happens the first time. Any other time you start the container, it will start from disk.

- Now, wait about two mins point and your webbrowser to [http://localhost/RaceDB]. This delay is required to allow the database container to start. From another computer on the network, use the IP number of your computer. For example, [http://192.168.30.23/RaceDB].  The first time RaceDB starts it will initialize the database and setup the default configuration, which can, depending on the speed of your system, take up to two minutes.

- The default admin login is super and the password is super. Be sure to use __python3 manage.py set_password super ???__ to change the password.

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

# OLD INSTALL METHOD

The following information describes the install RaceDB on the command line. It is a cumbersome process only recommended to those making code changes to the application. We strongly recommend users use the Docker Container.

## First Time Installation

- Step 1:  Install Python 3.X:

  If you are running Mac or Linux, you likely have this already.

  If not, go to [https://www.python.org/downloads/]

  Choose the latest installer of 64 bit python 3 for your platform. 32bit versions are not supported.

- Step 1a: Install GIT
  
  On Windows, download git from https://gitforwindows.org/. Make sure git is available on your path. On Linux and MacOSX, git is usually installed by default.

- Step 2:  Unzip RaceDB.zip

  In Windows, consider unzipping it into "C:" to make a folder called "C:\RaceDB".
  This will make it easier later.

  On Linux/Mac, pick an easy location - you could pick your home directory (eg. ~/RaceDB)

- Step 3:  Open a cmd window (windows) or terminal window (Mac/Linux)

  On Windows, type "cmd" into the "Search program and files" after clicking on the launch button in the lower left.

  On other platforms, launch a terminal.

- Step 4:  If on Windows, check and fix your Path.

  In a md window, type:

  ```
  python
  ```
	
  If you get the message:

  ```
    ‘python’ is not recognized as an internal or external command
  ```

  You need to set your PATH.  This is not hard, and you only need to do it once:

  - a)  Close the "cmd" window
  - b)  Follow the instructions to set your PATH here:
        [http://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/]
  - c)  Return to Step 3 - make sure you close the old "cmd" window and open a new one.

- Step 4a: 

    In a cmd window, type:
    ```bash
    git
    ```

  ```
    ‘git’ is not recognized as an internal or external command
  ```

  You need to set your PATH.  You should have said yes to ADD TO PATH during installation of git. Logout or reboot your system to get the path updated.

- Step 4:  If on Linux/Mac, make sure you are using Python3

  Linux can have many versions of python installed. Only python3 is supported. Check:

  python --version

  You may have to use the python3 command to get python3.


- Step 5:  Install the RaceDB Dependencies

  In your cmd/terminal window, make sure you are in the RaceDB install folder.  Do a:

```cmd
  cd C:\RaceDB
```

  or wherever you unzipped RaceDB.
  Then enter:

  Windows:

```
python dependencies.py
```

    Linux/Mac:
  ```
  sudo python dependencies.py
  ```
  
  You will see a text scrolling up as all the dependent modules are installed.  Be patient!   This may take a few minutes as the modules are downloaded and configured.

- Step 6:  Initialize the Database

  Ensure you are cd'd to the RaceDB directory (see above).
  In your cmd/terminal enter two commands:

```bash
  python manage.py migrate
  python manage.py init_data
```

  The first command builds the required database structure for all the RaceDB modules. During the process, you may be required to enter an admin login. I recommend calling the admin user "admin" with the password "admin".

  The second command initializes default disciplines and categories. This data includes:

  - Disciplines
  - Some starter Category Formats and Categories

- Step 6.5:  Initialize Demo Data

  Ensure you are cd'd to the RaceDB directory (see above). If you want s some demo data in your database and play with a tutorial, enter the following:

```
  python manage.py init_demo
```

  This data includes:

  - Some Tdf Riders
  - Some Tdf Teams

- Step 7:  Start the RaceDB Server (run RaceDB)

  If you are running on Windows, the install will create a desktop shortcut called "RaceDB Launch".This does the same as "python manage.py launch" shown below. If you are on Linux or wish to run from the command line, ensure you are cd'd to the RaceDB directory (see above).

  In your cmd/terminal enter:

```
  python manage.py launch
```

  After a few seconds, you will see a browser connected to the RaceDB server.

  For more details about RaceDB, scroll to the bottom of the browser screen and press "Help".

  To stop the RaceDB server, click in the cmd/terminal window, and press Ctrl-c.  Alternatively, close the cmd/terminal by pressing the X button on the window.

  RaceDB does not require the internet while it is running.

  It is not necessary for RaceDB to be connected to an rfid reader (eg. Impinj).  Rather, you can use relatively inexpensive (UHF USB Readers)[https://www.amazon.ca/s?k=usb+rfid+reader+uhf+epc&sprefix=uhf+usb+%2Caps%2C99&ref=nb_sb_ss_ts-doa-p_1_8] that work in the 902-928MHz range (don't get the 13.56MHz ones - these won't work).
  With these readers, you can issue pre-programmed tags, revoke lost tags for reuse, and enable self-checking for races using RFID tags from any computer, tablet or smart phone connnected to the RaceDB network.

  You can still run RaceDB with a traditional RFID reader with RaceDB, you must first open port 5084 on your operating system.
  
  To start RaceDB and connect to an Impinj RFID reader, use the following command:

```
  python manage.py launch --rfid_reader
```

  When RaceDB comes up, login with username="super", password="super". This will log you into the system with superuser capabilities, which you will need to configure races.
 
  To see all possible "launch" command options, do:
  
  
``` 
  python manage.py launch --help
```

  The options starting at '--host" are of particular interest.  They allow you to choose the host and port of the RaceDB web server, connect to a particular rfid reader on the network, suppress automatically opening a browser and other capabilities.
 
  After logging in to RaceDB, click on the "Tutorial" and "Help" link at the bottom right of the page to get started.

  The system also comes with another login username="reg" password="reg". This is what the registration staff should use.  It disables access to configuration data and makes the system easier to use. It is OK if multiple people log in with the same username.

- Step 8:  Windows Only:  Create Launch Icons with different options

  On Windows, you can customize the desktop icon to include additional parameters. For example, say you want to launch RaceDB with the "--rfid_read" option from a desktop icon. To do so:

  - 1. On the existing "RaceDB Launch" desktop icon, right-click and select "Copy".
  - 2. On the background of your desktop, right-click and select "Paste shortcut".  This will create "RaceDB Launch (2)"
  - 3. Right-click on "RaceDB Launch (2)" and select "Properties"
  - 4. In the "Target" field, add the additional command options.  In this case, you can set "launch --rfid__reader".
    The options exactly the same as described above.  Press OK when you are done.
  - 5. Right-click on "RaceDB Launch (2)" and select "Rename".  Change the name to "RFID RaceDB".
  - 6. It important to give your new launch icon a different name, otherwise it will be overwritten when you upgrade RaceDB.

### RaceDB Config File

It is possible to configure launch options in a RaceDB.cfg config file. Create the RaceDB.cfg file in the same folder as "manage.py" (default location). You can tell the launch command to look somewhere else for the file with the "--config" option.

The config file is used to set the parameters to the launch command (do "python manage.py launch --help" to see what they are). Parameters in the config file will override those given on the command line. Lines in the config file beginning with '#' or ';' are comments.

Sample config file:

```
#-------------------------------------------
[launch]
# Don't launch a browser on startup.
no_browser=true

# Start with rfid reader.
rfid_reader=true

# Open on port 8080 instead of default.
port=8080
#-------------------------------------------
```
 
## Upgrading from 3.x.x to a newer version

The upgrade will preserve your existing database and keep all your information. (But, make a backup of your database file, just in case).

If RaceDB is running, stop it by closing the cmd window or pressing Ctrl-C in the window.

Unzip RaceDB.zip into the folder you unzipped it in before.

Now, make sure that all the dependencies are up-to-date. Make sure you are connected to the internet. In the RaceDB folder, run the follow command:

Windows:

```
python dependencies.py --upgrade
```

Linux/Mac:

```
sudo python dependencies.py --upgrade
```

You will see a text scrolling as necessary as the modules are installed.  Be patient! This may take a few minutes.

That's it!

Now, follow Step 9 to launch RaceDB as usual with:

```
  python manage.py launch <your_usual_launch_options_if_you_have_any>
```

If there are a lot of database conversions, this might take a few minutes. Be patient! After the database has been updated, subsequent launches will be fast.


## Upgrading from 2.x.x

## Upgrade Process

If you are currently running a RaceDB 1.X.X, you need to follow these upgrade steps to get to 3.X.X. You only need to do this once. After you are on RaceDB 3.X.X, upgrades will work as described in Install-Readme.txt (easier).

RaceDB should work the same after the upgrade including the interface to the chip reader, CrossMgr download/upload, PDF generation, etc. etc. However, leave yourself some time before an event to do the upgrade and to check out things afterward. Testing has been extensive, but there is always the case there is something in your data that doesn't work. All related fixes are generally easy and I should be able to turn the around quickly. 

These instructions are designed to be safe - you can return to the old RaceDB if something goes wrong. The reality is that Python2.7 was stopped being supported by Python.org in Jan 2020.  Python3 is a necessary requirement for continued support. We will not assist with issues using version 2.7 of Python.

### High Level Overview

Before upgrading to the new RaceDB, you will export your database into a file. Then, you rename the existing install RaceDB_old. Upgrade to Python3, then upgrade to RaceDB3 into a new RaceDB folder. In the new RaceDB install, you create an empty database, then you import the previous data into  the new database.

If something goes horribly wrong, you have not deleted anything and can revert to the previous version. If everything works, you can delete the RaceDB_old folder you created.

Make sense?  Let's get started:

- Step 1: Make a RaceDB.json file from your current database.

In the folder with your existing RaceDB, run the following command:

  python manage.py dumpdata core -o RaceDB.json
  
  This will create a file called RaceDB.json containing all your database data.
  It may be large (50-100Meg).

- Step 2: Make a backup of your RaceDB folder.

  For safety, now is the time to make a backup of your entire RaceDB folder.
  Copy it to a flash drive, or to some other location you can recover it from.

- Step 3: Rename your existing RaceDB folder to RaceDB_old.

  Rename your existing RaceDB folder to RaceDB_old.  Don't copy it.  Rename it.
  Note: on Windows, make sure you don't have any cmd windows cd'd into this folder.
  If you do, the rename won't work.  Close these cmd windows, or do "cd \" to get out of the RaceDB folder.

- Step 4: Install 64bit Python 3.

  32BIT PYTHON IS NOT SUPPORTED.

  - Windows:
  First de-install Python 2.7.
  Now, check that ...\Python27\... is no longer in your PATH environment variable.

  - Install Python 3.X 64-bit from https://www.python.org/.   !!! THIS IS NOT THE DEFAULT INSTALL (as of 2019/6) !!!  To install the 64-bit version, select "Downloads", then "Windows" from the menu at the top of the python.org page.   In the "Stable Releases" section, look for "Download Windows x86-64 executable installer" and click on it.

  - Follow the install instructions for Python3.  If given the option, add Python3 to your PATH variable. Note: Python 3.X 32-bit works, but not as well.

  - Linux:
  Python3 may already be installed.  Check your distro if de-installing Python 2.7 will cause instability.
  Check your distro for how to de-install Python 2.7 and install Python3.

  - After installing python3, test your install.  On a command line, type:

```
  python --version
```

  You should see:

  Python 3.X.X

  Where X.X is the specific version. If you still see Python 2.7, check your path.  If you are on Linux, try "python3 --version".  If "python3" works, you will need to type "python3" to run RaceDB going forward.


- Step 5: Install the new version of RaceDB.

  Download RaceDB 3.X.X and unzip it next to the RaceDB_old folder.
  Make sure that RaceDB unzips into a "clean" folder.  You should not be replacing any files when you unzip.
  This will be the case if you renamed your old RaceDB folder to RaceDB_old in Step 5.

- Step 6: Update the dependencies.

  In the new RaceDB folder, enter:

```bash
  python dependencies.py
```

  If you see:
  Python 3 is required for RaceDB. Please upgrade. Python 2.7 is no longer supported

  ...you have the wrong version of python. Go back to Step 4. Alternatively, try running "python3 dependencies.py"

- Step 7: Initialize the new database.

  If you are using the default RaceDB.sqlite3 database, in the new RaceDB folder, enter:

```bash
  python manage.py migrate
```

  If you are running on a hosted server:
  - copy your time_zone.py file from RaceDB_old/RaceDB to RaceDB/RaceDB.

  If you have configured RaceDB to use another database (eg. MySql, PostGres), follow these steps:
  - copy your DatabaseConfig.py file from RaceDB_old/RaceDB to RaceDB/RaceDB.
  - log into your database and rename your existing RaceDB database to something else (I recommend the same name with '_old' on the end).
  - while logged into your database, create a new RaceDB database and give it the same username and password as the old database.
  - exit the database prompt
  - in the new RaceDB folder enter:
  
```bash
      python manage.py migrate
```      

- Step 8: Transfer your existing data.

  In the new RaceDB folder, enter:

  Windows:
```bash  
  python manage.py loaddata ..\RaceDB_old\RaceDB.json
```

  Linux:
```bash
  python3 manage.py loaddata ../RaceDB_old/RaceDB.json
```
  
  This may take a few minutes and the program may appear to have hung.
  Be patient!  Everything will be fine - just let it run to completion.

- Step 9: Launch RaceDB

    ```bash
    python manage.py launch
    ```

  Congradulations!  You have upgraded RaceDB!

  The default login names and passwords ("super", etc.) will be set up for you. Going forward, you can apply upgrades as usual as described in Install-Readme.txt.

  If after a few weeks everything is working properly, you can delete the RaceDB_old folder.  Keep the backup for a while just in case.

=======

RaceDB is written in Python 3.X in the Django web server framework. As a web server and a database, installation and initialization is more complicated than just installing a desktop app.

You will first need to install a number of supporting modules. To do this, you need to be connected to the internet. Try to get a reasonably fast connection as there is much to download. After installation, RaceDB will run without the internet.

## First Time Installation

- Step 1:  Install Python 3.X:

  If you are running Mac or Linux, you likely have this already.

  If not, go to [https://www.python.org/downloads/]

  Choose the latest installer of 64 bit python 3 for your platform. 32bit versions are not supported.

- Step 2:  Unzip RaceDB.zip

  In Windows, consider unzipping it into "C:" to make a folder called "C:\RaceDB".
  This will make it easier later.

  On Linux/Mac, pick an easy location - you could pick your home directory (eg. ~/RaceDB)

- Step 3:  Open a cmd window (windows) or terminal window (Mac/Linux)

  On Windows, type "cmd" into the "Search program and files" after clicking on the launch button in the lower left.

  On other platforms, launch a terminal.

- Step 4:  If on Windows, check and fix your Path.

  In a cmd window, type:
  ```
    python
    ```
	
  If you get the message:

    ```
    ‘python’ is not recognized as an internal or external command
    ```

  You need to set your PATH.  This is not hard, and you only need to do it once:

  - a)  Close the "cmd" window
  - b)  Follow the instructions to set your PATH here:
        [http://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/]
  - c)  Return to Step 3 - make sure you close the old "cmd" window and open a new one.

- Step 4:  If on Linux/Mac, make sure you are using Python3

  Linux can have many versions of python installed. Only python3 is supported. Check:

    ```
    python --version
    ```

  You may have to use the python3 command to get python3.


- Step 5:  Install the RaceDB Dependencies

  In your cmd/terminal window, make sure you are in the RaceDB install folder.  Do a:

    ```cmd
    cd C:\RaceDB
    ```

  or wherever you unzipped RaceDB.
  Then enter:

  Windows:

    ```
    python dependencies.py
    ```

    Linux/Mac:
    ```
    sudo python dependencies.py
    ```
  
  You will see a text scrolling up as all the dependent modules are installed.  Be patient!   This may take a few minutes as the modules are downloaded and configured.

- Step 6:  Initialize the Database

  Ensure you are cd'd to the RaceDB directory (see above).
  In your cmd/terminal enter two commands:

    ```bash
    python manage.py migrate
    python manage.py init_data
    ```

  The first command builds the required database structure for all the RaceDB modules. During the process, you may be required to enter an admin login. I recommend calling the admin user "admin" with the password "admin".

  The second command initializes default disciplines and categories. This data includes:

  - Disciplines
  - Some starter Category Formats and Categories

- Step 6.5:  Initialize Demo Data

  Ensure you are cd'd to the RaceDB directory (see above). If you want s some demo data in your database and play with a tutorial, enter the following:

    ```
    python manage.py init_demo
    ```

  This data includes:

  - Some Tdf Riders
  - Some Tdf Teams

- Step 7:  Start the RaceDB Server (run RaceDB)

  If you are running on Windows, the install will create a desktop shortcut called "RaceDB Launch".This does the same as "python manage.py launch" shown below. If you are on Linux or wish to run from the command line, ensure you are cd'd to the RaceDB directory (see above).

  In your cmd/terminal enter:

    ```
    python manage.py launch
    ```

  After a few seconds, you will see a browser connected to the RaceDB server.

  For more details about RaceDB, scroll to the bottom of the browser screen and press "Help".

  To stop the RaceDB server, click in the cmd/terminal window, and press Ctrl-c.  Alternatively, close the cmd/terminal by pressing the X button on the window.

  RaceDB does not require the internet while it is running.

  To start RaceDB and connect to an Impinj RFID reader, use the following command:

    ```
    python manage.py launch --rfid_reader
    ```

  You must open port 5084 on your operating system.
  
  When RaceDB comes up, login with username="super", password="super". This will log you into the system with superuser capabilities, which you will need to configure races.
 
  To see all possible "launch" command options, do:

    ``` 
    python manage.py launch --help
    ```

  The options starting at '--host" are of particular interest.  They allow you to choose the host and port of the RaceDB web server, connect to a particular rfid reader on the network, suppress automatically opening a browser and other capabilities.
 
  After logging in to RaceDB, click on the "Tutorial" and "Help" link at the bottom right of the page to get started.

  The system also comes with another login username="reg" password="reg". This is what the registration staff should use.  It disables access to configuration data and makes the system easier to use. It is OK if multiple people log in with the same username.

- Step 8:  Windows Only:  Create Launch Icons with different options

  On Windows, you can customize the desktop icon to include additional parameters. For example, say you want to launch RaceDB with the "--rfid_read" option from a desktop icon. To do so:

  - 1. On the existing "RaceDB Launch" desktop icon, right-click and select "Copy".
  - 2. On the background of your desktop, right-click and select "Paste shortcut".  This will create "RaceDB Launch (2)"
  - 3. Right-click on "RaceDB Launch (2)" and select "Properties"
  - 4. In the "Target" field, add the additional command options.  In this case, you can set "launch --rfid__reader".
    The options exactly the same as described above.  Press OK when you are done.
  - 5. Right-click on "RaceDB Launch (2)" and select "Rename".  Change the name to "RFID RaceDB".
  - 6. It important to give your new launch icon a different name, otherwise it will be overwritten when you upgrade RaceDB.

### RaceDB Config File

It is possible to configure launch options in a RaceDB.cfg config file. Create the RaceDB.cfg file in the same folder as "manage.py" (default location). You can tell the launch command to look somewhere else for the file with the "--config" option.

The config file is used to set the parameters to the launch command (do "python manage.py launch --help" to see what they are). Parameters in the config file will override those given on the command line. Lines in the config file beginning with '#' or ';' are comments.

Sample config file:

```
#-------------------------------------------
[launch]
# Don't launch a browser on startup.
no_browser=true

# Start with rfid reader.
rfid_reader=true

# Open on port 8080 instead of default.
port=8080
#-------------------------------------------
```
 
## Upgrading from 3.x.x to a newer version

The upgrade will preserve your existing database and keep all your information. (But, make a backup of your database file, just in case).

If RaceDB is running, stop it by closing the cmd window or pressing Ctrl-C in the window.

Unzip RaceDB.zip into the folder you unzipped it in before.

Now, make sure that all the dependencies are up-to-date. Make sure you are connected to the internet. In the RaceDB folder, run the follow command:

Windows:

```
python dependencies.py --upgrade
```

Linux/Mac:

```
sudo python dependencies.py --upgrade
```

You will see a text scrolling as necessary as the modules are installed.  Be patient! This may take a few minutes.

That's it!

Now, follow Step 9 to launch RaceDB as usual with:

```
  python manage.py launch <your_usual_launch_options_if_you_have_any>
```

If there are a lot of database conversions, this might take a few minutes. Be patient! After the database has been updated, subsequent launches will be fast.


## Upgrading from 2.x.x

## Upgrade Process

If you are currently running a RaceDB 1.X.X, you need to follow these upgrade steps to get to 3.X.X. You only need to do this once. After you are on RaceDB 3.X.X, upgrades will work as described in Install-Readme.txt (easier).

RaceDB should work the same after the upgrade including the interface to the chip reader, CrossMgr download/upload, PDF generation, etc. etc. However, leave yourself some time before an event to do the upgrade and to check out things afterward. Testing has been extensive, but there is always the case there is something in your data that doesn't work. All related fixes are generally easy and I should be able to turn the around quickly. 

These instructions are designed to be safe - you can return to the old RaceDB if something goes wrong. The reality is that Python2.7 was stopped being supported by Python.org in Jan 2020.  Python3 is a necessary requirement for continued support. We will not assist with issues using version 2.7 of Python.

### High Level Overview

Before upgrading to the new RaceDB, you will export your database into a file. Then, you rename the existing install RaceDB_old. Upgrade to Python3, then upgrade to RaceDB3 into a new RaceDB folder. In the new RaceDB install, you create an empty database, then you import the previous data into  the new database.

If something goes horribly wrong, you have not deleted anything and can revert to the previous version. If everything works, you can delete the RaceDB_old folder you created.

Make sense?  Let's get started:

- Step 1: Make a RaceDB.json file from your current database.

In the folder with your existing RaceDB, run the following command:

  python manage.py dumpdata core -o RaceDB.json
  
  This will create a file called RaceDB.json containing all your database data.
  It may be large (50-100Meg).

- Step 2: Make a backup of your RaceDB folder.

  For safety, now is the time to make a backup of your entire RaceDB folder.
  Copy it to a flash drive, or to some other location you can recover it from.

- Step 3: Rename your existing RaceDB folder to RaceDB_old.

  Rename your existing RaceDB folder to RaceDB_old.  Don't copy it.  Rename it.
  Note: on Windows, make sure you don't have any cmd windows cd'd into this folder.
  If you do, the rename won't work.  Close these cmd windows, or do "cd \" to get out of the RaceDB folder.

- Step 4: Install 64bit Python 3.

  32BIT PYTHON IS NOT SUPPORTED.

  - Windows:
  First de-install Python 2.7.
  Now, check that ...\Python27\... is no longer in your PATH environment variable.

  - Install Python 3.X 64-bit from https://www.python.org/.   !!! THIS IS NOT THE DEFAULT INSTALL (as of 2019/6) !!!  To install the 64-bit version, select "Downloads", then "Windows" from the menu at the top of the python.org page.   In the "Stable Releases" section, look for "Download Windows x86-64 executable installer" and click on it.

  - Follow the install instructions for Python3.  If given the option, add Python3 to your PATH variable. Note: Python 3.X 32-bit works, but not as well.

  - Linux:
  Python3 may already be installed.  Check your distro if de-installing Python 2.7 will cause instability.
  Check your distro for how to de-install Python 2.7 and install Python3.

  - After installing python3, test your install.  On a command line, type:

```
  python --version
```

  You should see:

  Python 3.X.X

  Where X.X is the specific version. If you still see Python 2.7, check your path.  If you are on Linux, try "python3 --version".  If "python3" works, you will need to type "python3" to run RaceDB going forward.


- Step 5: Install the new version of RaceDB.

  Download RaceDB 3.X.X and unzip it next to the RaceDB_old folder.
  Make sure that RaceDB unzips into a "clean" folder.  You should not be replacing any files when you unzip.
  This will be the case if you renamed your old RaceDB folder to RaceDB_old in Step 5.

- Step 6: Update the dependencies.

  In the new RaceDB folder, enter:

```bash
  python dependencies.py
```

  If you see:
  Python 3 is required for RaceDB. Please upgrade. Python 2.7 is no longer supported

  ...you have the wrong version of python. Go back to Step 4. Alternatively, try running "python3 dependencies.py"

- Step 7: Initialize the new database.

  If you are using the default RaceDB.sqlite3 database, in the new RaceDB folder, enter:

```bash
  python manage.py migrate
```

  If you are running on a hosted server:
  - copy your time_zone.py file from RaceDB_old/RaceDB to RaceDB/RaceDB.

  If you have configured RaceDB to use another database (eg. MySql, PostGres), follow these steps:
  - copy your DatabaseConfig.py file from RaceDB_old/RaceDB to RaceDB/RaceDB.
  - log into your database and rename your existing RaceDB database to something else (I recommend the same name with '_old' on the end).
  - while logged into your database, create a new RaceDB database and give it the same username and password as the old database.
  - exit the database prompt
  - in the new RaceDB folder enter:
  
```bash
      python manage.py migrate
```      

- Step 8: Transfer your existing data.

  In the new RaceDB folder, enter:

  Windows:
```bash  
  python manage.py loaddata ..\RaceDB_old\RaceDB.json
```

  Linux:
```bash
  python3 manage.py loaddata ../RaceDB_old/RaceDB.json
```
  
  This may take a few minutes and the program may appear to have hung.
  Be patient!  Everything will be fine - just let it run to completion.

- Step 9: Launch RaceDB

```bash
  python manage.py launch
```

  Congradulations!  You have upgraded RaceDB!

  The default login names and passwords ("super", etc.) will be set up for you. Going forward, you can apply upgrades as usual as described in Install-Readme.txt.

  If after a few weeks everything is working properly, you can delete the RaceDB_old folder.  Keep the backup for a while just in case.
