#!/usr/bin/env python

from appionlib import filterLoop
from appionlib import appiondata


#This program is used by Topaz to PreProcess Images

#=====================
#=====================
#=====================
class MiniFilterLoop(filterLoop.FilterLoop):
	def setupParserOptions(self):
		#uses mostly the default values :)
		self.parser.add_option("-S", "--selection-id", dest="selectionid", type="int",
			help="the particle selection id", metavar="#")
		self.parser.add_option("--require-particles", dest="requireparticles", default=False,
			action="store_true", help="Require that the micrographs have particle picks")
		return
	#=====================
	def preLoopFunctions(self):
		if self.requireparticles is False:
			return
		#make sure that all of the images processed have particle picks
		newimgtree = []
		selexonrun = appiondata.ApSelectionRunData.direct_query(self.params['selectionid'])
		for imgdata in self.imgtree:
			prtlq = appiondata.ApParticleData()
			prtlq['image'] = imgdata
			prtlq['selectionrun'] = selexonrun
			particles = prtlq.query(results=1)
			if len(particles) > 0:
				newimgtree.append(imgdata)
		self.imgtree = newimgtree
		return
	def checkConflicts(self):
		#uses all the default values :)
		return
	def commitToDatabase(self, imgdata):
		#do nothing
		return
	def processImage(self, imgdict, filtarray):
		return

#=====================
#=====================
if __name__ == '__main__':
	preprocessor = MiniFilterLoop()
	preprocessor.run()
	preprocessor.close()