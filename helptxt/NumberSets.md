[TOC]

# Number Sets

__Number Sets__ allow you to track existing Bib numbers handed out to riders from Competition to Competition.
__Number Sets__ track lost numbers (and are no longer available to be handed out) and recovered numbers.

Riders can have multiple numbers for different categories from the same __Number Set__, or just one number.
Whether this is required depends on how you have organized your Category Numbers.

The __Number Set__ can be selected in the Competition edit screen.

For a more complicated example, say you are running an MTB series and a Road series.
Let's pick a particular rider name Pat.

Pat rides in one category in MTB and a different category in Road.
Naturally, Pat has a number for each discipline used for each race for the entire season.  Say 117 for MTB and 207 for Road.

When Pat comes to a MTB race, we want to use the MTB bib number: 117.
And, when Pat comes to a Road race we want to use the Road bib number: 207.

This is accomplished by using a different __Number Set__ for each race type.

Define a __Number Set__ called "MTB Numbers" and another __Number Set__ called "Road Numbers".  Then, associate each __Number Set__ with each race in each series, respectively.

Now, RaceDB can correctly find the different Bib numbers.

## Ranges

The Bib number ranges of the Number Set.  Usually something like 1-999.

However, you can specify repeated ranges.  For example, say you want to assign 1-99 to both Elite Men and Elite Women.  In this case you would set the number ranges to:

1-999,1-99

This tells RaceDB that it is permissible to give out two copied of numbers 1-99.

## Sponsor

The Sponsor of this Number Set.  If you use the __Print Tags__ option in [System Info][], this is the name that will be printed on the tags.

## Description

Internal description of the Number Set.  Can be any text you like.

