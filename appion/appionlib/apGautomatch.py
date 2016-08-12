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
from appionlib import apTemplateCorrelator
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apPeaks
from appionlib import apParam
from appionlib import apImage


class GautomatchLoop(apTemplateCorrelator.TemplateCorrelationLoop):
#class GautomatchLoop(particleLoop2.ParticleLoop):

#class TemplateCorrelationLoop(particleLoop2.ParticleLoop):
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

		### True / False options
		self.parser.add_option("--ac",dest="ac",default=0.1,help="Amplitude contrast. Default = 0.1")
		self.parser.add_option("--use-mirrors", "--use_mirrors", dest="templatemirrors", default=False,
			action="store_true", help="Use mirrors as additional templates")
		return

	##=======================
	def checkConflicts(self):
		if self.params['thresh'] is None:
			apDisplay.printError("threshold was not defined")

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
				if self.params['templatemirrors'] is True:
					self.params['templateIds'].append(-1*templateid)

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
				if self.params['templatemirrors'] is True:
					i+=1
					self.params['startang'+str(i+1)] = float(angs[0])
					self.params['endang'+str(i+1)]   = float(angs[1])
					self.params['incrang'+str(i+1)]  = float(angs[2])
					self.params['mirror'+str(i+1)]  = True
				i+=1
		return

	##=======================
	def preLoopFunctions(self):


#                self.params['kV'] = imgdata['scope']['high tension']/1000.0
#                self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())

		if len(self.imgtree) > 0:
			self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		# CREATES TEMPLATES
		# SETS params['templatelist'] AND self.params['templateapix']

		if self.params['templateliststr'] is not None:
			apTemplate.getTemplates(self.params)
			apDisplay.printColor("Template list: "+str(self.params['templatelist']), "cyan")
			self.checkPreviousTemplateRun()

	def runTemplateCorrelator(self,imgdata):
		if self.params['spectral'] is True:
			ccmaplist = apFindEM.runSpectralFindEM(imgdata, self.params, thread=self.params['threadfindem'])
		else:
			ccmaplist = apFindEM.runFindEM(imgdata, self.params, thread=self.params['threadfindem'])
		return ccmaplist

	def findPeaks(self,imgdata,ccmaplist):
		return apPeaks.findPeaks(imgdata, ccmaplist, self.params)

	##=======================
	## Gautomatch

	def runGautomatch(self,imgdata,templateid=''):

		
		t0 = time.time()

		gautopath = getGautomatchPath()

		print 'Gautomatch params:'

		## Build Command

                fullinputfilepath = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')
                imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".mrc")

                if not os.path.exists(imgpath):
                        os.symlink(fullinputfilepath, imgpath)
		


		gautocmd = (gautopath + ' ')

		gautocmd += ('--apixM ' + str(self.params['apix']) + ' ')
		gautocmd += ('--ang_step ' + str(self.params['incrang1']) + ' ')
		print 'PIXEL SIZE IS ',self.params['apix']	
	
		if templateid is not None:

		 	templatedata = appiondata.ApTemplateImageData.direct_query(abs(templateid))
			if not (templatedata):
				apDisplay.printError("Template Id "+str(templateid)+" was not found in database.")
			else:
				print '********templatedata is ',templatedata

			if type(templateid) is int and templateid in self.params['templateIds']:
				print 'templateid exists, and is ',templateid
				print 'type is ',type(([i for i, j in enumerate(self.params['templateIds']) if j==templateid]))
				templateidIndex = [i for i, j in enumerate(self.params['templateIds']) if j==templateid]
				print '**************'
				print 'templateidIndex is ',templateidIndex[0]
				print '**************'

				gautocmd += ('--diameter ' + str(templatedata['diam']) + ' ')
				gautocmd += ('--T origTemplate'+str(templateidIndex[0]+1)+'.mrc ')

			#	gautocmd += ('--apixT '+str(self.params['apix'])+' ')
				gautocmd += ('--apixT '+str(templatedata['apix'])+' ')
				gautocmd += ('--min_dist '+str(self.params['overlapmult']*templatedata['diam']) + ' ')
					


		if self.params['invert'] is True:
			pass	
		else:
			gautocmd += '--dont_invertT 1 '
			


#		if self.params['templateliststr'] is not None:
#			continue

		gautocmd += ('--cc_cutoff ' + str(self.params['thresh']) + ' ')
		
		fullinputfilepath = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')
                imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".mrc")

		gautocmd += imgpath
		for key in self.params:
			print key,' : ', self.params[key]


		gautopath = getGautomatchPath()
		print 'Gauto path is ',gautopath	
		print 'command is ',gautocmd

		print 'vars are '

		for name in vars().keys():
			print(name)

		for value in vars().values():
			print value

		print 'self.params is equal to ',self.params
		print 'imgdata is ',imgdata
		gautocmd += ' ; rm '+imgpath
                gautoprogproc = subprocess.Popen(gautocmd, shell=True, stdin=subprocess.PIPE,)
                apDisplay.printColor(gautocmd, "magenta")
                gautoprogproc.stdin.write(gautocmd)
                apDisplay.printColor(gautocmd,"magenta")

                gautoprogproc.communicate()
                tdiff = time.time()-t0
                apDisplay.printMsg("Gautomatch completed in "+apDisplay.timeString(tdiff))

			

	
	
	##=======================
	def processImage(self, imgdata, filtarray):

		if self.params['templateliststr'] is not None:
			if abs(self.params['apix'] - self.params['templateapix']) > 0.01:
				#rescale templates, apix has changed
				apTemplate.getTemplates(self.params)


		### RUN FindEM

		### save filter image to .dwn.mrc
		imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".dwn.mrc")
		apImage.arrayToMrc(filtarray, imgpath, msg=False)

		### run FindEM
		looptdiff = time.time()-self.proct0
		self.proct0 = time.time()
		proctdiff = time.time()-self.proct0
		f = open("template_image_timing.dat", "a")
		datstr = "%d\t%.5f\t%.5f\n"%(self.stats['count'], proctdiff, looptdiff)
		f.write(datstr)
		f.close()

		### run Template Correlation program
#		cclist = self.runTemplateCorrelator(imgdata)


		### run Gautomatch program like dogPicker
                if self.params['templateliststr'] is None:

			self.runGautomatch(self,imgdata)
			peaktree = getPeaksFromBoxFile(self,imgdata['filename']+'_automatch.box')
			apPeaks.peakTreeToPikFile(peaktree, imgdata['filename'], 0, self.params['rundir'])
			return peaktree


		### run Gautomatch program like templateCorrelator
		else:
			print 'templateliststr is ',self.params['templateIds']

			templateids = self.params['templateIds']

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
                        return peaktree
			
			
			
	##=======================
	def getParticleParamsData(self):
		selectparamsq = appiondata.ApSelectionParamsData()
		return selectparamsq

	##=======================
	def commitToDatabase(self, imgdata, rundata):
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


#leave diameter as zero for now - CJN

		peakdict['diameter'] = self.params['diam']
                peakTree.append(peakdict)
        return peakTree

