#!/usr/bin/env python

#pythonlib
import os
import numpy
import time
#leginon
from leginon import leginondata
#appion
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import appiondata

class LoopDDTester(appionLoop2.AppionLoop):
	'''
	This simple script pretends to create aligned image. It can
	be used to test autoRelauncher with dependency.
	'''

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "testdd"

	#======================
	def processImage(self, imgdata):
		apDisplay.printMsg('processing %s' % (imgdata['filename']))
		time.sleep(2)

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--alignlabel", dest="alignlabel", default='a',
			help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")
		return

	#======================
	def checkConflicts(self):
		return

	#======================
	def commitToDatabase(self, imgdata):
		label = '-%s' % self.params['alignlabel']
		camq = leginondata.CameraEMData(initializer=imgdata['camera'])
		camq['align frames'] = True
		new_preset = leginondata.PresetData(initializer=imgdata['preset'])
		new_preset['name'] = imgdata['preset']['name']+label
		q = leginondata.AcquisitionImageData(initializer=imgdata)
		q['preset']=new_preset
		q['filename']=imgdata['filename']+label
		q['image']=imgdata['image']
		q['camera']=camq
		q.insert()
		# save alignpair
		appiondata.ApDDAlignImagePairData(source=imgdata, result=q).insert()
		return

	def insertFunctionRun(self):
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=True,bin=1)
		qpath = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		sessiondata = self.getSessionData()
		q = appiondata.ApDDStackRunData(runname=self.params['runname'],params=qparams,session=sessiondata,path=qpath)
		results = q.query()
		if results:
			return results[0]
		else:
			if self.params['commit'] is True:
				q.insert()
				return q

if __name__ == '__main__':
	testLoop = LoopDDTester()
	testLoop.run()

