# Command line options
param (
	[switch]$help = $false,
	[switch]$getver = $false,
	[switch]$updver = $false,
	[switch]$install = $false,
	[switch]$build = $false,
	[switch]$all = $false
)

function updateVersion
{
	if (-not [string]::IsNullOrEmpty($env:GITHUB_REF))
	{
		Write-Host "GITHUB_REF=$env:GITHUB_REF"
		$version = GetVersion
		$githubref = $env:GITHUB_REF.Split('/')
		$version = $version.Split('-')[0]
		$shortsha = $env:GITHUB_SHA.SubString(0, 7)
		if ($githubref[1] -eq 'heads' -and $githubref[2] -eq 'dev')
		{
			$appvername = "version=`"$version-beta-$shortsha`""
			$version = "${version}-beta-${shortsha}"
		}
		if ($githubref[1] -eq 'tags')
		{
			$verno = $githubref[2].Split('-')[0]
			$refdate = $githubref[2].Split('-')[1]
			$major = $verno.Split('.')[0]
			$minor = $verno.Split('.')[1]
			$release = $verno.Split('.')[2]
			if ($major -ne 'v3' -or [string]::IsNullOrEmpty($minor) -or [string]::IsNullOrEmpty($release) -or [string]::IsNullOrEmpty($refdate))
			{
				Write-Host "Invalid Tag format. Must be v3.0.3-20200101010101. Refusing to build!"
				exit 1
			}
			$appvername = "version=`"$version-$refdate`""
			$version = $githubref[2]
		}
		Write-Host "RaceDB version is now $version"
		Set-Content -Path "helptxt\version.py" -Value "$appvername"
	}
	else
	{
		Write-Host "Local build..."
	}
}

function GetVersion
{
	if (!(Test-Path -Path "helptxt\version.py"))
	{
		Write-Host "No version file in helptxt/version.py. Aborting..."
		exit 1
	}
	$version = Get-Content "helptxt\version.py"
	Write-Host "RaceDB Version is", $version
	return $version
}

function installPSEXE
{
	Install-Module -Scope CurrentUser -AllowClobber -Force PS2EXE
}

function build
{
	$version = GetVersion
	if (Test-Path release -PathType leaf)
	{
		rmdir -Recurse -Force release
	}
	if (Test-Path racedb-container -PathType leaf)
	{
		rmdir -Recurse -Force racedb-container
	}
	mkdir racedb-container
	mkdir release
	$fileversion = $version.Split('=')[1]
	$setupversion = $fileversion.Split('-')[0].SubString(2)
	$fileversion2 = $fileversion.Replace("`"", "")
	Write-Host "Setup Version: $setupversion"
	Write-Host "File Version: $fileversion2"
	ps2exe -inputFile .\docker\windows\RaceDBController.Export.ps1 -outputFile .\racedb-container\RaceDBController.exe -x64 -noConsole -title "RaceDB Controller" -version "$fileversion2" -noOutput -noError -iconFile .\docker\windows\RaceDB.ico
	copy docker\racedb.env racedb-container\
	copy docker\docker-compose.yml racedb-container\
	copy docker\README.md racedb-container\
	$zipfilename = "release\RaceDB-Container-Windows-$fileversion2.zip"
	if (Test-Path $zipfilename -PathType leaf)
	{
		del $zipfilename
	}
	Compress-Archive -DestinationPath $zipfilename -Path racedb-container\*
	Write-Host "Created: $zipfilename"
}

function buildall
{
	installPSEXE
	updateVersion
	build
}

function doHelp
{
	Write-Host '
	compile.ps1 [-help]
	-help        - Help
	-getver      - Get Version
	-updver      - Update version
	-install     - Install PS2EXE
	-build       - Build Release Zip
	
	To setup the build environment after a fresh checkout, use:
	compile.ps1 -setupenv
	
	To build all the applications and package them, use:
	compile.ps1 -all -everything
	'
	exit 1
}

if ($help -eq $true)
{
	doHelp
}

if ($all -eq $true)
{
	buildall	
}
else
{
	if ($getver -eq $true)
	{
		GetVersion
	}
	
	if ($updver -eq $true)
	{
		updateVersion
	}
	
	if ($install -eq $true)
	{
		installPSEXE
	}
	
	if ($build -eq $true)
	{
		build
	}
}
