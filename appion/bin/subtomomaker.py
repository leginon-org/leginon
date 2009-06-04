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
import apAlignment

#=====================
#=====================
class tomoMaker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --rundir=<dir> "
			+"[options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--fulltomoId", dest="fulltomoId", type="int",
			help="Full tomogram id for subvolume creation, e.g. --fulltomoId=2", metavar="int")
		self.parser.add_option("--selexonId", dest="selexonId", type="int",
			help="Volume selection by particle selection, e.g. --selexonId=2", metavar="int")
		self.parser.add_option("--stackId", dest="stackId", type="int",
			help="Volume selection by stack, e.g. --stackId=2", metavar="int")
		self.parser.add_option("--sizex", dest="sizex", default=0, type="int",
			help="Volume column pixels in the tilt series image, e.g. --sizex=20", metavar="int")
		self.parser.add_option("--sizey", dest="sizey", default=0, type="int",
			help="Volume row pixels in the tilt series image, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--sizez", dest="sizez", type="int",
			help="Volume depth pixels in the tilt series image, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--offsetz", dest="offsetz", default=0, type="int",
			help="Volume z offset from the full tomogram center and in pixel unit of the full tomogram, e.g. --offsetz=0", metavar="int")
		self.parser.add_option("--bin", dest="bin", default=1, type="int",
			help="binning relative to the full tomogram, e.g. --bin=2", metavar="int")
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert density")
		return 

	#=====================
	def checkConflicts(self):
		if self.params['rundir'] is not None:
			apDisplay.printError("Directory requirement too complex for simple specification, better skip it")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")
		if self.params['fulltomoId'] is None:
			apDisplay.printError("enter a fulltomogram run id, e.g. --fulltomoId=2")
		if self.params['stackId'] is None and self.params['selexonId'] is None:
			apDisplay.printError("enter a stack or selection run id, e.g. --stackId=2 or --selexonId=2")
		if self.params['stackId'] is not None and self.params['selexonId'] is not None:
			apDisplay.printError("enter a stack or selection run id, NOT BOTH")
		if self.params['stackId'] is not None or self.params['selexonId'] is not None:
			if int(self.params['sizex']) < 1 or int(self.params['sizey']) < 1:
				apDisplay.printError("must enter non-zero subvolume size")
			if int(self.params['sizez']) is None:
				self.params['sizez'] = self.params['thickness']
			if int(self.params['bin']) < 1:
				apDisplay.printError("binning must be larger or equal to 1")

	def setRunDir(self):
		tomodata = apTomo.getFullTomoData(self.params['fulltomoId'])
		path=tomodata['path']['path']
		self.params['fulltomodir'] = path
		self.params['rundir'] = os.path.join(path,self.params['runname'])
		self.params['subrunname'] = self.params['runname']
		self.params['subdir'] = self.params['rundir']

	#=====================
	def start(self):
		commit = self.params['commit']
		description = self.params['description']
		processdir = self.params['fulltomodir']
		runname = self.params['runname']
		offsetz = self.params['offsetz']
		subbin = self.params['bin']
		invert = self.params['invert']
		fulltomodata = apTomo.getFullTomoData(self.params['fulltomoId'])
		#subvolume making
		if (self.params['selexonId'] is not None or self.params['stackId']) and fulltomodata is not None:
			sessiondata = fulltomodata['session']
			seriesname = fulltomodata['name'].rstrip('_full')
			fullbin = fulltomodata['alignment']['bin']
			subrunname = self.params['subrunname']
			volumeindex = apTomo.getLastVolumeIndex(fulltomodata) + 1
			dimension = {'x':int(self.params['sizex']),'y':int(self.params['sizey']),'z':int(self.params['sizez'])}
			zprojimagedata = fulltomodata['zprojection']
			apDisplay.printMsg("getting pixelsize")
			pixelsize = apTomo.getTomoPixelSize(zprojimagedata) * fullbin * subbin
			gtransform = [1,0,0,1,0,0]
			if self.params['selexonId']:
				particles = apParticle.getParticles(zprojimagedata, self.params['selexonId'])
			if self.params['stackId']:
				particles,stackparticles = apStack.getImageParticles(zprojimagedata, self.params['stackId'])
				stackdata = apStack.getOnlyStackData(self.params['stackId'])
			for p, particle in enumerate(particles):
				print particle['xcoord'],particle['ycoord']
				center = apTomo.transformParticleCenter(particle,fullbin,gtransform)
				size = (dimension['x']/fullbin,dimension['y']/fullbin,dimension['z']/fullbin)
				volumename = 'volume%d'% (volumeindex,)
				volumedir = os.path.join(processdir,subrunname+'/',volumename+'/')
				apParam.createDirectory(volumedir)
				apImod.trimVolume(processdir, subrunname,seriesname,volumename,center,offsetz,size,True)
				long_volumename = seriesname+'_'+volumename
				subvolumepath = os.path.join(processdir, runname+"/",volumename+"/",long_volumename+".rec")
				if subbin > 1 or invert:
					apTomo.modifyVolume(subvolumepath,subbin,invert)
				if commit:
					subtomorundata = apTomo.insertSubTomoRun(sessiondata,
							self.params['selexonId'],self.params['stackId'],subrunname,invert,subbin)
					subtomodata = apTomo.insertSubTomogram(fulltomodata,subtomorundata,
							particle,offsetz,dimension,
							volumedir,long_volumename,volumeindex,pixelsize,
							description)
					apTomo.makeMovie(subvolumepath)
					apTomo.makeProjection(subvolumepath)
				volumeindex += 1
#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()

	
