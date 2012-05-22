#!/usr/bin/env python

#pythonlib
import os
import sys
import math

#pyami
from pyami import mrc
#appion
from appionlib import apDDParticleMovie
from appionlib import apMovie

class MakeDDParticleMRCMovieLoop(apDDParticleMovie.MakeDDParticleMovieLoop):
	def preLoopFunctions(self):
		super(MakeDDParticleMRCMovieLoop,self).preLoopFunctions()
		self.movieformat = 'mrc'

	def saveFrameFromArray(self,array,fileprefix,particleid,frameid):
		filenamebase = '%s_%03d_%03d' % (fileprefix,particleid,frameid)
		mrc.write(array,filenamebase+'.mrc')
		return filenamebase

	def combineFramesToMovie(self,partdatas,framepath_prefix,moviepath_prefix):
		''' Combine frames to movie.  framepath_prefix and moviepath_prefix should
		include be absolute'''
		for p in range(len(partdatas)):
			framepath = '%s_%03d_*.mrc' % (framepath_prefix,p)
			moviepath = '%s_%03d' % (moviepath_prefix,p)
			self.makeMovie(framepath,moviepath)
			self.movieparticles[p] = partdatas[p]

	def makeMovie(self,framepaths_wild,moviepath):
		files = os.listdir(self.params['rundir'])
		moviepath += '.mrc'
		for filename in files:
			bits = framepaths_wild.split('*')
			if bits[0] in filename:
				print filename
				array = mrc.read(os.path.join(self.params['rundir'],filename))
				if os.path.isfile(moviepath):
					mrc.append(array,moviepath)
				else:
					mrc.write(array,moviepath)

if __name__ == '__main__':
	makeMovie = MakeDDParticleMRCMovieLoop()
	makeMovie.run()



