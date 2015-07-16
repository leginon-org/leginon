#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import shutil
import re
import subprocess
import math
#pyami
from pyami import mrc
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apTomo
from appionlib import apProTomo
from appionlib import apImod
from appionlib import apRaptor
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apStack
#leginon
import leginon.leginondata

#=====================
#=====================
class tomoRaptor(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")

		### strings
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")

		### integers
		self.parser.add_option("--tiltseriesnumber", dest="tiltseriesnumber", type="int",
			help="tilt series number in the session", metavar="int")
		self.parser.add_option("--othertilt", dest="othertilt", type="int",
			help="2nd tilt group series number if needed", metavar="int")
		self.parser.add_option("--markersize", dest="markersize", default=10, type="int",
			help="Mark size in nanometer, e.g. --markersize=10", metavar="int")
		self.parser.add_option("--markernumber", dest="markernumber", default=0, type="int",
			help="number of markers, e.g. --markernumber=10", metavar="int")
		self.parser.add_option("--reconbin", dest="reconbin", default=2, type="int",
			help="binning factor for reconstruction", metavar="int")
		self.parser.add_option("--thickness", dest="reconthickness", default=500, type="int",
			help="estimated thickness of the specimen in pixels", metavar="int")
		return

	#=====================
	def checkConflicts(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		self.sessiondata = sessiondata
		if self.params['tiltseriesnumber'] is None :
			apDisplay.printError("There is no tilt series specified")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		self.params['tiltseries'] = tiltdata
		if self.params['othertilt'] is not None:
			othertiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['othertilt'],sessiondata)
			self.params['othertiltseries'] = othertiltdata
		else:
			self.params['othertiltseries'] = None

	def setProcessingDirName(self):
		self.setTiltSeriesDir()
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.processdirname = "tomo/"+tiltseriespath

	def onInit(self):
		pieces = self.params['rundir'].split('/')
		self.params['tiltseriesdir'] = '/'.join(pieces[:-1])
		self.params['alignmethod'] = 'raptor'
		self.params['fulltomodir'] = self.params['rundir']

	def setTiltSeriesDir(self):
		path = os.path.abspath(self.sessiondata['image path'])
		pieces = path.split('leginon')
		path = 'leginon'.join(pieces[:-1]) + 'appion' + pieces[-1]
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.params['tiltseriesdir'] = os.path.join(path,tiltseriespath)

	#=====================
	def start(self):
		# set local parameters
		commit = self.params['commit']
		tiltdatalist = apTomo.getTiltdataList(self.params['tiltseries'],self.params['othertiltseries'])
		sessiondata = tiltdatalist[0]['session']
		description = self.params['description']
		runname = self.params['runname']
		alignmethod = self.params['alignmethod']
		reconbin = int(self.params['reconbin'])
		thickness_pixel = int(self.params['reconthickness'])
		markersize_nm = int(self.params['markersize'])
		markernumber = int(self.params['markernumber'])

		apDisplay.printMsg("getting imagelist")
		imagelist = apTomo.getImageList(tiltdatalist)
		tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(imagelist)
		apDisplay.printMsg("getting pixelsize")
		pixelsize = apTomo.getTomoPixelSize(ordered_imagelist[refimg])
		imgshape = apTomo.getTomoImageShape(ordered_imagelist[refimg])
		#thickness_binnedpixel = int(thickness_nm * 1e-9 / (pixelsize * reconbin))
		markersize_pixel = int(markersize_nm * 1e-9 / pixelsize)
		processdir = os.path.abspath(self.params['rundir'])
		imodseriesname = apTomo.getFilename(tiltdatalist)
		seriesname = imodseriesname
		# Write tilt series stack images and tilt angles
		stackdir = self.params['tiltseriesdir']
		stackname = imodseriesname+".st"
		apTomo.writeTiltSeriesStack(stackdir,stackname,ordered_mrc_files,1e10*pixelsize)
		apRaptor.linkStToMrcExtension(stackdir,imodseriesname)
		apImod.writeRawtltFile(stackdir,imodseriesname,tilts)
		# Get Leginon tomography settings
		leginontomosettingslist = []
		for tiltdata in tiltdatalist:
			settingsdata = apTomo.getTomographySettings(sessiondata,tiltdata)
			leginontomosettingslist.append(settingsdata)
		aligndir = processdir
		# run the script and get alignment results when raptor can output alignment results in the future. raptoraligndata is None for now.
		returncode, raptoraligndata, raptorfailed = apRaptor.alignAndRecon(stackdir, stackname, processdir, markersize_pixel, reconbin, thickness_pixel, markernumber, commit)
		# Create Aligned Stack for record, not done in apRaptor yet, currently raptoraligndata is None
		if not raptorfailed:
			alifilename = imodseriesname+'.ali'
			alifilepath = os.path.join(aligndir,'align',alifilename)
			print alifilepath
		# commit to database
		if commit:
			# parameters
			raptorparamsdata = apRaptor.insertRaptorParams(markersize_nm,markernumber)
			alignrun = apTomo.insertTomoAlignmentRun(sessiondata,None,None,None,raptorparamsdata,1,self.params['runname'],self.params['rundir'],self.params['description'],raptorfailed)
			# to accomodate iterative alignment, one alignmentrun may have 
			# used the aligner several times, for this case a single 
			# aligner params data is inserted as in the case of Imod xcorr
			alignerdata = apTomo.insertAlignerParams(alignrun,self.params)
			#results
			if raptoraligndata:
				# if raptor has alignment result, it is converted to protomo
				# format which is more parameterized and saved
				prexgfile = os.path.join(aligndir,imodseriesname+'.prexg')
				shifts = apImod.readShiftPrexgFile(aligndir, imodseriesname)
				resulttltparams = apProTomo.convertShiftsToParams(tilts,shifts,center)
				if resulttltparams:
					modeldata = apProTomo.insertModel(alignerdata, resulttltparams)
					for i,imagedata in enumerate(ordered_imagelist):
						apProTomo.insertTiltAlignment(alignerdata,imagedata,i,resulttltparams[0][i],center)
			# multiple tilt series in one alignrun
			for i in range(0,len(tiltdatalist)):
				if i == 0:
					primary = True
				else:
					primary = False
				# Record tilts in align run allows more than one tilt series to be
				# used in one align run.
				apTomo.insertTiltsInAlignRun(alignrun, tiltdatalist[i],leginontomosettingslist[i],primary)
			if not raptorfailed:
				apTomo.makeAlignStackMovie(alifilepath)
			os.chdir(processdir)

			# Full tomogram created with raptor is ???? handness?????
			if not raptorfailed:
				'''
				voltransform = '????'
				origtomopath = os.path.join(processdir, seriesname+"_full.rec")
				currenttomopath = apImod.transformVolume(origtomopath,voltransform)
				shutil.move(currenttomopath, origtomopath)
				'''
				zprojectfile = apImod.projectFullZ(processdir, runname, seriesname,reconbin,False,False)
				try:
					zimagedata = apTomo.uploadZProjection(runname,imagelist[0],zprojectfile)
				except:
					zimagedata = None
				fullrundata = apTomo.insertFullTomoRun(sessiondata,processdir,runname,'imod-wbp')
				fulltomodata = apTomo.insertFullTomogram(sessiondata,tiltdatalist[0],alignerdata,
						fullrundata,runname,description,zimagedata,thickness_pixel,reconbin)


				# if raptor succeeded, upload data and parameters to database
				session_time = sessiondata.timestamp
				description = self.params['description']
				raptordatabase = apRaptor.commitToJensenDatabase(session_time, fulltomodata, stackdir, processdir, stackname, description)
				if raptordatabase == 0:
					apDisplay.printMsg("RAPTOR and uploading to Jensen database done.")
				else:
					apDisplay.printWarning("Uploading to Jensen database failed.")
				


#=====================
if __name__ == '__main__':  
	app = tomoRaptor()
	app.start()
	app.close()



