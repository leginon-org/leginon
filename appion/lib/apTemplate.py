# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import shutil
import math
import re
import time
import numpy
import sys
import glob
import pprint
#import numarray.convolve as convolve
#appion
import apImage
import apFile
import apParam
import apDisplay
import apDatabase
import appionData

def getTemplates(params):
	"""
	Inputs:
		params['templateIds'], a list of template ids
		params['apix'], desired pixel size
		params['rundir'], output directory
		image processing params
	Processing:
		Copies, scales, and filters templates
	Outputs:
		params['templatelist'], a list of template file basenames
	"""

	apDisplay.printMsg("getting templates")

	if not params['templateIds']:
		apDisplay.printError("No template ids were specified")

	params['templatelist'] = [] #list of scaled files 
	for i,templateid in enumerate(params['templateIds']):
		index = i+1
		#print templateid
		templateid = int(templateid)
		if templateid < 0:
			continue

		#QUERY DB FOR TEMPLATE INFO
		templatedata = appionData.ApTemplateImageData.direct_query(abs(templateid))
		if not (templatedata):
			apDisplay.printError("Template Id "+str(templateid)+" was not found in database.")

		#COPY THE FILE OVER
		origtemplatepath = os.path.join(templatedata['path']['path'], templatedata['templatename'])
		if not os.path.isfile(origtemplatepath):
			apDisplay.printError("Template file not found: "+origtemplatepath)
		apDisplay.printMsg("getting template: "+origtemplatepath)
		copytemplatepath = os.path.join(params['rundir'], "origTemplate"+str(index)+".mrc")
		scaletemplatepath = os.path.join(params['rundir'], "scaledTemplate"+str(index)+".mrc")
		filtertemplatepath = os.path.join(params['rundir'], "filterTemplate"+str(index)+".mrc")
		#masktemplatepath = os.path.join(params['rundir'], "maskTemplate"+str(index)+".mrc")
		shutil.copyfile(origtemplatepath, copytemplatepath)

		#RESCALE THE TEMPLATE
		templatearray = apImage.mrcToArray(copytemplatepath)
		#scale to correct apix
		scalefactor = templatedata['apix'] / params['apix']
		if abs(scalefactor - 1.0) > 0.01:
			apDisplay.printMsg("rescaling template "+str(index)+": "+str(templatedata['apix'])+"->"+str(params['apix']))
		templatearray = scaleTemplate(templatearray, scalefactor)
		apImage.arrayToMrc(templatearray, scaletemplatepath, msg=False)
		#bin and filter
		templatearray = apImage.preProcessImage(templatearray, params=params, highpass=0, planeReg=False, invert=False)
		#write to file
		apImage.arrayToMrc(templatearray, filtertemplatepath, msg=False)

		### MASK THE TEMPLATE AND SAVE
		#mask the template, visual purposes only
		#maskrad = params['diam']/params['apix']/params['bin']/2.0
		#maskarray = 
		#apImage.arrayToMrc(templatearray, masktemplatepath, msg=False)

		#ADD TO TEMPLATE LIST
		params['templatelist'].append(os.path.basename(filtertemplatepath))

		### ADD MIRROR IF REQUESTED
		if 'templatemirrors' in params and params['templatemirrors'] is True:
			mirrortemplatepath = os.path.join(params['rundir'], "mirrorTemplate"+str(index)+".mrc")
			mirrorarray = numpy.fliplr(templatearray)
			apImage.arrayToMrc(mirrorarray, mirrortemplatepath, msg=False)
			params['templatelist'].append(os.path.basename(mirrortemplatepath))

	#FINISH LOOP OVER template ids
	#Set the apix
	params['templateapix'] = params['apix']
	apDisplay.printMsg("scaled & filtered "+str(len(params['templatelist']))+" file(s)")

	return params['templatelist']


def getTemplateFromId(templateid):
	return appionData.ApTemplateImageData.direct_query(templateid)

def scaleTemplate(templatearray, scalefactor=1.0, boxsize=None):

	if(templatearray.shape[0] != templatearray.shape[1]):
		apDisplay.printWarning("template shape is NOT square, this may cause errors")

	if abs(scalefactor - 1.0) > 0.01:
		apDisplay.printMsg("scaling template by a factor of "+str(scalefactor))
		templatearray = apImage.scaleImage(templatearray, scalefactor)

	#make sure the box size is divisible by 16
	if boxsize is not None or (templatearray.shape[0] % 16 != 0):
		edgeavg = apImage.meanEdgeValue(templatearray)
		origsize = templatearray.shape[0]
		if boxsize is None:
			padsize  = int(math.floor(float(origsize)/16)*16)
		else:
			padsize = boxsize
		padshape = numpy.array([padsize,padsize])
		apDisplay.printMsg("changing box size from "+str(origsize)+" to "+str(padsize))
		if origsize > padsize:
			#shrink image
			templatearray = apImage.frame_cut(templatearray, padshape)
		else:
			#grow image
			templatearray = apImage.frame_constant(templatearray, padshape, cval=edgeavg)

	if templatearray.shape[0] < 20 or templatearray.shape[1] < 20:
		apDisplay.printWarning("template is only "+str(imgdata.shape[0])+" pixels wide\n"+\
		  " and may only correlation noise in the image")

	return templatearray

