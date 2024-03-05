def get_version():
	try:
		version = RaceDBVersion
	except Exception as e:
		import os
		import re
		import builtins
		fname = os.path.join( os.path.dirname(os.path.dirname(__file__)), 'helptxt', 'version.py' )
		with open(fname) as f:
			text = f.read()
		version = re.search( '"([^"]+)"', text ).group(1)
		builtins.__dict__['RaceDBVersion'] = version
	return version	

