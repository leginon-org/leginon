#!/usr/bin/env python

import os
import time
import numpy
from pyami import mrc
from appionlib import apDisplay
from appionlib.StackClass import ProcessStack
from appionlib import apRelion

########################################
########################################
########################################
def numImagesInStack(filename):
	stackClass = ProcessStack.createStackClass(filename)
	return stackClass.numpart

########################################
########################################
########################################
#===============
def averageStack(stackfile="start.hed", outfile="average.mrc", partlist=None, msg=True):
	"""
	partlist starts at 1
	"""
	if msg is True:
		apDisplay.printMsg("averaging stack for summary web page")
	stackfile = os.path.abspath(stackfile)
	if not os.path.isfile(stackfile):
		apDisplay.printWarning("could not create stack average, average.mrc")
		return False
	avgStack = AverageStack(msg)
	# check if a star file
	if os.path.splitext(stackfile)[1]==".star":
		mrcfiles = apRelion.getMrcParticleFilesFromStar(stackfile)
		count=0
		for mrcfile in mrcfiles:
			avgStack.start(mrcfile)
			try:
				sum += avgStack.summed
			except:
				sum = avgStack.summed
			count += avgStack.index
		average = sum / count
		if outfile is not None:
			avgmrc = os.path.join(os.path.dirname(stackfile), outfile)
			mrc.write(average,avgmrc)
		return average
	# otherwise just one file to average
	else:
		avgStack.start(stackfile, partlist)
		if outfile is not None:
			avgmrc = os.path.join(os.path.dirname(stackfile), outfile)
			avgStack.save(avgmrc)
		avgstack = avgStack.getdata()
		return avgstack

#=======================
class AverageStack(ProcessStack.ProcessStack):
	#===============
	def preLoop(self):
		self.summed = numpy.zeros((self.boxsize,self.boxsize))
		#override self.partlist to get a subset
		self.count = 0

	#===============
	def processStack(self, stackarray):
		if isinstance(stackarray, list):
			stackarray = numpy.array(stackarray)
		self.index += stackarray.shape[0]
		self.summed += stackarray.sum(0)

	#===============
	def save(self, avgfile):
		#normalize
		self.average = self.summed / self.index
		#report
		mean = self.average.mean()
		std = self.average.std()
		apDisplay.printMsg("mean/std pixel value of average.mrc %.8f +/- %.8f"%(mean, std))
		#save
		mrc.write(self.average, avgfile)

	#===============
	def getdata(self):
		return self.average/self.index

########################################
########################################
########################################
if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		stackfile = sys.argv[1]
		averageStack(stackfile, 'average.mrc')
	else:
		stackfile = 'stackfile.mrc'
		if not os.path.isfile(stackfile):
			print "creating huge stack"
			shape = (10,256,256)
			a = numpy.random.random(shape)
			mrc.write(a, stackfile)
			for i in range(1000):
				sys.stderr.write(".")
				a = numpy.random.random(shape)
				mrc.append(a, stackfile)
				time.sleep(0.001)
			print "done"
		averageStack(stackfile, 'average.mrc')
