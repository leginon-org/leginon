import os, socket
import random
#import threading, weakref
import sys
import copy

class LeginonObject(object):
	'''Generic base class for objects. Defines ID and location.'''
	def __init__(self, id):
		self.id = id
		self.idcounter = 0

	def location(self):
		'''Returns a dict describing the location of this object.'''
		loc = {}
		loc['hostname'] = socket.gethostname()
		loc['PID'] = os.getpid()
		loc['python ID'] = id(self)
		#loc['thread'] = threading.currentThread()
		#loc['weakref'] = weakref.ref(self)
		return loc

	def print_location(self):
		'''Output the location this object to stdout.'''
		loc = self.location()
		print '     Leginon Object: %s' % (self.id,)
		for key,value in loc.items():
			print '         %-25s  %s' % (key,value)

	def ID(self):
		'''Generate a new ID for a child object.'''
		newid = self.id + (self.idcounter,)
		self.idcounter += 1
		return newid

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

		# hurray for spagetti code
		if sys.platform == 'win32':
			color = None

		printstring = ''
		if color is not None:
			printstring += '\033[%sm' % color	
		if self.__module__ != '__main__':
			printstring += self.__module__ + '.'
		printstring += self.__class__.__name__
		try:
			printstring += ' ' + str(self.id)
		except AttributeError:
			printstring += ' (ID unknown)'
		printstring += ': '
		printstring += errorstring
		if color is not None:
			printstring += '\033[0m'
		print printstring

	def printException(self):
		excinfo = sys.exc_info()
		sys.excepthook(*excinfo)

	def checkPythonVersion(self):
		message = '''
		XXXXXXXXXXXXXXXXXX X X X  WARNING  X X X XXXXXXXXXXXXXXXXXX
		You are not using Python 2.2.2!  deepcopy at your own risk!
		XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
		'''
		vinfo = sys.version_info

		if vinfo[0] == 2 and vinfo[1] == 2 and vinfo[2] >=2:
			pass
		else:
			self.printerror(message)
