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
import apDisplay
import apDatabase
import apDB
import appionData

appiondb = apDB.apdb


def getTemplates(params):
	"""
	Reads params['templateIds'], a list of template ids
	Copies and scales templates
	Returns params['templatelist'], a list of template file basenames
	"""

	apDisplay.printMsg("getting templates")

	if not params['templateIds']:
		apDisplay.printError("No template ids were specified")

	params['templatelist'] = [] #list of scaled files 
	for i,templateid in enumerate(params['templateIds']):
		index = i+1
		#QUERY DB FOR TEMPLATE INFO
		templatedata = appiondb.direct_query(appionData.ApTemplateImageData, templateid)
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
		shutil.copy(origtemplatepath, copytemplatepath)

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

		#ADD TO TEMPLATE LIST
		params['templatelist'].append(os.path.basename(filtertemplatepath))

	#FINISH LOOP OVER template ids
	#Set the apix
	params['templateapix'] = params['apix']
	apDisplay.printMsg("scaled & filtered "+str(len(params['templatelist']))+" file(s)")

	return params['templatelist']


def getTemplateFromId(templateid):
	return appiondb.direct_query(appionData.ApTemplateImageData, templateid)

def scaleTemplate(templatearray, scalefactor=1.0, boxsize=None):

	if(templatearray.shape[0] != templatearray.shape[1]):
		apDisplay.printWarning("template shape is NOT square, this may cause errors")

	if abs(scalefactor - 1.0) > 0.01:
		templatearray = apImage.scaleImage(templatearray, scalefactor)

	#make sure the box size is divisible by 16
	if boxsize is not None or (templatearray.shape[0] % 16 != 0):
		edgeavg = apImage.meanEdgeValue(templatearray)
		origsize = templatearray.shape[0]
		if boxsize is None:
			padsize  = int(math.ceil(float(origsize)/16)*16)
		else:
			padsize = boxsize
		padshape = numpy.array([padsize,padsize])
		apDisplay.printMsg("changing box size from "+str(origsize)+" to "+str(padsize))
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

	apDisplay.printColor("Template List:","green")
	pprint.pprint(params['templatelist'])

	time.sleep(1)

	return(params)

def copyTemplatesToOutdir(params):
	newlist = []
	for tmpl in params['templatelist']:
		base = os.path.basename(tmpl)
		old = os.path.abspath(tmpl)
		
		#append the name of the directory to the filename
		basedir = os.path.split(os.path.dirname(old))[1]
		base = basedir+"_"+base
		newlist.append(base)

		new = os.path.join(params['outdir'], base)
		if os.path.isfile(new):
			apDisplay.printError("template \'"+new+"\' already exists!\n")
		apDisplay.printMsg("copying file "+old+" to "+new)
		shutil.copy(old, new)
		#and only allow user read access just so they don't get deleted
		os.chmod(new, 0666)
	params['templatelist'] = newlist
	apDisplay.printColor("New template List:","green")
	pprint.pprint(params['templatelist'])
	return
		
def insertTemplateRun(params,runq,templatenum):
	tid=params['templateIds'][templatenum]
	templateimagedata=appiondb.direct_query(appionData.ApTemplateImageData,tid)
	# if no templates in the database, exit
	if not (templateimagedata):
		apDisplay.printError("Template '"+tid+"' not found in database. Use uploadTemplates.py")

	if params['multiple_range']:
		strt=params["startang"+str(templatenum+1)]
		end=params["endang"+str(templatenum+1)]
		incr=params["incrang"+str(templatenum+1)]
	else:
		strt=params['startang']
		end=params['endang']
		incr=params['incrang']
	
	templaterunq=appionData.ApTemplateRunData()
	templaterunq['selectionrun']=runq	
	templaterunq['template']=templateimagedata
	templaterunq['range_start']=float(strt)
	templaterunq['range_end']=float(end)
	templaterunq['range_incr']=float(incr)
	if params['commit'] is True:
		appiondb.insert(templaterunq)
	return

def insertTemplateImage(params):
	for name in params['templatelist']:
		if os.path.basename(name) != name:
			apDisplay.printError("please contact an appion developer, because the database insert is wrong")

		#check if template exists
		templateq=appionData.ApTemplateImageData()
		templateq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
		templateq['templatename']=name
		templateId = appiondb.query(templateq, results=1)
		if templateId:
			apDisplay.printWarning("template already in database.\nNot reinserting")
			continue

		#check if duplicate template exists
		temppath = os.path.join(params['outdir'], name)
		md5sum = apFile.md5sumfile(temppath)
		templateq2=appionData.ApTemplateImageData()
		templateq2['md5sum']=md5sum
		templateId = appiondb.query(templateq2, results=1)
		if templateId:
			apDisplay.printWarning("template with the same check sum already exists in database.\nNot reinserting")
			continue

		#insert template to database if doesn't exist
		print "Inserting",name,"into the template database"
		templateq['apix']=params['apix']
		templateq['diam']=params['diam']
		templateq['md5sum']=md5sum 
		if params['norefid'] is not None:
			templateq['noref'] = appiondb.direct_query(appionData.ApNoRefClassData, params['norefid'])
		if params['stackid'] is not None:
			templateq['stack'] = appiondb.direct_query(appionData.ApStackData, params['stackid'])
		if params['stackimgnum'] is not None:
			templateq['stack_image_num']=params['stackimgnum']
		templateq['description']=params['description']
		templateq['project|projects|project']=params['projectId']
		if params['commit'] is True:
			time.sleep(2)
			appiondb.insert(templateq)

	return

def checkTemplateParams(runq, params):
	templaterunq = appionData.ApTemplateRunData(selectionrun=runq)
	templaterundata = appiondb.query(templaterunq)
	if not templaterundata:
		return True
	#make sure of using same number of templates
	if len(params['templateIds']) != len(templaterundata):
		apDisplay.printError("All parameters for a selexon run must be identical!\n"+\
			"You do not have the same number of templates as your last run")
	# check all templates

	if params['multiple_range']:
		for n in range(0,len(params['templateIds'])):
			strt=params["startang"+str(n+1)]
			end=params["endang"+str(n+1)]
			incr=params["incrang"+str(n+1)]
			tmpltimagedata=appiondb.direct_query(appionData.ApTemplateImageData,params['templateIds'][n])
			tmpltrunq=appionData.ApTemplateRunData()
			tmpltrunq['selectionrun']=runq
			tmpltrunq['template']=tmpltimagedata
			tmpltrundata=appiondb.query(tmpltrunq,results=1)
			if (tmpltrundata[0]['range_start']!=strt or
				tmpltrundata[0]['range_end']!=end or
				tmpltrundata[0]['range_incr']!=incr):
				apDisplay.printError("All parameters for a selexon run must be identical!"+\
					"Template search ranges are not the same as your last run")
	else:
		if (templaterundata[0]['range_start']!=params['startang'] or
			templaterundata[0]['range_end']!=params['endang'] or
			templaterundata[0]['range_incr']!=params['incrang']):
			apDisplay.printError("All parameters for a selexon run must be identical!"+\
				"Template search ranges are not the same as your last run")
	return
