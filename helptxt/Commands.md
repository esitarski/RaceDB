[TOC]

# Commands

All commands can be run in the form:

    python manage.py cmd <parameters>
    
## Password Management

    python manage.py set_password username password
    
Where username can be "super", "reg" or "serve".  Sets the password of the role.
If you are running RaceDB over the internet, make sure you set the passwords to something different that the default.

## Data Initialization

### init_usac <filename.csv>
Reads a usac .csv formatted data dump.
It initializes riders using the USAC license number as the key.
If is OK to run this command multiple times on the same data. If the license number for a rider is already in the database, the record data will be updated.  If it is new rider, a record will be added.

### init_ccn <spreadsheet.xlsx>
Reads a ccn (Canadian Cycling) formatted spreadsheet.  This command looks for the sheet ending in "CCN" and reads it.
It initializes riders using the "Licence Numbers" as the key.
If is OK to run this command multiple times on the same data. If the license number for a rider is already in the database, the record data will be updated.  If it is new rider, a record will be added.

## Database Commands

### dumpdata

Creates an extract for all the data in the RaceDB database in various formats, including json and xml.
For details, see [the Django docs.](https://docs.djangoproject.com/en/1.6/ref/django-admin/#dumpdata-app-label-app-label-app-label-model)

This can be useful for backups, or to move an entire dataset from one database to another.

### loaddata

Imports data previously extracted with dumpdata.
For details, see [the Django docs.](https://docs.djangoproject.com/en/1.6/ref/django-admin/#loaddata-fixture-fixture).

### dbshell

Gives you command-line access to the database so you can type in SQL statements.  You need to have sqlite installed for this to work.
For details, see [the Django docs.](https://docs.djangoproject.com/en/1.6/ref/django-admin/#dbshell).
