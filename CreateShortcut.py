import sys, os
import tempfile
import subprocess

vbTemplate = '''
Set oWS = WScript.CreateObject("WScript.Shell")
strDesktop = oWS.SpecialFolders("Desktop")
Set oLink = oWS.CreateShortcut(strDesktop + "\{name}.lnk")
oLink.TargetPath = "{targetPath}"
oLink.WorkingDirectory = "{workingDirectory}"
oLink.Arguments = "{arguments}"
oLink.Description = "{description}"
oLink.IconLocation =  "{icon}"
oLink.WindowStyle = 4
oLink.Save
'''

def CreateShortcut( cmd="launch" ):
	'''
		Create a desktop shortcut on Windows without win32shell module.
		Write a visual basic script, then run it with CScript.
	'''
	current_folder = os.path.dirname(os.path.realpath(__file__))
	
	vbStr = vbTemplate.format(
		name			='RaceDB Launch',
		targetPath		=sys.executable,
		arguments		=' '.join( ("manage.py", cmd) ),
		description		="RaceDB Launch",
		icon			='{},{}'.format(os.path.join(current_folder, 'core', 'static', 'images', 'RaceDB.ico'), 0),
		workingDirectory=current_folder,
	)
	
	#fd, fname = tempfile.mkstemp( suffix='.vbs' )
	#f = os.fdopen( fd, 'wb' )
	
	fname = os.path.join( current_folder, 'create_shortcut.vbs' )
	f = open( fname, 'w' )
	
	f.write( vbStr )
	f.close()
	
	try:
		subprocess.call( ['cscript.exe', '//Nologo', fname], shell=True )
	except Exception as e:
		print 'Failed: ', e
	finally:
		#os.remove( fname )
		pass

if __name__ == '__main__':
	CreateShortcut()
