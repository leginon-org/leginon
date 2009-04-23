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
import appionData
import apTomo
import apImod
import apImage
import apParam
import apDisplay
import apDatabase
import apParticle
import apStack

#=====================
#=====================
class tomoMaker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --rundir=<dir> "
			+"[options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--tiltseriesnumber", dest="tiltseriesnumber", type="int",
			help="tilt series number in the session", metavar="int")
		self.parser.add_option("--othertilt", dest="othertilt", type="int",
			help="2nd tilt group series number if needed", metavar="int")
		self.parser.add_option("--thickness", dest="thickness", default=100, type="int",
			help="Full tomo reconstruction thickness before binning, e.g. --thickness=200", metavar="int")
		self.parser.add_option("--bin", "-b", dest="bin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")
		self.parser.add_option("--xmethod", dest="xmethod", default="imod",
			help="correlation method, e.g. --xmdethod=imod,leginon, or sift", metavar="Method")
		return 

	#=====================
	def checkConflicts(self):
		if self.params['tiltseriesnumber'] is None :
			apDisplay.printError("There is no tilt series specified")
		if self.params['xmethod'] not in ('imod','leginon','sift'):
			apDisplay.printError("No valid correlation method specified")
		if self.params['rundir'] is not None:
			apDisplay.printError("Directory requirement too complex for simple specification, better skip it")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")

	def setRunDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		self.params['tiltseries'] = tiltdata
		if self.params['othertilt'] is not None:
			othertiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['othertilt'],sessiondata)
			self.params['othertiltseries'] = othertiltdata
		else:
			self.params['othertiltseries'] = None
		if self.params['subvolumeonly']:
			tomodata = apTomo.getFullTomoData(self.params['fulltomoId'])
			path=tomodata['path']['path']
			self.params['fulltomodir'] = path
			self.params['rundir'] = os.path.join(path,self.params['runname'])
			self.params['subrunname'] = self.params['runname']
			self.params['subdir'] = self.params['rundir']
		else:
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","/tomo",path)
			tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
			tomorunpath = self.params['runname']
			intermediatepath = os.path.join(tiltseriespath,tomorunpath)
			self.params['tiltseriesdir'] = os.path.join(path,tiltseriespath)
			self.params['rundir'] = os.path.join(path,intermediatepath)
			self.params['fulltomodir'] = self.params['rundir']
			if self.params['selexonId']:
				subrunname = 'subtomo_pick%d' % self.params['selexonId']
			elif self.params['stackId']:
				subrunname = 'subtomo_stack%d' % self.params['stackId']
			else:
				subrunname = ''
			self.params['subrunname'] = subrunname
			self.params['subdir'] = os.path.join(self.params['rundir'],subrunname)

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
		if self.params['subvolumeonly'] and self.params['fulltomoId']:
			fulltomodata = apTomo.getFullTomoData(self.params['fulltomoId'])
			gcorrfilepath = os.path.join(processdir, seriesname+".xf")
			gtransforms = apImod.readTransforms(gcorrfilepath)
		else:
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
			zprojectfile = apImod.projectFullZ(processdir, self.params['runname'], seriesname,True)
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

	
