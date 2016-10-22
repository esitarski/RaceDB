***********************************************************************
Welcome to RaceDB!

If you have already installed RaceDB and are doing an upgrade,
follow the instructions for upgrading at the end of this document.

Otherwise, you will need to do a full install.

RaceDB is written in Python 2.7 in the Django web server framework.
As a web server and a database, installation and initialization is more
complicated than just installing a desktop app.

You will first need to install a number of supporting modules.
To do this, you need to be connected to the internet.
Try to get a reasonably fast connection as there is much to download.

After installation, RaceDB will run without the internet.

***********************************************************************
Step 1:  Install Python 2.7:

If you are running Mac or Linux, you likely have this already.

If not,

Go to https://www.python.org/downloads/

Choose the latest installer of python 2.7.xx for your platform:

***********************************************************************
Step 2:  Unzip RaceDB.zip

In Windows, consider unzipping it into "C:" to make a folder called "C:\RaceDB".
This will make it easier later.

On Linux/Mac, pick an easy location - you could pick your home directory.

***********************************************************************
Step 3:  Open a cmd window or terminal

On Windows, type "cmd" into the "Search program and files" after
clicking on the launch button in the lower left.

On other platforms, launch a terminal.

***********************************************************************
Step 4:  Install "pip"

"pip" is the python package installer.
If you have python 2.7.9 or greater (but not python 3!) you can skip this step.
To check what version of python you have, on the command line, enter:

  python --version

If this is earlier than python 2.7.9, you need to install pip.

First, make sure you are connect to the internet.
In your cmd/terminal window, enter:

  cd C:\RaceDB
  
or wherever you unzipped RaceDB.
Then, enter:

  Windows:     python get-pip.py
  Linux/Mac:   sudo python get-pip.py

You will see a bunch of text scroll up as pip installs.

***********************************************************************
Step 5:  If on Windows, check and fix your Path.

In a cmd window, type:
    python
	
If you get the message:

    ‘python’ is not recognized as an internal or external command

You need to set your PATH.  This is not hard, and you only need to do it once:

a)  Close the "cmd" window
b)  Follow the instructions to set your PATH here:
      http://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/
c)  Return to Step 3 - make sure you close the old "cmd" window and open a new one.


***********************************************************************
Step 6:  Install the RaceDB Dependencies

In your cmd/terminal enter:

  Windows:    python dependencies.py
  Linux/Mac:  sudo python dependencies.py
  
You will see a text scrolling up as all the dependent modules
are installed.

By patient!
This may take a few minutes as the modules are downloaded and configured.

***********************************************************************
Step 7:  Set your time zone.

cd to the RaceDB directory.
In your cmd/terminal entry:

    python set_timezone.py

Select you time zone from the list and press OK.
This will configure RaceDB for your timezone.
If you change timezones, make sure you run set_timezone again.

***********************************************************************
Step 8:  Initialize the Database

In your cmd/terminal enter two commands:

  python manage.py migrate
  python manage.py init_data

The first command builds the required database structure for all the RaceDB modules.
During the process, you may be required to enter an admin login.
I recommend calling the admin user "admin" with the password "admin".

The second command will initialize default disciplines and categories.
This data includes:

* Disciplines
* Some starter Category Formats and Categories

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
Step 8.5:  Initialize Demo Data

If you want the demo data in your database and play with a tutorial, enter the following:

  python manage.py init_demo

This data includes:

* Some Tdf Riders
* Some Tdf Teams

***********************************************************************
Step 9:  Start the RaceDB Server (run RaceDB)

In your cmd/terminal enter:

  python manage.py launch
  
After a few seconds, you will see a browser open connected to the RaceDB server.

For more details about RaceDB, scroll to the bottom of the browser screen
and press "Help".

To stop the RaceDB server, click in the cmd/terminal window,
and press Ctrl-c.  Alternatively, close the cmd/terminal by pressing the X button on the window.

RaceDB does not require the internet while it is running.

To start RaceDB and connect to an Impinj RFID reader, use the following command:

  python manage.py launch --rfid_reader
  
You must open port 5084 on your operating system.
  
When RaceDB comes up, login with username="super", password="super".
This will log you into the system with superuser capabilities, which you will need to configure races.
 
 To see all possible "launch" command options, do:
 
  python manage.py launch --help
   
The options starting at '--host" are of particular interest.  They allow you to choose the host and port of the RaceDB web server, connect to a particular rfid reader on the network, suppress automatically opening a browser and other capabilities.
 
After logging in to RaceDB, click on the "Tutorial" and "Help" link at the bottom right of the page to get started.

The system also comes with another login username="reg" password="reg".
This is what the registration staff should use.  It disables access to configuration data and makes the system easier to use.
It is OK if multiple people log in with the same username.
 
***********************************************************************
RaceDB Config File:
It is possible to configure launch options in a RaceDB.cfg config file.
Create the RaceDB.cfg file in the same folder as "manage.py" (default location).
You can tell the launch command to look somewhere else for the file with the "--config" option.

The config file is used to set the parameters to the launch command (do "python manage.py launch --help" to see what they are).
Parameters in the config file will override those given on the command line.
Lines in the config file beginning with '#' or ';' are comments.

Sample config file:

#-------------------------------------------
[launch]
# Don't launch a browser on startup.
no_browser=true

# Open on port 8080 instead of default.
port=8080
#-------------------------------------------

 
***********************************************************************
***********************************************************************
***********************************************************************
Upgrading:

These instructions assume that you are running RaceDB 0.3.145 or later.
Change: it is no longer necessary to do a "migrate" command - it is now done automatically.

The upgrade will preserve your existing database and keep all your information.
(But, make a backup of your database file, just in case).

If RaceDB is running, stop it by closing the cmd window or pressing Ctrl-C in the window.

Unzip RaceDB.zip into the folder you unzipped it in before.

Now, make sure that all the dependencies are up-to-date:

Make sure you are connected to the internet.
In the RaceDB folder, run the follow command:

  Windows:    python dependencies.py --upgrade
  Linux/Mac:  sudo python dependencies.py --upgrade

You will see a text scrolling as necessary as the modules are installed.

By patient!
This may take a few minutes.

That's it!
Now, follow Step 9 to launch RaceDB as usual with:

  python manage.py launch <your_usual_launch_options_if_you_have_any>
