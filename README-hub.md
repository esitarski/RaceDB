# RaceDB Container

RaceDB is a database system for for Cross Manager. It allows registration of riders via web browser, and allows the timing person to refer to the race data in RaceDB from Cross Manager.

If you have already installed RaceDB and are doing an upgrade, follow the instructions for upgrading at the end of this document. Otherwise, you will need to do a full install.

RaceDB is written in Python 3.X in the Django web server framework. As a web server and a database, installation and initialization is more complicated than just installing a desktop app.

You will first need to install a number of supporting modules. To do this, you need to be connected to the internet. Try to get a reasonably fast connection as there is much to download. After installation, RaceDB will run without the internet.

The container require PostgresSQL to be connected to it. We recommend using the docker-compose.yml file from the git repo. See details below.

# Tags

There are two supported master tags along with the versioned containers:

  - beta: Latest beta version built from the development branch (use for testing only)
  - latest: Current released version of the container

# Details

For details on how to use the container, please see [https://github.com/esitarski/RaceDB]

