#!/usr/bin/env python

#python
import os
import numpy
import subprocess
#appion
from appionlib import apParam
from appionlib import starFile
from appionlib import apDisplay
from appionlib import apTemplate
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import appionLoop2
from appionlib.apImage import imagefilter

#pyami
from pyami import mrc

"""
This file uploads particles to database that were
downloaded using the myamiweb interface
"""

#===========================
class gAutomatch(appionLoop2.AppionLoop):
	#=====================
	def setProcessingDirName(self):
		self.processdirname = "extract"

	### ==================================
	def setupParserOptions(self):
		## in order to gautomatch documentation

		### Basic options
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert image density to match templates")
		self.parser.add_option("--diam", "--pdiam", dest="diam", type="int",
			help="Diameter of the particle in Angstroms", metavar="INT")
		self.parser.add_option("--template-list", "--template_list", dest="templateliststr",
			help="Template Ids", metavar="#,#" )
		self.parser.add_option("--ang_step", dest="ang_step", default=5, type="int",
			help="Angular step between template rotations (in degrees).")
		self.parser.add_option("--speed",dest="speed", type="int", default=2,
			help="Speed level (0, 1, 2, 3, 4), larger is faster but less accurate.")

		### Advanced options, according to gautomatch documentation
		self.parser.add_option("--overlapmult", dest="overlapmult", type="float",
			help="overlapmult: Maximum distance between particles in angstrom; 0.9~1.1X diameter; "
				+"can be 0.3~0.5 for filament-like particle")
		self.parser.add_option("--thresh", "--minthresh", dest="thresh", type="float",
			help="Cross-correlation cutoff, 0.2-0.4 normally; "
			+"Try to select several typical micrographs to optimize this value.", metavar="FLOAT")

		### Carbon edges
		self.parser.add_option("--lsigma_cutoff",dest="lsigma_cutoff", type="float", metavar="FLOAT",
			help="Local sigma cutoff (relative value), 1.2~1.5 should be a good range; normally a value"
			+" >1.2 will be ice, protein aggregation or contamination")
		self.parser.add_option("--lsigma_D",dest="lsigma_D", type="int", metavar="#",
			help="Diameter for estimation of local sigma, in Angstroms.")

		### Ice/Contamination
		self.parser.add_option("--lave_D",dest="lave_D", type="int", metavar="#",
			help="Diameter for estimation of local average, in angstrom, 0.5~2.0X particle diameter suggested.")
		self.parser.add_option("--lowpass", "--lp", "--lpval", dest="lowpass", type="float", default=30,
			help="Low pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--highpass", "--hp", "--hpval", dest="highpass", type="int", default=1000,
			help="High pass filter radius in Angstroms", metavar="#")

		return

	##=======================
	def checkConflicts(self):

		# check to make sure that incompatible parameters are not set
		if self.params['diam'] is None or self.params['diam']<=0:
			apDisplay.printError("Please input the diameter of your particle (for display purposes only)")

		if self.params['templateliststr'] is None:
			apDisplay.printError("template list was not defined")
		### Parse template list
		oldtemplateids = self.params['templateliststr'].split(',')
		self.params['templateIds'] = []
		for tid in oldtemplateids:
			templateid = abs(int(tid))
			self.params['templateIds'].append(templateid)


		### insert params for manual picking
		self.rundata = self.insertGautomatchRunParams()

		return

	#=====================
	def makeTemplateMrcStack(self):
		## first get most common pixel size for templates
		pixelsizes = []
		rescaleTemplates = False
		minboxsize = None

		for templateid in self.params['templateIds']:
			### pass 1: query database
			templatedata = appiondata.ApTemplateImageData.direct_query(templateid)
			if not (templatedata):
				apDisplay.printError("Template Id "+str(templateid)+" was not found in database.")
			pixelsizes.append(int(templatedata['apix']*1000))

			### pass 2: get min boxsize
			origtemplatepath = os.path.join(templatedata['path']['path'], templatedata['templatename'])
			if not os.path.isfile(origtemplatepath):
				apDisplay.printError("Template file not found: "+origtemplatepath)
			apDisplay.printMsg("reading template: "+origtemplatepath)
			templatearray = mrc.read(origtemplatepath)
			boxsize = max(templatearray.shape)
			if minboxsize is None or boxsize < minboxsize:
				minboxsize = boxsize

		apDisplay.printMsg("List of pixel sizes: "+str(pixelsizes))
		### determine pixel size
		if max(pixelsizes) - min(pixelsizes) > 20:
			rescaleTemplates = True
			self.templateApix = self.params['apix']
		else:
			rescaleTemplates = False
			mostcommon_apix = max(set(pixelsizes), key=pixelsizes.count)
			self.templateApix = mostcommon_apix/1000.

		### pass 3: make into a stack
		templatearraylist = []
		for templateid in self.params['templateIds']:
			templatedata = appiondata.ApTemplateImageData.direct_query(templateid)
			#COPY THE FILE OVER
			origtemplatepath = os.path.join(templatedata['path']['path'], templatedata['templatename'])
			templatearray = mrc.read(origtemplatepath)

			#RESCALE THE TEMPLATE
			if rescaleTemplates is True:
				#scale to correct apix
				scalefactor = templatedata['apix'] / self.params['apix']
				if abs(scalefactor - 1.0) > 0.01:
					apDisplay.printMsg("rescaling template: "+str(templatedata['apix'])+"->"+str(self.params['apix']))
					templatearray = apTemplate.scaleTemplate(templatearray, scalefactor)

			#SET COMMON BOXSIZE
			boxsize = max(templatearray.shape)
			if boxsize > minboxsize:
				templatearray = imagefilter.frame_cut(templatearray, (minboxsize, minboxsize))

			templatearraylist.append(templatearray)
		#FINISH LOOP OVER template ids

		### write template stack
		templateMrcStack = os.path.join(self.params['rundir'], "templates.mrcs")
		templatestackarray = numpy.array(templatearraylist)
		mrc.write(templatestackarray, templateMrcStack)
		return templateMrcStack

	### ==================================
	def preLoopFunctions(self):
		self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		self.templateMrcStack = self.makeTemplateMrcStack()

	### ==================================
	def processImage(self, imgdata):
		### do all the work...
		starname = imgdata['filename']+'_automatch.star'
		if not os.path.isfile(starname):
			# only run when there are no results
			gautocmd = self.getGautomatchCommand(imgdata)
			apDisplay.printColor("Running Gautomatch", "purple")
			print gautocmd
			proc = subprocess.Popen(gautocmd, shell=True)
			proc.communicate()

		self.peaktree = self.processGautomatchResults(imgdata)
		apDisplay.printMsg("%d particles for image %s"
			%(len(self.peaktree), apDisplay.short(imgdata['filename'])))

	### ==================================
	def commitToDatabase(self, imgdata):
		apParticle.insertParticlePeaks(self.peaktree, imgdata, self.params['runname'], msg=True)
		return

	#=====================
	def getGautomatchPath(self):
		exename = 'gautomatch'
		gautopath = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(gautopath):
			gautopath = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(gautopath):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return gautopath

	### ==================================
	def getGautomatchCommand(self, imgdata):
		exe = self.getGautomatchPath()
		gautocmd = exe
		gautocmd += " --apixM %.3f "%(self.params['apix'])
		gautocmd += " --diameter %d "%(self.params['diam'])
		gautocmd += " --T %s "%(self.templateMrcStack)
		gautocmd += " --apixT %.3f "%(self.templateApix)
		gautocmd += " --ang_step %d "%(self.params['ang_step'])
		gautocmd += " --speed %d "%(self.params['speed'])
		if self.params['overlapmult'] is not None:
			gautocmd += " --min_dist %d "%(self.params['overlapmult']*self.params['diam'])
		if self.params['thresh'] is not None:
			gautocmd += " --cc_cutoff %.2f "%(self.params['thresh'])
		if self.params['lsigma_cutoff'] is not None:
			gautocmd += " --lsigma_cutoff %.2f "%(self.params['lsigma_cutoff'])
		if self.params['lsigma_D'] is not None:
			gautocmd += " --lsigma_D %d "%(self.params['lsigma_D'])
		if self.params['lave_D'] is not None:
			gautocmd += " --lave_D %d "%(self.params['lave_D'])
		gautocmd += " --lp %.1f "%(self.params['lowpass'])
		gautocmd += " --hp %d "%(self.params['highpass'])
		if self.params['invert'] is False:
			## backward system: templates are auto inverted, flag says to not invert them.
			gautocmd += " --dont_invertT 1 "
		## add the image
		origimgpath = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')
		runimgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.mrc')
		if not os.path.exists(runimgpath):
			os.symlink(origimgpath, runimgpath)
		gautocmd += " %s "%(runimgpath)
		gautocmd = gautocmd.replace("  ", " ")
		return gautocmd


	### ==================================
	def processGautomatchResults(self, imgdata):
		starname = imgdata['filename']+'_automatch.star'
		if not os.path.isfile(starname):
			apDisplay.printError("Gautomatch did not run")
		peaktree = self.GautomatchStarFile(imgdata, starname)
		if peaktree is None:
			apDisplay.printError("Gautomatch did not run")
		##FIXME
		return peaktree

	### ==================================
	def GautomatchStarFile(self, imgdata, starname):
		### preload db entries for templates
		templatedatalist = []
		for templateid in self.params['templateIds']:
			templatedata = appiondata.ApTemplateImageData.direct_query(templateid)
			templatedatalist.append(templatedata)

		### read file
		star = starFile.StarFile(starname)
		star.read()
		dataBlock = star.getDataBlock("data_")
		loopDict  = dataBlock.getLoopDict() # returns a list with a dictionary for each line in the loop

		### create peak tree
		peaktree = []
		for i, item in enumerate(loopDict):
			#see appiondata.ApParticleData() for documentation...
			peakdict = {'peakarea':1,'peakstddev':1,'peakmoment':1,
				'angle': float(item['_rlnAnglePsi']),
				'xcoord': int(item['_rlnCoordinateX']),
				'ycoord': int(item['_rlnCoordinateY']),
				'correlation': float(item['_rlnAutopickFigureOfMerit']),
				'selectionrun': self.rundata,
				'image': imgdata,
				'diameter': self.params['diam'],
				'label': "template%02d"%(int(item['_rlnClassNumber'])),
			}
			templatenum = int(item['_rlnClassNumber'])-1
			peakdict['template'] = templatedatalist[templatenum]
			peaktree.append(peakdict)
		return peaktree


	#===========================
	def insertGautomatchRunParams(self):
		runq = appiondata.ApSelectionRunData()
		runq['name'] = self.params['runname']
		runq['session'] = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		runq['description'] = self.params['description']
		runq['program'] = 'gautomatch' #lower case
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		rundatas = runq.query(results=1)
		if rundatas and rundatas[0]['params']['diam'] != self.params['diam']:
			apDisplay.printError("upload diameter not the same as last run")

		selectparams = appiondata.ApSelectionParamsData()
		selectparams['diam'] = self.params['diam']
		selectparams['bin'] = 1
		selectparams['manual_thresh'] = self.params['thresh']
		selectparams['lp_filt'] = self.params['lowpass']
		selectparams['hp_filt'] = self.params['highpass']
		selectparams['overlapmult'] = self.params['overlapmult']
		selectparams['invert'] = self.params['invert']

		runq['params'] = selectparams

		if self.params['commit'] is True:
			apDisplay.printColor("Inserting gautomatch selection run into database", "green")
			runq.insert()
		return runq



if __name__ == '__main__':
	gautomatch = gAutomatch()
	gautomatch.run()
	gautomatch.close()





