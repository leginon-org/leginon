#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

"""
This module serves two puposes:
        - provides the class CallLauncher
        - acts as an executable process which can be launched by a 
          CallLauncher instance
A CallLauncher instance has a method launchCall which is used to launch a
call to any callable python object either in a new thread or a new process
"""

import os, sys, threading, cPickle

class CallLauncher(object):
	def __init__(self, slave=0):
		self.calls = []
		if slave:
			self.acceptCall()
		else:
			self.procname = __file__

	def launchCall(self, targetcall, args=(), kwargs={}):
		if not callable(targetcall):
			raise TypeError('targetcall %s must be callable object' % (targetcall,))

		c = self.newCallThread(targetcall, args, kwargs)

		callinfo = {}
		callinfo['handle'] = c
		self.calls.append(callinfo)
		#print 'CALLINFO', callinfo
	
	def newCallThread(self, targetcall, args=(), kwargs={}):
		"""
		make a call to targetcall in a new thread
		"""
		t = threading.Thread(name='%s node thread' % targetcall.__name__,
													target=targetcall, args=args, kwargs=kwargs)
		t.setDaemon(1)
		t.start()
		return t

	def acceptCall(self):
		"""
		used by a new process to get the target call from the 
		parent process
		"""
		targetinfo = cPickle.load(sys.stdin)
		sys.stdin.close()
		targetcall = targetinfo['targetcall']
		args = targetinfo['args']
		kwargs = targetinfo['kwargs']
		#apply(targetcall, args, kwargs)
		self.newCallThread(targetcall, args, kwargs)


if __name__ == '__main__':
	c = CallLauncher(slave=1)

