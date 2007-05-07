# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import shutil
import math
import re
import numarray
import numarray.convolve as convolve
#appion
import apImage
import apDisplay
import apDatabase
import apDB
import appionData

def getTemplates(params):
	print " ... getting templates"
	if params['templateIds']:
		params['template'] = 'originalTemporaryTemplate'
		# get the templates from the database
		apDatabase.getDBTemplates(params)
		# scale them to the appropriate pixel size
		rescaleTemplates(params)
		# set the template name to the copied file names
		params['template']='scaledTemporaryTemplate'
	checkTemplates(params)
	# go through the template mrc files and downsize & filter them
	for tmplt in params['templatelist']:
		downSizeTemplate(tmplt, params)
	print " ... downsize & filtered "+str(len(params['templatelist']))+ \
		" file(s) with root \""+params["template"]+"\""

def rescaleTemplates(params):
	i=1
	#removePreviousTemplates(params)
	for tmplt in params['ogTmpltInfo']:
		ogtmpltname  = "originalTemporaryTemplate"+str(i)+".mrc"
		ogtmpltname  = os.path.join(params['rundir'], ogtmpltname)
		newtmpltname = "scaledTemporaryTemplate"+str(i)+".mrc"
		newtmpltname = os.path.join(params['rundir'], newtmpltname)

		if params['apix'] != params['scaledapix'][i]:
			print "rescaling template",str(i),":",tmplt['apix'],"->",params['apix']
			scalefactor = tmplt['apix'] / params['apix']
			scaleAndClipTemplate(ogtmpltname,(scalefactor,scalefactor),newtmpltname)
			params['scaledapix'][i] = params['apix']
			downSizeTemplate(newtmpltname, params)
		i+=1
	return

def removePreviousTemplates(params):
	for i in range(15):
		filename = "scaledTemporaryTemplate"+str(i)+".dwn.mrc"
		filename = os.path.join(params['rundir'],filename)
		if os.path.isfile(filename):
			apDisplay.printWarning(filename+" already exists. Removing it")
			os.remove(filename)

def scaleAndClipTemplate(filename, scalefactor, newfilename):
	imgdata = apImage.mrcToArray(filename)
	if(imgdata.shape[0] != imgdata.shape[1]):
		apDisplay.printWarning("template is NOT square, this may cause errors")

	scaledimgdata = apImage.scaleImage(imgdata, scalefactor)

	origsize  = scaledimgdata.shape[1]
	#make sure the box size is divisible by 16
	if (origsize % 16 != 0):
		edgeavg = apImage.meanEdgeValue(scaledimgdata)
		padsize  = int(math.ceil(float(origsize)/16)*16)
		padshape = numarray.array([padsize,padsize])
		apDisplay.printMsg("changing box size from "+str(origsize)+" to "+str(padsize))
		scaledimgdata = convolve.iraf_frame.frame(scaledimgdata, padshape, mode="constant", cval=edgeavg)
		#WHY ARE WE USING EMAN???
		#os.system("proc2d "+newfilename+" "+newfilename+" clip="+str(padsize)+\
			#","+str(padsize)+" edgenorm")
	apImage.arrayToMrc(scaledimgdata, newfilename)

def downSizeTemplate(filename, params):
	#downsize and filter arbitary MRC template image
	bin = params['bin']
	imgdata = apImage.mrcToArray(filename)
	boxsize = imgdata.shape
	if (boxsize[0]/bin) % 2 !=0:
		apDisplay.printError("binned image must be divisible by 2")
	if boxsize[0] % bin != 0:
		apDisplay.printError("box size not divisible by binning factor")
	imgdata = apImage.preProcessImage(imgdata, params=params, planeReg=False)

	#replace extension with .dwn.mrc
	ext=re.compile('\.mrc$')
	filename=ext.sub('.dwn.mrc', filename)
	apImage.arrayToMrc(imgdata, filename)
	return

def checkTemplates(params, upload=None):
	# determine number of template files
	# if using 'preptemplate' option, will count number of '.mrc' files
	# otherwise, will count the number of '.dwn.mrc' files
	name = os.path.join(params['rundir'], params['template'])
	params['templatelist'] = []
	stop = False
	# count number of template images.
	# if a template image exists with no number after it
	# counter will assume that there is only one template
	n=0
	while not stop:
		if (os.path.isfile(name+'.mrc') and os.path.isfile(name+str(n+1)+'.mrc')):
			# templates not following naming scheme
			apDisplay.printError("Both "+name+".mrc and "+name+str(n+1)+".mrc exist\n")
		if (os.path.isfile(name+'.mrc')):
			params['templatelist'].append(name+'.mrc')
			n+=1
			stop=True
		elif (os.path.isfile(name+str(n+1)+'.mrc')):
			params['templatelist'].append(name+str(n+1)+'.mrc')
			n+=1
		else:
			stop=True

	if not params['templatelist']:
		apDisplay.printError("There are no template images found with basename \'"+name+"\'\n")

	return(params)

def insertTemplateRun(params,runq,templatenum):

	tid=params['templateIds'][templatenum]
	templateimagedata=apDB.apdb.direct_query(appionData.ApTemplateImageData,tid)
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
	apDB.apdb.insert(templaterunq)
	return

def insertTemplateImage(params):
	for name in params['templatelist']:
		templateq=appionData.ApTemplateImageData()
		templateq['templatepath']=params['abspath']
		templateq['templatename']=name
		templateId=apDB.apdb.query(templateq, results=1)
	        #insert template to database if doesn't exist
		if not (templateId):
			print "Inserting",name,"into the template database"
			templateq['apix']=params['apix']
			templateq['diam']=params['diam']
			templateq['description']=params['description']
			templateq['project|projects|project']=params['projectId']
			apDB.apdb.insert(templateq)
		else:
			print "Warning: template already in database."
			print "Not reinserting"
	return

def checkTemplateParams(params, runq):
	templaterunq=appionData.ApTemplateRunData(selectionrun=runq)
	templaterundata=apDB.apdb.query(templaterunq)
	#make sure of using same number of templates
	if len(params['templateIds'])!=len(templaterundata):
		apDisplay.printError("All parameters for a selexon run must be identical!"+\
			"You do not have the same number of templates as your last run")
	# check all templates

	if params['multiple_range']:
		for n in range(0,len(params['templateIds'])):
			strt=params["startang"+str(n+1)]
			end=params["endang"+str(n+1)]
			incr=params["incrang"+str(n+1)]
			tmpltimagedata=apDB.apdb.direct_query(appionData.ApTemplateImageData,params['templateIds'][n])
			tmpltrunq=appionData.ApTemplateRunData()
			tmpltrunq['selectionrun']=runq
			tmpltrunq['template']=tmpltimagedata
			tmpltrundata=apDB.apdb.query(tmpltrunq,results=1)
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
