#!/usr/bin/env python

#pythonlib
import os
import sys
import math

from pyami import mrc
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
		self.parser.add_option("--denoise", dest="denoise", default=False,
			action="store_true", help="use KVSD to denoise the frames")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	def checkConflicts(self):
		super(MakeDDParticleMovieLoop,self).checkConflicts()
		if self.params['bin'] != 1:
			apDisplay.printError('binning is not yet implemented, please use bin=1')
		#if self.params['denoise'] and not self.params['ddstack']:
		#	apDisplay.printError('denoise only works with ddstack')
		if self.params['denoise'] and self.params['framestep'] > 1:
			apDisplay.printWarning('Interval of frames must be one when denoising')
			apDisplay.printWarning('Forcing it to 1....')
			self.params['framestep'] = 1
		if not self.params['nframe']:
			# force nframe to a large member so that checkIsDD will consider it as dd data
			# This number will limit the total processing frames if smaller than
			# the actual number of frames in the images
			self.params['nframe'] = 1000

	#=======================
	def preLoopFunctions(self):
		super(MakeDDParticleMovieLoop,self).preLoopFunctions()
		if self.noimages and not self.params['wait']:
			return
		self.firstframe = self.params['startframe']
		self.frameavg = self.params['frameavg']
		self.framestep = self.params['framestep']
		if self.params['commit']:
			self.insertRun()
		if self.params['denoise']:
			from appionlib import apDenoise
			self.denoise = apDenoise.KSVDdenoise(self.params['rundir'])

	def processImage(self, imgdata):
		self.movieparticles = {}
		super(MakeDDParticleMovieLoop,self).processImage(imgdata)

	def saveFrameFromArray(self,array,fileprefix,particleid,frameid):
		filenamebase = '%s_%03d_%03d' % (fileprefix,particleid,frameid)
		apTomo.array2jpg(filenamebase,array,imin=None,imax=None,size=self.boxsize)
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
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
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
			raise
			apDisplay.printWarning('%s: %s' % (e.__class__.__name__,e))
			return
		
		#make frames for the movies
		self.nframe = self.dd.getNumberOfFrameSaved()
		if self.params['nframe'] and (self.nframe is None or self.nframe > self.params['nframe']):
			self.nframe = self.params['nframe']
			
		if not self.params['denoise']:
			self.makeParticleJPGFrames(partdatas,shiftdata,shortname)
		else:
			self.makeDenoisedParticleJPGFrames(partdatas,shiftdata,shortname)
		# make movies
		self.combineFramesToMovie(partdatas,shortname,imgname)

	def getDDStackDirFile(self,imgdata):
		stackpath = self.dd.framestackpath
		return os.path.dirname(stackpath), os.path.basename(stackpath)

	def makeParticleJPGFrames(self,partdatas,shiftdata,shortname):
		'''
		Make corrected frame images and then box off the particles.
		'''
		imgdata = partdatas[0]['image']
		for start_frame in range(self.firstframe,self.nframe-self.frameavg-self.firstframe+1,self.framestep):
			if self.is_dd_frame:
				corrected = self.dd.correctFrameImage(start_frame,self.frameavg)
			else:
				ddstackdir,stackfile = self.getDDStackDirFile(imgdata)
				corrected = self.dd.getDDStackFrameSumImage(start_frame,self.frameavg)
			for p,partdata in enumerate(partdatas):
				col_start,row_start = apBoxer.getBoxStartPosition(imgdata,self.half_box,partdata, shiftdata)
				row_end = row_start + self.boxsize
				col_end = col_start + self.boxsize
				array = corrected[row_start:row_end,col_start:col_end]
				# bin is not used for now
				movieframe_number = start_frame
				self.saveFrameFromArray(array,shortname,p,movieframe_number)

	def makeDenoisedParticleJPGFrames(self,partdatas,shiftdata,shortname):
		'''
		Denoise the boxed particles and then read in the resulting frame stack of the particle for saving as movie frames.
		'''
		if not partdatas:
			return
		if not self.is_dd_stack:
			apDisplay.printError('Denoising works only with ddstack for now')
		imgdata = partdatas[0]['image']
		ddstackdir,stackfile = self.getDDStackDirFile(imgdata)
		framestacks = []
		for p,partdata in enumerate(partdatas):
			# denoise within the particle box
			col_start,row_start = apBoxer.getBoxStartPosition(imgdata,self.half_box,partdata, shiftdata)
			row_end = row_start + self.boxsize
			col_end = col_start + self.boxsize
			roi = ((row_start,row_end),(col_start,col_end))
			paramstr = self.denoise.setupKSVDdenoise(self.frameavg,self.firstframe,self.nframe,roi)
			apDisplay.printMsg('denoise param string: %s' % paramstr)
			self.denoise.makeDenoisedStack(ddstackdir, stackfile)
			outputstackfile = '%s_%s.mrc' % (stackfile[:-4], paramstr)
			framestacks.append(outputstackfile)
		for i,start_frame in enumerate(range(self.firstframe,self.nframe-self.frameavg-self.firstframe+1,self.framestep)):
			for p,partdata in enumerate(partdatas):
				array = mrc.read(os.path.join(self.params['rundir'],'results/mrc',framestacks[p]),i)
				# bin is not used for now
				movieframe_number = start_frame
				self.saveFrameFromArray(array,shortname,p,movieframe_number)

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



