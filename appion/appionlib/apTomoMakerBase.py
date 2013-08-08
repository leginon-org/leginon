#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
#leginon
import leginon.leginondata
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apTomo
from appionlib import apImod
from appionlib import apProTomo
from appionlib import apDisplay
from appionlib import apDatabase

#=====================
#=====================
class TomoMaker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --alignerid=<#> --session=<session> "
			+"[options]")

		### integers
		self.parser.add_option("--alignerid", dest="alignerid", type="int",
			help="aligner Id used for reconstruction", metavar="int")
		self.parser.add_option("--thickness", dest="thickness", default=100, type="int",
			help="Full tomo reconstruction thickness before binning, e.g. --thickness=200", metavar="int")
		self.parser.add_option("--bin", "-b", dest="bin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")

		### strings
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--exclude", dest="exclude",
			help="Tilt images to be excluded,start from 1 (1,5,8)", metavar="1,2,...")

		### choices
		self.methods = ( "imodwbp", "xmippart", "upload", "etomo","protomo2wbp" )
		return

	def setMethod(self):
		self.params['method'] = self.params['jobtype']
	
	#=====================
	def checkConflicts(self):
		self.setMethod()
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['alignerid'] is None:
			apDisplay.printError("There is no aligner specified")

	def setTiltSeries(self):
		self.tiltdatalist = apTomo.getTiltListFromAligner(self.params['alignerid'])
		self.params['tiltseriesnumber'] = self.tiltdatalist[0]['number']
		self.params['tiltseries'] = self.tiltdatalist[0]

	#=====================
	def setProcessingDirName(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		self.sessiondata = sessiondata
		self.setTiltSeries()
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.processdirname = "tomo/"+tiltseriespath

	#=====================
	def onInit(self):
		pieces = self.params['rundir'].split('/')
		self.params['tiltseriesdir'] = '/'.join(pieces[:-1])
		self.params['fulltomodir'] = self.params['rundir']
		self.fullrundata = None
		self.fulltomodata = None

	def setupExcludeList(self):
		### list of tilt images to be excluded
		excludelist = []
		if self.params['exclude']:
			excludestrlist = self.params['exclude'].split(",")
			for excld in excludestrlist:
				excludelist.append(int(excld.strip())-1)
		apDisplay.printMsg("Exclude list: "+str(excludelist))
		self.excludelist = excludelist

	def setupImageInfo(self):
		apDisplay.printMsg("getting imagelist")
		self.orig_imagelist = apTomo.getImageList(self.tiltdatalist)
		apDisplay.printMsg("getting pixelsize")
		self.zerotiltimage = self.orig_imagelist[0]
		self.pixelsize = apTomo.getTomoPixelSize(self.zerotiltimage)
		apDisplay.printMsg("getting image shape and center")
		self.imgshape = apTomo.getTomoImageShape(self.zerotiltimage)
		self.imgcenter = {'x':self.imgshape[1]/2,'y':self.imgshape[0]/2}

	def setupTiltSeries(self):
		tilts,self.ordered_imagelist,ordered_mrc_files,refindex = apTomo.orderImageList(self.orig_imagelist)
		self.seriesname = apTomo.getFilename(self.tiltdatalist)
		stackdir = self.params['tiltseriesdir']
		stackname = self.seriesname+".st"
		apTomo.writeTiltSeriesStack(stackdir,stackname,ordered_mrc_files,1e10*self.pixelsize)
		apImod.writeRawtltFile(stackdir,self.seriesname,tilts)

	def createTransformFile(self):
		# Get alignment from database
		specimen_euler, tiltaz, origins, rotations = apTomo.getAlignmentFromDB(self.alignerdata,self.imgcenter)
		centertuple = (self.imgcenter['x'],self.imgcenter['y'])
		imodaffines = apProTomo.convertProtomoToImod(specimen_euler, tiltaz, origins, rotations,centertuple)
		processdir = self.params['rundir']
		apImod.writeTransformFile(processdir, self.seriesname,imodaffines,ext='xf')
		imodlocalaffines = apTomo.convertGlobalToLocalAffines(imodaffines)
		apImod.writeTransformFile(processdir, self.seriesname,imodlocalaffines,ext='prexf')

	def getReconParams(self):
		return apTomo.insertFullReconParams()
		
	#=====================
	def commitToDatabase(self):
		processdir = self.params['rundir']
		runname = self.params['runname']
		# insertTomoRun
		self.fullrundata = apTomo.insertFullTomoRun(self.sessiondata,processdir,runname,self.params['method'])
		reconname = self.seriesname+"_full"
		if os.path.exists(os.path.join(processdir,reconname+'.rec')):
			#insertTomograma and z projection
			if 'bin' not in self.params.keys():
				self.params['bin']=1
			bin = self.params['bin']
			zerotiltimage = self.orig_imagelist[0]

			zprojectfile = apImod.projectFullZ(processdir, runname, self.seriesname,bin,True,False)
			q=leginon.leginondata.AcquisitionImageData()
			zimagedata = apTomo.uploadZProjection(runname,zerotiltimage,zprojectfile)
			excludeimages = apTomo.getExcludedImageIds(self.ordered_imagelist,self.excludelist)
			reconparamdata = self.getReconParams()
			self.fulltomodata = apTomo.insertFullTomogram(self.sessiondata,self.tiltdatalist[0],self.alignerdata,
					self.fullrundata,reconname,self.params['description'],zimagedata,self.params['thickness'],reconparamdata,bin,excludeimages)

	def prepareRecon(self):
		''' 
		Preparations before Reconstruction. Thickness may need to be
		redefined or some setup files need to be made.
		'''
		pass

	def recon3D(self):
		'''
		Actual 3D reconstruction.
		'''
		pass
		
	def postProcessingRecon(self):
		'''
		Possible 3D volume transformation required to be consistent
		with Appion convention
		'''
		pass
		
	#=====================
	def start(self):
		# Process image list and information
		self.setupImageInfo()
		self.setupExcludeList()

		# Tilt Series Preparation
		self.setupTiltSeries()
		# Make Transformation File from Alignment
		self.alignerdata = apTomo.getAlignerdata(self.params['alignerid'])
		self.createTransformFile()

		self.prepareRecon()

		self.recon3D()

		if self.params['commit']:
			self.postProcessingRecon()
			self.commitToDatabase()

if __name__ == '__main__':
	app = TomoMaker()
	app.start()
	app.close()
