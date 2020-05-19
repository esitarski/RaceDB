#-----------------------------------------------------------------------
# Date and time formats for RaceDB.
#
# To make this work, rename this file to DataTimeConfig.py.
# Then uncomment/edit the lines beloe to configure the format you want to be shown in RaceDB.
#
# Date/time fields supported are y, Y, m, d, H, h, i, s, a
# Do NOT use named months or days for RACEDB_DATE_SHORT and RACEDB_TIME_HHMMSS.
# See: https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date

RACEDB_DATE_SHORT = 'Y-m-d'				# ISO (default)
#RACEDB_DATE_SHORT = 'd-m-Y'			# UK.
#RACEDB_DATE_SHORT = 'm-d-Y'			# USA.
	
RACEDB_TIME_HHMMSS = 'H:i:s'			# 24 hour:minute:second (ISO)
#RACEDB_TIME_HHMMSS = 'h:i:s P'			# 12 hour:minute:second am/pm (UK/USA).  There *must* be a space before the P.

# RACEDB_DATE_MONTH_DAY is display only and can be of any format.
RACEDB_DATE_MONTH_DAY = 'M d'			# Month, day (default)
#RACEDB_DATE_MONTH_DAY = 'd M'			# day, Month (USA, UK)
