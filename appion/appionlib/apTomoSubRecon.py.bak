#!/usr/bin/env python

import os
import shutil
import subprocess

from pyami import mrc
#appion
from appionlib import appionScript
from appionlib import apTomoMakerBase
from appionlib import apImod
from appionlib import apTomo
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apParticle
from appionlib import appiondata

#=====================
#=====================
class SubTomoMaker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --rundir=<dir> "
			+"[options]")
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--fulltomoId", "--fulltomoid", dest="fulltomoId", type="int",
			help="Full tomogram id for subvolume creation, e.g. --fulltomoId=2", metavar="int")
		self.parser.add_option("--bin", "-b", dest="bin", default=1, type="int",
			help="Extra binning from fulltomogram, e.g. --bin=2", metavar="int")
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert density")

	#=====================
	def checkConflicts(self):
		if self.params['runname'] is None:
			apDisplay.printError("enter a run name")
		if self.params['description'] is None:
			apDisplay.printError("enter a description, e.g. --description='awesome data'")
		if self.params['fulltomoId'] is None:
			apDisplay.printError("enter a fulltomogram run id, e.g. --fulltomoId=2")
		if int(self.params['bin']) < 1:
			apDisplay.printError("binning must be larger or equal to 1")

	def setProcessingDirName(self):
		tomodata = apTomo.getFullTomoData(self.params['fulltomoId'])
		path=tomodata['reconrun']['path']['path']
		self.params['fulltomodir'] = path
		tiltseriesnumber = tomodata['tiltseries']['number']
		tiltseriespath = "tiltseries%d" %  tiltseriesnumber
		self.processdirname = "tomo/%s/%s" % (tiltseriespath,tomodata['reconrun']['runname'])

	def setRunDir(self):
		self.params['rundir'] = os.path.join(self.params['fulltomodir'],self.params['runname'])

	def onInit(self):
		self.params['subrunname'] = self.params['runname']
		self.params['subdir'] = self.params['rundir']

	def getParticleSelectionRunId(self):
		return None

	def getStackId(self):
		return None

	#=====================
	def start(self):
		commit = self.params['commit']
		processdir = self.params['fulltomodir']
		runname = self.params['runname']
		subbin = self.params['bin']
		invert = self.params['invert']
		self.fulltomodata = apTomo.getFullTomoData(self.params['fulltomoId'])
		if self.fulltomodata is None:
			return
		#subvolume making
		self.seriesname = self.fulltomodata['name'].rstrip('_full')
		self.fulltomoshape = self.getFullTomoShape()
		sessiondata = self.fulltomodata['session']
		self.fullbin = self.fulltomodata['bin']
		if not self.fullbin:
			apDisplay.printWarning("no binning in full tomogram, something is wrong, use alignment bin for now")
			self.fullbin = self.fulltomodata['aligner']['alignrun']['bin']
		volumeindex = apTomo.getLastVolumeIndex(self.fulltomodata) + 1
		zprojimagedata = self.fulltomodata['zprojection']
		apDisplay.printMsg("getting pixelsize")
		pixelsize = apTomo.getTomoPixelSize(zprojimagedata) * self.fullbin * subbin
		particles = self.getParticles(zprojimagedata)
		for p, particle in enumerate(particles):
			size,offsetz = self.recon3D(particle,volumeindex)
			volumedir = os.path.dirname(self.subvolumepath)
			# not include .rec
			long_volumename = os.path.basename(self.subvolumepath)[:-4]
			# size is the subtomogram dimension tuple after full tomogram binning
			if commit:
				subtomorundata = apTomo.insertSubTomoRun(sessiondata,
						self.getParticleSelectionRunId(),self.getStackId(),self.params['subrunname'],invert,subbin)
				description = self.updateDescription()
				subtomodata = apTomo.insertSubTomogram(self.fulltomodata,subtomorundata,
						particle,offsetz,{'x':size[0],'y':size[1],'z':size[2]},
						volumedir,long_volumename,volumeindex,pixelsize,
						description)
				apTomo.makeMovie(self.subvolumepath)
				apTomo.makeProjection(self.subvolumepath)
			volumeindex += 1

	def updateDescription(self):
		return self.params['description']

	def getFullTomoShape(self):
		'''
		This function returns tuple of array shape as int, not numpy.int without reading the whole map
		'''
		fulltomopath = os.path.join(self.fulltomodata['reconrun']['path']['path'], self.seriesname+"_full.rec")
		fulltomoheader = mrc.readHeaderFromFile(fulltomopath)
		# conversion to int is important for sinedon insert
		return tuple(map((lambda x:int(x)),fulltomoheader['shape']))

	def getSubTomogramSize(self):
		# dimension is the subtomogram dimension dictionary before full tomogram binning
		dimension = self.getSubTomoDimensionWithoutBinning()
		if dimension['z'] > self.fulltomoshape[1]*self.fullbin :
			dimension['z'] = self.fulltomoshape[1]*self.fullbin
		# size is the subtomogram dimension tuple after full tomogram binning
		size = (dimension['x']/self.fullbin,dimension['y']/self.fullbin,dimension['z']/self.fullbin)
		return size

	def setSubVolumePath(self,volumeindex):
		processdir = self.params['fulltomodir']
		subrunname = self.params['subrunname']
		volumename = 'volume%d'% (volumeindex,)
		volumedir = os.path.join(processdir,subrunname+'/',volumename+'/')
		apParam.createDirectory(volumedir)
		long_volumename = self.seriesname+'_'+volumename
		subvolumepath = os.path.join(processdir, subrunname+"/",volumename+"/",long_volumename+".rec")
		self.subvolumepath = subvolumepath
		return volumename

	def getOffsetZ(self):
		return self.params['offsetz']

	def recon3D(self,particle,volumeindex):
		processdir = self.params['fulltomodir']
		subrunname = self.params['subrunname']
		subbin = self.params['bin']
		invert = self.params['invert']
		gtransform = [1,0,0,1,0,0]
		size = self.getSubTomogramSize()
		volumename = self.setSubVolumePath(volumeindex)
		center = apTomo.transformParticleCenter(particle,self.fullbin,gtransform)
		apImod.trimVolume(processdir, subrunname,self.seriesname,volumename,center,self.params['offsetz'],size,True)
		offsetz = self.getOffsetZ()
		if subbin > 1 or invert:
			apTomo.modifyVolume(self.subvolumepath,subbin,invert)
		return size, self.params['offsetz']

	def getSubTomoDimensionWithoutBinning(self):
		'''
		Return integer size of the tomogram in x,y,z direction in a dictionary.
		There is no binning relative to the data collection. Must convert to integer
		in case that it is a numpy scaler	
		'''
		raise NotImplementedError
	
	def getParticles(self,zprojimagedata):
		'''Return a list of ApParticleData	for reconstruction'''
		raise NotImplementedError

