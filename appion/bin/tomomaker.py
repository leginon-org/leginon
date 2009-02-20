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
import apUpload
import apDatabase
import apParticle

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
			help="Full tomo reconstruction thickness before binning, e.g. --sizez=200", metavar="int")
		self.parser.add_option("--fulltomoId", dest="fulltomoId", type="int",
			help="Full tomogram id for subvolume creation, e.g. --fulltomoId=2", metavar="int")
		self.parser.add_option("--bin", "-b", dest="bin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")
		self.parser.add_option("--xmethod", dest="xmethod", default="imod",
			help="correlation method, e.g. --xmdethod=imod,leginon, or sift", metavar="Method")
		self.parser.add_option("--selexonId", dest="selexonId", type="int",
			help="Volume selection, e.g. --selexonId=2", metavar="int")
		self.parser.add_option("--sizex", dest="sizex", default=0, type="int",
			help="Volume size in column before binning, e.g. --sizex=20", metavar="int")
		self.parser.add_option("--sizey", dest="sizey", default=0, type="int",
			help="Volume size in row before binning, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--sizez", dest="sizez", type="int",
			help="Volume size in row before binning, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--offsetz", dest="offsetz", default=0, type="int",
			help="Volume z offset from the full tomogram center after binning, e.g. --offsetz=0", metavar="int")
		self.parser.add_option("--subvolumeonly", dest="subvolumeonly", default=False,
			action="store_true", help="Flag for only trim sub volume, e.g. --subvolumeonly")

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
		if self.params['subvolumeonly']:
			if self.params['fulltomoId'] is None:
				apDisplay.printError("enter a fulltomogram run id, e.g. --fulltomoId=2")
			if self.params['selexonId'] is None:
				apDisplay.printError("enter a selection run id, e.g. --selexonId=2")
		if self.params['selexonId'] is not None:
			if int(self.params['sizex']) < 1 or int(self.params['sizey']) < 1:
				apDisplay.printError("must enter non-zero subvolume size")
			if int(self.params['sizez']) is None:
				self.params['sizez'] = self.params['thickness']

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
				subrunname = 'subtomo_%d' % self.params['selexonId']
				self.params['subrunname'] = subrunname
				self.params['subdir'] = os.path.join(self.params['rundir'],subrunname)
	#=====================
	def start(self):
		commit = self.params['commit']
		tiltseriesdata = self.params['tiltseries']
		othertiltdata = self.params['othertiltseries']
		if othertiltdata is not None:
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
		#subvolume making
		if self.params['selexonId'] is not None and fulltomodata is not None:
			bin = fulltomodata['alignment']['bin']
			subrunname = self.params['subrunname']
			volumeindex = apTomo.getLastVolumeIndex(fulltomodata) + 1
			dimension = {'x':int(self.params['sizex']),'y':int(self.params['sizey']),'z':int(self.params['sizez'])}
			for i,imagedata in enumerate(ordered_imagelist):
				particles = apParticle.getParticles(imagedata, self.params['selexonId'])
				for particle in particles:
					print particle['xcoord'],particle['ycoord']
					center = apTomo.transformParticleCenter(particle,bin,gtransforms[i])
					print center,bin
					offsetz = self.params['offsetz']
					size = (dimension['x']/bin,dimension['y']/bin,dimension['z'])
					volumename = 'volume%d'% (volumeindex,)
					volumedir = os.path.join(processdir,subrunname+'/',volumename+'/')
					apParam.createDirectory(volumedir)
					apImod.trimVolume(processdir, subrunname,seriesname,volumename,center,offsetz,size)
					if commit:
						long_volumename = seriesname+'_'+volumename
						subtomodata = apTomo.insertSubTomogram(fulltomodata,particle,offsetz,dimension,
								volumedir, subrunname,long_volumename,volumeindex,pixelsize
								,description)
						tomogramfile = subtomodata['path']['path']+'/'+subtomodata['name']+'.rec'
						apTomo.makeMovie(tomogramfile)
						apTomo.makeProjection(tomogramfile)
					volumeindex += 1
#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()

	
