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
import leginondata
#appion
import appionScript
import appiondata
import apTomo
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
class tomoMaker(appionScript.AppionScript):
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
		self.parser.add_option("--thickness", dest="thickness", default=100, type="int",
			help="Full tomo reconstruction thickness before binning, e.g. --thickness=200", metavar="int")
		self.parser.add_option("--bin", "-b", dest="bin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")

		### choices
		self.xmethods = ( "imod", "leginon", "sift", "projalign" )
		self.parser.add_option("--xmethod", dest="xmethod",
			help="correlation method, e.g. --xmdethod=imod,leginon, or sift", metavar="Method",
			type="choice", choices=self.xmethods, default="imod" )
		return

	#=====================
	def checkConflicts(self):
		if self.params['tiltseriesnumber'] is None :
			apDisplay.printError("There is no tilt series specified, use one of: "+str(self.xmethods))
		if self.params['xmethod'] not in self.xmethods:
			apDisplay.printError("No valid correlation method specified")
		if self.params['xmethod'] == 'leginon' and no_wx:
			apDisplay.printError("Leginon tiltcorrelater can not be used without wx. Try another one")
		if self.params['rundir'] is not None:
			apDisplay.printError("Directory requirement too complex for simple specification, better skip it")
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

	#=====================
	def setRunDir(self):
		"""
		this function only runs if no rundir is defined at the command line
		"""
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		tomorunpath = self.params['runname']
		intermediatepath = os.path.join(tiltseriespath,tomorunpath)
		self.params['tiltseriesdir'] = os.path.join(path,tiltseriespath)
		self.params['rundir'] = os.path.join(path,intermediatepath)
		self.params['fulltomodir'] = self.params['rundir']

	#=====================
	def runProjalign(self):
		"""
		Uses Hans Peters' projalign
		takes individual MRC files not an MRC stack
		"""
		tltfile = self.writeProjalignParamFile(imglist)
		env = self.setProjalignParams()

		while "transmation matrices are inconsistent":
			#run tomo-refine.sh which iteratively run projalign
			### changes origin and rotation for each image
			tomorefineexe = apParam.getExecPath("tomo-refine.sh", die=True)
			cmd = ( tomorefineexe
				+" "+paramfile
			)
			proc = subprocess.Popen(cmd, shell=True, environ=env)
			proc.wait()
			### results got to runname-iter-numimgs.tlt
			### convert postscript files to png images
			#apSpider.alignment.convertPostscriptToPng()

			#run tomofit.sh
			tomofitexe = apParam.getExecPath("tomofit.sh", die=True)
			cmd = ( tomofitexe
				+" "+paramfile
			)
			proc = subprocess.Popen(cmd, shell=True, environ=env)
			proc.wait()
			## refines geometric parameters: inplane rotation and tilt axis angle

			### repeat tomo-refine.sh
			### stop when the transmation matrices are consistent, less than 1% difference

	#=====================
	def writeProjalignTltFile(self, imglist):
		### see c2-00.tlt file
		tltfile = self.params['runname']+"-00.tlt"
		f = open(tltfile, "w")
		f.write("TILT SERIES "+self.params['runname']+"\n")
		f.write("PARAMETER\n")
		f.write("TILT AZIMUTH %.6f\n"%(tiltaxis))
		for img in imglist:
			# fileprefix must start with a letter and only contain numbers, letters, and underscores with no extension
			f.write("  IMAGE %d\tFILE %s\tORIGIN [ %.3f %.3f ]\tTILT ANGLE %.3f\tROTATION %.3f\n"
			%(num, fileprefix, x, y, ang, rot))
		f.write("END")
		f.close()
		return tltfile

	#=====================
	def setProjalignParams(self):
		### see c2-00.params file
		env['imgref'] = 59
		return env

	#=====================
	def start(self):
		commit = self.params['commit']
		tiltseriesdata = self.params['tiltseries']
		othertiltdata = self.params['othertiltseries']
		if othertiltdata is None:
			tiltdatalist = [tiltseriesdata]
		else:
			tiltdatalist = [tiltseriesdata,othertiltdata]
			apDisplay.printMsg('Combining images from two tilt series')
		sessiondata = tiltseriesdata['session']
		description = self.params['description']
		bin = int(self.params['bin'])
		apDisplay.printMsg("getting imagelist")
		imagelist = apTomo.getImageList(tiltdatalist)
		apDisplay.printMsg("getting pixelsize")
		pixelsize = apTomo.getTomoPixelSize(imagelist[0])
		imgshape = apTomo.getTomoImageShape(imagelist[0])
		processdir = self.params['fulltomodir']
		seriesname = apTomo.getFilename(tiltdatalist)
		stackname = seriesname+".st"
		tilts,ordered_imagelist,mrc_files = apTomo.orderImageList(imagelist)
		reconname = seriesname+"_full"
		# Write tilt series stack images and tilt angles

		stackpath = os.path.join(self.params['tiltseriesdir'], stackname)
		stackdir = self.params['tiltseriesdir']
		if os.path.exists(stackpath):
			stheader = mrc.readHeaderFromFile(stackpath)
			stshape = stheader['shape']
			imageheader = mrc.readHeaderFromFile(mrc_files[0])
			imageshape = imageheader['shape']
			if stshape[1:] == imageshape and stshape[0] == len(imagelist):
				apDisplay.printMsg("No need to get new stack of the tilt series")
			else:
				apImage.writeMrcStack(self.params['tiltseriesdir'],stackname,mrc_files, 1)
		else:
			apImage.writeMrcStack(self.params['tiltseriesdir'],stackname,mrc_files, 1)
		apImod.writeRawtltFile(stackdir,seriesname,tilts)
		leginonxcorrlist = []
		imodxcorrlist = []
		if self.params['xmethod']=='leginon':
			# Correlation by tiltcorrelator
			corrpeaks = apTomo.getOrderedImageListCorrelation(imagelist, 1)
			apImod.writeShiftPrexfFile(processdir,seriesname,corrpeaks)
			for tiltseriesdata in tiltdatalist:
				leginonxcorrdata = apTomo.getTomographySettings(sessiondata,tiltseriesdata)
				imodxcorrdata = None
				leginonxcorrlist.append(leginoncorrdata)
				imodxcorrlist.append(imodxcorrdata)
		elif self.params['xmethod']=='sift':
			# Correlation with rotation by Feature Matching
			transforms = apTomo.getFeatureMatchTransform(ordered_imagelist, 1)
			apImod.writeTransformPrexfFile(processdir,seriesname,transforms)
			# pretend to be gotten from tomogram until fixed
			for tiltseriesdata in tiltdatalist:
				leginonxcorrdata = apTomo.getTomographySettings(sessiondata,tiltseriesdata)
				imodxcorrdata = None
				leginonxcorrlist.append(leginonixcorrdata)
				imodxcorrlist.append(imodxcorrdata)
		elif self.params['xmethod']=="projalign":
			# Uses Hans Peters' projalign
			self.runProjalign()
		else:
			# Correlation by Coarse correlation in IMOD
			for tiltseriesdata in tiltdatalist:
				imodxcorrdata = apImod.coarseAlignment(stackdir, processdir, seriesname, commit)
				leginonxcorrdata = None
				leginonxcorrlist.append(leginonxcorrdata)
				imodxcorrlist.append(imodxcorrdata)

		# Global Transformation
		gtransforms = apImod.convertToGlobalAlignment(processdir, seriesname)
		# Add fine alignments here ----------------
		# use the croase global alignment as final alignment
		origxfpath = os.path.join(processdir, seriesname+".prexg")
		newxfpath = os.path.join(processdir, seriesname+".xf")
		shutil.copyfile(origxfpath, newxfpath)
		# Create Aligned Stack
		apImod.createAlignedStack(stackdir, processdir, seriesname,bin)
		if commit:
			alignlist = []
			for i in range(0,len(tiltdatalist)):
				alignrun = apTomo.insertTomoAlignmentRun(sessiondata,tiltdatalist[i],leginonxcorrlist[i],imodxcorrlist[i],bin,self.params['runname'])
				alignlist.append(alignrun)
		# Reconstruction
		thickness = int(self.params['thickness'])
		apImod.recon3D(stackdir, processdir, seriesname, imgshape, thickness)
		zprojectfile = apImod.projectFullZ(processdir, self.params['runname'], seriesname,bin,True,False)
		if commit:
			zimagedata = apTomo.uploadZProjection(self.params['runname'],imagelist[0],zprojectfile)
			fulltomodata = apTomo.insertFullTomogram(sessiondata,tiltdatalist,alignlist,
						processdir,reconname,description,zimagedata)
#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()



