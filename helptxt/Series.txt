[TOC]

# Series

Series allow you to compute a combined result from a number of races.

## Edit Details

Edit the details of the Series.

If the Series name starts with '_' (underscore), the Series is considered "private" and will only be shown to __Super__ user.  This is useful when you are in the process of developing a new Series.

## Category Format

When creating a new Series, you must choose a Category Format.  Only Competitions with the same CategoryFormat can be added to the Series.
It is important to get this right.

## Ranking Criteria

A Series can be scored by 3 Ranking Criteria:

1. Points Structure
1. Time
1. Percent Winner / Finish time

A __Points Structure__ is a list of points-for-place in the finish.  A points structure can also specify points for finishing a race, points for DNF and points for DNS (see below).

Time ranks by the finish time.  A series scored by time is always first scored by events completed, then by the total time.  There is no score considered for DNF, DNS or lapped riders.

Percent Winner / Finish time is a points system computed as follows Points = Winner's Time / Athlete's Time * 100.  This means that the winner gets 100 points.  All other athletes are awarded pointed based on a ratio of the winner's time.

For example, say the Winner's time was 52 minutes, and another Athlete's time was 56 minutes.  The points awarded for this event would be:

    Points = 100.0 * 52 / 56 = 92.86

For this option, there are no points for DNF, DNS or lapped riders.

## Callup Max

Number of athletes to list in Callups.  If zero, this Series will not be used for Callups.
If non-zero, the first Series with non-zero Callup Max will be used for Callups.
A reasonable number might be 16 - the first two rows of a CycloCross Race start.

If you wish all athletes in each start Wave to be included in the Callups, set the __Callup Max__ to a large number, like 500.

A __Callups__ button when then be displayed for each event in the Competition Dashboard.

If there are multiple Series that include the same Event, the first Series will be used for Callups.

### Randomize if no Results

If a Rider has no results, he/she is not included in the callup by default.  This option includes riders up to __Callup Max__, but randomizes riders with no results.

## Points Structures

Specify the Points-for-place, Finisher, DNF and DNS points.  You can specify multiple structures and configure them by event.

## Upgrade Progressions

Tells RaceDB how athletes progress through categories, allowing some or all points to be "carried forward" to the new category, or points to be "burned" in the category the athlete left.

Specify the category progression.  Then specify the Factor.  This tells RaceDB what portion of the old points to carry forward.  Specify a Factor of zero if you wish to "burn" the points.

## Combined Categories

Sometimes you want a Series ranking to be across a number of Categories.  Specify this here.

## Competitions

The Competitions in this Series.  You can configure different Points Structure (see above) by Event in each Competition.

You can use a different points structure by Event.  For example, say you want to award double points for a Hill-climb TT.
Or, you wish to allocate more points at a regional championship.