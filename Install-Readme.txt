***********************************************************************
Welcome to RaceDB!

RaceDB is written in Python 2.7 in the Django web server framework.
As a web server and a database, installation and initialization is more
complicated than just installing a desktop app.

To run RaceDB, you need to install a number of supporting modules.
For this, you need to be connected to the internet.
Try to get a reasonably fast connnection.  This will save time.

Once everything is installed, RaceDB will run without the internet.

If you have already installed RaceDB and are doing an upgrade,
follow the instructions for upgrading.

***********************************************************************
Step 1:  Install Python 2.7:

If you are running Mac or Linux, you likely have this already.

If running Windows:

Go to www.python.org/download/releases/2.7.6

Choose the installer for your platform:

For Windows:
* Windows x86 MSI Installer (for 32-bit windows).
* Windows x86-64 MSI Installer (for 64-bit windows).

To determine what whether you are running 32 or 64 bit Windows, see:
  windows.microsoft.com/en-us/windows7/find-out-32-or-64-bit

***********************************************************************
Step 2:  Unzip RaceDB.zip

In Windows, consider unzipping it into "C:".
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

In your cmd/terminal window, enter:

  cd C:\RaceDB
  
or wherever you unzipped RaceDB.
Then, enter:

  Windows:     python get-pip.py
  Linux/Mac:   sudo python get-pip.py

You will see a bunch of text scroll up as pip installs.

If you are running on Windows and get the message:

    ‘python’ is not recognized as an internal or external command

You need to set your PATH.  This is not hard, and you only need to do it once:

a)  Close the "cmd" window
b)  Follow the instructions to set your PATH here:
      http://www.pythoncentral.io/add-python-to-path-python-is-not-recognized-as-an-internal-or-external-command/
c)  Return to Step 3 - make sure you close the "cmd" window and open a new one.


***********************************************************************
Step 5:  Install the RaceDB Dependencies

In your cmd/terminal enter:

  Windows:    python dependencies.py
  Linux/Mac:  sudo python dependencies.py
  
You will see a text scrolling up as all the dependent modules
are installed.

By patient!
This may take a few minutes as all the modules are downloaded and configured.

***********************************************************************
Step 6:  Initialize the Database

In your cmd/terminal enter two commands:

  python manage.py syncdb
  python manage.py init_data

The first command builds the database structure.
It requires you to enter an admin login.
I recommend calling the admin user "admin" with the password "admin".

The second command will initialize some data into the database (default categories and some riders from the TdF).
This data includes:

* Some starter Category Formats and Categories
* Disciplines
* Some Tdf Riders
* Some Tdf Teams

***********************************************************************
Step 7:  Start the RaceDB Server (run RaceDB)

In your cmd/terminal enter:

  python manage.py launch
  
After a few seconds, you will see a browser open connected to the RaceDB server.

For more details about RaceDB, scroll to the bottom of the browser screen
and press "Help".

To stop the RaceDB server, click in the cmd/terminal window,
and press Ctrl-c.  Alternatively, close the cmd/terminal window.

RaceDB does not require the internet while it is running.

This is the command you need to issue to run RaceDB from now on.

To start RaceDB and connect to the rfid reader, use the following command:

  python manage.py launch --rfid_reader
  
 When RaceDB comes up, login with username="super", password="super".
 This will log you into the system with superuser capabilities, which you will need to configure races.
 
 After logging in, click on the "Tutorial" link at the bottom of the page to get started.
 
 The system also comes with another login username="reg" password="reg".
 This is what the registration staff should use.  It disables access to configuration data and makes the system easier to use.
 It is OK if multiple people log in with the same username.
 
***********************************************************************
***********************************************************************
Upgrading:

Unzip RaceDB.zip into the folder your unzipped it in before.
This will *not* replace your existing database.
After unzipping, run the program using the instructions of Step 7 above.

*************************************************************************
* Important Note about upgrading to Version 0.2.50 from Earlier Versions
*************************************************************************

Version 0.2.50 introduces a new feature - the Season's Pass.
If you need to migrate an an existing pre-0.2.50 database, you must follow these steps.

If you are not upgrading from a previous version of RaceDB, then don't worry - nothing extra is required.

First, make a backup copy of your database file just in case something goes wrong.

In the RaceDB folder, run the follow commands:

  python manage.py syncdb
  python manage.py dbshell

The last command will create an SQL command line.  Carefully cut-and-paste the following commands, one line at a time, into the command line.  Make sure you include the trailing semi-colon on the first line.  Press Enter after each command:
  
	ALTER TABLE "core_competition" ADD COLUMN "seasons_pass_id" integer REFERENCES "core_seasonspass" ("id") DEFAULT NULL;
	.exit

That's it!
Now, follow Step 7 to launch RaceDB as usual.

A Season's Pass is a collection of Season's Pass Holders.
When you link a Competition to a Season's Pass, riders who check-in to a Competition will be automatically marked as Paid.
