#!/usr/bin/env python

import os
import shutil
import subprocess
#appion
from appionlib import apTomoMakerBase
from appionlib import apImod
from appionlib import apTomo
from appionlib import apParam
from appionlib import apDisplay

#=====================
#=====================
class ImodMaker(apTomoMakerBase.TomoMaker):
	#=====================
	def checkConflicts(self):
		super(ImodMaker,self).checkConflicts()
		if self.params['method'] not in self.methods:
			apDisplay.printError("No valid recon method specified")

	#=====================
	def postProcessingRecon(self):
		# Full tomogram created with imod is left-handed XZY
		voltransform = 'flipx'
		origtomopath = os.path.join(self.params['rundir'], self.seriesname+"_full.rec")
		currenttomopath = apImod.transformVolume(origtomopath,voltransform)
		shutil.move(currenttomopath, origtomopath)

class ImodFullMaker(ImodMaker):
	def setMethod(self):
		self.params['method'] = 'imodwbp'
	
	def recon3D(self):
		processdir = self.params['rundir']
		stackdir = self.params['tiltseriesdir']
		bin = self.params['bin']
		# Create Aligned Stack
		apImod.createAlignedStack(stackdir, processdir, self.seriesname,bin)
		# Reconstruction
		apImod.recon3D(stackdir, processdir, self.seriesname, self.imgshape, self.params['thickness']/bin, False, self.excludelist)


class ETomoMaker(ImodMaker):
	def setMethod(self):
		self.params['method'] = 'etomo'
	
	def setupParserOptions(self):
		#super(ETomoMaker,self).setupParserOptions()
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--samplerunid", dest="samplerunid", type="int",
			help="Runid of the recon sample generation, e.g. --samplerunid=2", metavar="int")
		self.parser.remove_option("--runname")
		self.parser.remove_option("--rundir")
		return

	def checkConflicts(self):
		self.rundata = apTomo.getFullTomoRunById(self.params['samplerunid'])
		if self.rundata['method'] != 'etomo':
			apDisplay.printError('The fulltomoram run is not made for ETOMO manual reconstruction')
		paramfile = os.path.join(self.rundata['path']['path'],'%s_sample.params' % (self.rundata['runname']))
		sampleparams = apParam.readRunParameters(paramfile)
		self.params['alignerid'] = sampleparams['alignerid']
		self.params['description'] = sampleparams['description'] + '\n' + self.params['description']
		self.params['method'] = self.rundata['method']
		self.params['runname'] = self.rundata['runname']
		self.params['rundir'] = self.rundata['path']['path']

	def setupExcludeList(self):
		self.params['exclude'] = apImod.getETomoExcludeTiltNumber(self.params['rundir'])
		super(ETomoMaker,self).setupExcludeList()

	def createTransformFile(self):
		pass

	def prepareRecon(self):
		pass

	def recon3D(self):
		proc = subprocess.Popen("etomo --debug --fg %s.edf" % (self.seriesname), shell=True)
		proc.wait()
		reconfilepath = os.path.join(self.params['rundir'],'%s_full.rec' % (self.seriesname))
		if not os.path.exists(reconfilepath):
			apDisplay.printError('%s not generated, can not commit to database.' % (reconfilepath))

	def getReconParams(self):
		tilt_angle_offset = float(apImod.getETomoParam(self.params['rundir'], 'tilt.com', ['OFFSET'])[0])
		z_shift = apImod.getImodZShift(self.params['rundir'])
		tilt_axis_tilt = float(apImod.getETomoParam(self.params['rundir'], 'tilt.com', ['XAXISTILT'])[0])
		image_rotation = float(apImod.getETomoParam(self.params['rundir'], self.seriesname+'.edf', ['Setup.ImageRotationA='])[0])
		return apTomo.insertFullReconParams(tilt_angle_offset,z_shift,tilt_axis_tilt,image_rotation)

	def commitToDatabase(self):
		self.params['bin'] = apImod.getETomoBin(self.params['rundir'],self.seriesname)
		self.params['thickness'] = apImod.getETomoThickness(self.params['rundir'],self.seriesname)
		super(ETomoMaker,self).commitToDatabase()

	def onClose(self):
		if self.fulltomodata:
			apDisplay.printMsg('------------------------')
			apDisplay.printWarning('To create sub tomogram reconstruction and commit the result to database with this full tomogram, you need to use etomo_subrecon.py to start eTOMO and continue at "Post-Processing" with the .edf file by running this AppionScript:')
			apDisplay.printColor('etomo_subrecon.py --session=%s --projectid=%d --fulltomoid=%d --description="" --commit --expId=%d --jobtype=%s --runname=etomosub' % (self.params['sessionname'],self.params['projectid'],self.fulltomodata.dbid,self.params['expid'],'etomo_subrecon'),'cyan')
			apDisplay.printMsg('------------------------')

#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()
