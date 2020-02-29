[TOC]

# Hub Mode

RaceDB supports a fully indexed results capability accessible by Competition and Athlete.

Hub mode is intended to be accessed by external users.  When in Hub mode, RaceDB is completely read-only and it is impossible to change data.

Of course, it is possible to access Hub mode when logged in as a RaceDB Reg or Super user.
There are a number of screens in RaceDB that access Hub mode to show additional information.

## Uploading Results from CrossMgr

Hub Mode displays results.  The results must be uploaded from CrossMgr.  See CrossMgr's __File/Upload Upload Results to RaceDB Server...__ for details.

## Launching Hub Mode

Hub Mode can be launched by adding the __--hub__ parameters to the launch command.  For example:

    python manage.py launch --hub --port 8100

This will start RaceDB in hub mode.  Hub mode restricts access to the Hub screens only so that data editing is impossible.  It is suitable to launch as a public-facing web site.

All other parameters work as usual, except the rfid parameters which are ignored.
The example command above launches the Hub server on port 8100.  If you are also launching regular RaceDB, it is necessary to launch Hub mode on a different ports.

It is possible to Upload CrossMgr results to a web server in hub mode.

## Searching by Competition and Athlete

Hub mode is straight-forward.  Search by Competitions or Athletes.  Click on the links and explore the results.

## Showing Combined Results by Start Wave

Most of the time, riders in a Start Wave are ranked separately by Category.

Sometimes all categories in a Wave should be ranked together (for example, a combined Women's Master's race).

If this is the case, set __Rank Categories Together__ in the RaceDB Wave edit screen (accessible from the __Competition Dashboard__).


