#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import shutil
import re
#pyami
from pyami import mrc
#leginon
import leginon.leginondata
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apTomo
from appionlib import apImod
from appionlib import apProTomo
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apStack
try:
	no_wx = False
	import wx
except ImportError:
	no_wx = True

#=====================
#=====================
class tomoMaker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")

		### strings
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--exclude", dest="exclude",
			help="Tilt images to be excluded (0,5,8)", metavar="0,1,...")

		### integers
		self.parser.add_option("--alignerid", dest="alignerid", type="int",
			help="aligner Id used for reconstruction", metavar="int")
		self.parser.add_option("--thickness", dest="thickness", default=100, type="int",
			help="Full tomo reconstruction thickness before binning, e.g. --thickness=200", metavar="int")
		self.parser.add_option("--bin", "-b", dest="bin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")

		### true/false
		self.parser.add_option("--sample", dest="sample", default=False,
			action="store_true", help="make sample tomogram and prepare for etomo to reconstruct it manually")

		### choices
		self.methods = ( "imod-wbp", "xmipp-art", "upload" )
		self.parser.add_option("--method", dest="method",
			help="reconstruction method, e.g. --method=imod-wbp", metavar="Method",
			type="choice", choices=self.methods, default="imod-wbp" )
		return

	#=====================
	def checkConflicts(self):
		if self.params['alignerid'] is None :
			apDisplay.printError("There is no aligner specified")
		if self.params['method'] not in self.methods:
			apDisplay.printError("No valid correlation method specified")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		self.sessiondata = sessiondata
		if self.params['rundir']:
			self.setTiltSeriesDir()

	def setTiltSeries(self):
		self.tiltdatalist = apTomo.getTiltListFromAligner(self.params['alignerid'])
		self.params['tiltseriesnumber'] = self.tiltdatalist[0]['number']
		self.params['tiltseries'] = self.tiltdatalist[0]

	def setTiltSeriesDir(self):
		self.setTiltSeries()
		path = os.path.abspath(self.sessiondata['image path'])
		if len(self.tiltdatalist) > 1:
			self.params['other tiltseries'] = self.tiltdatalist[1]
		pieces = path.split('leginon')
		path = 'leginon'.join(pieces[:-1]) + 'appion' + pieces[-1]
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.params['tiltseriesdir'] = os.path.join(path,tiltseriespath)

	#=====================
	def setProcessingDirName(self):
		self.setTiltSeries()
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.processdirname = "tomo/"+tiltseriespath

	#=====================
	def onInit(self):
		pieces = self.params['rundir'].split('/')
		self.params['tiltseriesdir'] = '/'.join(pieces[:-1])
		self.params['fulltomodir'] = self.params['rundir']

	#=====================
	def start(self):
		commit = self.params['commit']
		tiltdatalist = self.tiltdatalist
		sessiondata = tiltdatalist[0]['session']
		runname = self.params['runname']
		processdir = self.params['fulltomodir']
		description = self.params['description']
		bin = int(self.params['bin'])
		### list of particles to be excluded
		excludelist = []
		if self.params['exclude']:
			excludestrlist = self.params['exclude'].split(",")
			for excld in excludestrlist:
				excludelist.append(int(excld.strip()))
		apDisplay.printMsg("Exclude list: "+str(excludelist))
		# Get image list and information
		apDisplay.printMsg("getting imagelist")
		imagelist = apTomo.getImageList(tiltdatalist)
		apDisplay.printMsg("getting pixelsize")
		pixelsize = apTomo.getTomoPixelSize(imagelist[0])
		imgshape = apTomo.getTomoImageShape(imagelist[0])
		center = {'x':imgshape[1]/2,'y':imgshape[0]/2}
		centertuple = (center['x'],center['y'])
		alignerdata = apTomo.getAlignerdata(self.params['alignerid'])
		seriesname = apTomo.getFilename(tiltdatalist)
		stackname = seriesname+".st"
		tilts,ordered_imagelist,ordered_mrc_files,refindex = apTomo.orderImageList(imagelist)
		reconname = seriesname+"_full"
		# Write tilt series stack images and tilt angles
		stackdir = self.params['tiltseriesdir']
		apTomo.writeTiltSeriesStack(stackdir,stackname,ordered_mrc_files)
		apImod.writeRawtltFile(stackdir,seriesname,tilts)
		# Get alignment from database
		specimen_euler, tiltaz, origins, rotations = apTomo.getAlignmentFromDB(alignerdata,center)
		imodaffines = apProTomo.convertProtomoToImod(specimen_euler, tiltaz, origins, rotations,centertuple)
		apImod.writeTransformFile(processdir, seriesname,imodaffines,ext='xf')
		imodlocalaffines = apTomo.convertGlobalToLocalAffines(imodaffines)
		apImod.writeTransformFile(processdir, seriesname,imodlocalaffines,ext='prexf')
		thickness = int(self.params['thickness'])
		if self.params['sample']:
			# Make Sample Tomogram for etomo manual positioning and exit
			aligndir = alignerdata['alignrun']['path']['path']
			templatedir = os.path.join(os.path.dirname(apImod.__file__),'data')
			apImod.sampleRecon(stackdir, processdir, aligndir, seriesname, 10, 0.66, thickness, excludelist)
			has_rotation = False
			if alignerdata['protomo']:
				if alignerdata['refine_cycle']['cycle'] > 0:
					has_rotation = True
			apImod.makeFilesForETomoSampleRecon(processdir, stackdir,aligndir, templatedir, seriesname, thickness, pixelsize,has_rotation)
			apDisplay.printMsg('------------------------')
			apDisplay.printWarning('You should run etomo and continue on "Tomogram Positioning" in %s with the .edf file of the tile series like this' % processdir)
			apDisplay.printColor('cd %s' % processdir,'cyan')
			apDisplay.printColor('etomo %s.edf' % seriesname,'cyan')
			apDisplay.printMsg('------------------------')
			return

		# Create Aligned Stack
		apImod.createAlignedStack(stackdir, processdir, seriesname,bin)
		# Reconstruction
		apImod.recon3D(stackdir, processdir, seriesname, imgshape, thickness/bin, False, excludelist)
		# Full tomogram created with imod is left-handed XZY
		voltransform = 'flipx'
		origtomopath = os.path.join(processdir, seriesname+"_full.rec")
		currenttomopath = apImod.transformVolume(origtomopath,voltransform)
		shutil.move(currenttomopath, origtomopath)
		zprojectfile = apImod.projectFullZ(processdir, runname, seriesname,bin,True,False)
		if commit:
			q=leginon.leginondata.AcquisitionImageData()
			zimagedata = apTomo.uploadZProjection(runname,imagelist[0],zprojectfile)
			excludeimages = apTomo.getExcludedImageIds(ordered_imagelist,excludelist)
			fullrundata = apTomo.insertFullTomoRun(sessiondata,processdir,runname,self.params['method'],excludeimages)
			fulltomodata = apTomo.insertFullTomogram(sessiondata,tiltdatalist[0],alignerdata,
						fullrundata,reconname,description,zimagedata,thickness,bin)
#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()



