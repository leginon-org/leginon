#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import os
import socket
import sys

class LeginonObject(object):
	'''Generic base class for objects. Defines ID and location.'''
	def location(self):
		'''Returns a dict describing the location of this object.'''
		loc = {}
		loc['hostname'] = socket.gethostname().lower()
		return loc

	def printerror(self, errorstring, color=None):
		'''Format error output with color and identifcation. Print to stdout.'''
		# there is better way, but since ANSI colors hurt my eyes
		# I don't know if we'll keep them
		if self.__class__.__name__ == 'Manager':
			color = 41
		elif self.__class__.__name__ == 'Launcher':
			color = 44
		elif self.__class__.__base__.__name__ == 'Node':
			color = 42
		else:
			color = 45

		if sys.platform == 'win32':
			color = None

		printstring = ''
		if color is not None:
			printstring += '\033[%sm' % color	
		if self.__module__ != '__main__':
			printstring += self.__module__ + '.'
		printstring += self.__class__.__name__
		printstring += ': '
		printstring += errorstring
		if color is not None:
			printstring += '\033[0m'
		print printstring

	def printException(self):
		excinfo = sys.exc_info()
		sys.excepthook(*excinfo)

