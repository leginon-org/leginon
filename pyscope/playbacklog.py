#!/usr/bin/env python

import sys
import pyscope.registry

logfilename = sys.argv[1]
classname = sys.argv[2]

inst = pyscope.registry.getClass(classname)()

f = open(logfilename)

for line in f:
	parts = line.split('\t')
	if parts[1] != classname:
		continue
	if parts[2] == '__init__':
		continue
	methodname = parts[2]
	args = eval(parts[3])
	kwargs = eval(parts[4])
	getattr(inst, methodname)(*args, **kwargs)
