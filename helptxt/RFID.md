[TOC]

# RFID

## Background

The philosophy behind RaceDB is that a competitor's machine readable rfid code is different from the race number.

This makes it easy to change the race number without changeing the tag, or you can change the tag without changing the race number.
This makes it easier to support multi-event competitions with participants competing in more then one event.
It is also makes it easier to support upgrades.

In RaceDB, each competitor has up to two unique rfid codes.

The link between the competitor's bib number and the rfid code is managed in the database.

Make sure you order your RFID tags with sqeuential or random codes so they are universally unique.

## Using RFID Tags in Competitions

RaceDB support up to two RFID tags for each participant.

RaceDB supports RFID tags in two modes:

1. RFID tags that a License Holder keeps and uses at multiple competitions.  This works best when you have a regularly scheduled race series where riders keep their tags between races.  Riders can use self-checkin when they arrive at the race site.
2. Competition-specific RFID tags that are issued for one competition only (potentially collected afterwards).  This works when you have a one-off competition where riders will receive their chips in their race package.

In the __Competition Edit Screen__, select __Use Competitor's Existing Tags__ for option 1.

RaceDB does not allow duplicate RFID tags:

1. If Option 1, the RFID tag must be unique across all License Holders in the system.
2. If Option 2, the RFID tag must be unique to all License Holders at that competition.

## Self Check-in

For a 
