#!/usr/bin/python -O

import os
import sys
import particleLoop
import apImage
import subprocess
import apFindEM
import appionData
import apParticle
import apDatabase
import apDisplay
import time
import wx
import pyami
import numpy
import ApTiltPicker

##################################
##
##################################

class manualPicker(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "tiltalign"

	def preLoopFunctions(self):
		if self.params['dbimages']:
			self.processAndSaveAllImages()
		self.app = ApTiltPicker.PickerApp(0)
		self.app.appionloop = self

	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	def processImage(self, imgdata):
		if not self.params['dbimages']:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
		self.runTiltAligner(imgdata)

	def commitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		#self.insertTiltAlignParams(expid)
		return

	def specialParseParams(self, args):
		"""
		put in any additional parameters to parse
		"""
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	def specialDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		return

	def specialParamConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		return

	def specialCreateOutputDirs(self):
		"""
		put in any additional directories to create
		"""
		return	

	##### END PRE-DEFINED APPION LOOP FUNCTIONS #####

	def processAndSaveAllImages(self):
		print "Pre-processing images before picking"
		for imgdata in self.imgtree:
			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if os.path.isfile(imgpath):
				print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				apFindEM.processAndSaveImage(imgdata, params=self.params)

	def insertTiltAlignParams(self, expid):
		tiltparamsq=appionData.ApTiltParamsData()
		tiltparamsq['diam']    = self.params['diam']
		tiltparamsq['lp_filt'] = self.params['lp']
		tiltparamsq['hp_filt'] = self.params['hp']
		tiltparamsq['bin']     = self.params['bin']
		tiltparamsdata = self.appiondb.query(tiltparamsq, results=1)
		
		runq=appionData.ApSelectionRunData()
		runq['name'] = self.params['runid']
		runq['dbemdata|SessionData|session'] = expid
		runids = self.appiondb.query(runq, results=1)
		
		if not runids:
			runq['tiltparams']=tiltparamsq
			self.appiondb.insert(runq)
		else:
			#make sure all params are the same as previous session
			for pkey in tiltparamsq:
				if tiltparamsq[pkey] != tiltparamsdata[0][pkey]:
					print "All parameters for a particular manualpicker run must be identical"
					print pkey,tiltparamsq[pkey],"not equal to",tiltparamsdata[0][pkey]
					sys.exit()
			for i in tiltparamsq:
				if tiltparamsdata[0][i] != tiltparamsq[i]:
					apDisplay.printError("All parameters for a particular manualpicker run must be identical\n"+
						str(i)+":"+str(tiltparamsq[i])+" not equal to "+str(tiltparamsdata[0][i]))
		return

	def runTiltAligner(self, imgdata):
		#reset targets
		self.app.panel.setTargets('Select Particles', [])
		self.targets = []
		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		self.app.panel1.openImageFile(imgpath)
		#run the picker
		self.app.MainLoop()
		self.app.panel1.openImageFile(None)
		self.app.panel2.openImageFile(None)
		#targets are copied to self.targets by app
		#parse and return the targets in peaktree form


if __name__ == '__main__':
	imgLoop = manualPicker()
	imgLoop.run()



