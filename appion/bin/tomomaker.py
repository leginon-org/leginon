#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import re
#leginon
import leginondata
#appion
import appionScript
import appionData

import apTomo
import apImod
import apImage
import apParam
import apRecon
import apDisplay
import apEMAN
import apFile
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
		self.parser.add_option("--bin", "-b", dest="bin", type="int",
			help="Extra binning, e.g. --bin=2", metavar="int")
		self.parser.add_option("--selexonId", dest="selexonId", type="int",
			help="Volume selection, e.g. --selexonId=2", metavar="int")
		self.parser.add_option("--sizex", dest="sizex", default=0, type="int",
			help="Volume size in column, e.g. --sizex=20", metavar="int")
		self.parser.add_option("--sizey", dest="sizey", default=0, type="int",
			help="Volume size in row, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--subvolumeonly", dest="subvolumeonly", default=False,
			action="store_true", help="Flag for only trim sub volume, e.g. --subvolumeonly")

		return 

	#=====================
	def checkConflicts(self):
		if self.params['tiltseriesnumber'] is None :
			apDisplay.printError("There is no tilt series specified")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")
		if self.params['subvolumeonly']:
			if self.params['selexonId'] is None:
				apDisplay.printError("enter a selection run id, e.g. --selexonId=2")
		if self.params['selexonId'] is not None:
			if int(self.params['sizex']) < 1 or int(self.params['sizey']) < 1:
				apDisplay.printError("must enter non-zero subvolume size")

	def setRunDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		tomorunpath = self.params['runname']
		intermediatepath = os.path.join(tiltseriespath,tomorunpath)
		self.params['rundir'] = os.path.join(path,intermediatepath)
		self.params['tiltseries'] = tiltdata
	#=====================
	def start(self):
		commit = self.params['commit']
		tiltseriesdata = self.params['tiltseries']
		sessiondata = tiltseriesdata['session']
		description = self.params['description']
		bin = int(self.params['bin'])
		use_original_peaks = False
		print "getting imagelist"
		imagelist = apTomo.getImageList(tiltseriesdata)
		print "getting pixelsize"
		pixelsize = apTomo.getTomoPixelSize(imagelist[0])
		processpath = self.params['rundir']
		seriesname = apTomo.getFilename(tiltseriesdata)
		stackname = seriesname+".st"
		tilts,ordered_imagelist,mrc_files = apTomo.orderImageList(imagelist)
		reconname = seriesname+"_full"
		fulltomodata = apTomo.checkExistingFullTomoData(processpath,reconname)
		if self.params['subvolumeonly'] and fulltomodata:
			gcorrfilepath = os.path.join(processpath, seriesname+".xf")
			gtransforms = apImod.readTransforms(gcorrfilepath)
		else:
			apImage.writeMrcStack(self.params['rundir'],stackname,mrc_files, bin)
			apImod.writeRawtltFile(processpath,seriesname,tilts)
			corrpeaks = apTomo.writeOrderedImageListCorrelation(imagelist, bin)
			if use_original_peaks:
				apImod.writePrexfFile(processpath,seriesname,corrpeaks)
				leginonxcorrdata = apTomo.getTomographySettings(sessiondata,tiltdata)
				imodxcorrdata = None
			else:
				imodxcorrdata = apImod.coarseAlignment(processpath, seriesname, commit)
				leginonxcorrdata = None
			gtransforms = apImod.convertToGlobalAlignment(processpath, seriesname)
			# Add fine alignments here ----------------
			# use the croase global alignment as final alignment
			origxfpath = os.path.join(processpath, seriesname+".prexg")
			newxfpath = os.path.join(processpath, seriesname+".xf")
			shutil.copyfile(origxfpath, newxfpath)

			apImod.createAlignedStack(processpath, seriesname)
			if commit:
				alignrun = apTomo.insertTomoAlignmentRun(sessiondata,tiltseriesdata,leginonxcorrdata,imodxcorrdata,bin)
			apImod.recon3D(processpath, seriesname)
			if commit:
				fulltomodata = apTomo.insertFullTomogram(sessiondata,tiltseriesdata,alignrun,
							processpath,reconname,description)
		#subvolume making
		if self.params['selexonId'] is not None:
			volumeindex = apTomo.getLastVolumeIndex(fulltomodata) + 1
			dimension = {'x':int(self.params['sizex']),'y':int(self.params['sizey'])}
			for i,imagedata in enumerate(ordered_imagelist):
				particles = apParticle.getParticles(imagedata, self.params['selexonId'])
				for particle in particles:
					center = apTomo.transformParticleCenter(particle,bin,gtransforms[i])
					size = (dimension['x']/bin,dimension['y']/bin)
					# Note: Currently subvolumes are in separate subdirectory.  This may not
					# make sense in the future
					volumename = 'volume%d'% (volumeindex,)
					volumepath = os.path.join(processpath,volumename+'/')
					apParam.createDirectory(volumepath)
					apImod.trimVolume(processpath, seriesname,volumename,center,size)
					if commit:
						full_volumename = seriesname+'_'+volumename
						apTomo.insertSubTomogram(fulltomodata,particle,dimension,volumepath,full_volumename,volumeindex,pixelsize,description)
					volumeindex += 1
#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()

	
