[TOC]

# Participant Edit

## Participant Fields

### Participant (License Holder)
The License Holder for this Participant (see [License Holders][] for details).

### Role
The Role of the Participant.
This defaults to Competitor.
Participants are usually Competitors, however, RaceDB can track License Holders in other roles (Officials, Timing, Organizer, Managers, Drivers, etc.).

The Competition Age is calculated from the License Holder's Date of Birth, the date of the Competition, and can be effected by the Discipline of the Competition.
Specifically, Cyclocross Competitions use a different calculation to determine the Competition Age
(see [Disciplines][] for details).

### Team
The Team of this Participant.  Optional.  A Competitor does not require a Team (but, no Team will show up in the results).

If the Participant is an Official or Organizer, there should not be a Team assigned.

### Category
The Category of the rider.  The options available are the same as the Categories defined in the Competition's Category Format (see [Category Formats][] for details).

### Confirmed
Flag indicating whether rider is confirmed for the race.  This flag is normally set by the Race Secretary and indicates that the Rider's license, team and category have been checked, are in good standing, and the rider is cleared to compete.

### Signature
The rider's signature.  Clicking on this option will open a page capable of capturing the rider's signature with an appropriate Electronic Signature Pad (see [Hardware and Devices][] for details).

The signature capture works with any web browser - no special software is required. 

### Preregistered
Flag indicating whether rider is preregistered.  RaceDB does not use this flag, it exists for tracking and reporting only.

Sometimes the race fee is different for day-of registration than for pre-registration.  This flag allows you to track preregistered riders that still have not paid as different from day-of riders that have not paid.

### Paid
Flag indicating whether the rider has paid.  RaceDB does not use this flag, it exists for tracking and reporting only.
Use this flag is you are charging a different amount based on whether the competitor has pre-registered for the race or arrives day-of.

### Bib
The rider's bib number.  This brings up a screen to select available bib for the rider's categories.

The screen shows available bib numbers and allocated bib numbers.  Click on an available bib number to assign it to this rider.  To see who has an allocated bib number, move the mouse pointer over the number.  The rider who has it will be shown in the hover window.

### Chip Tag
The rider's chip tag.  This brings up a screen to set or write a EPC chip tag.

In order for this to work, RaceDB must be started with the __python launch --rfid_reader__ option, an RFID reader must be connectd to the computer, and a near-field antenna must be available next to the workstation to write the tags.

* For more info on how to launch RaceDB, see [Tutorial][].
* For more info on the hardware required to write tags, see [Hardware and Devices][].

### Competition Note
A note that applies to this competition only.  For example, "Permissiong given to race up a category".

### General Note
A note that stays with the rider from competition to competition.  For example, "We have your lost driver's license".

### Optional Events
Events for which this rider can choose.

## Starts
A list of the Mass Start Events and Waves for this rider.

## Category
A list of the categories this rider is participating in at the Competition.

Each Category entry is treated as a separate "Participant".  This is to allow tracking separate payment, bib number (if required by the Category Number ranges) and different team (for example, a rider may compete in his/her Elite category with a trade team, but in the SingleSpeed category as an individual).

## "Incomplete.  Prcess Next Entry Anyway" or "Complete and Accurate.  Process Next Entry" Button

Shows the state entry, but allows moving on if required.  Fields that require attention are shown with a caution symbol next to them.  When all required fields are filled in, the button will turn green and "Complete and Accurate.  Process Next Entry" will be enabled.

This changing status helps the registration staff to get complete information about the rider, but to move on if that information is not available.

## Print Race Voucher

Formats the Participant information for printing.  This can be used as a receipt to give to the rider as it contains all the information the rider needs.

