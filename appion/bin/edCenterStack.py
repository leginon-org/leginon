#!/usr/bin/env python

#python
import os
import numpy
from scipy import ndimage
#appion
import appionScript
import apStack
import apDisplay
import apEMAN
from pyami import correlator, peakfinder

class centerStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-x", "--maxshift", dest="maxshift", type="int",
			help="Maximum shift")

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
		if self.params['mask'] is not None:
			self.params['runname'] = self.params['runname']+"_"+str(self.params['mask'])
		if self.params['maxshift'] is not None:
			self.params['runname'] = self.params['runname']+"_"+str(self.params['maxshift'])
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])
		
	#=====================
	def centerParticles(self, oldstack, centerstack, badstack)
		maxshift = self.params['maxshift']
		centerparts = []
		badparts = []
		keeplist = []
		i = 0
		while partnum < numparts:
			### if need more particles
				### read 4000 parts from oldstack
				### write centerparts to centerstack
				### write badparts to badstack

			### set current image
			oldpart = oldparts[i]

			### mirror about x
			xmirror = numpy.flipud(oldpart)
			### cross-correlate
			xcc = correlator.cross_correlate(oldpart, xmirror)
			### find peak
			peakdict = peakfinder.findSubpixelPeak(xcc)
			xpeak = correlator.wrap_coord(peakdict['pixel peak'], xcc.shape)

			### mirror about y
			ymirror = numpy.fliplr(oldpart)
			### cross-correlate
			ycc = correlator.cross_correlate(oldpart, ymirror)
			### find peak
			peakdict = peakfinder.findSubpixelPeak(ycc)
			ypeak = correlator.wrap_coord(peakdict['pixel peak'], ycc.shape)

			### mirror about y then x
			xymirror = numpy.flipud(ymirror)
			### cross-correlate
			xycc = correlator.cross_correlate(oldpart, xymirror)
			### find peak
			peakdict = peakfinder.findSubpixelPeak(xycc)
			xypeak = correlator.wrap_coord(peakdict['pixel peak'], xycc.shape)

			### do some math to get shift

			### shift particle, by integers only
			if xshift < maxshift and yshift < maxshift:
				xyshift = (xshift, yshift)
				centerpart = ndimage.shift(oldpart, shift=xyshift, mode='wrap', order=0)
				centerparts.append(centerpart)
				keeplist.append(partnum)
			else:
				badparts.append(oldpart)		
		return keeplist

	#=====================
	def start(self):
		### new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

		### checks
		centerstack = os.path.join(self.params['rundir'], 'align.img')
		badstack = os.path.join(self.params['rundir'], 'bad.img')
		apStack.checkForPreviousStack(centerstack)

		### run centering algorithm
		keeplist = self.centerParticles(oldstack, centerstack, badstack)
		if not os.path.isfile(centerstack):
			apDisplay.printError("No stack was created")

		self.params['keepfile'] = os.path.join(self.params['rundir'], 'keepfile.txt')

		### get number of particles
		self.params['description'] += (
			(" ... %d eman centered substack id %d" 
			% (numparticles, self.params['stackid']))
		)
		
		apStack.commitSubStack(self.params, newname=os.path.basename(centerstack), centered=True)
		apStack.averageStack(stack=centerstack)
		if os.path.isfile(badstack):
			apStack.averageStack(stack=badstack, outfile='badaverage.mrc')

#=====================
if __name__ == "__main__":
	cenStack = centerStackScript()
	cenStack.start()
	cenStack.close()

