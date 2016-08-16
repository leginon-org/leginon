#!/usr/bin/env python

import math
import numpy
from appionlib.StackClass import stackTools
from appionlib.StackClass import ProcessStack

extensions = ['.hed', '.hdf', '.mrc']

numpart = 16
boxsize = (128,128)

filelist = []
for ext in extensions:
	filename = "testfile"+ext
	filelist.append(filename)
	print "\nFILENAME: %s"%(filename)
	stackClass = ProcessStack.createStackClass(filename, msg=True)
	stackClass.removeStack(warn=False)

	a = numpy.random.random((numpart, boxsize[0], boxsize[0]))
	a = numpy.array(a, dtype=numpy.float64)

	stackClass.writeParticlesToFile(a)
	print "  getNumberOfParticles", stackClass.getNumberOfParticles()
	print "  getBoxSize", stackClass.getBoxSize()

	b = stackClass.readParticlesFromFile()
	squareError = ((a-b)**2).sum()
	print "+ %s squareError: %.8f"%(ext, squareError)

	average = stackTools.averageStack(filename, msg=False)
	averageError = ((average-0.5)**2).sum()
	print "+ %s averageError: %.8f"%(ext, squareError)

	stackClass.appendParticlesToFile(a)
	b = stackClass.readParticlesFromFile()
	c = b[-numpart:] #only take appended particles
	squareError = ((a-c)**2).sum()
	print "+ %s append squareError: %.8f"%(ext, squareError)

	average = stackTools.averageStack(filename, msg=False)
	averageError = ((average-0.5)**2).sum()
	print "+ %s append averageError: %.8f"%(ext, squareError)


average = stackTools.averageStackList(filelist, msg=False)
averageError = ((average-0.5)**2).sum()
print "\nallstack averageError: %.8f\n"%(squareError)

for filename in filelist:
	stackClass = ProcessStack.createStackClass(filename)
	stackClass.removeStack(warn=True)
