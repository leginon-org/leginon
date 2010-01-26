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
pyscopefolder = os.path.join(programsfolder, 'pyscope')

if __name__ == '__main__':

	if sys.argv[1] == '-install':
		try:
			import pyscope.updatecom
			pyscope.updatecom.run(os.path.join(pythonfolder, 'pyscope'))
		except:
			print 'Failed to update COM'

		try:
			import pyscope.tietzping
			pyscope.tietzping.register()
		except:
			print 'Failed to register pyscope.Ping'

		try:
			os.mkdir(pyscopefolder)
			directory_created(pyscopefolder)
		except OSError:
			pass

		target = os.path.join(pythonfolder, 'pyscope', 'updatecom.py')
		path = os.path.join(pyscopefolder, 'Update COM.lnk')
		create_shortcut(target, 'Update COM', path, '',
										os.path.join(pythonfolder, 'pyscope'))
		file_created(path)

		target = os.path.join(pythonfolder, 'pyscope', 'tietzping.py')
		path = os.path.join(pyscopefolder, 'Update Ping.lnk')
		create_shortcut(target, 'Update Ping', path, '',
										os.path.join(pythonfolder, 'pyscope'))
		file_created(path)

	elif sys.argv[1] == '-remove':
		pass
	else:
		print 'Invalid argument for installation script'

