#!/usr/bin/env python
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

	def launchCall(self, launchtype, targetcall, lock, args=(), kwargs={}):
		self.lock = lock
		launchtypes = ('thread', 'fork', 'pipe')
		if launchtype not in launchtypes:
			raise ValueError("allowed launchtypes %s" % launchtypes)
		if not callable(targetcall):
			raise TypeError('targetcall %s must be callable object' % (targetcall,))

		if launchtype == 'thread':
			c = self.newCallThread(targetcall, args, kwargs)
		elif launchtype == 'pipe':
			c = self.newCallPipe(targetcall, args, kwargs)
		elif launchtype == 'fork':
			c = self.newCallFork(targetcall, args, kwargs)

		callinfo = {}
		callinfo['type'] = launchtype
		callinfo['handle'] = c
		self.calls.append(callinfo)
		#print 'CALLINFO', callinfo
	
	def newCallThread(self, targetcall, args=(), kwargs={}):
		"""
		make a call to targetcall in a new thread
		"""
		#t = threading.Thread(name='%s node thread' % targetcall.__name__, target=targetcall, args=args, kwargs=kwargs)
		wrapperargs = (targetcall, args, kwargs)
		t = threading.Thread(name='%s node thread' % targetcall.__name__, target=self.callableWrapper, args=wrapperargs)
		t.setDaemon(1)
		t.start()
		return t

	def callableWrapper(self, callable, args=(), kwargs={}):
		'''
		the callable is responsible for releasign the launchlock
		but if it doesn't because of an exception, this will release it
		'''
		try:
			apply(callable, args, kwargs)
		except Exception, detail:
			print '***** exception while calling %s: %s' % (callable,detail)
			try:
				self.lock.release()
			except:
				pass

	def newCallFork(self, targetcall, args=(), kwargs={}):
		"""
		make a call to targetcall in a forked process
		(unix only)
		"""
		pid = os.fork()
		if pid:
			#print 'THIS IS PARENT PROCESS, child is %s' % (pid,)
			return pid
		else:
			#print 'THIS IS CHILD PROCESS'
			#print 'applying targetcall'
			apply(targetcall, args, kwargs)
			#print 'apply returned'
			#sys.exit()
	
	def newCallPipe(self, targetcall, args=(), kwargs={}):
		"""
		A failed attempt at an alternative to the fork method
		make a call to targetcall in a popen process
		(can't figure out how to close the pipe without killing
		the new process)
		"""
		targetinfo = {}
		targetinfo['targetcall'] = targetcall
		targetinfo['args'] = args
		targetinfo['kwargs'] = kwargs

		print 'opening pipe'
		wpipe = os.popen(self.procname, 'w')
		print 'dumping pickle'
		cPickle.dump(targetinfo, wpipe, 1)
		print 'closing'
		#wpipe.close()
		print 'closed'
		## need to figure out pid of new process
		newpid = None
		return newpid

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

