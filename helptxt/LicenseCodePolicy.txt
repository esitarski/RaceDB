{TOC]

# License Code Policy

Unfortunately, there are no globally unique License Codes.

Sure, there is the UCI code, but that is formed from the 3-letter country code and the date of birth.
This is certainly not unique globally, and sometimes it is not unique for riders in the same race (this causes havoc at UCI races, by the way).
At best, the UCI code is an identifier that is usually unique for riders in the same race.

To deal with this problem, National Federations issue licenses numbers that are unique.

For example, USA Cycling License Codes are issued by USA Cycling, and are guaranteed unique across all USA riders.
Canada has a similar central association that issues unique license numbers for all riders in Canada.

But, are there any Canadian Cycling License codes that are the same as USA Cycling codes?  Sadly, yes.
There is no central body responsible for issuing license codes for the two association, so there may be duplicate license numbers between riders in the US and Canada.

Of course, it doesn't have to be this way.  "Universal Unique Identifiers" were invented to solve the problem of creating unique identifiers without any central control (see [UUIDs](http://en.wikipedia.org/wiki/Universally_unique_identifier)).

It would be fantastic if all License Codes for all riders from all countries were a UUID.  Then, one could build a *perfect* database, with a unique UUID key.

The UUID is 36 characters long.  However, it it were represented licenses as a barcode, no one would have to type it in.  For race results, one could just print the last 6 digits as a check (like the last digits of a credit card).
It could work!

Sigh...

Back in the real world, we have to cope with non-unique license codes.

RaceDB requires the license code to be unique (of course, it allows non-unique UCI codes).