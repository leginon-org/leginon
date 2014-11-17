#!/usr/bin/env python

#python
import os
import sys
import math
import time
import shutil
import numpy
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apEMAN
from appionlib import apStackMeanPlot
from appionlib import apDDprocess
from appionlib import apDatabase
from pyami import mem


class StackIntoPicksScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [options]")

		### Ints
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack id", metavar="ID")
		self.parser.add_option("--ddstack", dest="ddstack", type="int",
			help="ID for ddstack run to make aligned ddstack(required)", metavar="INT")

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

	def chooseValidResultImageInDDAlignPairs(self, alldata):
		'''
		Return the first non-rejected result image
		'''
		if not alldata:
			# no data
			return False
		for pairdata in alldata:
			if apDatabase.getImgCompleteStatus(pairdata['result']) is False:
				# bad status
				continue
			# good status
			return pairdata['result']
		# no data with valid image status
		return False

	def getNewImageFromDDStack(self,imagedata):
		'''
		Returns aligned image for the specified ddstack according to
		the image input.  The input may be another aligned image or
		a source image in the alignpair
		'''
		# This has the side effect of resetting ddstackrun in self.dd
		# However getAlignImagePairData has specific input for it.
		self.dd.setImageData(imagedata)
		alignpairdata = self.dd.getAlignImagePairData(None,query_source=not self.dd.getIsAligned())
		if alignpairdata is False:
			apDisplay.printWarning('Image not used for nor a result of alignment.  Will not transfer pick')
			return False
		# search for aligned image from source and specific ddstackrun
		source_image = alignpairdata['source']
		self.dd.setImageData(source_image)
		allpairs = self.dd.getAllAlignImagePairData(self.newddstackrun,query_source=True)
		newalignedimagedata = self.chooseValidResultImageInDDAlignPairs(allpairs)
		# repeat without specifying the ddstack
		# This is required due to possibility of new ddstack runs that need
		# to continue from an archived runs due to failure in the middle
		# This assumes that the most recent aligned image  is the one to use.
		if newalignedimagedata is False:
			if source_image.dbid not in self.other_ddstack_used:
				apDisplay.printWarning('Matched aligned image not found for %s in specified ddstack %s.  Searching in all ddstacks' % (source_image['filename'],self.newddstackrun['runname']))
			allpairs = self.dd.getAllAlignImagePairData(None,query_source=True)
			newalignedimagedata = self.chooseValidResultImageInDDAlignPairs(allpairs)
			self.other_ddstack_used.append(source_image.dbid)
			# set ddstack run back
			self.dd.setDDStackRun(self.newddstackrun)
		if newalignedimagedata is False:
			apDisplay.printWarning('Matched aligned image not found in ddstack.  Will not transfer pick')
			return False
		return newalignedimagedata

	#=====================
	def start(self):
		### check for existing run
		selectrunq = appiondata.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		selectrundata = selectrunq.query(readimages=False)
		if selectrundata:
			apDisplay.printError("Runname already exists")

		if self.params['ddstack']:
			self.other_ddstack_used = []
			self.dd = apDDprocess.DDStackProcessing()
			self.dd.setDDStackRun(self.params['ddstack'])
			self.newddstackrun = self.dd.getDDStackRun(show_msg=True)
		### stack data
		stackdata = apStack.getOnlyStackData(self.params['stackid'])

		### stack particles
		stackparts = apStack.getStackParticlesFromId(self.params['stackid'], msg=True)
		stackparts.reverse()

		### selection run for first particle
		oldselectrun = stackparts[0]['particle']['selectionrun']

		### set selection run
		manualparamsq = appiondata.ApManualParamsData()
		manualparamsq['diam'] = self.getDiamFromSelectionRun(oldselectrun)
		manualparamsq['oldselectionrun'] = oldselectrun
		manualparamsq['trace'] = False
		selectrunq = appiondata.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['hidden'] = False
		selectrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		selectrunq['session'] = apStack.getSessionDataFromStackId(self.params['stackid'])
		selectrunq['manparams'] = manualparamsq

		### insert particles
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
			newpartq = appiondata.ApParticleData(initializer=oldpartdata)
			newpartq['selectionrun'] = selectrunq
			if self.params['ddstack']:
				newimagedata = self.getNewImageFromDDStack(oldpartdata['image'])
				if newimagedata is False:
					# no pick transferred
					continue
				newpartq['image'] = newimagedata
			if self.params['commit'] is True:
				newpartq.insert()
		apDisplay.printMsg("Completed in %s"%(apDisplay.timeString(time.time()-t0)))



#=====================
if __name__ == "__main__":
	stackIntoPicks = StackIntoPicksScript()
	stackIntoPicks.start()
	stackIntoPicks.close()


