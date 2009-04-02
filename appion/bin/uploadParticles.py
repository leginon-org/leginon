#!/usr/bin/env python
# Upload pik or box files to the database

import os
import sys
import time
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
	params['apix']=None
	params['diam']=None
	params['bin']=None
	params['description']=None
	params['template']=None
	params['session']=None
	params['runname']=None
	params['imgs']=None
	params['rundir']=os.path.abspath('.')
	params['abspath']=os.path.abspath('.')
	params['rundir']=None
	params['scale']=None
	params['commit']=True
	params['sym']=None
	params['res']=None
	params['contour']=1.5
	params['zoom']=1.5
	params['reconid']=None
	params['rescale']=False
	params['newbox']=None
	return params

#===========================	
class UploadParticles(appionScript.AppionScript):
	def setupParserOptions(self):
		""" NEED TO COPY PARAM SETTING FROM ABOVE """

		# create params dictionary & set defaults
		params = createDefaults()
		params['runname'] = "manual1"

		# parse command line input
		#parsePrtlUploadInput(sys.argv,params)

	def checkConflicts(self):
		# check to make sure that incompatible parameters are not set
		if params['diam'] is None or params['diam']==0:
			apDisplay.printError("please input the diameter of your particle (for display purposes only)")
		
		# get list of input images, since wildcards are supported
		if params['imgs'] is None:
			apDisplay.printError("please enter the image names with picked particle files")
		imglist = params["imgs"]

	def start(self):
		print "getting image data from database:"
		totimgs = len(imglist)
		imgtree = []
		for i in range(len(imglist)):
			imgname = imglist[i]
			print "image",i+1,"of",totimgs,":",apDisplay.short(imgname)
			imgdata = apDatabase.getImageData(imgname)
			imgtree.append(imgdata)
		params['session'] = imgdata['session']['name']

		# upload Particles
		for imgdata in imgtree:
			# insert selexon params into dbappiondata.selectionParams table
			expid = int(imgdata['session'].dbid)
			insertManualParams(params,expid)
			apParticle.insertParticlePicks(params, imgdata, manual=True)

if __name__ == '__main__':
	uploadpart = UploadParticles()
	uploadpart.start()
	uploadpart.close()




