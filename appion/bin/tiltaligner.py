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

class tiltAligner(particleLoop.ParticleLoop):
	#def __init__(self):
	#	raise NotImplementedError()
	
	#####################################################
	##### START PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	#####################################################

	def setProcessingDirName(self):
		self.processdirname = "tiltalign"

	def preLoopFunctions(self):
		if self.params['dbimages']:
			self.processAndSaveAllImages()
		self.app = ApTiltPicker.PickerApp(0)
		self.app.appionloop = self
		#self.app.quit = wx.Button(self.app.frame, wx.ID_FORWARD, '&Forward')

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

	def particleDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		self.params['usepicks'] = False
		self.params['outtype'] = 'pickle'
		self.params['outtypeindex'] = None

	def particleParseParams(self, args):
		"""
		put in any additional parameters to parse
		"""
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			if arg == 'usepicks':
				self.params['usepicks'] = True
			elif elements[0] == 'outtype':
				self.params['outtype'] = elements[1]
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	def particleParamConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		for i,v in enumerate(('text','xml','spider','pickle')):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: text, xml, pickle or spider; NOT "+str(self.params['outtype']))
		return

	def particleCreateOutputDirs(self):
		"""
		put in any additional directories to create
		"""
		self.params['pickdatadir'] = os.path.join(self.params['rundir'],"pickdata")
		self._createDirectory(self.params['pickdatadir'], warning=False)
	
		return

	def processImage(self, imgdata):
		# run it
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is not None:
			self.runTiltAligner(imgdata, tiltdata)

		#parse the data
		#self.parseTiltParams()

	def commitToDatabase(self, imgdata):
		"""
		Over-writes the particleLoop commit and uses the appionLoop commit
		"""
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is not None:
			expid = int(imgdata['session'].dbid)
			if self.params['usepicks'] is True:
				apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
		apTiltPair.insertTiltParams(imgdata, tiltdata, self.tiltparams)

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################

	def parseTiltParams(self):
		theta = self.tiltparams['theta']
		gamma = self.tiltparams['gamma']
		phi   = self.tiltparams['phi']

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
		imgname = imgdata['filename']+".dwn.mrc"
		imgpath = os.path.join(self.params['rundir'],imgname)
		self.app.panel1.openImageFile(imgpath)
		#open tilt file
		tiltname = tiltdata['filename']+".dwn.mrc"
		tiltpath = os.path.join(self.params['rundir'],tiltname)
		self.app.panel2.openImageFile(tiltpath)
		#run the picker
		self.app.MainLoop()
		self.app.panel1.openImageFile(None)
		self.app.panel2.openImageFile(None)
		#tilt data are copied to self.tiltparams by app

		if self.tiltparams:
			print self.tiltparams


if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()



