import os
import platform

def which( program ):
	def is_exe( fpath ):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			path = path.strip('"')
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file

	return None

def gs_find():
	gs_exe = which('gs')
	if not gs_exe:
		if platform.system() == 'Windows':
			install_dir = r'C:\Program Files\gs'
			dirs = sorted( [d for d in os.listdir(install_dir)
				if d.startswith('gs') and d[-3] == '.' and os.path.isdir(os.path.join(install_dir, d, 'bin'))], reverse=True )
			for e in ('gswin64.exe', 'gswin32.exe'):
				gs_exe = os.path.join(install_dir, dirs[0], 'bin', 'gswin64.exe')
				if os.path.exists(gs_exe):
					return gs_exe
		
	return gs_exe
	
def gs_cmd():
	gs_exe = gs_find()
	if gs_exe:
		return '"{}" -dBATCH -dNOPAUSE -sDEVICE=mswinpr2'.format( gs_exe )
	return None
	
if __name__ == '__main__':
	print gs_cmd()