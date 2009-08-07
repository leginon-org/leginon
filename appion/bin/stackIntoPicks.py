#!/usr/bin/env python

#python
import os
import sys
import math
import time
import shutil
import numpy
#appion
import appionScript
import apStack
import apDisplay
import appionData
import apEMAN
import apStackMeanPlot
from pyami import mem


class StackIntoPicksScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [options]")

		### Ints
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack id", metavar="ID")

	#=====================
	def checkConflicts(self):
		### check and make sure we got the stack id
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("runname was not defined")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		self.params['rundir'] = os.path.join(uppath, "extract", self.params['runname'])

	#=====================
	def getDiamFromSelectionRun(self, selectrundata):
		if selectrundata['params'] is not None:
			return selectrundata['params']['diam']
		elif selectrundata['dogparams'] is not None:
			return selectrundata['dogparams']['diam']
		elif selectrundata['manparams'] is not None:
			return selectrundata['manparams']['diam']
		elif selectrundata['tiltparams'] is not None:
			return selectrundata['tiltparams']['diam']
		return 10

	#=====================
	def start(self):
		### check for existing run
		selectrunq = appionData.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		selectrundata = selectrunq.query(readimages=False)
		if selectrundata:
			apDisplay.printError("Runname already exists")

		### stack data
		stackdata = apStack.getOnlyStackData(self.params['stackid'])

		### stack particles
		stackparts = apStack.getStackParticlesFromId(self.params['stackid'], msg=True)
		### selection run for first particle
		oldselectrun = stackparts[0]['particle']['selectionrun']

		### set selection run
		manualparamsq = appionData.ApManualParamsData()
		manualparamsq['diam'] = self.getDiamFromSelectionRun(oldselectrun)
		manualparamsq['oldselectionrun'] = oldselectrun
		selectrunq = appionData.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['hidden'] = False
		selectrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		selectrunq['session'] = apStack.getSessionDataFromStackId(self.params['stackid'])
		selectrunq['manparams'] = manualparamsq

		### insert particles
		dupfields = ('image', 'xcoord', 'ycoord', 'diameter', 
			'correlation', 'template', 'peakmoment', 'peakstddev', 'peakarea',)
		apDisplay.printMsg("Inserting particles into database")
		count = 0
		t0 = time.time()
		startmem = mem.active()
		numpart = len(stackparts)
		for stackpart in stackparts:
			count += 1
			if count > 10 and count%100 == 0:
				perpart = (time.time()-t0)/float(count+1)
				apDisplay.printColor("part %d of %d :: %.1fM mem :: %s/part :: %s remain"%
					(count, numpart, (mem.active()-startmem)/1024. , apDisplay.timeString(perpart), 
					apDisplay.timeString(perpart*(numpart-count))), "blue")
			oldpartdata = stackpart['particle']
			newpartq = appionData.ApParticleData()
			newpartq['selectionrun'] = selectrunq
			### copy old values
			for field in dupfields:
				newpartq[field] = oldpartdata[field]
			if self.params['commit'] is True:
				newpartq.insert()
		apDisplay.printMsg("Completed in %s"%(apDisplay.timeString(time.time()-t0)))



#=====================
if __name__ == "__main__":
	stackIntoPicks = StackIntoPicksScript()
	stackIntoPicks.start()
	stackIntoPicks.close()