class SubTomoFixSizeMaker(SubTomoMaker):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--sizex", dest="sizex", default=0, type="int",
			help="Volume column pixels in the tilt series image, e.g. --sizex=20", metavar="int")
		self.parser.add_option("--sizey", dest="sizey", default=0, type="int",
			help="Volume row pixels in the tilt series image, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--sizez", dest="sizez", type="int",
			help="Volume depth pixels in the tilt series image, e.g. --sizey=20", metavar="int")
		self.parser.add_option("--offsetz", dest="offsetz", default=0, type="int",
			help="Volume z offset from the full tomogram center and in pixel unit of the full tomogram, e.g. --offsetz=0", metavar="int")

	#=====================
	def checkConflicts(self):
		if int(self.params['sizex']) < 1 or int(self.params['sizey']) < 1:
			apDisplay.printError("must enter non-zero subvolume size")

	def getSubTomoDimensionWithoutBinning(self):
		return {'x':int(self.params['sizex']),'y':int(self.params['sizey']),'z':int(self.params['sizez'])}

class SubTomoParticleMaker(SubTomoFixSizeMaker):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--selexonId", dest="selexonId", type="int",
			help="Volume selection by particle selection, e.g. --selexonId=2", metavar="int")

	def getParticles(self,zprojimagedata):
		'''Return a list of ApParticleData	for reconstruction'''
		return apParticle.getParticles(zprojimagedata, self.params['selexonId'])

	def getParticleSelectionRunId(self):
		return self.params['selexonId']

