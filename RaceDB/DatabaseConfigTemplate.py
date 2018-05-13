#-----------------------------------------------------------------------
# Configure this file to get RaceDB to use another database other than sqlite3.
#
# **** New RaceDB Install:
#
# Copy this file to DatabaseConfig.py in the same folder.
# Then, uncomment/edit the parameters below required for your database.
# If you want to go back to using the RaceDB.sqlite3 database,
# delete DatabaseConfig.py *and* DatabaseConfig.pyc in this directory.
#
# Make sure you only have one of each parameter defined (i.e. not two 'ENGINE' parameters).
# And preserve all quotes and commas.
# Follow in the existing install instructions.
#
# **** Convert from Existing RaceDB:
#
# You have an existing RaceDB sqlite3 database, you can transfer all the data
# to your new database.
# This is a one-time process - you can't merge changes between the databases.
# You have to use one and *only* one going forward.
#
# First, stop RaceDB if it is running.
# Then, before configuring a new database, dump the data from your exising database
# with the command:
#
#    python manage.py dumpdata core > mydata.json
#
# This can take a few minutes, so be patient.
#
# Now, configure your new database.
# Copy this file to DatabaseConfig.py in the same folder.
# Then, uncomment/edit the parameters below required for your database.
# Make sure you only have one of each parameter defined (i.e. not two 'ENGINE' parameters).
# And preserve all quotes and commas.
# If you want to go back to using the RaceDB.sqlite3 database,
# delete DatabaseConfig.py *and* DatabaseConfig.pyc in this directory.
#
# Initialize the new database with:
#
#    python manage.py migrate
#
# Now, loaded the data you saved previously with the command:
#
#    python manage.py loaddata mydata.json
#
# That will read all the data into your new database.
# This can take a while, so be patient.
# For safety, delete they "mydata.json" file afterwards.
#

DatabaseConfig = {
	# Uncomment one of the following lines to indicate which database you want to use.
	'ENGINE': 'django.db.backends.mysql',
	# 'ENGINE': 'django.db.backends.postgresql',
	# 'ENGINE': 'django.db.backends.oracle',
	'NAME': 'DATABASE_NAME',		# Name of the database.  Must be configured in your database.
	'USER': 'DATABASE_USER',		# Username to access the database.  Must be configured in your database.
	'PASSWORD': 'USER_PASSWORD',	# Username password.
	'HOST': 'localhost',   # Or the IP Address that your DB is hosted on (eg. '10.156.131.101')
	# 
	'PORT': '3306',	# MySql database port
	# 'PORT': '5432', # Postgres database port
}
