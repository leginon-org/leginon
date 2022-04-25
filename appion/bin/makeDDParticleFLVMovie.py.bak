#!/usr/bin/env python

#pythonlib
import os
import sys
import math
#appion
from appionlib import apDDParticleMovie
from appionlib import apMovie

class MakeDDParticleFLVMovieLoop(apDDParticleMovie.MakeDDParticleMovieLoop):
	def preLoopFunctions(self):
		super(MakeDDParticleFLVMovieLoop,self).preLoopFunctions()
		self.movieformat = 'gif'

	def makeMovie(self,framepaths_wild,moviepath):
		apMovie.makeflv('jpg',framepaths_wild,moviepath)

if __name__ == '__main__':
	makeMovie = MakeDDParticleFLVMovieLoop()
	makeMovie.run()



