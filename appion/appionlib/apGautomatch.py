#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import time
import subprocess
#appion
from appionlib import particleLoop2
from appionlib import apFindEM
from appionlib import apFindEMG
from appionlib import apDisplay
from appionlib import apTemplate
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apPeaks
from appionlib import apParam
from appionlib import apImage


class GautomatchLoop(particleLoop2.ParticleLoop):

	##=======================
	def checkPreviousTemplateRun(self):
		### check if we have a previous selection run
		selectrunq = appiondata.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['session'] = sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		rundatas = selectrunq.query(results=1)
		if not rundatas:
			return True
		rundata = rundatas[0]


		### check if we have a previous template run
		templaterunq = appiondata.ApTemplateRunData(selectionrun=rundata)
		templatedatas = templaterunq.query()
		if not templatedatas:
			return True

		### make sure of using same number of templates
		if len(self.params['templateIds']) != len(templatedatas):
			apDisplay.printError("different number of templates from last run")

		### make sure we have same rotation parameters
		for i, templateid in enumerate(self.params['templateIds']):
			templaterunq  = appiondata.ApTemplateRunData()
			templaterunq['selectionrun'] = rundata
			templaterunq['template']     = appiondata.ApTemplateImageData.direct_query(templateid)
			### this is wrong only check last template run not this run
			templatedata = templaterunq.query(results=1)[0]
			if ( templatedata['range_start'] != self.params["startang"+str(i+1)] or
				 templatedata['range_end']   != self.params["endang"+str(i+1)] or
				 templatedata['range_incr']  != self.params["incrang"+str(i+1)] ):
				print i+1, templateid
				print templatedata['range_start'], self.params["startang"+str(i+1)]
				print templatedata['range_end'], self.params["endang"+str(i+1)]
				print templatedata['range_incr'], self.params["incrang"+str(i+1)]
				apDisplay.printWarning("different template search ranges from last run")
		return True

	##################################################
	### COMMON FUNCTIONS
	##################################################



	def setupParserOptions(self):
		self.parser.add_option("--template-list", "--template_list", dest="templateliststr",
			help="Template Ids", metavar="#,#" )
		self.parser.add_option("--range-list", "--range_list", dest="rangeliststr",
			help="Start, end, and increment angles: e.g. 0,360,10x0,180,5", metavar="#,#,#x#,#,#")

		self.parser.add_option("--pre_lp", dest="pre_lp",help="The same as --lp, but before the ice/contamination detection, might be better in severely gradient ice. Does not matter to use both --lp and --pre_lp, but suggested to use much smaller --pre_lp for better ice/contamination detection.")
		self.parser.add_option("--pre_hp", dest="pre_hp",help="The same as --hp, but before the ice/contamination detection, might be better in severely gradient ice. Otherwise, do not use --pre_hp or use a very big value")

		self.parser.add_option("--speed",dest="speed",help="Speed level (0,1, 2, 3, 4), larger is faster but less accurate.")
		self.parser.add_option("--lsigma_D",dest="lsigma_D",help="Diameter for estimation of local sigma, in Angstroms.")
		self.parser.add_option("--lsigma_cutoff",dest="lsigma_cutoff",help="Local sigma cutoff (relative value), 1.2~1.5 should be a good range; normally a value >1.2 will be ice, protein aggregation or contamination")


		self.parser.add_option("--lave_D",dest="lave_D",help="Diameter for estimation of local average, in angstrom, 0.5~2.0X particle diameter suggested.")
		self.parser.add_option("--boxsize",dest="boxsize",help="Box size, in pixel, NOT in angstrom; a suggested value will be automatically calculated by --diameter and --apixM")

		self.parser.add_option("--min_dist",dest="min_dist",help="Maximum distance between particles in angstrom; 0.9~1.1X diameter; can be 0.3~0.5 for filament-like particle")


		self.parser.add_option("--ang_step",dest="ang_step",default=10,type="int",help="Angular step between template rotations (presumably degrees).")

		self.parser.add_option("--do_pre_filter",dest="do_pre_filter",default=False,
			action="store_true", help="Do pre filtering (not recommended)")
		return

	##=======================
	def checkConflicts(self):
		if self.params['thresh'] is None:
			apDisplay.printError("threshold was not defined")


		self.peaktreelist = []
		### Check if we have templates
		if self.params['templateliststr'] is None:
			apDisplay.printWarning("Template list was not specified, e.g. --template-list=34,56,12. If running Gautomatch without templates, continue. Otherwise kill job and select templates from the Gautomatch web form.")


		if self.params['templateliststr'] is not None:
				### Parse template list
			oldtemplateids = self.params['templateliststr'].split(',')
			self.params['templateIds'] = []
			for tid in oldtemplateids:
				templateid = abs(int(tid))
				self.params['templateIds'].append(templateid)
	#			if self.params['templatemirrors'] is True:
	#				self.params['templateIds'].append(-1*templateid)

			### Check if we have ranges
			if self.params['rangeliststr'] is None:
				apDisplay.printError("range not specified, please provide range in the order of templateIds")

			### Check that numbers of ranges and templates are equal
			rangestrlist = self.params['rangeliststr'].split('x')
			if len(oldtemplateids) != len(rangestrlist):
				apDisplay.printError("the number of templates and ranges do not match")

			### Parse range list
			i = 0
			for rangestr in rangestrlist:
				self.params['range'+str(i)] = rangestr
				angs = rangestr.split(",")
				if not len(angs) == 3:
					apDisplay.printError("the range is not defined correctly")
				self.params['startang'+str(i+1)] = float(angs[0])
				self.params['endang'+str(i+1)]   = float(angs[1])
				self.params['incrang'+str(i+1)]  = float(angs[2])
				self.params['mirror'+str(i+1)]  = False
		#		if self.params['templatemirrors'] is True:
		#			i+=1
		#			self.params['startang'+str(i+1)] = float(angs[0])
		#			self.params['endang'+str(i+1)]   = float(angs[1])
		#			self.params['incrang'+str(i+1)]  = float(angs[2])
		#			self.params['mirror'+str(i+1)]  = True
				i+=1
		return

	##=======================
	def preLoopFunctions(self):



		if len(self.imgtree) > 0:
			self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		# CREATES TEMPLATES
		# SETS params['templatelist'] AND self.params['templateapix']

		if self.params['templateliststr'] is not None:
			apTemplate.getTemplates(self.params)
			apDisplay.printColor("Template list: "+str(self.params['templatelist']), "cyan")
			self.checkPreviousTemplateRun()


	def findPeaks(self,imgdata,ccmaplist):
		return apPeaks.findPeaks(imgdata, ccmaplist, self.params)

	##=======================
	## Gautomatch