def findTemplates(params):
	name = params['template']

	globlist = glob.glob(name+"*")

	params['templatelist'] = []
	for f in globlist:
		if os.path.isfile(f) and f[-4:] == ".mrc":
			params['templatelist'].append(f)

	if not params['templatelist']:
		apDisplay.printError("There are no MRC images found with basename \'"+os.path.basename(name)+"\'\n")

	return(params)

def copyTemplatesToOutdir(params, timestamp=None):
	newlist = []
	for tmpl in params['templatelist']:
		base = os.path.basename(tmpl)
		old = os.path.abspath(tmpl)
		
		### Rename file for new location
		if timestamp is None:
			timestamp = apParam.makeTimestamp()
		#append the name of the directory to the filename
		#basedir = os.path.split(os.path.dirname(old))[1]
		#base = basedir+"_"+base
		name,ext = os.path.splitext(base)
		base = name+"-"+timestamp+ext

		new = os.path.join(params['rundir'], base)
		if os.path.isfile(new):
			mdnew = apFile.md5sumfile(new)
			mdold = apFile.md5sumfile(old)
			if mdnew != mdold:
				apDisplay.printError("a different template with name \'"+new+"\' already exists!")
			elif apDatabase.isTemplateInDB(mdnew):
				apDisplay.printWarning("same template with md5sum \'"+mdnew+"\' already exists in the DB!")
				apDisplay.printMsg("skipping template \'"+old+"\'")
			else:
				apDisplay.printWarning("the same template with name \'"+new+"\' already exists!")
				newlist.append(base)
		else:
			#template is okay to copy and insert
			apDisplay.printMsg("copying file "+old+" to "+new)
			shutil.copyfile(old, new)
			newlist.append(base)
			#and only allow user read access just so they don't get deleted
			os.chmod(new, 0666)
	params['templatelist'] = newlist
	apDisplay.printColor("New template List:","green")
	pprint.pprint(params['templatelist'])
	return
		
def insertTemplateImage(params):
	for i,name in enumerate(params['templatelist']):
		if os.path.basename(name) != name:
			apDisplay.printError("please contact an appion developer, because the database insert is wrong")

		#check if template exists
		templateq=appionData.ApTemplateImageData()
		templateq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
		templateq['templatename']=name
		templateId = templateq.query(results=1)
		if templateId:
			apDisplay.printWarning("template already in database.\nNot reinserting")
			continue

		#check if duplicate template exists
		temppath = os.path.join(params['rundir'], name)
		md5sum = apFile.md5sumfile(temppath)
		templateq2=appionData.ApTemplateImageData()
		templateq2['md5sum']=md5sum
		templateId = templateq2.query(results=1)
		if templateId:
			apDisplay.printWarning("template with the same check sum already exists in database.\nNot reinserting")
			continue

		#insert template to database if doesn't exist
		print "Inserting",name,"into the template database"
		templateq['apix']=params['apix']
		templateq['diam']=params['diam']
		templateq['md5sum']=md5sum 
		if 'alignid' in params and params['alignid'] is not None:
			templateq['alignstack'] = appionData.ApAlignStackData.direct_query(params['alignid'])
		if 'clusterid' in params and params['clusterid'] is not None:
			templateq['clusterstack'] = appionData.ApClusteringStackData.direct_query(params['clusterid'])
		if 'stackid' in params and params['stackid'] is not None:
			templateq['stack'] = appionData.ApStackData.direct_query(params['stackid'])
		if 'imgnums' in params and params['imgnums'] is not None:
			imgnums = params['imgnums'].split(",")
			templateq['stack_image_number']=int(imgnums[i])
		templateq['description']=params['description']
		templateq['project|projects|project']=params['projectId']
		## PHP web tools expect 'hidden' field, set it to False initially
		templateq['hidden'] = False
		if params['commit'] is True:
			time.sleep(2)
			templateq.insert()
		else:
			apDisplay.printWarning("Not commiting template to DB")
	return

