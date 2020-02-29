[TOC]

# Disciplines

These list the various competitive disciplines including Road, MTB, Cyclocross, etc.
You can add your own.

The Cyclocross discipline can change the Competitive Age calculation.

In cycling, the Competition Age of License Holders is normally determined by:

    CompetitionAge = YearOfCompetition - YearOfBirth

For example if a License Holder's birth year was 1984 and the a race was held in 2014, his/her Competition Age would be 20.

However, for Cyclocross Competitions in the months of September to December, the Competition Age is determined by:

    CompetitionAge = YearOfCompetition + 1 - YearOfBirth

That is, Cyclocross Competitions in the last three months of the year use the Competition Age of the next year.

This is a rule, not a bug.

So, give the same previous example of a Licence Holder born in 1984, and if the Cyclocross race was held in November, 2014, his/her Competition Age would be 21.

RaceDB handles this automatically.

If you don't want this behaviour, get creative, and change the Discipline to something that does not contain "cyclo" in the name.
For example, a Discipline named "C-y-c-l-o-c-r-o-s-s" would not trigger the behaviour.
