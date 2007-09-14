#!/usr/bin/python -O

import os
import sys
import time
import wx
import appionLoop
import particleLoop
import apFindEM
import appionData
import apDatabase
import apDisplay
import ApTiltPicker
import apTiltTransform
import apTiltPair

##################################
##
##################################

class tiltAligner(appionLoop.AppionLoop):
	#def __init__(self):
	#	raise NotImplementedError()
	
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
			if (elements[0]=='lp'):
				self.params['lp']= float(elements[1])
			elif (elements[0]=='hp'):
				self.params['hp']= float(elements[1])
			elif (elements[0]=='invert'):
				self.params['invert']=True
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif (elements[0]=='median'):
				self.params['median']=int(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	def specialDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		self.params['lp']=0.0
		self.params['hp']=600.0
		self.params['invert']=False
		self.params['median']=0
		self.params['bin']=4
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


	def processImage(self, imgdata):
		tiltdata = apTiltPair.getTiltPair(imgdata)
		self.runTiltAligner(imgdata, tiltdata)

	##### END PRE-DEFINED APPION LOOP FUNCTIONS #####

	def processAndSaveAllImages(self):
		print "Pre-processing images before picking"
		for imgdata in self.imgtree:
			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if os.path.isfile(imgpath):
				print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				apFindEM.processAndSaveImage(imgdata, params=self.params)
			tiltdata = apTiltPair.getTiltPair(imgdata)
			if tiltdata is None:
				continue
			tiltpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
			if os.path.isfile(tiltpath):
				print "already processed: ",apDisplay.short(tiltdata['filename'])
			else:
				apFindEM.processAndSaveImage(tiltdata, params=self.params)

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
					sys.exit(1)
			for i in tiltparamsq:
				if tiltparamsdata[0][i] != tiltparamsq[i]:
					apDisplay.printError("All parameters for a particular manualpicker run must be identical\n"+
						str(i)+":"+str(tiltparamsq[i])+" not equal to "+str(tiltparamsdata[0][i]))
		return

	def runTiltAligner(self, imgdata, tiltdata):
		#reset targets
		self.app.onClearPicks(None)
		self.app.onResetParams(None)
		self.tiltparams = {}
		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		self.app.panel1.openImageFile(imgpath)
		#open tilt file
		tiltname = tiltdata['filename']+'.dwn.mrc'
		tiltpath = os.path.join(self.params['rundir'],tiltname)
		self.app.panel2.openImageFile(tiltpath)
		#run the picker
		self.app.MainLoop()
		self.app.panel1.openImageFile(None)
		self.app.panel2.openImageFile(None)
		#tilt data are copied to self.tiltparams by app
		#parse and return the targets in peaktree form
		if self.tiltparams:
			print self.tiltparams


if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()



