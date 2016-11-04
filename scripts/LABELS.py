#!/usr/bin/env python

#
# RaceDB Labels Python Script
#
# Usage
# In the RaceDB System Info Edit screen:
#
#   Cmd used to print Bib Tag (parameter is PDF file)
#
#       [  /home/RaceDB/scripts/LABELS.py $1 ]
# 

#
# The arguement provided is the file name which contains information about what is to 
# be printed. E.g.:
#
#       230489203498023809_bib-356_port-8000_antenna-2_type-Frame.pdf
#
# "type" is one of Frame, Body, Shoulder or Emergency.
# "port" is the RaceDB server port.
# "antenna" is the antenna of the user.
#
# The combination of server port and antenna allows different printers to 
# be used for different registration stations. The server port refers to
# the TCP port that the server responds to, e.g. 8000 or 8001 etc.
#

#
# For Linux we will have one or more printers added to the CUPS printing system. E.g.:
#
#   Printers: 
#       1. QL710W1 - first 2x4 printer
#       2. QL710W2 - second 2x4  printer
#       3. QL1060n1 - first 4x6 printer
#       4. QL1060n1 - second 4x6 printer
#   Classes:
#       1. QL710W 
#           - QL710W1
#           - QL710W2
#       2. QL1060N
#           - QL1060N1
#           - QL1060N2
#
# Multiple printers of each type is not required. But if available it improves throughput.
# Also if one printer runs out of labels the other continues to work alone until it is refilled.
# 
# The alternative with multiple printers is to allocate them to different registration
# tables. E.g. table with Antenna 0 and 1 get first printer and the table with Antenna 2 and 3
# get the second printer.
#
# 

import sys
import os
import subprocess

fname = sys.argv[1]

# Split file name apart to get information about the label.
# Numeric fields are converted to numbers to allow comparisons like params['antenna'] == 1
params = { k:(int(v) if v.isdigit() else v) for k, v in (p.split('-') for p in os.path.splitext(fname)[0].split('_')[1:] ) }

# debug
# print '\n'.join( '{}={}'.format(k,v if isinstance(v,int) else "'{}'".format(v)) for k, v in params.iteritems() )

# determine printer destination by label type.  Can also use 'type', 'port' and 'antenna'.
if params['type'] in ('Frame', 'Shoulder', 'Emergency'):
	printer_device = 'QL710W'
else:
	printer_device = 'QL1060N'

# Linux
#subprocess.check_call( ['lp', '-d', printer_device] )

# Windows
# Requires Adobe Acrobat Reader
#subprocess.check_call( ['AcroRd32.exe', '/t', fname, printer_device], shell=True )

