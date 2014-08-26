#!/usr/bin/env python

import sys
import pyscope.registry

logfilename = 'methods.log'
classname = 'SimCCDCamera'

# Create the instance, but first turn off logging during playback
# to avoid infinitely growing log file
cls = pyscope.registry.getClass(classname)
cls.logged_methods_on = False
inst = cls()

f = open(logfilename)

for line in f:
	# parse line of tabbed values
	timestamp,caller,base,fname,args,kwargs = line.split('\t')
	if caller != classname:
		continue
	if fname == '__init__':
		continue
	# recreate args
	args = eval(args)
	kwargs = eval(kwargs)
	# call method
	f = getattr(inst, fname)
	print fname, args, kwargs
	f(*args, **kwargs)
raw_input('enter to quit')
