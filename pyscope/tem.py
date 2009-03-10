# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyScope/tem.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2005-03-29 22:33:48 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import time
import threading

class TEM(object):
	name = None
	def __init__(self):
		self.idletimers = {}

	def getSystemTime(self):
		return time.time()

	def __getattr__(self, name):
		self.resetIdleTimers()
		#object.__getattr__(self, name)

	def registerIdleTimer(self, name, interval, function, args=(), kwargs={}):
		timer_args = (interval, function, args, kwargs)
		self.ideltimers[name] = {}
		self.idletimers[name]['args'] = timer_args
		self.idletimers[name]['timer'] = None
		self.initIdleTimer(name)

	def initIdleTimer(self, name):
		if self.ideltimers[name]['timer'] is not None:
			self.idletimers[name]['timer'].cancel()
		timer_args = self.idletimers[name]['args']
		timer = threading.Timer(*timer_args)
		self.idletimers[name]['timer'] = timer
		timer.start()

	def resetIdleTimers(self):
		for name in self.idletimers.keys():
			self.initIdleTimer(name)
