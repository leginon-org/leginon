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
pyscopefolder = os.path.join(programsfolder, 'pyScope')

if __name__ == '__main__':

	if sys.argv[1] == '-install':
		try:
			import pyScope.updatecom
			pyScope.updatecom.run(os.path.join(pythonfolder, 'pyScope'))
		except ImportError:
			print 'Failed to update COM'
		try:
			os.mkdir(pyscopefolder)
			directory_created(pyscopefolder)
		except OSError:
			pass

		target = os.path.join(pythonfolder, 'pyScope', 'updatecom.py')
		path = os.path.join(pyscopefolder, 'Update COM.lnk')
		create_shortcut(target, 'Update COM', path, '',
										os.path.join(pythonfolder, 'pyScope'))
		file_created(path)

	elif sys.argv[1] == '-remove':
		pass
	else:
		print 'Invalid argument for installation script'

