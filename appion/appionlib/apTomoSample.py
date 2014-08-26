#!/usr/bin/env python
import os
import shutil
#appion
from appionlib import apTomoMakerBase
from appionlib import apImod
from appionlib import apParam
from appionlib import apFile
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
		yspacing_fraction = 0.66
		apImod.sampleRecon(stackdir, processdir, aligndir, self.seriesname, 10, 0.66, thickness, self.excludelist)
		stackpath = os.path.join(stackdir, self.seriesname+".st")
		yspacing_pixel = apFile.getMrcFileShape(stackpath)[1] * yspacing_fraction * 0.5
		has_rotation = False
		if self.alignerdata['protomo']:
			if self.alignerdata['refine_cycle']['cycle'] > 0:
				has_rotation = True
		apImod.makeFilesForETomoSampleRecon(processdir, stackdir,aligndir, templatedir, self.seriesname, thickness, self.pixelsize,yspacing_pixel,has_rotation)
		paramfile = os.path.join(processdir,'%s_sample.params' % (self.params['runname']))
		apParam.dumpParameters(self.params, paramfile)
		return

	def onClose(self):
		if self.fullrundata:
			apDisplay.printMsg('------------------------')
			apDisplay.printWarning('To create full tomogram reconstruction and commit the result to database with these sampled tomograms, you need to use etomo_recon.py to start eTOMO and continue at "Tomogram Positioning" in %s with the .edf file by running this AppionScript:')
			apDisplay.printColor('etomo_recon.py --session=%s --projectid=%d --samplerunid=%d --description="" --commit --expId=%d --jobtype=%s' % (self.params['sessionname'],self.params['projectid'],self.fullrundata.dbid,self.params['expid'],'etomo_recon'),'cyan')
			apDisplay.printMsg('------------------------')
		
#=====================
#=====================
if __name__ == '__main__':
	app = TomoSampleMaker()
	app.start()
	app.close()
