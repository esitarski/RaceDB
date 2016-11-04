#!/bin/bash
#
# RaceDB Labels Script
#
# Usage
# In the RaceDB System Info Edit screen:
#
#   Cmd used to print Bib Tag (parameter is PDF file)
#
#       [  /home/RaceDB/scripts/LABELS $1 ]
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


# split file name apart to get information on who requested the label and the type of label.
#
for i in $(echo $1 | sed -e 's/_/ /g'); do
case $i in
port-*)
    PORT=$i
    ;;
antenna-*)
    ANTENNA=$i
    ;;
type-*)
    TYPE=$i
    ;;
*.pdf)
    FILE=$i
    ;;
esac
done

# determine lp destination by label type
#
case ${TYPE} in
type-Tag | type-Frame | type-Shoulder | type-Emergency )
    PRINTERCLASS=QL710W
    ;;
type-Body)
    PRINTERCLASS=QL1060N
    ;;
esac

# debug
#echo PORT: $PORT
#echo ANTENNA: $ANTENNA
#echo TYPE: $TYPE
#echo FILE: $FILE
#cat > /tmp/$FILE

# XXX remove echo 
echo lp -d ${PRINTERCLASS}

