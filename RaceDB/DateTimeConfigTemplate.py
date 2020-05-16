#-----------------------------------------------------------------------
# Date and time formats for RaceDB.
#
# To make this work, rename this file to DataTimeConfig.py.
# Then uncomment/edit the lines beloe to configure the format you want to be shown in RaceDB.
# For reference, see here: https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
#
# Note: Date and DateTime editing use the browser's built-in date/datetime pickers.
# Browser pickers follow the format of whatever locale the user has configured on their computer.
#
#RACEDB_DATE_SHORT = 'Y-m-d'				# ISO (default)
RACEDB_DATE_SHORT = 'd-m-Y'			# UK.
#RACEDB_DATE_SHORT = 'm-d-Y'			# USA.
	
#RACEDB_DATE_MONTH_DAY = 'M d'			# Month, day (default)
RACEDB_DATE_MONTH_DAY = 'd M'			# day, Month (USA, UK)

#RACEDB_TIME_HHMMSS = 'H:i:s'			# 24 hour:minute:second (ISO)
RACEDB_TIME_HHMMSS = 'h:i:sa'			# 12 hour:minute:second am/pm (UK/NA)
