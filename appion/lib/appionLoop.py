#!/usr/bin/env python

import data
import dbdatakeeper
import imagefun
import time
import sys

db = dbdatakeeper.DBDataKeeper()

class AppionLoop(object):
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		"""
		self.images = None
		self.functionname = sys.argv[0]

		### setup default params: output directory, etc.
		params = self.createDefaultParams()

		### setup default stats: timing variables, etc.
		stats = self.createDefaultStats()

		### parse command line options: diam, apix, etc.
		self.parseCommandLineInput(sys.argv,params)

		### check for conflicts in params
		self.checkParamConflicts(params)

		### get images from database
		images = self.getAllImages(stats,params)

		### create output directories
		self.createOutputDirs(params)

		### write log of command line options
		self.writeFunctionLogs(args,file=params['function']+".log")
		self.writeFunctionLogs(sys.argv,params=params)

		### read/create dictionary to keep track of processed images
		donedict = self.readDoneDict(params)

		return (images,stats,params,donedict)

	def loop(self):
		notdone=True
		while notdone:
			for img in self.images:
				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if( self.startLoop(img, donedict, stats, params)==False ):
					continue
 
				### START any custom functions HERE:
				self.processImage(img)
				### FINISH with custom functions
 
	 			apLoop.writeDoneDict(donedict, params, img['filename'])
				apLoop.printSummary(stats, params)
				#END LOOP OVER IMAGES
			notdone,images = apLoop.waitForMoreImages(stats, params)
			#END NOTDONE LOOP
		apLoop.completeLoop(stats)

	def getImages(self, **kwargs):
		q = data.AcquisitionImageData(**kwargs)
		self.images = db.query(q, readimages=False, results=50)
		print 'LEN', len(self.images)

	def writeDoneDict(self, donedict, params, imgname):
		return

	def startLoop(self, img, donedict, stats, params):
		return True

	def printSummary(self, stats, params):
		return

	def waitForMoreImages(self, stats, params):
		return notdone, images

	def completeLoop(self, stats):
		return

	def process(self, image):
		raise NotImplementedError()

class BinLoop(AppionLoop):
	def process(self, image):
		imagefun.bin(image['image'], 2)

if __name__ == '__main__':
	imageiter = BinLoop()
	## WARNING bin ALL 'en' images
	p = data.PresetData(name='en')
	imageiter.getImages(preset = p)
	imageiter.loop()
