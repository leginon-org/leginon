#!/usr/bin/env python

import sys
import os
import apDisplay

class AppionLoop(object):
	def __init__(self):
		self.functionname = None
		self.images   = None
		self.params   = {}
		self.stats    = {}
		self.donedict = {}

		self.start()

	def start(self):
		"""
		Starts a new function and gets all the parameters
		"""
		#set the name of the function; needed for param setup
		self.setFunctionName(sys.argv[0])
		print self.functionname

		### setup default params: output directory, etc.
		self.createDefaultParams()

		### setup default stats: timing variables, etc.
		self.createDefaultStats()

		### parse command line options: diam, apix, etc.
		self.parseCommandLineInput(sys.argv)

		### create output directories
		#self.createOutputDirs()

		### write log of command line options
		self.writeFunctionLog(sys.argv)

		### read/create dictionary to keep track of processed images
		#self.readDoneDict()


	def createDefaultParams(self):
		self.params['functionname'] = self.functionname
		print "opening XML parameter file:",self.functionname+".xml"

	def createDefaultStats(self):
		import time
		try:
			import mem
		except:
			apDisplay.printError("Please load 'usepythoncvs' for CVS leginon code, which includes 'mem.py'")
		stats={}
		stats['startTime']=time.time()
		stats['count']  = 1
		stats['skipcount'] = 1
		stats['lastcount'] = 0
		stats['startmem'] = mem.active()
		stats['peaksum'] = 0
		stats['lastpeaks'] = None
		stats['imagesleft'] = 1
		stats['peaksumsq'] = 0
		stats['timesum'] = 0
		stats['timesumsq'] = 0
		stats['skipcount'] = 0
		stats['waittime'] = 0
		stats['lastimageskipped'] = False
		stats['notpair'] = 0
		stats['memlist'] = [mem.active()]
		return stats

	def parseCommandLineInput(self, args):
		self.params['functionname'] = self.functionname
		#self.checkParamConflicts()

	def writeFunctionLog(self, args):
		file = os.path.join(self.params['rundir'],self.functionname+".log")
		out=""
		for arg in args:
			out += arg+" "
		f=open(file,'aw')
		f.write(out)
		f.write("\n")
		f.close()


	def readDoneDict():
		"""
		reads or creates a done dictionary
		"""
		doneDictName = self.params['doneDictName']
		if os.path.isfile(doneDictName):
			print " ... reading old done dictionary:\n\t",doneDictName
			# unpickle previously modified dictionary
			f = open(doneDictName,'r')
			self.donedict = cPickle.load(f)
			f.close()
			print " ... found",len(donedict),"dictionary entries"
		else:
			#set up dictionary
			self.donedict = {}
			print " ... creating new done dictionary:\n\t",doneDictName

	def loop(self):
		"""
		processes all images
		"""
		### get images from database
		self.getAllImages()
		### start the loop
		notdone=True
		while notdone:
			for img in self.images:
				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if self.alreadyProcessed(img):
					continue
 
				### START any custom functions HERE:
				self.processImage(img)
				### FINISH with custom functions
 
	 			self.writeDoneDict(donedict, params, img['filename'])
				self.printSummary(stats, params)
				#END LOOP OVER IMAGES
			notdone = self.waitForMoreImages(stats, params)
			#END NOTDONE LOOP
		self.finishLoop(stats)

	def getAllImages(self):
		#import apDatabase
		#self.images = getAllImages(self.stats,self.params)
		import data
		import dbdatakeeper
		p = data.PresetData(name='en')
		q = data.AcquisitionImageData(preset = p)
		legdb = dbdatakeeper.DBDataKeeper()
		self.images = legdb.query(q, readimages=False, results=50)
		print 'LEN', len(self.images)

	def writeDoneDict(self, imgname):
		return

	def alreadyProcessed(self, img):
		return False

	def printSummary(self):
		return

	def reduceImages(self):
		return

	def waitForMoreImages(self):
		return notdone

	def finishLoop(self, stats):
		return

	def setFunctionName(self, arg):
		self.functionname = arg

	def processImage(self, img):
		raise NotImplementedError()

class BinLoop(AppionLoop):
	def processImage(self, img):
		import imagefun
		imagefun.bin(img['image'], 2)

if __name__ == '__main__':
	print "__init__"
	imageiter = BinLoop()
	print "start"
	imageiter.start()
	print "loop"
	imageiter.loop()