class SubTomoStackMaker(SubTomoFixSizeMaker):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--stackId", dest="stackId", type="int",
			help="Volume selection by stack, e.g. --stackId=2", metavar="int")

	def getParticles(self,zprojimagedata):
		'''Return a list of ApParticleData	for reconstruction'''
		particles,stackparticles = apStack.getImageParticles(zprojimagedata, self.params['stackId'])
		stackdata = apStack.getOnlyStackData(self.params['stackId'])
		return particles

	def getStackId(self):
		return self.params['stackId']


class SubTomoETomoMaker(SubTomoMaker):
	# There can only be one subtomogram created per running of the script
	def getParticles(self,zprojimagedata):
		'''
		start Etomo
		insert particles
		'''
		os.chdir(self.params['fulltomodir'])
		proc = subprocess.Popen("etomo --fg %s.edf" % (self.seriesname), shell=True)
		proc.wait()
		xrange = apImod.getSubTomoBoundary(self.params['fulltomodir'],self.seriesname,'x')
		if not len(xrange):
			apDisplay.printError('Subtomogram coordinate not generated, can not commit to database.')

		# get subtomogram center from edf log
		xmin,xmax = apImod.getSubTomoBoundary(self.params['fulltomodir'],self.seriesname,'x')
		ymin,ymax = apImod.getSubTomoBoundary(self.params['fulltomodir'],self.seriesname,'y')
		xcenter = self.fullbin * (xmin+xmax) / 2
		ycenter = self.fullbin * (ymin+ymax) / 2
		peaktree = [{'xcoord':xcenter,'ycoord':ycenter,'peakarea':1}]
		# Use the same selection run name for all subtomogram centers
		selectionrunname = zprojimagedata['session']['name']+'_subtomo'
		self.insertCenterSelectionRunData(zprojimagedata['session'],selectionrunname)
		apParticle.insertParticlePeaks(peaktree, zprojimagedata, selectionrunname)
		particles = apParticle.getParticlesForImageFromRunName(zprojimagedata,selectionrunname)
		return [particles[0]]

	def insertCenterSelectionRunData(self,sessiondata,selectionrunname):
		manparamsq=appiondata.ApManualParamsData()
		manparamsq['bin'] = self.fullbin
		manparamsq['tomocenter'] = True
		runq = appiondata.ApSelectionRunData(session=sessiondata,name=selectionrunname,manparams=manparamsq)
		runq.insert()
		self.params['selexonId'] = runq.dbid

	def getOffsetZ(self):
		processdir = self.params['fulltomodir']
		zmin,zmax = apImod.getSubTomoBoundary(self.params['fulltomodir'],self.seriesname,'z')
		offsetz = ((zmax + zmin) - self.fulltomoshape[1] ) / 2
		return offsetz

	def getSubTomogramSize(self,subtomopath):
		tomoheader = mrc.readHeaderFromFile(subtomopath)
		# conversion to int is important for sinedon insert
		return (int(tomoheader['mx']),int(tomoheader['my']),int(tomoheader['mz']))

	def moveSubTomogram(self,subvolumepath):
		shutil.move(os.path.join(self.params['fulltomodir'],self.seriesname+'.rec'),subvolumepath)

	def getParticleSelectionRunId(self):
		return self.params['selexonId']

	def recon3D(self,particle,volumeindex):
		# calculation of offsetz from boundary uses a function that requires that it is in
		# the processing dir
		offsetz = self.getOffsetZ()
		volumename = self.setSubVolumePath(volumeindex)
		self.moveSubTomogram(self.subvolumepath)
		size = self.getSubTomogramSize(self.subvolumepath)
		return size, offsetz

	def updateDescription(self):
		return raw_input('Describe the subtomogram in one line->')

	def onClose(self):
		if self.params['fulltomoId']:
			apDisplay.printMsg('------------------------')
			apDisplay.printWarning('Repeat the same script to create more subtomogram')
			apDisplay.printColor('etomo_subrecon.py --session=%s --projectid=%d --fulltomoid=%d --description="" --commit --expId=%d --jobtype=%s --runname=etomosub' % (self.params['sessionname'],self.params['projectid'],self.params['fulltomoId'],self.params['expid'],'etomo_subrecon'),'cyan')
			apDisplay.printMsg('------------------------')

#=====================
#=====================
if __name__ == '__main__':
	app = tomoMaker()
	app.start()
	app.close()
