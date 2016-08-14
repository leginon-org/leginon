#!/usr/bin/env python

import math
import numpy
from appionlib.StackClass import stackTools
from appionlib.StackClass import ProcessStack

extensions = ['.hed', '.hdf', '.mrc']

filelist = []
for ext in extensions:
	filename = "testfile"+ext
	filelist.append(filename)
	print "\nFILENAME: %s"%(filename)
	stackClass = ProcessStack.createStackClass(filename, msg=True)
	stackClass.removeStack(warn=False)
	# 4 particles with box 128x128
	a = numpy.random.random((4, 128, 128))
	a = numpy.array(a, dtype=numpy.float64)
	stackClass.writeParticlesToFile(a)
	print "getNumberOfParticles", stackClass.getNumberOfParticles()
	b = stackClass.readParticlesFromFile()
	#print b.shape
	#print b
	squareError = ((a-b)**2).sum()
	print "%s squareError: %.8f"%(ext, squareError)
	average = stackTools.averageStack(filename, msg=False)
	averageError = ((average-0.5)**2).sum()
	print "%s averageError: %.8f"%(ext, squareError)

average = stackTools.averageStackList(filelist, msg=False)
averageError = ((average-0.5)**2).sum()
print "\nallstack averageError: %.8f\n"%(squareError)

for filename in filelist:
	stackClass = ProcessStack.createStackClass(filename)
	stackClass.removeStack(warn=True)
