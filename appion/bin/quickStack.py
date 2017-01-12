#!/usr/bin/env python

import os
import sys
import time
import numpy
import multiprocessing
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import starFile

import sinedon

def makeStack(starfile):
	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock("data_images")
	loopDict  = dataBlock.getLoopDict()
	print "Found %d particles"%(len(loopDict))
	return

def start_process():
	print 'Starting', multiprocessing.current_process().name

#=====================
#=====================
class QuickStack(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--selectid", dest="selectid", type="int",
			help="Particle Selction ID", metavar="#")
		self.parser.add_option("--preset", dest="preset",
			help="Preset Name", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['expid'] is None:
			apDisplay.printError("Please provide a session id, e.g. --expid=15")
		if self.params['selectid'] is None:
			apDisplay.printError("Please provide a Particle Selction id, e.g. --selectid=15")

	#==========AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--selectid", dest="selectid", type="int",
			help="Particle Selction ID", metavar="#")
		self.parser.add_option("--preset", dest="preset",
			help="Preset Name", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['expid'] is None:
			apDisplay.printError("Please provide a session id, e.g. --expid=15")
		if self.params['selectid'] is None:
			apDisplay.printError("Please provide a Particle Selction id, e.g. --selectid=15")

	#================================
	def start(self):
		self.params['sessionname'] = apDatabase.getSessionDataFromSessionId(self.params['expid'])['name']
		self.imgtree = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		starlist = []
		for imgdata in self.imgtree:
			imgfile = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')
			sys.stderr.write(".")
			starfile = self.writeStarFile(imgdata)
			starlist.append(starfile)
		print ""
		del self.imgtree
		nproc = 6
		t0 = time.time()
		print "nproc %d"%(nproc)
		p = multiprocessing.Pool(processes=nproc, initializer=start_process)
		p.map(makeStack, starlist)
		p.close()
		p.join()
		p.terminate()
		print "Complete %.3f"%((time.time()-t0)*1)

	#================================
	def writeStarFile(self, imgdata):
		starfile = imgdata['filename']+".star"
		stackfile = imgdata['filename']+".particles.mrcs"
		micrograph = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')

		particles = apParticle.getParticles(imgdata, self.params['selectid'])
		labels = ["_rlnCoordinateX", "_rlnCoordinateY", "_rlnImageName", "_rlnMicrographName"]
		count = 0
		valueSets = []
		for part in particles:
			count += 1
			valueString = "%d %d %05d@%s %s"%(part['xcoord'], part['ycoord'], count, stackfile, micrograph)
			valueSets.append(valueString)
		star = starFile.StarFile(starfile)
		star.buildLoopFile( "data_images", labels, valueSets )
		star.write()
		return starfile


#=====================
#=====================
if __name__ == '__main__':
	quickstack = QuickStack()
	quickstack.start()
	quickstack.close()

