[TOC]

# Competitions

In a nutshell, a Competition contains a set of Mass Start events or Time Trial events with some extra overall information.

A Mass Start event is a set of uniquely numbered riders on course at the same time, and can have a number of Start Waves within it.
Each Start Wave consists of one or more Categories starting together.

A Time Trial event is a sequence of uniquely numbered riders on course one at a time, and can have a number of Start Waves within it.  Each rider is assigned a Start Time in a process known as __seeding__.

This is summarized as:

{% include "CompetitionStructure.md" %}

This is the fundamental structure of a competition.  Get comfortable with this structure, as it forms the foundation of everything else.

You describe this structure in RaceDB.  It then "knows" exactly where riders need to go when the check-in.

RaceDB has a powerful "Copy" feature that allows you to use the same race structure over again.  So, once you have your race formats defined, using them again for future races is quick.

# Competitions Screen

Shows a list of all Competitions in the system with the most recent shown first.  You can use the "Search text" feature to find a particular Competition.

Clicking on a Competition row triggers the default button (Dashboard).  This brings you to the main Competetion screen, the [Competition Dashboard][].

The __Import Competition__ can import a previously Expored Competition.  All information associated with a Competition is imported.  Existing data records are re-used, missing data is created from the import.

This feature enables a __decentralized__ approach to managing races:

1. Create an empty Competition, configure it with all the required Categories, Start Waves, etc. and send it to organizers.  The organizers __Import__ the template then customize it for their race.
1. Organizers send back the Competition after the race.  The data contains all the permanent number assignments and waivers.  Importing the Competition will update the master database.

## Competition Copy
Makes a copy of the competition including all category information, Mass Start Events, Start Waves and Category numbers.  The Participants are not copied.

To create a new Competition from an existing one, press Copy, then change the fields in the new Competition to customize it (for example, Name, Date, Organizer).

## Competition Export

Exports the Competition and all its data dependencies including Categories, Start Waves, Number Ranges, Participants, Options, etc.

## Competition Edit

Shows all the data associated with a Competition.

There are some additional buttons:

1. __Auto Generate Missing Tags for Existing Participants__
1. __Reapply Number Set to Existing Participants__

The first automatically generates missing tags for all participants.

The second re-applies the number set to get the Bib numbers of all participants.
Use this feature if:

1. You change the NumberSet of a Competition after you have added Participants.  This will apply the new Number Set values to all existing riders.
1. Or, you add pre-reg Participants to two future races.  In one, you assign bib numbers, but you want the same bib numbers to show up in the other.

Other than that, you don't need to worry about it.

Another interesting field is the __Legal Entity__.  This allociates this competition with a Legal Entity, which allows you to specify an Expiry dates for rider's waivers (see [Legal Entity][]).
