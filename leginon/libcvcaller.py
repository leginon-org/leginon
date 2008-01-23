#!/usr/bin/env python

import libCVwrapper
import threading
import time
import subprocess
import os
import signal
import sys
import cPickle
## This is a wrapper around PolygonACD
## It will run PolygonACD in a subprocess and kill it if it takes too long
def PolygonACD(regionarray, x, timeout=5):
	## the script to execute in the subprocess is this script
	exe = 'libcvcaller.py'
	## set up input to the subprocess
	rstr = cPickle.dumps(regionarray, cPickle.HIGHEST_PROTOCOL)
	xarg = str(x)

	## start subprocess, give it input
	PIPE = subprocess.PIPE
	print 'exe', exe
	sub = subprocess.Popen([exe, xarg], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	sub.stdin.write(rstr)
	sub.stdin.close()

	## start a kill timer
	killargs = (sub.pid, signal.SIGKILL)
	killer = threading.Timer(timeout, os.kill, args=killargs)
	killer.start()
	
	## wait for subprocess to end
	ret = sub.wait()
	## cancel killer
	killer.cancel()

	print 'ret', ret
	if ret == 0:
		newstr = sub.stdout.read()
		result = cPickle.loads(newstr)
	elif ret == -signal.SIGKILL:
		print 'process ran too long and was killed'
		result = None
	else:
		print 'process exited with error'
		result = None
	return result

def Test(a, value):
	# simulate PolygonACD
	time.sleep(4)
	return [a, value*a]

### this is the external process
if __name__ == '__main__':
	value = float(sys.argv[1])

	astr = sys.stdin.read()
	a = cPickle.loads(astr)

	result = libCVwrapper.PolygonACD(a, value)
	#result = Test(a, value)

	rstr = cPickle.dumps(result, cPickle.HIGHEST_PROTOCOL)
	sys.stdout.write(rstr)
