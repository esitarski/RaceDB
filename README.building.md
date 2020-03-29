# Building RaceDB

The RaceDB build system requires Linux or MacOSX. The same linux build script creates a tar.gz and zip file. Both are usable on all platforms. Windows is required to build the RaceDB-Controller.exe use for the Windows Docker Container.

Please understand that understanding how to build the software is only required for making updates and changes to RaceDB. Actually builds are made available on GitHub using their CI/CD (see workflows under .github/workflows)

## Required Software

Linux/MacOSX:

- recent Linux distro (Ubuntu 18.XX or newer) or MacOSX Catalina
- bash 3.x
- Python 3.8 or newer
- git
- Visual Studio Code (optional)

Windows:
- Windows 10 with Powershell (used for Docker Controller only!)

## Compile Script

The compile.sh script drives the build for the code. This is the same script that is called by the GitHub CI/CD. You can run it manually to make a build. The package.py supplements the compile.sh script is NOT meant to be run directly. Running the script with no options shows the help information:

```
compile.sh [ -hcCtaep: ]
 -h        - Help
 -E [env]  - Use Environment ()
 -p [pythonexe]  - Python version (Default python3.8)

 -S        - Setup environment
 -C        - Clean up everything
 -B        - Compile code
 -k        - Package application
 -c        - Build container
 -u        - Update docker-compose
 -b        - Build docker containers
 -P        - Push docker containers
 -A        - Build everything and package (except push containers)

 -T        - Tag for release
 -r        - do release

Running on: Darwin

To setup the build environment after a fresh checkout, use:
compile.sh -S

To build all the applications and package them, use:
compile.sh -A
```

The basic setups for building the code are as follows:

- Checkout the code
- Setup the virtual environment:
    ```bash
    bash compile.sh -S
    ```
- Build and package the code:
    ```
    bash compile.sh -A
    ```

The resultant files will reside in the release directory.

## Building the Windows RaceDB Controller

For Windows users using the RaceDB container, we provide a special powershell GUI app to help drive the container. To build this controller requires a recent 64bit Windows 10 system. 32bit systems are not supported.

To build the Windows RaceDB container package, do the following from the powershell prompt:

- Checkout the code
- To build all the applications and package them, use:
    ```
	compile.ps1 -all
    ```

The RaceDB-Windows-Container.zip is built and stored in the release directory.

## Releasing the Code

First, all development work is to be completed on the "dev" branch. Any pull requests made to any branch outside of the dev branch will be rejected. This means under no circumstances is code to be checked into master directly.

When development work has been completed, check in your changes to the dev branch. This will cause a development build to be created on github. Be sure to download and test the development version.

Once the development version testing is completed, the next step is to make a release. A release involves the following steps:

- bump the version
  
  ```bash
  compile.sh -B
  ```

  You must use the script to update the version. Failure to do so will cause a difference in version numbers between the tgz/zip file versions and the published docker container. This will confuse users.

- Check in the version change:
  
  ```
  git commit -a -m 'updated version'
  ```

- Do a release
  
  ```bash
  compile.sh -r
  ```

  The script will merge the changes from the dev branch into the master branch, and tag the release with the current version. The tag will cause github to do a release build and publish the updated container to Docker Hub.


## Forcing a Release

Occationally, it may be required to force a release build. This can be done with the tag command on the compile script. With the master branch checked out, run:

```bash
compile.sh -T
```

This will tag master branch with the version number and cause github to release the code.

