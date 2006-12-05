import os
import sys
from distutils.sysconfig import get_python_lib

if sys.platform != 'win32':
	sys.exit()

try:
	programsfolder = get_special_folder_path('CSIDL_COMMON_PROGRAMS')
except OSError:
	try:
		programsfolder = get_special_folder_path('CSIDL_PROGRAMS')
	except OSError, e:
		print 'Creation of shortcuts failed: %s' % e
		sys.exit()

pythonfolder = get_python_lib(plat_specific=True)
leginonfolder = os.path.join(programsfolder, 'Leginon')

if __name__ == '__main__':
	if sys.argv[1] == '-install':
		try:
			os.mkdir(leginonfolder)
			directory_created(leginonfolder)
		except OSError:
			pass

		target = os.path.join(pythonfolder, 'Leginon', 'start.py')
		path = os.path.join(leginonfolder, 'Leginon.lnk')
		create_shortcut(target, 'Leginon', path, '',
										os.path.join(pythonfolder, 'Leginon'))
		file_created(path)

		target = os.path.join(pythonfolder, 'Leginon', 'launcher.py')
		path = os.path.join(leginonfolder, 'Leginon Client.lnk')
		create_shortcut(target, 'Leginon Client', path, '',
										os.path.join(pythonfolder, 'Leginon'))
		file_created(path)

		target = os.path.join(pythonfolder, 'Leginon')
		path = os.path.join(leginonfolder, 'Leginon Folder.lnk')
		create_shortcut(target, 'Leginon Folder', path, '',
										os.path.join(pythonfolder, 'Leginon'))
		file_created(path)
	elif sys.argv[1] == '-remove':
		pass
	else:
		print 'Invalid argument for installation script'

