#!/usr/bin/env python
# Upload pik or box files to the database

import os
import sys
import time
import glob
import string
import apParam
import apDisplay
import apDatabase
import apParticle
import appionScript
import leginondata
import appionData

#===========================
def insertManualParams(params, expid):
	sessiondata = leginondata.SessionData.direct_query(expid)
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runname']
	runq['session']=sessiondata
	#runq['path'] = appionData.ApPathData(path=os.path.abspath(????????))

	manparams=appionData.ApSelectionParamsData()
	manparams['diam']=params['diam']

	selectionruns=runq.query(results=1)

	# if no run entry exists, insert new run entry into run.dbparticledata
	# then create a new selexonParam entry
	if not selectionruns:
		print "inserting manual selection run into database"
		runq['params']=manparams
		runq.insert()
	elif selectionruns[0]['params'] != manparams:
		apDisplay.printError("upload parameters not the same as last run - check diameter")

#===========================
def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runname=<runname>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"
	sys.exit(1)

#===========================	
def createDefaults():
	params={}
	self.params['apix']=None
	self.params['diam']=None
	self.params['bin']=None
	self.params['description']=None
	self.params['template']=None
	self.params['session']=None
	self.params['runname']=None
	self.params['imgs']=None
	self.params['rundir']=os.path.abspath('.')
	self.params['abspath']=os.path.abspath('.')
	self.params['rundir']=None
	self.params['scale']=None
	self.params['commit']=True
	self.params['sym']=None
	self.params['res']=None
	self.params['contour']=1.5
	self.params['zoom']=1.5
	self.params['reconid']=None
	self.params['rescale']=False
	self.params['newbox']=None
	return params

#===========================	
class UploadParticles(appionScript.AppionScript):
	def setupParserOptions(self):
		""" NEED TO COPY PARAM SETTING FROM ABOVE """

		self.parser.set_usage("Usage:\nuploadParticles.py <boxfiles> scale=<n>\n")
		self.parser.add_option("--files", dest="files",
			help="EMAN box file(s) containing picked particle coordinates", metavar="FILE")
		self.parser.add_option("--scale", dest="scale",
			help="If particles were picked on binned images, enter the binning factor", type='int')
		self.parser.add_option("--diam", dest="diam",
			help="particle diameter in angstroms", type="int")

	#===========================	
	def checkConflicts(self):
		# check to make sure that incompatible parameters are not set
		if self.params['diam'] is None or self.params['diam']==0:
			apDisplay.printError("please input the diameter of your particle (for display purposes only)")
		
		# get list of input images, since wildcards are supported
		if self.params['files'] is None:
			apDisplay.printError("please enter the image names with picked particle files")

	#===========================
	def getPrtlImgs(self):
		# first get all box files
		imglist=glob.glob(self.params['files'])
		if len(imglist)==0:
			apDisplay.printError("no images specified")
		imgs=[]
		for img in imglist:
			if (os.path.isfile(img)):
				# in case of multiple extenstions, such as pik files
				splitfname=(os.path.basename(img).split('.'))
				imgs.append(splitfname[0])
				self.params['extension'] = string.join(splitfname[1:],'.')
				self.params['prtltype'] = splitfname[-1]
			else:
				apDisplay.printError("file '"+img+"' does not exist \n")
		return imgs

	#===========================	
	def start(self):
		print "getting image data from database:"
		self.params['imgs']=self.getPrtlImgs()
		print self.params['extension']
		imgtree = []
		imgtree=apDatabase.getSpecificImagesFromDB(self.params['imgs'])
		self.params['session'] = imgtree[0]['session']['name']

		# upload Particles
		for imgdata in imgtree:
			# insert selexon params into dbappiondata.selectionParams table
			expid = int(imgdata['session'].dbid)
			insertManualParams(self.params,expid)
			apParticle.insertParticlePicks(self.params, imgdata, manual=True)

if __name__ == '__main__':
	uploadpart = UploadParticles()
	uploadpart.start()
	uploadpart.close()




