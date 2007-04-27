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

def rescaleTemplates(params):
	i=1
	#removePreviousTemplates(params)
	for tmplt in params['ogTmpltInfo']:
		ogtmpltname  = "originalTemporaryTemplate"+str(i)+".mrc"
		ogtmpltname  = os.path.join(params['rundir'],ogtmpltname)
		newtmpltname = "scaledTemporaryTemplate"+str(i)+".mrc"
		newtmpltname = os.path.join(params['rundir'],newtmpltname)

		if params['apix'] != params['scaledapix'][i]:
			print "rescaling template",str(i),":",tmplt['apix'],"->",params['apix']
			scalefactor = tmplt['apix']/params['apix']
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
	imgdata = apImage.preProcessImage(imgdata, bin=params['bin'], apix=params['apix'], lowpass=params['lp'], planeReg=False)

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
