#!/usr/bin/env python
# Upload pik or box files to the database

import os
import sys
import time
import glob
import apParam
import apDisplay
import apDatabase
import apParticle
import appionScript

#===========================
def insertManualParams(params, expid):
	sessiondata = leginondata.SessionData.direct_query(expid)
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runname']
	runq['session']=sessiondata
	#runq['path'] = appionData.ApPathData(path=os.path.abspath(????????))

	manparams=appionData.ApSelectionParamsData()
	manself.params['diam']=params['diam']

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
def parsePrtlUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printPrtlUploadHelp()
	lastarg=1
	# first get all box files
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		else:
			boxfile=arg
			if (os.path.isfile(boxfile)):
				# in case of multiple extenstions, such as pik files
				splitfname=(os.path.basename(boxfile).split('.'))
				mrcfileroot.append(splitfname[0])
				params['extension'] = string.join(splitfname[1:],'.')
				params['prtltype'] = splitfname[-1]
			else:
				apDisplay.printError("file '"+boxfile+"' does not exist \n")
		lastarg+=1
	params["imgs"]=mrcfileroot

	# save the input parameters into the "params" dictionary
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='scale'):
			params['scale']=int(elements[1])
		elif (elements[0]=='runname'):
			params['runname']=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

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
		self.parser.add_option("--imgs", dest="imgs",
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
		if self.params['imgs'] is None:
			apDisplay.printError("please enter the image names with picked particle files")

	#===========================	
	def start(self):
		print "getting image data from database:"
		imglist=glob.glob(self.params['imgs'])
		totimgs = len(imglist)
		if totimgs==0:
			apDisplay.printError("no images specified")
		imgtree = []
		for img in imglist:
			print "image",img,"of",totimgs,":",apDisplay.short(img)
			fileinfo=os.path.splitext(img)
			imgdata = apDatabase.getImageData(fileinfo[0]+".mrc")['image']
			imgtree.append(imgdata)
		self.params['session'] = imgdata['session']['name']

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




