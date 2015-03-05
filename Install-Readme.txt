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

If running Windows:

Go to https://www.python.org/download/releases/2.7.8/

Choose the installer for your platform:

For Windows:
* Windows x86 MSI Installer (for 32-bit windows).
* Windows x86-64 MSI Installer (for 64-bit windows).

To determine whether you are running 32 or 64 bit Windows, see:
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
c)  Return to Step 3 - make sure you close the old "cmd" window and open a new one.


***********************************************************************
Step 5:  Install the RaceDB Dependencies

In your cmd/terminal enter:

  Windows:    python dependencies.py
  Linux/Mac:  sudo python dependencies.py
  
You will see a text scrolling up as all the dependent modules
are installed.

By patient!
This may take a few minutes as the modules are downloaded and configured.

***********************************************************************
Step 6:  Set your timezone.

cd to the RaceDB directory.
There is another RaceDB directory there.
cd to that one.

Use an editor to create a file called "time_zone.py".
In your time_zone.py file, add the following line:

TIME_ZONE = '<your_time_zone>'

where <your_time_zone> is the timezone you are in from http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
Make sure <your_time_zone> is surrounded by quotes.
Do not put anything else in the file.
Save it.
Quit editor.
Return to the main RaceDB directory with: cd ..

***********************************************************************
Step 7:  Initialize the Database

In your cmd/terminal enter two commands:

  python manage.py migrate
  python manage.py init_data

The first command builds the required database structure for all the RaceDB modules.
During the process, you may be required to enter an admin login.
I recommend calling the admin user "admin" with the password "admin".

The second command will initialize some data into the database (default categories and some riders from the TdF).
This data includes:

* Some starter Category Formats and Categories
* Disciplines
* Some Tdf Riders
* Some Tdf Teams

***********************************************************************
Step 8:  Start the RaceDB Server (run RaceDB)

In your cmd/terminal enter:

  python manage.py launch
  
After a few seconds, you will see a browser open connected to the RaceDB server.

For more details about RaceDB, scroll to the bottom of the browser screen
and press "Help".

To stop the RaceDB server, click in the cmd/terminal window,
and press Ctrl-c.  Alternatively, close the cmd/terminal by pressing the X button on the window.

RaceDB does not require the internet while it is running.

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
***********************************************************************
Upgrading:

These instructions assume that you are running RaceDB 0.2.50 or later.

The upgrade will *not* replace your existing database or time zone.
But, make a backup of your database file, just in case.

Unzip RaceDB.zip into the folder you unzipped it in before.

Now, make sure that all the dependencies are up-to-date:

Make sure you are connected to the internet.
In the RaceDB folder, run the follow command:

  Windows:    python dependencies.py --upgrade
  Linux/Mac:  sudo python dependencies.py --upgrade

You will see a text scrolling up as any updated modules are installed.

By patient!
This may take a few minutes as the modules are downloaded and configured.

In the RaceDB folder, run the follow command:

  python manage.py migrate

The "migrate" command will make changes to your existing database to support the latest functionality.
Your existing data will be preserved.
  
That's it!
Now, follow Step 7 to launch RaceDB as usual.