#	def checkGlobalConflicts(self):
#		pass
	def runGautomatch(self,imgdata,templateid=''):

		
		t0 = time.time()

	

		gautopath = getGautomatchPath()

		## Build Command
                fullinputfilepath = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')

		print 'imgdata type is ',(dir(imgdata))
		print 'imgdata filename is ',imgdata['filename']
	
                imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".mrc")
                if not os.path.exists(imgpath):
                       os.symlink(fullinputfilepath, imgpath)
		
		gautocmd = (gautopath + ' ')
		gautocmd += ('--apixM ' + str(self.params['apix']) + ' ')
		gautocmd += ('--ang_step ' + str(self.params['ang_step']) + ' ')
		print 'PIXEL SIZE IS ',self.params['apix']	
	
		if templateid != '':

			try: 
				print 'templateid type is ',type(templateid)
		 		templatedata = appiondata.ApTemplateImageData.direct_query(abs(templateid))
			except:
				apDisplay.printError("Template Id  was not found in database.")


			if templateid.__class__.__name__ == 'int' and templateid in self.params['templateIds']:
				print 'templateid exists, and is ',templateid
				print 'type is ',type(([i for i, j in enumerate(self.params['templateIds']) if j==templateid]))
				templateidIndex = [i for i, j in enumerate(self.params['templateIds']) if j==templateid]
				print '**************'
				print 'templateidIndex is ',templateidIndex[0]
				print '**************'

				gautocmd += ('--diameter ' + str(templatedata['diam']) + ' ')
				gautocmd += ('--T origTemplate'+str(templateidIndex[0]+1)+'.mrc ')
				gautocmd += ('--apixT '+str(self.params['apix'])+' ')
				gautocmd += ('--apixT '+str(templatedata['apix'])+' ')
				gautocmd += ('--min_dist '+str(self.params['overlapmult']*templatedata['diam']) + ' ')
					

		else:
			print 'overlapmult is ',self.params['overlapmult']
			print 'overlapmult type is ',self.params['overlapmult'].__class__.__name__

#		        particle diameter is stored in diam for particleLoop, not pdiam
			gautocmd += ('--diameter ' +str(self.params['diam']) + ' ')
                        gautocmd += ('--min_dist '+str(float(self.params['overlapmult'])*float(self.params['diam'])) + ' ')

		if self.params['invert'] is True:
			pass	
		else:
			gautocmd += '--dont_invertT 1 '
			
