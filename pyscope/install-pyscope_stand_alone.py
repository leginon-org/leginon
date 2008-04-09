import os
import sys

if sys.platform != 'win32':
	sys.exit()


if __name__ == '__main__':

	try:
		import pyScope.updatecom
		pyScope.updatecom.run()
	except:
		print 'Failed to update COM'

	try:
		import pyScope.tietzping
		pyScope.tietzping.register()
	except:
		print 'Failed to register pyScope.Ping'


