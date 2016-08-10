#!/usr/bin/env python

#python
import os
import sys
import numpy
import scipy.ndimage.interpolation
#appion
from appionlib import apFile
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appionScript
from appionlib import asymmetrical
from appionlib import apImagicFile
#pyami
from pyami import correlator

#======================
#======================
#======================
#======================
class CenterStackClass(apImagicFile.processStack):
	#===============
	def preLoop(self):
		#apStack.averageStack(stack=centerstack)
		#avgarray = XXXXXXX
		#self.transformList = asymmetrical.getEightTransforms(self.boxsize, avgarray)
		self.transformList = asymmetrical.getEightTransforms(self.boxsize)

		self.sigmoidImage = asymmetrical.sigmoidImage(self.boxsize)
		self.stacksToMerge = []

	#===============
	def processStack(self, stackarray):
		tempstackfile = "temp.%03d.hed"%(self.index)
		self.stacksToMerge.append(tempstackfile)
		#flipping so particles are unchanged
		centeredStack = []
		for partarray in stackarray:
			self.index += 1 #you must have this line in your loop
			if self.index % 100 == 0:
				sys.stderr.write(".")
			newpart = self.processParticle(partarray)
			centeredStack.append(newpart)
		apFile.removeStack(tempstackfile, warn=self.msg)
		apImagicFile.writeImagic(centeredStack, tempstackfile, msg=self.msg)

	#===============
	def processParticle(self, partarray):
		correlations = []
		for transarray in self.transformList:
			rawcorr = correlator.cross_correlate(partarray, transarray)
			rawcorr = numpy.fft.fftshift(rawcorr)
			finalcorr = rawcorr*self.sigmoidImage
			correlations.append(finalcorr)
		corrarray = numpy.array(correlations)
		peakindex = numpy.argmax(corrarray)
		peakcoordinate = numpy.unravel_index(peakindex, corrarray.shape)  #rot, xshift, yshift
		newpart = self.transformParticle(partarray, peakcoordinate)
		return newpart

	#===============
	def transformParticle(self, partarray, peakcoordinate):
		tnum = peakcoordinate[0]
		xshift = self.boxsize/2 - peakcoordinate[1]
		yshift = self.boxsize/2 - peakcoordinate[2]
		newpart = asymmetrical.transformFromNumber(partarray, tnum)
		newpart = scipy.ndimage.interpolation.shift(newpart, (xshift, yshift), order=0)
		#newpart = numpy.roll(newpart, newpart.shape[0]*yshift)
		return newpart

	#===============
	def writeStack(self, outfile):
		apImagicFile.mergeStacks(self.stacksToMerge, outfile, self.msg)
		for tempstackfile in self.stacksToMerge:
			apFile.removeStack(tempstackfile, warn=self.msg)
		return outfile

class centerStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-i", "--num-iter", dest="numiter", type="int",
			help="Number of iterations", default=2, metavar="#")
		self.parser.add_option("--new-stack-name", dest="runname",
			help="New stack name", metavar="STR")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		# add mask & maxshift to rundir if specifie
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		originalstackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstackfilename = "center.hed"
		centerstack = os.path.join(self.params['rundir'], newstackfilename)

		laststackfile = originalstackfile
		for i in range(self.params['numiter']):
			centerstack = os.path.join(self.params['rundir'], "iter%d.hed"%(i))
			centerClass = CenterStackClass()
			centerClass.start(originalstackfile)
			centerClass.writeStack(centerstack)
			laststackfile = centerstack

		self.params['keepfile'] = "keepfile.lst"
		f = open(self.params['keepfile'], "w")
		for i in range(centerClass.numpart):
			f.write("%d\n"%(i))
		f.close()

		if not os.path.isfile(centerstack):
			apDisplay.printError("No stack was created")

		self.params['description'] += (
			(" ... appion centered substack id %d"
			% (self.params['stackid']))
		)
		
		apStack.commitSubStack(self.params, newname=newstackfilename, centered=True)
		apStack.averageStack(stack=centerstack)

#=====================
if __name__ == "__main__":
	cenStack = centerStackScript()
	cenStack.start()
	cenStack.close()