#		minthresh is stored as thresh in particleLoop

		gautocmd += ('--cc_cutoff ' + str(self.params['thresh']) + ' ')
		
		fullinputfilepath = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')
                imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".mrc")

		gautocmd += imgpath
		gautopath = getGautomatchPath()
		gautocmd += ' ; rm '+imgpath
                gautoprogproc = subprocess.Popen(gautocmd, shell=True, stdin=subprocess.PIPE,)
                apDisplay.printColor(gautocmd, "magenta")
                gautoprogproc.stdin.write(gautocmd)
                apDisplay.printColor(gautocmd,"magenta")

                gautoprogproc.communicate()
                tdiff = time.time()-t0
                apDisplay.printMsg("Gautomatch completed in "+apDisplay.timeString(tdiff))


	##=======================
	def processImage(self, imgdata,filtarray):

		if self.params['templateliststr'] is not None:
			if abs(self.params['apix'] - self.params['templateapix']) > 0.01:
				#rescale templates, apix has changed
				apTemplate.getTemplates(self.params)

		### run Gautomatch program like dogPicker
                if self.params['templateliststr'] is None:

			print 'DOGPICKER MODE'
			print 'imgdata filename is ',imgdata['filename']
			self.runGautomatch(imgdata,'')
			peaktree = getPeaksFromBoxFile(self,imgdata['filename']+'_automatch.box')
			self.peaktreelist.append(peaktree)
			apPeaks.peakTreeToPikFile(peaktree, imgdata['filename'], 0, self.params['rundir'])
			return peaktree


		### run Gautomatch program like templateCorrelator
		else:
			print 'templateliststr is ',self.params['templateIds']

			templateids = self.params['templateIds']
			peaktreelist = []
			for i in self.params['templateIds']:
				print 'templateids type is ',type(templateids)
				print 'templateids is ',templateids
				print 'i is ',i
				print 'i is ',i
				templateidIndex = [k for k, j in enumerate(self.params['templateIds']) if j==i]
				print 'templateidIndex is ',templateidIndex
			        self.runGautomatch(imgdata,i)
        	                peaktree = getPeaksFromBoxFile(self,imgdata['filename']+'_automatch.box')
                	     #   apPeaks.peakTreeToPikFile(peaktree, imgdata['filename'], templateidIndex[0]+1, self.params['rundir'])
                	        apPeaks.peakTreeToPikFile(peaktree, imgdata['filename'],i, self.params['rundir'])
				peaktreelist.append(peaktree)
			#self.params['doubles'] = True
			apPeaks.mergePeakTrees(imgdata, peaktreelist, self.params, msg=True, pikfile=True)

			print 'peaktreelist is ',peaktreelist
			

                        return peaktree
			
			
			
	##=======================
	def getParticleParamsData(self):
		selectparamsq = appiondata.ApSelectionParamsData()
		return selectparamsq


	## loop
	##=======================
	def commitToDatabase(self, imgdata,rundata):

		#insert template rotation data
		if "templateIds" in self.params:

			for i, templateid in enumerate(self.params['templateIds']):
				templaterunq = appiondata.ApTemplateRunData()
				templaterunq['selectionrun'] = rundata
				templaterunq['template']     = appiondata.ApTemplateImageData.direct_query(abs(templateid))
				templaterunq['range_start']  = self.params["startang"+str(i+1)]
				templaterunq['range_end']    = self.params["endang"+str(i+1)]
				templaterunq['range_incr']   = self.params["incrang"+str(i+1)]
				templaterunq['mirror']   = self.params["mirror"+str(i+1)]
				if self.params['commit'] is True:
					templaterunq.insert()
		return


if __name__ == '__main__':
	imgLoop = GautomatchLoop()
	imgLoop.run()

def getGautomatchPath():


	exename = 'Gautomatch-v0.53_sm_20_cu7.5_x86_64'
	gautopath = os.path.join(apParam.getAppionDirectory(), 'bin', exename)

	if not os.path.isfile(gautopath):
		gautopath = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(gautopath):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return gautopath


def getPeaksFromBoxFile(self,boxfilename):
        peakTree = []
        f = open(boxfilename,'r')
	print 'boxfilename is ',boxfilename
        lines = f.readlines()
        for line in lines:
                good = []
		bits = re.split(r'[ \t]+',line)
                for bit in bits:
                        if len(bit):
                                good.append(bit)
                peakdict = apFindEMG.initializePeakDict()
                peakdict['ycoord']    = int(good[1])
                peakdict['xcoord']    = int(good[0])
                peakdict['correlation'] = float(good[4])
		peakdict['diameter'] = float(self.params['diam'])
                peakTree.append(peakdict)
        return peakTree

