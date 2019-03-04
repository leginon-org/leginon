#!/usr/bin/env python

import os
from appionlib import apDisplay
from appionlib import apParticle
from appionlib import filterLoop
from appionlib import appionScript

#=====================
#=====================
class TopazPicker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):

		### Session Info
		### session id and preset id can be obtained from the selection id
		#self.parser.add_option("--sessionid", dest="sessionid", type="int",
		#	help="the session code, e.g., '21sep21a' ", metavar="#")
		#self.parser.add_option("--presetid", dest="presetid", type="int",
		#	help="the preset id, e.g., 'enn' ", metavar="#")
		self.parser.add_option("-S", "--selection-id", dest="selectionid", type="int",
			help="the particle selection id", metavar="#")

		### Topaz Parameters
		self.parser.add_option("--num-images", dest="numimages", type="int", default=30,
			help="Number of micrographs to use for training purposes", metavar="#")
		self.parser.add_option("--threshold", dest="threshold", type="float", default=0.01,
			help="Threshold for particle cutoff, higher number -> less particles", metavar="#")
		
		### True/False flags
		self.parser.add_option("--do-it", dest="doit", default=True,
			action="store_true", help="Do it")
		self.parser.add_option("--do-not-do-it", dest="doit", default=True,
			action="store_false", help="Do not do it")

		### Image Filters (copied from filterLoop.y)
		self.parser.add_option("--lowpass", "--lp", "--lpval", dest="lowpass", type="float",
			help="Low pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--highpass", "--hp", "--hpval", dest="highpass", type="float",
			help="High pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--median", "--medianval", dest="median", type="int",
			help="Median filter radius in Pixels", metavar="INT")
		self.parser.add_option("--pixlimit", dest="pixlimit", type="float",
			help="Limit pixel values to within <pixlimit> standard deviations", metavar="FLOAT")
		self.parser.add_option("--bin","--binval", "--shrink", "--binby", dest="bin", type="int", default=4,
			help="Bin the image", metavar="INT")
		### True/False Image Filter options
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert image density before processing")
		self.parser.add_option("--planereg", dest="planereg", default=False,
			action="store_true", help="Fit a 2d plane regression to the data and subtract")
		self.parser.add_option("--keepall", dest="keepall", default=False,
			action="store_true", help="Do not delete .dwn.mrc files when finishing")

	#=====================
	def checkConflicts(self):
		if self.params['selectionid'] is None:
			apDisplay.printError("Please provide a particle selection id, e.g. --selection-id=15")
		self.particledata = apParticle.getOneParticleFromSelectionId(self.params['selectionid'])
		#print(self.particledata.keys())
		#print(self.particledata['image'].keys())
		self.sessiondata = self.particledata['image']['session']
		self.params['sessionname'] = self.sessiondata['name']
		print("Session Name: %s"%(self.params['sessionname']))
		self.presetdata = self.particledata['image']['preset']
		self.params['preset'] = self.presetdata['name']
		print("Preset Name:  %s"%(self.params['preset']))

	#=====================
	def setRunDir(self):
		if self.params['rundir'] is None:
			if self.sessiondata is not None:
				self.params['rundir'] = self.getDefaultBaseAppionDir(self.sessiondata, [self.processdirname, self.params['runname']])

		self.params['outdir'] = self.params['rundir']

	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		self.processdirname = "topazpicker"
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
		apDisplay.printMsg("\n\n")
		### get info about the stack
		apDisplay.printMsg("Information about particle selection id %d"%(self.params['selectionid']))
		filterloop = MiniFilterLoop()
		filterloop.params = self.params
		filterloop.params['limit'] = self.params['numimages']
		
		filterloop.run()

#=====================
#=====================
#=====================
class MiniFilterLoop(filterLoop.FilterLoop):
	def setupParserOptions(self):
		return
	def checkConflicts(self):
		return
	def commitToDatabase(self):
		return
	def setupGlobalParserOptions(self):
		#Neil hack, not recommended
		return
	def setParams(self,optargs,useglobalparams=True):
		#Neil hack, not recommended
		return
	def checkGlobalConflicts(self):
		#Neil hack, not recommended
		return
	def processImage(self, imgdict, filtarray):
		from pyami import mrc
		mrc.write(filtarray, apDisplay.short(imgdict['filename'])+"_sm.mrc")

#=====================
#=====================
if __name__ == '__main__':
	topazpicker = TopazPicker()
	topazpicker.start()
	topazpicker.close()

