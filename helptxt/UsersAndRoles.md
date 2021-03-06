[TOC]

# Users and Roles

There are three types of users in the system:

1. __super__: the super user can create/edit/delete anything.  Default password is "super".
1. __reg__: the registration staff person can check it riders only.  Default passwors is "reg".
1. __serve__: self-serve users.  Allows riders to confirm pre-reg data only - cannot edit data in database.  Default password is "serve".
1. __hub__: hub users.  These are read-only anonymous users who can view race and series results.  It is impossible to change data in hub mode.

It is possible to change the default passwords with the following command:

    python manage.py set_password username password
    
Where __username__ can be super, reg or serve and __password__ is the new password.
If you are running RaceDB over a public internet, make sure you reset the default passwords to protect your system.  If you feel the passwords have been compromised, don't hesitate to reset them.

Forgot a password?  No problem - just change it to something else.

As a __reg__ user, a much simpler view of the system is presented, for example, Delete options are absent.

Additionally, Competitions are only shown if they are active today.  This makes it harder for a __reg__ user to start registering
people for the wrong competition.

Don't tell your registration staff about the __super__ login and/or change the password.

It is safest to do work on the system logged in __reg__ as much as possible, even if you are the super user.
It is a lot harder to mess things up that way.

You can quickly tell if you are __super__ or __reg__ by looking at the icon at the top of the screen.
When super-user, it looks like superman.  When reg, it looks like a regular person.

You can also quickly log in and log out by pressing the round red button at the top of the screen.
Of course, changing users returns you to the same web page.

This is useful feature if you find yourself at a __reg__ user's computer and you have to do something on the spot to fix a problem.
Just log in as __super__, make your change right on the screen, then switch back in to __reg__.

The __serve__ user is great for self-serve application where riders confirm that their chip tags work and that their pre-reg information is correct.

## Self-Serve

Using the __serve__ user, it is possible to set up a number of kiosks that allow riders to check in by reading their tags.
The Self-Serve screen validates all important rider information (waiver, payment, category, etc.).  If there are any problems, the rider is directed to the registration desk.

Self-Serve can also be used for on-site drop-in racing (no prereg).  Of course, you will need to set up a Seasons Pass for payment, and track Waivers to cover the insurance.

