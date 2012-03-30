#!/usr/bin/env python
import os
import shutil
#appion
from appionlib import apTomoMakerBase
from appionlib import apImod
from appionlib import apParam
from appionlib import apDisplay

#=====================
#=====================
class SampleMaker(apTomoMakerBase.TomoMaker):
	#=====================
	def setupParserOptions(self):
		super(SampleMaker,self).setupParserOptions()
		self.parser.remove_option("--bin")
		return

	def setMethod(self):
		self.params['method'] = 'etomo'
	
	#=====================
	def checkConflicts(self):
		super(SampleMaker,self).checkConflicts()
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")

	def prepareRecon(self):
		processdir = self.params['rundir']
		stackdir = self.params['tiltseriesdir']
		thickness = int(self.params['thickness'])
		# Make Sample Tomogram for etomo manual positioning and exit
		aligndir = self.alignerdata['alignrun']['path']['path']
		templatedir = os.path.join(os.path.dirname(apImod.__file__),'data')
		apImod.sampleRecon(stackdir, processdir, aligndir, self.seriesname, 10, 0.66, thickness, self.excludelist)
		has_rotation = False
		if self.alignerdata['protomo']:
			if self.alignerdata['refine_cycle']['cycle'] > 0:
				has_rotation = True
		apImod.makeFilesForETomoSampleRecon(processdir, stackdir,aligndir, templatedir, self.seriesname, thickness, self.pixelsize,has_rotation)
		apDisplay.printMsg('------------------------')
		apDisplay.printWarning('You should run etomo and continue on "Tomogram Positioning" in %s with the .edf file of the tile series like this' % processdir)
		apDisplay.printColor('cd %s' % processdir,'cyan')
		apDisplay.printColor('etomo %s.edf' % self.seriesname,'cyan')
		apDisplay.printMsg('------------------------')
		paramfile = os.path.join(processdir,'%s_sample.params' % (self.params['runname']))
		apParam.dumpParameters(self.params, paramfile)
		return

#=====================
#=====================
if __name__ == '__main__':
	app = TomoSampleMaker()
	app.start()
	app.close()
