#!/usr/bin/env python

#pythonlib
import os
import sys
import math
#appion
from appionlib import apParticleExtractor
from appionlib import apDDprocess
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apParticle
from appionlib import apBoxer
from appionlib import apTomo
from appionlib import apMovie

class MakeDDParticleMovieLoop(apParticleExtractor.ParticleBoxLoop):
	#=======================
	def setupParserOptions(self):
		super(MakeDDParticleMovieLoop,self).setupParserOptions()
		self.parser.add_option("--rawarea", dest="rawarea", default=False,
			action="store_true", help="use full area of the raw frame, not leginon image area")
		self.parser.add_option("--frameavg", dest="nframe", type="int", default=1,
			help="number of raw frame averaged as a single movie frame")
		self.parser.add_option("--framestep", dest="framestep", type="int", default=1,
			help="interval of raw frames used as starting frame for averaging")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

	#=======================
	def preLoopFunctions(self):
		super(MakeDDParticleMovieLoop,self).preLoopFunctions()
		self.dd = apDDprocess.DirectDetectorProcessing()
		self.nframe = self.params['nframe']
		self.framestep = self.params['framestep']

	#=======================
	def processParticles(self,imgdata,partdatas,shiftdata):
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			self.dd.log.write('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return

		### first remove any existing files
		rundir = self.params['rundir']
		imgname = imgdata['filename']
		moviegrouppath = os.path.join(rundir, '%s_*.flv' % (imgname))
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
		for start_frame in range(0,total_frames-self.nframe+1,self.framestep):
			corrected = self.dd.correctFrameImage(start_frame,self.nframe)
			for p,partdata in enumerate(partdatas):
				col_start,row_start = apBoxer.getBoxStartPosition(imgdata,self.half_box,partdata, shiftdata)
				row_end = row_start + self.boxsize
				col_end = col_start + self.boxsize
				array = corrected[row_start:row_end,col_start:col_end]
				filenamebase = '%s_%03d_%03d' % (shortname,p,start_frame)
				apTomo.array2jpg(filenamebase,array,imin=None,imax=None,size=self.boxsize)
				print filenamebase

		# make movies
		for p in range(len(partdatas)):
			framepath = os.path.join(rundir,'%s_%03d_*.jpg' % (shortname,p))
			moviepath = os.path.join(rundir,'%s_%03d.flv' % (imgname,p))
			apMovie.makeflv('jpg',framepath,moviepath)

	def commitToDatabase(self, imgdata):
		pass

if __name__ == '__main__':
	makeMovie = MakeDDParticleMovieLoop()
	makeMovie.run()



