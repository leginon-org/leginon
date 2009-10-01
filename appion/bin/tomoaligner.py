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
#leginon
import leginondata
#appion
import appionScript
import appiondata
import apTomo
import apProTomo
import apImod
import apImage
import apParam
import apDisplay
import apDatabase
import apParticle
import apStack
try:
	no_wx = False
	import wx
except ImportError:
	no_wx = True

#=====================
#=====================
class protomoAligner(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")

		### strings
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")

		### integers
		self.parser.add_option("--tiltseriesnumber", dest="tiltseriesnumber", type="int",
			help="tilt series number in the session", metavar="int")
		self.parser.add_option("--othertilt", dest="othertilt", type="int",
			help="2nd tilt group series number if needed", metavar="int")
		self.alignmethods = ( "imod-shift", "protomo" )
		self.parser.add_option("--alignmethod", dest="xmethod",
			help="aligning method, e.g. --alignmethod=protomo or imod-shift", metavar="Method",
			type="choice", choices=self.alignmethods, default="protomo" )
		self.parser.add_option("--cycle", dest="cycle", default=1, type="int",
			help="Protomo only: Align cycle, e.g. --cycle=1", metavar="int")
		self.parser.add_option("--sample", dest="sample", default=1.0, type="float",
			help="Protomo only: Align sample rate, e.g. --sample=2.0", metavar="float")
		self.parser.add_option("--region", dest="region", default=1, type="int",
			help="Protomo only: Percentage of image used in alignment, e.g. --region=80", metavar="int")
		self.parser.add_option("--goodcycle", dest="goodcycle", type="int",
			help="Protomo only: Reset to image origin to that of this align cycle, e.g. --goodcycle=1", metavar="int")
		self.parser.add_option("--goodstart", dest="goodstart",  type="int",
			help="Protomo only: Reset beginning image origin and rotation before this image number, e.g. --goodstart=1", metavar="int")
		self.parser.add_option("--goodend", dest="goodend",  type="int",
			help="Protomo only: Reset ending image origin and rotation after this image number, e.g. --goodend=50", metavar="int")
		return

	#=====================
	def checkConflicts(self):
		if self.params['tiltseriesnumber'] is None :
			apDisplay.printError("There is no tilt series specified, use one of: "+str(self.alignmethods))
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		self.sessiondata = sessiondata
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		self.params['tiltseries'] = tiltdata
		if self.params['othertilt'] is not None:
			othertiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['othertilt'],sessiondata)
			self.params['othertiltseries'] = othertiltdata
		else:
			self.params['othertiltseries'] = None
		if self.params['goodcycle'] is None:
			if self.params['goodstart'] or self.params['goodend']:
					apDisplay.printError("Cannot specify reseting image range without knowing the cycle number to reset to")
		elif self.params['goodcycle'] >= self.params['cycle']:
			apDisplay.printError("Only older cycle can be used as the base to reset image origin to")
		if self.params['rundir']:
			self.setTiltSeriesDir()

	#=====================
	def setRunDir(self):
		"""
		this function only runs if no rundir is defined at the command line
		"""
		self.setTiltSeriesDir()
		alignrunpath = os.path.join('align',self.params['runname'])
		self.params['rundir'] = os.path.join(self.params['tiltseriesdir'],alignrunpath)

	def setTiltSeriesDir(self):
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.params['tiltseriesdir'] = os.path.join(path,tiltseriespath)

	#=====================
	def runProjalign(self,paramfile):
		"""
		Uses Hans Peters' projalign
		takes individual MRC files not an MRC stack
		"""
	#	while "transmation matrices are inconsistent":
		if True:
			#run tomo-refine.sh which iteratively run projalign
			### changes origin and rotation for each image
			tomorefineexe = apParam.getExecPath("tomo-refine.sh", die=True)
			cmd = ( tomorefineexe
				+" "+paramfile
			)
			print cmd
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
			### results got to runname-iter-numimgs.tlt
			### convert postscript files to png images
			#apSpider.alignment.convertPostscriptToPng()
			#run tomofit.sh
			tomofitexe = apParam.getExecPath("tomo-fit.sh", die=True)
			cmd = ( tomofitexe
				+" "+paramfile
			)
			print cmd
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
			## refines geometric parameters: inplane rotation and tilt axis angle

			### repeat tomo-refine.sh
			### stop when the transmation matrices are consistent, less than 1% difference

	#=====================
	def start(self):
		commit = self.params['commit']
		tiltdatalist = apTomo.getTiltdataList(self.params['tiltseries'],self.params['othertiltseries'])
		sessiondata = tiltdatalist[0]['session']
		description = self.params['description']
		alignsample = self.params['sample']
		cycle = self.params['cycle']
		alignmethod = self.params['xmethod']
		apDisplay.printMsg("getting imagelist")
		imagelist = apTomo.getImageList(tiltdatalist)
		tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(imagelist)
		for file in ordered_mrc_files:
			apImage.shiftMRCStartToZero(file)
		apDisplay.printMsg("getting pixelsize")
		pixelsize = apTomo.getTomoPixelSize(imagelist[refimg])
		imgshape = apTomo.getTomoImageShape(imagelist[refimg])
		center = {'x':imgshape[1]/2,'y':imgshape[0]/2}
		processdir = os.path.abspath(self.params['rundir'])
		imodseriesname = apTomo.getFilename(tiltdatalist)
		seriesname = 'tomo'+ imodseriesname
		# Write tilt series stack images and tilt angles
		stackdir = self.params['tiltseriesdir']
		stackname = imodseriesname+".st"
		apTomo.writeTiltSeriesStack(stackdir,stackname,ordered_mrc_files)
		apImod.writeRawtltFile(stackdir,imodseriesname,tilts)
		if alignmethod == 'protomo':
			self.params['aligndir'],self.params['imagedir'] =	apProTomo.setProtomoDir(self.params['rundir'])
			aligndir = self.params['aligndir']
			# Link images into rundir/raw
			rawimagenames = apProTomo.linkImageFiles(ordered_imagelist,self.params['imagedir'])
			tltfile = os.path.join(aligndir,seriesname+'-%02d-itr.tlt' % (cycle,))
			leginonxcorrlist = []
			if cycle <= 1:
				# If first run, get initial shift alignment from leginon tiltcorrelator
				for tiltseriesdata in tiltdatalist:
					leginonxcorrdata = apTomo.getTomographySettings(sessiondata,tiltseriesdata)
					leginonxcorrlist.append(leginonxcorrdata)
				shifts = apTomo.getGlobalShift(ordered_imagelist, 1, refimg)
				apProTomo.writeInitialProtomoTltFile(aligndir, seriesname,tilts, rawimagenames,shifts,center,refimg)
				refineparamdict=apProTomo.createRefineDefaults(refimg,
						os.path.join(processdir,'raw'),os.path.join(processdir,'out'))
			else:
				lasttltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (cycle-1,))
				for tiltseriesdata in tiltdatalist:
					leginonxcorrlist.append(None)
				if not self.params['goodcycle']:
					shutil.copy(lasttltfile,tltfile)
				else:
					if not (self.params['goodstart'] or self.params['goodend']):
						shutil.copy(lasttltfile,tltfile)
					else:
						# Reset bad ending tilts before alignment cycle
						goodtltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (self.params['goodcycle'],))
						goodtltparams = apProTomo.parseTilt(goodtltfile)
						lasttltparams = apProTomo.parseTilt(lasttltfile)
						tltparams = apProTomo.resetTiltParams(lasttltparams,goodtltparams,self.params['goodstart'],self.params['goodend'])
						apProTomo.writeTiltFile(tltfile,seriesname, tltparams[0], tltparams[1])
				lastrefineparamfile = os.path.join(aligndir,seriesname+'-%02d.param' % (cycle-1,))
				refineparamdict = apProTomo.parseRefineParamFile(lastrefineparamfile)
			refineparamdict = apProTomo.updateRefineParams(refineparamdict,imgshape,alignsample,self.params['region'])
			# Write param file in rundir/align
			paramfilepath = os.path.join(seriesname+'-%02d.param' % (cycle))
			fullparamfilepath = os.path.join(aligndir,paramfilepath)
			apProTomo.writeRefineParamFile(refineparamdict,fullparamfilepath)
			# run porjalign script
			os.chdir(aligndir)
			if cycle > 0:
				self.runProjalign(paramfilepath)
			else:
				lasttltfile = os.path.join(aligndir,seriesname+'-%02d-itr.tlt' % (1,))
				newtltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (self.params['cycle'],))
				shutil.copy(lasttltfile,newtltfile)
			# convert to imod alignment
			alignpathprefix = os.path.join(processdir, seriesname)
			centertuple = (center['x'],center['y'])
			apProTomo.convertGlobalTransformProtomoToImod(seriesname+'-%02d' %(cycle),imodseriesname, centertuple)
		elif alignmethod == 'imod-shift':
			# Correlation by Coarse correlation in IMOD
			aligndir = processdir
			imodxcorrlist = []
			for tiltseriesdata in tiltdatalist:
				imodxcorrdata = apImod.coarseAlignment(stackdir, processdir, imodseriesname, commit)
				imodxcorrlist.append(imodxcorrdata)
			# Global Transformation
			gtransforms = apImod.convertToGlobalAlignment(processdir, imodseriesname)
		# Create Aligned Stack for record
		bin = int(math.ceil(min(imgshape) / 512.0))
		apImod.createAlignedStack(stackdir, aligndir, imodseriesname,bin)
		if alignmethod == 'protomo':
			os.rename(imodseriesname+'.ali',imodseriesname+'-%02d.ali' % cycle)
		if commit:
			if alignmethod == 'protomo':
				protomodata = apProTomo.insertProtomoParams(seriesname)
				apProTomo.insertProtomoAlignIteration(protomodata, self.params, refineparamdict)
			alignlist = []
			for i in range(0,len(tiltdatalist)):
				if alignmethod == 'protomo':
					alignrun = apTomo.insertTomoAlignmentRun(sessiondata,tiltdatalist[i],leginonxcorrlist[i],None,protomodata,1,self.params['runname'],self.params['rundir'],self.params['description'])
				else:
					alignrun = apTomo.insertTomoAlignmentRun(sessiondata,tiltdatalist[i],None,imodxcorrlist[i],None,1,self.params['runname'],self.params['rundir'],self.params['description'])
				alignlist.append(alignrun)
#=====================
#=====================
if __name__ == '__main__':
	app = protomoAligner()
	app.start()
	app.close()



