import sys, os, winshell

# RaceDB command and arguments to create shortcut.
cmd = "launch"

def CreateShortcut():
	current_folder = os.path.dirname(os.path.realpath(__file__))
	desktop = winshell.desktop()
	shortcut_path = os.path.join(desktop, "RaceDB Launch.lnk")

	with winshell.shortcut(shortcut_path) as link:
		link.description = "RaceDB Shortcut"
		link.working_directory = current_folder
		link.icon_location = (os.path.join(current_folder, 'core', 'static', 'images', 'RaceDB.ico'), 1)
		link.path = sys.executable
		link.arguments = "manage.py" + " " + cmd

if __name__ == '__main__':
	CreateShortcut()