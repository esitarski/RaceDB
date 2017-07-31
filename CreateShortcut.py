import sys, os
import tempfile
import subprocess

vbTemplate = '''
Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{link}")

oLink.TargetPath = "{targetPath}"
oLink.Arguments = "{arguments}"
oLink.Description = "{description}"
oLink.IconLocation =  "{icon}"
oLink.WorkingDirectory = "{workingDirectory}"
oLink.WindowStyle = 1
oLink.Save
'''

def CreateShortcut( cmd="launch" ):
	'''
		Create a desktop shortcut on Windows without win32shell module.
		Write a visual basic script, then run it with CScript.
	'''
	current_folder = os.path.dirname(os.path.realpath(__file__))
	
	vbStr = vbTemplate.format(
		link			=os.path.join( current_folder, 'RaceDB Launch.LNK' ),
		targetPath		=sys.executable,
		arguments		=' '.join( ("manage.py", cmd) ),
		description		="RaceDB",
		icon			='{},{}'.format(os.path.join(current_folder, 'core', 'static', 'images', 'RaceDB.ico'), 0),
		workingDirectory=current_folder,
	)
	
	print vbStr
	
	fd, fname = tempfile.mkstemp( suffix='.vbs' )
	f = os.fdopen( fd, 'wb' )
	f.write( vbStr )
	f.close()
	
	try:
		subprocess.call( ['CScript.exe', fname], shell=True )
	except Exception as e:
		print 'Failed: ', e
	finally:
		os.remove( fname )

if __name__ == '__main__':
	CreateShortcut()
