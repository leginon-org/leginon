#!/usr/bin/env python

import types
import logging
import logging.handlers
import threading

logger = logging.getLogger('method_logger')
logger.setLevel(logging.INFO)
rothandler = logging.handlers.TimedRotatingFileHandler('methods.log', when='h', backupCount=72)
rothandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s\t%(message)s')
rothandler.setFormatter(formatter)
logger.addHandler(rothandler)

## hack to keep track of our recursion level
mylock = threading.RLock()

def logged_method(f, classname, fname):
	def new_f(*args, **kwargs):
		mylock.acquire()
		try:
			if mylock._RLock__count == 1 and args[0].__class__.__name__ == classname and args[0].logged_methods_on:
				message = '%s\t%s\t%s\t%s' % (classname, fname, args[1:], kwargs)
				logger.info(message)
			result = f(*args, **kwargs)
			return result
		finally:
			mylock.release()
	return new_f

class meta_logged(type):
	def __new__(self, classname, bases, classdict):
		# replace all functions in classdict with logged ones
		for fname, f in classdict.items():
			if isinstance(f, types.FunctionType):
				classdict[fname] = logged_method(f, classname, fname)
		return type.__new__(self, classname, bases, classdict)

class LoggedMethodsBase(object):
	__metaclass__ = meta_logged
	logged_methods_on = False

class TestClass(LoggedMethodsBase):
	logged_methods_on = True
	def __init__(self, x):
		self.x = x

	def util(self):
		print 'util', self.x

	def get(self):
		self.util()
		return self.x

	def set(self, value):
		self.x = value
		self.util()

def test():
	a = TestClass(10)
	a.get()
	a.set(5)

if __name__ == '__main__':
	test()
