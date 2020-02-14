![DevelopmentBuild](https://github.com/esitarski/RaceDB/workflows/DevelopmentBuild/badge.svg)
![ReleaseBuild](https://github.com/esitarski/RaceDB/workflows/ReleaseBuild/badge.svg)

# Welcome to RaceDB

RaceDB is a database system for for Cross Manager. It allows registration of riders via web browser, and allows the timing person to refer to the race data in RaceDB from Cross Manager.

If you have already installed RaceDB and are doing an upgrade, follow the instructions for upgrading at the end of this document. Otherwise, you will need to do a full install.

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
    python
	
  If you get the message:

    ‘python’ is not recognized as an internal or external command

  You need to set your PATH.  This is not hard, and you only need to do it once:

  - a)  Close the "cmd" window
  - b)  Follow the instructions to set your PATH here:
        [http://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/]
  - c)  Return to Step 3 - make sure you close the old "cmd" window and open a new one.

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
    python
	
  If you get the message:

    ‘python’ is not recognized as an internal or external command

  You need to set your PATH.  This is not hard, and you only need to do it once:

  - a)  Close the "cmd" window
  - b)  Follow the instructions to set your PATH here:
        [http://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/]
  - c)  Return to Step 3 - make sure you close the old "cmd" window and open a new one.

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

