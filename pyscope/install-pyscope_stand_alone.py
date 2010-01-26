import os
import sys

if sys.platform != 'win32':
	sys.exit()


if __name__ == '__main__':

	try:
		import pyscope.updatecom
		pyscope.updatecom.run()
	except:
		print 'Failed to update COM'

	try:
		import pyscope.tietzping
		pyscope.tietzping.register()
	except:
		print 'Failed to register pyscope.Ping'


