#!/usr/bin/env python

'''
Call a function in an external process.  Kill it if time limit is exceeded.
'''

import sys
import cPickle

def call(module_name, func_name, args=(), kwargs={}, timeout=None):
	import os
	import signal
	import threading

	## make pickle from args
	pickledargs = cPickle.dumps((module_name, func_name, args, kwargs), cPickle.HIGHEST_PROTOCOL)

	## start subprocess, give it input
	import subprocess
	import fileutil
	# launch this script in a subprocess
	executable = fileutil.getMyFilename()
	sub = subprocess.Popen([executable, 'call'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	sub.stdin.write(pickledargs)
	sub.stdin.close()

	## start a kill timer
	if timeout is not None:
		killargs = (sub.pid, signal.SIGKILL)
		killer = threading.Timer(timeout, os.kill, args=killargs)
		killer.start()
	

	newstr = sub.stdout.read()
	result = cPickle.loads(newstr)
	if isinstance(result, Exception):
		raise result

	ret = sub.wait()

	## cancel killer
	if timeout is not None:
		killer.cancel()

	if ret == 0:
		return result
	if ret == -signal.SIGKILL:
		raise RuntimeError('%s ran too long and was killed' % (func_name,))
	else:
		raise RuntimeError('%s had unknown error' % (func_name,))


def import_module(module_name):
	import imp
	dotted_names = module_name.split('.')
	if len(dotted_names) > 2:
		namep = '.'.join(dotted_names[:-1])
		p = import_module('.'.join(dotted_names[:-1]))
	else:
		namep = dotted_names[0]
		f,pathname,desc = imp.find_module(namep)
		try:
			p = imp.load_module(namep, f, pathname, desc)
		finally:
			if f is not None:
				f.close()

	if len(dotted_names) < 2:
		return p

	namem = dotted_names[-1]
	f,pathname,desc = imp.find_module(namem, p.__path__)
	try:
		m = imp.load_module(module_name, f, pathname, desc)
	finally:
		if f is not None:
			f.close()
	return m

def wrapper():
	module_name, func_name, args, kwargs = cPickle.loads(sys.stdin.read())

	# import module, get function
	mod = import_module(module_name)
	func = getattr(mod, func_name)

	# call function, return result as pickle
	try:
		result = func(*args, **kwargs)
	except Exception, e:
		result = e
	pickled_result = cPickle.dumps(result)
	sys.stdout.write(pickled_result)
	sys.stdout.flush()
	sys.stdout.close()
	sys.exit()

def test_caller():
	result = call('os', 'listdir', args=())
	print 'RESULT'
	print result

def main():
	if sys.argv[1] == 'call':
		wrapper()
	elif sys.argv[1] == 'test':
		test_caller()

if __name__ == '__main__':
	main()
