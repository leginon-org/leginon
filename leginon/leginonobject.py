import os, socket
import random
#import threading, weakref

class LeginonObject(object):
	def __init__(self, id):
		self.id = id
		self.idcounter = 0

	def location(self):
		'return a dict describing the location of this object'
		loc = {}
		loc['hostname'] = socket.gethostname()
		loc['PID'] = os.getpid()
		loc['python ID'] = id(self)
		#loc['thread'] = threading.currentThread()
		#loc['weakref'] = weakref.ref(self)
		return loc

	def print_location(self):
		loc = self.location()
		print '     Leginon Object: %s' % (self.id,)
		for key,value in loc.items():
			print '         %-25s  %s' % (key,value)

	def ID(self):
		newid = self.id + (self.idcounter,)
		self.idcounter += 1
		return newid

	def printerror(self, errorstring, color=None):

		if self.__class__.__name__ == 'Manager':
			color = 41
		elif self.__class__.__name__ == 'Launcher':
			color = 44
		elif self.__class__.__base__.__name__ == 'Node':
			color = 42
		else:
			color = 45

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

