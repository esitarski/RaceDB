Install-Module PS2EXE
if (Test-Path release -PathType leaf)
{
	rmdir -Recurse -Force release
}
mkdir release
ps2exe -inputFile .\windows\RaceDBController.Export.ps1 -outputFile .\release\RaceDBController.exe -x64 -noConsole -title "RaceDB Controller" -version 1.0.0 -noOutput -noError -iconFile windows\RaceDB.ico
copy racedb.env release\
copy docker-compose*.yml release\
copy dbconfig.env.tmpl release\
copy README.md release\
$zipfilename = "RaceDB-Container-Windows.zip"
if (Test-Path $zipfilename -PathType leaf)
{
	del $zipfilename
}
Compress-Archive -DestinationPath $zipfilename -Path release\*