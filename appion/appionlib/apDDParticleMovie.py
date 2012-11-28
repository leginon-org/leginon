#!/usr/bin/env python

#pythonlib
import os
import sys
import math
#appion
from appionlib import apParticleExtractor
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apParticle
from appionlib import apBoxer
from appionlib import apTomo
from appionlib import apMovie
from appionlib import apDatabase
from appionlib import appiondata

class MakeDDParticleMovieLoop(apParticleExtractor.ParticleBoxLoop):
	#=======================
	def setMovieFormat(self,format):
		self.movieformat = format

	def getMovieFormat(self):
		return self.movieformat

	def setupParserOptions(self):
		super(MakeDDParticleMovieLoop,self).setupParserOptions()
		self.parser.add_option("--frameavg", dest="frameavg", type="int", default=1,
			help="number of raw frame averaged as a single movie frame")
		self.parser.add_option("--framestep", dest="framestep", type="int", default=1,
			help="interval of raw frames used as starting frame for averaging")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	def checkConflicts(self):
		super(MakeDDParticleMovieLoop,self).checkConflicts()
		if self.params['bin'] != 1:
			apDisplay.printError('binning is not yet implemented, please use bin=1')

	def checkIsDD(self):
		self.is_dd_frames = True

	#=======================
	def preLoopFunctions(self):
		super(MakeDDParticleMovieLoop,self).preLoopFunctions()
		self.frameavg = self.params['frameavg']
		self.framestep = self.params['framestep']
		if self.params['commit']:
			self.insertRun()

	def processImage(self, imgdata):
		self.movieparticles = {}
		super(MakeDDParticleMovieLoop,self).processImage(imgdata)

	def saveFrameFromArray(self,array,fileprefix,particleid,frameid):
		filenamebase = '%s_%03d_%03d' % (fileprefix,particleid,frameid)
		apTomo.array2jpg(filenamebase,array,imin=None,imax=None,size=self.boxsize)
		print filenamebase
		return filenamebase

	def makeMovie(self,framepaths_wild,moviepath):
		raise NotImplementedError

	def combineFramesToMovie(self,partdatas,framepath_prefix,moviepath_prefix):
		''' Combine frames to movie.  framepath_prefix and moviepath_prefix should
		include be absolute'''
		for p in range(len(partdatas)):
			framepath = '%s_%03d_*.jpg' % (framepath_prefix,p)
			moviepath = '%s_%03d' % (moviepath_prefix,p)
			self.makeMovie(framepath,moviepath)
			self.movieparticles[p] = partdatas[p]

	#=======================
	def processParticles(self,imgdata,partdatas,shiftdata):
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			self.dd.log.write('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return

		### first remove any existing files
		rundir = self.params['rundir']
		imgname = imgdata['filename']
		moviegrouppath = os.path.join(rundir, '%s_*.%s' % (imgname,self.movieformat))
		apFile.removeFile(moviegrouppath)
		
		shortname = apDisplay.short(imgdata['filename'])
		
		apFile.removeFile(os.path.join(rundir,'%s*.jpg' % (shortname)))

		### set processing image
		try:
			self.dd.setImageData(imgdata)
		except Exception, e:
			apDisplay.printWarning(e.message)
			return
		
		#make frames for the movies
		total_frames = self.dd.getNumberOfFrameSaved()
		for start_frame in range(0,total_frames-self.frameavg+1,self.framestep):
			corrected = self.dd.correctFrameImage(start_frame,self.frameavg)
			for p,partdata in enumerate(partdatas):
				col_start,row_start = apBoxer.getBoxStartPosition(imgdata,self.half_box,partdata, shiftdata)
				row_end = row_start + self.boxsize
				col_end = col_start + self.boxsize
				array = corrected[row_start:row_end,col_start:col_end]
				# bin is not used for now
				movieframe_number = start_frame
				self.saveFrameFromArray(array,shortname,p,movieframe_number)
		
		# make movies
		self.combineFramesToMovie(partdatas,shortname,imgname)

	def fakeprocessParticles(self,imgdata,partdatas,shiftdata):
		self.movieparticles = {}
		for p in range(len(partdatas)):
			self.movieparticles[p] = partdatas[p]

	def insertRun(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		pathq = appiondata.ApPathData(path=self.params['rundir'])
		pmparamq=appiondata.ApParticleMovieParamsData()

		paramlist = pmparamq.keys()
		for p in paramlist:
			if p.lower() in self.params:
				pmparamq[p] = self.params[p.lower()]
			else:
				print "missing", p.lower()
		pmrunq = appiondata.ApParticleMovieRunData(path = pathq, movieRunName=self.params['runname'],session=sessiondata,movieParams=pmparamq,selectionrun=self.selectiondata)
		r = pmrunq.insert()
		self.rundata = pmrunq
		
	def commitToDatabase(self, imgdata):
		keys = self.movieparticles.keys()
		keys.sort()
		for p in keys:
			q = appiondata.ApParticleMovieData(movieNumber=p,movieRun=self.rundata,particle=self.movieparticles[p],format=self.movieformat)
			q.insert()



