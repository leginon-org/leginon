#!/usr/bin/env python

#appion
from appionlib import apPrepXmipp3D
from appionlib import apDisplay

class XmippPrepML3DRefinement(apPrepXmipp3D.XmippPrep3DRefinement):
	def setRefineMethod(self):
		self.refinemethod = 'xmippml3d'

#=====================
if __name__ == "__main__":
	app = XmippPrepML3DRefinement()
	app.start()
	app.close()

