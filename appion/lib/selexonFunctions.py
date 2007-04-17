#!/usr/bin/python -O
# Python functions for selexon.py

#python lib
import os, re, sys
import cPickle
import math
import string
import time
#numarray
import numarray
import numarray.convolve as convolve
import numarray.nd_image as nd_image
#leginon
import data
import dbdatakeeper
import convolver
import Mrc
import imagefun
import peakfinder
import correlator
import project
#appion
import particleData
import apDisplay

db=dbdatakeeper.DBDataKeeper()
partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
projdb=dbdatakeeper.DBDataKeeper(db='project')

def createDefaults():
	# create default values for parameters
	params={}
	params["mrcfileroot"]=''
	params["template"]=''
	params["templatelist"]=[]
	params["apix"]=None
	params["diam"]=0
	params["bin"]=4
	params["startang"]=0
	params["endang"]=10
	params["incrang"]=20
	params["thresh"]=0.5
	params["autopik"]=0
	params["lp"]=30
	params["hp"]=600
	params["box"]=0
	params["crud"]=False
	params["cdiam"]=0
	params["cblur"]=3.5
	params["clo"]=0.6
	params["chi"]=0.95
	params["cstd"]=1
	params["crudonly"]=False
	params["continue"]=False
	params["multiple_range"]=False
	params["dbimages"]=False
	params["alldbimages"]=False
	params["session"]=None
	params["preset"]=None
	params["runid"]='run1'
	params["commit"]=False
	params["defocpair"]=False
	params["abspath"]=os.path.abspath('.')+'/'
	params["shiftonly"]=False
	params["templateIds"]=''
	params["ogTmpltInfo"]=[]
	params["scaledapix"]={}
	params["outdir"]=None
	params['description']=None
	params['scale']=1
	params['projectId']=None
	params['prtltype']=None
	params['method']="updated"
	params['overlapmult']=1.5
	params['maxpeaks']=1500
	params["cschi"]=1
	params["csclo"]=0
	params["convolve"]=0
	params["no_hull"]=False
	params["cv"]=False
	params["no_length_prune"]=False
	params["stdev"]=0
	params["test"]=False

	return params

def printUploadHelp():
	print "\nUsage:\nuploadTemplate.py template=<name> apix=<pixel> session=<session> [commit]\n"
	print "selexon template=groEL apix=1.63 session=06nov10a commit\n"
	print "template=<name>      : name should not have the extension, or number."
	print "                       groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>         : angstroms per pixel (unbinned)"
	print "diam=<n>             : approximate diameter of particle (in Angstroms, unbinned)"
	print "session=<sessionId>  : session name associated with template (i.e. 06mar12a)"
	print "description=\"text\"   : description of the template - must be in quotes"
	print "\n"

	sys.exit(1)

def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"

	sys.exit(1)

def printSelexonHelp():
	print "\nUsage:\nselexon.py <file> template=<name> apix=<pixel> diam=<n> bin=<n> [templateIds=<n,n,n,n,...>] [range=<start,stop,incr>] [thresh=<threshold> or autopik=<n>] [lp=<n>] [hp=<n>] [crud or cruddiam=<n>] [crudonly] [crudblur=<n>] [crudlow=<n>] [crudhi=<n>] [box=<n>] [continue] [dbimages=<session>,<preset>] [alldbimages=<session>] [commit] [defocpair] [shiftonly] [outdir=<path>] [method=<method>] [overlapmult=<n>]"
	print "Examples:\nselexon 05jun23a_00001en.mrc template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud"
	print "selexon template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud dbimages=05jun23a,en continue\n"
	print "template=<name>    : name should not have the extension, or number."
	print "                     groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>       : angstroms per pixel (unbinned)"
	print "diam=<n>           : approximate diameter of particle (in Angstroms, unbinned)"
	print "bin=<n>            : images will be binned by this amount (default is 4)"
	print "range=<st,end,i>   : each template will be rotated from the starting angle to the"
	print "                     stop angle at the given increment"
	print "                     User can also specify ranges for each template (i.e. range1=0,60,20)"
	print "                     NOTE: if you don't want to rotate the image, leave this parameter out"
	print "thresh=<thr>       : manual cutoff for correlation peaks (0-1), don't use if want autopik (default is 0.5)"
	print "autopik=<thr>      : automatically calculate threshold, n = average number of particles per image"
	print "                     NOTE: autopik does NOT work for *updated* method"
	print "lp=<n>, hp=<n>     : low-pass and high-pass filter (in Angstroms) - (defaults are 30 & 600)"
	print "                     NOTE: high-pass filtering is currently disabled"
	print "crud               : run the crud finder after the particle selection"
	print "                     (will use particle diameter by default)"
	print "cruddiam=<n>       : set the diameter to use for the crud finder"
	print "                     (don't need to use the \"crud\" option if using this)"
	print "crudblur=<n>       : amount to blur the image for edge detection (default is 3.5 binned_pixels)"
	print "crudlo=<n>         : lower limit for edge detection (0-1, default=0.6)"
	print "crudhi=<n>         : upper threshold for edge detection (0-1, default=0.95)"
	print "crudstd=<n>        : lower limit for scaling the edge detection limits (i.e. stdev of the image) (default=1= never scale)"
	print "crudonly           : only run the crud finder to check and view the settings"
	print "box=<n>            : output will be saved as EMAN box file with given box size"
	print "continue           : if this option is turned on, selexon will skip previously processed"
	print "                     micrographs"
	print "commit             : if commit is specified, particles will be stored to the database (not implemented yet)"
	print "dbimages=<sess,pr> : if this option is turned on, selexon will continuously get images from the database"
	print "alldbimages=<sess> : if this option is turned on selexon will query the database for all images"
	print "                     associated with the session"
	print "runid=<runid>      : subdirectory for output (default=run1)"
	print "                     do not use this option if you are specifying particular images"
	print "defocpair          : calculate shift between defocus pairs"
	print "shiftonly          : skip particle picking and only calculate shifts"
	print "templateIds        : list the database id's of the templates to use"
	print "outdir=<path>      : output directory in which results will be written"
	print "method=<method>    : choices: classic, updated (default), and experimental"
	print "                       classic - calls findem and viewit"
	print "                       updated - uses findem and internally find peaks (default)"
	print "                       experimental - internally generates cc maps and find peaks"
	print "overlapmult=<n>    : distance multiple for two particles to overlap (default is 1.5 X)"
	print "maxpeaks=<n>       : maximum number of particles allowed per image"
	print "crudschi=<n>               : image standard deviation hi limit for scaling the edge detection limits (default=1: use crudhi&crudlo)"
	print "crudsclo=<n>               : image standard deviation lower limit for scaling the edge detection limits (default=0: use crudhi&crudlo)"
	print "convolve=<n>               : if not zero, convolve the thresholded edge blobs with a disk at the particle diameter to unify blobs"
	print "                             and then threshold it at <n> fraction of peak self covolution of the disk (0-1, default=0"
	print "no_hull                    : if ON, convex hull is not calculated"
	print "cv                         : if ON, polygon vertices are calculated us libCV"
	print "no_length_prune            : if ON, pruning by crud perimeters is not done before convex hull"
	print "stdev=<n>                  : if not zero, only regions with stdev larger than n*image_stdev is passed (default=0)"
	print "test                       : if ON, images at each step are saved"
	print "\n"

	sys.exit(1)

def parseUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printUploadHelp()

	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		elif (elements[0]=='session'):
			params['session']=elements[1]
		elif (elements[0]=='description'):
			params['description']=elements[1]
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

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
			if (os.path.exists(boxfile)):
				# in case of multiple extenstions, such as pik files
				splitfname=(os.path.basename(boxfile).split('.'))
				mrcfileroot.append(splitfname[0])
				params['extension']=string.join(splitfname[1:],'.')
				params['prtltype']=splitfname[-1]
			else:
				apDisplay.printError("file \'"+boxfile+"\' does not exist \n")
		lastarg+=1
	params["imgs"]=mrcfileroot

	# save the input parameters into the "params" dictionary
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='scale'):
			params['scale']=int(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

def parseSelexonInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help' or args[1]=='--help' \
		or args[1]=='-h' or args[1]=='-help') :
		printSelexonHelp()

	lastarg=1

	# save the input parameters into the "params" dictionary

	# first get all images
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		elif (arg=='crudonly' or arg=='crud'):
			break
		else:
			mrcfile=arg
			mrcfileroot.append(os.path.splitext(mrcfile)[0])
		lastarg+=1
	params['mrcfileroot']=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=float(elements[1])
		elif (elements[0]=='bin'):
			params['bin']=int(elements[1])
		elif (elements[0]=='range'):
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang']=int(angs[0])
				params['endang']=int(angs[1])
				params['incrang']=int(angs[2])
			else:
				apDisplay.printError("\'range\' must include 3 angle parameters: start, stop, & increment\n")
		elif (re.match('range\d+',elements[0])):
			num=elements[0][-1]
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang'+num]=int(angs[0])
				params['endang'+num]=int(angs[1])
				params['incrang'+num]=int(angs[2])
				params['multiple_range']=True
			else:
 				apDisplay.printError("\'range\' must include 3 angle parameters: start, stop, & increment\n")
		elif (elements[0]=='thresh'):
			params["thresh"]=float(elements[1])
		elif (elements[0]=='autopik'):
			params["autopik"]=float(elements[1])
		elif (elements[0]=='lp'):
			params["lp"]=float(elements[1])
		elif (elements[0]=='hp'):
			params["hp"]=float(elements[1])
		elif (elements[0]=='box'):
			params["box"]=int(elements[1])
		elif (arg=='crud'):
			params["crud"]=True
		elif (elements[0]=='cruddiam'):
			params["crud"]=True
			params["cdiam"]=float(elements[1])
		elif (elements[0]=='crudblur'):
			params["cblur"]=float(elements[1])
		elif (elements[0]=='crudlo'):
			params["clo"]=float(elements[1])
		elif (elements[0]=='crudhi'):
			params["chi"]=float(elements[1])
		elif (elements[0]=='crudstd'):
			params["cstd"]=float(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (arg=='crudonly'):
			params["crudonly"]=True
		elif (arg=='continue'):
			params["continue"]=True
		elif (elements[0]=='templateIds'):
			templatestring=elements[1].split(',')
			params['templateIds']=templatestring
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['session']=dbinfo[0]
				params['preset']=dbinfo[1]
				params["dbimages"]=True
				params["continue"]=True # continue should be on for dbimages option
			else:
				apDisplay.printError("dbimages must include both \'session\' and \'preset\'"+\
					"parameters (ex: \'07feb13a,en\')\n")
		elif (elements[0]=='alldbimages'):
			params['session']=elements[1]
			params['alldbimages']=True
		elif arg=='commit':
			params['commit']=True
		elif arg=='defocpair':
			params['defocpair']=True
		elif arg=='shiftonly':
			params['shiftonly']=True
		elif (elements[0]=='method'):
			params['method']=str(elements[1])
		elif (elements[0]=='overlapmult'):
			params['overlapmult']=float(elements[1])
		elif (elements[0]=='maxpeaks'):
			params['maxpeaks']=int(elements[1])
		elif (elements[0]=='crudschi'):
			params["cschi"]=float(elements[1])
		elif (elements[0]=='crudsclo'):
			params["csclo"]=float(elements[1])
		elif (elements[0]=='convolve'):
			params["convolve"]=float(elements[1])
		elif (elements[0]=='stdev'):
			params["stdev"]=float(elements[1])
		elif (arg=='no_hull'):
			params["no_hull"]=True
		elif (arg=='cv'):
			params["cv"]=True
			params["no_hull"]=True
		elif (arg=='no_length_prune'):
			params["no_length_prune"]=True
		elif (arg=='test'):
			params["test"]=True
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

def runFindEM(params,file):
	apDisplay.printError("this FindEM function no longer exists here")

def getProjectId(params):
	projectdata=project.ProjectData()
	projects=projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name']==params['session']:
			params['projectId']=i['projectId']
	if not params['projectId']:
		apDisplay.printError("no project associated with this session\n")
	return
	
def getOutDirs(params):
	sessionq=data.SessionData(name=params['session']['name'])
	sessiondata=db.query(sessionq)
	impath=sessiondata[0]['image path']
	params['imgdir']=impath+'/'

	if params['outdir']:
		pass
	else:
		outdir=os.path.split(impath)[0]
		outdir=os.path.join(outdir,'extract/')
		params['outdir']=outdir

	params['rundir']=os.path.join(params['outdir'],params['runid'])
	
	if os.path.exists(params['rundir']):
		print " !!! WARNING: run directory for \'"+str(params['runid'])+"\' already exists.\n"
		if params["continue"]==False:
			print " !!! WARNING: continue option is OFF if you WILL overwrite previous run."
			time.sleep(10)
	else:
		os.makedirs(params['rundir'],0777)

	return(params)

def createImageLinks(imagelist):
	apDisplay.printError("this ViewIt function no longer exists here")

def findPeaks(params,file):
	apDisplay.printError("this ViewIt function no longer exists here")

def createJPG(params,img):
	apDisplay.printError("this ViewIt function no longer exists here")

def findCrud(params,file):
	apDisplay.printError("this ViewIt function no longer exists here")

def getImgSize(fname):
	# get image size (in pixels) of the given mrc file
	imageq=data.AcquisitionImageData(filename=fname)
	imagedata=db.query(imageq, results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+fname+" not found in database\n")
	return(size)

def checkTemplates(params,upload=None):
	# determine number of template files
	# if using 'preptemplate' option, will count number of '.mrc' files
	# otherwise, will count the number of '.dwn.mrc' files

	name=params["template"]
	stop=0 

	# count number of template images.
	# if a template image exists with no number after it
	# counter will assume that there is only one template
	n=0
	while (stop==0):
		if (os.path.exists(name+'.mrc') and os.path.exists(name+str(n+1)+'.mrc')):
			# templates not following naming scheme
			apDisplay.printError("Both "+name+".mrc and "+name+str(n+1)+".mrc exist\n")
		if (os.path.exists(name+'.mrc')):
			params['templatelist'].append(name+'.mrc')
			n+=1
			stop=1
		elif (os.path.exists(name+str(n+1)+'.mrc')):
			params['templatelist'].append(name+str(n+1)+'.mrc')
			n+=1
		else:
			stop=1

	if not params['templatelist']:
		apDisplay.printError("There are no template images found with basename \'"+name+"\'\n")

	return(params)

def dwnsizeImg(params,img):
	#downsize and filter leginon image
	imagedata=getImageData(img)    
	bin=params['bin']
	im=binImg(imagedata['image'],bin)
	apix=params['apix']*bin
	im=filterImg(im,apix,params['lp'])

	Mrc.numeric_to_mrc(im,(img+'.dwn.mrc'))
	return

def dwnsizeTemplate(params,filename):
	#downsize and filter arbitary MRC template image
	bin=params['bin']
	im=Mrc.mrc_to_numeric(filename)
	boxsize=im.shape
	if ((boxsize[0]/bin)%2!=0):
		apDisplay.printError("binned image must be divisible by 2\n")
	if (boxsize[0]%bin!=0):
		apDisplay.printError("box size not divisible by binning factor\n")
	#print " ... downsizing", filename
	im=binImg(im,bin)
	#print " ... filtering",filename
	apix=params['apix']*bin
	im=filterImg(im,apix,params['lp'])

	#replace extension with .dwn.mrc
	ext=re.compile('\.mrc$')
	filename=ext.sub('.dwn.mrc',filename)
	Mrc.numeric_to_mrc(im,(filename))
	return

def binImg(img,binning):
	#bin image using leginon imagefun library
	#img must be a numarray image
	return imagefun.bin(img,binning)

def filterImg(img,apix,res):
	# low pass filter image to res resolution
	if res==0:
		print " ... skipping low pass filter"
		return(img)
	else:
		print " ... performing low pass filter"
		c=convolver.Convolver()
		sigma=(res/apix)/3.0
		kernel=convolver.gaussian_kernel(sigma)
		#Mrc.numeric_to_mrc(kernel,'kernel.mrc')
	return(c.convolve(image=img,kernel=kernel))

def pik2Box(params,file):
	box=params["box"]

	if (params["crud"]==True):
		fname="pikfiles/"+file+".a.pik.nocrud"
	else:
		fname="pikfiles/"+file+".a.pik"

	# read through the pik file
	pfile=open(fname,"r")
	piklist=[]
	for line in pfile:
		elements=line.split(' ')
		xcenter=int(elements[1])
		ycenter=int(elements[2])
		xcoord=xcenter - (box/2)
		ycoord=ycenter - (box/2)
		if (xcoord>0 and ycoord>0):
			piklist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
	pfile.close()

	# write to the box file
	bfile=open(file+".box","w")
	bfile.writelines(piklist)
	bfile.close()

	print "results written to \'"+file+".box\'"
	return

def writeSelexLog(commandline, file=".selexonlog"):
	f=open(file,'a')
	out=""
	for n in commandline:
		out=out+n+" "
	f.write(out)
	f.write("\n")
	f.close()

def getDoneDict(selexondonename):
	if os.path.exists(selexondonename):
		# unpickle previously modified dictionary
		f=open(selexondonename,'r')
		donedict=cPickle.load(f)
		f.close()
	else:
		#set up dictionary
		donedict={}
	return (donedict)

def writeDoneDict(donedict,selexondonename):
	f=open(selexondonename,'w')
	cPickle.dump(donedict,f)
	f.close()

def doneCheck(donedict,im):
	# check to see if image has been processed yet and
	# append dictionary if it hasn't
	# this may not be the best way to do this
	if donedict.has_key(im):
		pass
	else:
		donedict[im]=None
	return

def getImageData(imagename):
	# get image data object from database
	imagedataq = data.AcquisitionImageData(filename=imagename)
	imagedata = db.query(imagedataq, results=1, readimages=False)
	#imagedata[0].holdimages=False
	if imagedata:
		return imagedata[0]
	else:
		apDisplay.printError("Image"+imagename+"not found in database\n")

def getPixelSize(img):
	# use image data object to get pixel size
	# multiplies by binning and also by 1e10 to return image pixel size in angstroms
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=img['scope']['magnification']
	pixelsizeq['tem']=img['scope']['tem']
	pixelsizeq['ccdcamera'] = img['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	
	binning=img['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	
	return(pixelsize*1e10)

def getImagesFromDB(session,preset):
	# returns list of image names from DB
	print "Querying database for images"
	sessionq = data.SessionData(name=session)
	presetq=data.PresetData(name=preset)
	imageq=data.AcquisitionImageData()
	imageq['preset'] = presetq
	imageq['session'] = sessionq
	# readimages=False to keep db from returning actual image
	# readimages=True could be used for doing processing w/i this script
	imagelist=db.query(imageq, readimages=False)
	#loop through images and make data.holdimages false 	 
	#this makes it so that data.py doesn't hold images in memory 	 
	#solves a bug where selexon quits after a dozen or so images 	 
	#for img in imagelist: 	 
		#img.holdimages=False
	return (imagelist)

def getAllImagesFromDB(session):
	# returns list of image data based on session name
	print "Querying database for images"
	sessionq= data.SessionData(name=session)
	imageq=data.AcquisitionImageData()
	imageq['session']=sessionq
	imagelist=db.query(imageq, readimages=False)
	return (imagelist)
	


def getDBTemplates(params):
	tmptmplt=params['template']
	i=1
	for tid in params['templateIds']:
		# find templateImage row
		tmpltinfo=partdb.direct_query(data.templateImage, tid)
		if not (tmpltinfo):
			apDisplay.printError("TemplateId "+str(tid)+" not found in database.  Use 'uploadTemplate.py'\n")
		fname=tmpltinfo['templatepath']
		apix=tmpltinfo['apix']
		# store row data in params dictionary
		params['ogTmpltInfo'].append(tmpltinfo)
		# copy file to current directory
		print "getting image:",fname
		os.system("cp "+fname+" "+tmptmplt+str(i)+".mrc")
		params['scaledapix'][i]=0
		i+=1
	return

def rescaleTemplates(img,params):
	i=1
	for tmplt in params['ogTmpltInfo']:
		ogtmpltname="originalTemporaryTemplate"+str(i)+".mrc"
		newtmpltname="scaledTemporaryTemplate"+str(i)+".mrc"
		
		if params['apix']!=params['scaledapix'][i]:
			print "rescaling template",str(i),":",tmplt['apix'],"->",params['apix']
			scalefactor=tmplt['apix']/params['apix']
			scaleandclip(ogtmpltname,(scalefactor,scalefactor),newtmpltname)
			params['scaledapix'][i]=params['apix']
			dwnsizeTemplate(params,newtmpltname)
		i+=1
	return
	
def scaleandclip(fname,scalefactor,newfname):
	image=Mrc.mrc_to_numeric(fname)
	if(image.shape[0] != image.shape[1]):
		apDisplay.printWarning("template is NOT square, this may cause errors")
	boxsz=image.shape
	scaledimg=imagefun.scale(image,scalefactor)

	scboxsz=scaledimg.shape[1]
	#make sure the box size is divisible by 16
	if (scboxsz%16!=0):
		padsize=int(math.ceil(float(scboxsz)/16)*16)
		padshape = numarray.array([padsize,padsize])
		print " ... changing box size from",scboxsz,"to",padsize
		#GET AVERAGE VALUE OF EDGES
		leftedgeavg = nd_image.mean(scaledimg[0:scboxsz, 0:0])
		rightedgeavg = nd_image.mean(scaledimg[0:scboxsz, scboxsz:scboxsz])
		topedgeavg = nd_image.mean(scaledimg[0:0, 0:scboxsz])
		bottomedgeavg = nd_image.mean(scaledimg[scboxsz:scboxsz, 0:scboxsz])
		edgeavg = (leftedgeavg + rightedgeavg + topedgeavg + bottomedgeavg)/4.0
		#PAD IMAGE
		scaledimg = convolve.iraf_frame.frame(scaledimg, padshape, mode="constant", cval=edgeavg)
		#WHY ARE WE USING EMAN???
		#os.system("proc2d "+newfname+" "+newfname+" clip="+str(padsize)+\
			#","+str(padsize)+" edgenorm")
	Mrc.numeric_to_mrc(scaledimg,newfname)

def getDefocusPair(imagedata):
	apDisplay.printError("this DefocusPair function no longer exists here")

def getShift(imagedata1,imagedata2):
	apDisplay.printError("this DefocusPair function no longer exists here")

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	apDisplay.printError("this DefocusPair function no longer exists here")

def recordShift(params,img,sibling,peak):
	apDisplay.printError("this DefocusPair function no longer exists here")

def insertShift(img,sibling,peak):
	apDisplay.printError("this DefocusPair function no longer exists here")

def insertManualParams(params,expid):
	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		print "inserting manual runId into database"
 		manparams=particleData.selectionParams()
 		manparams['runId']=runq
 		manparams['diam']=params['diam']
 		partdb.insert(runq)
 	       	partdb.insert(manparams)
	
def insertSelexonParams(params,expid):

	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		if len(params['templatelist'])==1:
			if params['templateIds']:
				imgname=params['templateIds'][0]
			else:
				imgname=params['abspath']+params['template']+'.mrc'
			insertTemplateRun(params,runq,imgname,params['startang'],params['endang'],params['incrang'])
		else:
			for i in range(1,len(params['templatelist'])+1):
				if params['templateIds']:
					imgname=params['templateIds'][i-1]
				else:
					imgname=params['abspath']+params['template']+str(i)+'.mrc'
				if (params["multiple_range"]==True):
					strt=params["startang"+str(i)]
					end=params["endang"+str(i)]
					incr=params["incrang"+str(i)]
					insertTemplateRun(params,runq,imgname,strt,end,incr)
				else:
					insertTemplateRun(params,runq,imgname,params['startang'],params['endang'],params['incrang'])
 		selexonparams=particleData.selectionParams()
 		selexonparams['runId']=runq
 		selexonparams['diam']=params['diam']
 		selexonparams['bin']=params['bin']
 		selexonparams['manual_thresh']=params['thresh']
 		selexonparams['auto_thresh']=params['autopik']
 		selexonparams['lp_filt']=params['lp']
 		selexonparams['hp_filt']=params['hp']
 		selexonparams['crud_diameter']=params['cdiam']
 		selexonparams['crud_blur']=params['cblur']
 		selexonparams['crud_low']=params['clo']
 		selexonparams['crud_high']=params['chi']
 		selexonparams['crud_std']=params['cstd']
 		partdb.insert(runq)
 	       	partdb.insert(selexonparams)
		
 	# if continuing a previous run, make sure that all the current
 	# parameters are the same as the previous
 	else:
		# get existing selexon parameters from previous run
 		partq=particleData.selectionParams(runId=runq)
		tmpltq=particleData.templateRun(runId=runq)

 		partresults=partdb.query(partq, results=1)
		tmpltresults=partdb.query(tmpltq)
		selexonparams=partresults[0]
		# make sure that using same number of templates
		if len(params['templatelist'])!=len(tmpltresults):
			apDisplay.printError("All parameters for a selexon run must be identical!"+\
				"You do not have the same number of templates as your last run")
		# param check if using multiple ranges for templates
		if (params['multiple_range']==True):
			# check that all ranges have same values as previous run
			for i in range(0,len(params['templatelist'])):
				if params['templateIds']:
					tmpltimgq=partdb.direct_query(data.templateImage,params['templateIds'][i])
				else:
					tmpltimgq=particleData.templateImage()
					tmpltimgq['templatepath']=params['abspath']+params['template']+str(i+1)+'.mrc'

				tmpltrunq=particleData.templateRun()

				tmpltrunq['runId']=runq
				tmpltrunq['templateId']=tmpltimgq

				tmpltNameResult=partdb.query(tmpltrunq,results=1)
				strt=params["startang"+str(i+1)]
				end=params["endang"+str(i+1)]
				incr=params["incrang"+str(i+1)]
				if (tmpltNameResult[0]['range_start']!=strt or
				    tmpltNameResult[0]['range_end']!=end or
				    tmpltNameResult[0]['range_incr']!=incr):
					apDisplay.printError("All parameters for a selexon run must be identical!"+\
						"Template search ranges are not the same as your last run")
		# param check for single range
		else:
			if (tmpltresults[0]['range_start']!=params["startang"] or
			    tmpltresults[0]['range_end']!=params["endang"] or
			    tmpltresults[0]['range_incr']!=params["incrang"]):
				apDisplay.printError("All parameters for a selexon run must be identical!"+\
					"Template search ranges are not the same as your last run")
 		if (selexonparams['diam']!=params['diam'] or
		    selexonparams['bin']!=params['bin'] or
		    selexonparams['manual_thresh']!=params['thresh'] or
		    selexonparams['auto_thresh']!=params['autopik'] or
		    selexonparams['lp_filt']!=params['lp'] or
		    selexonparams['hp_filt']!=params['hp'] or
		    selexonparams['crud_diameter']!=params['cdiam'] or
		    selexonparams['crud_blur']!=params['cblur'] or
		    selexonparams['crud_low']!=params['clo'] or
		    selexonparams['crud_high']!=params['chi'] or
		    selexonparams['crud_std']!=params['cstd']):
			apDisplay.printError("All parameters for a selexon run must be identical!"+\
				"please check your parameter settings.")
	return

def insertTemplateRun(params,runq,imgname,strt,end,incr):
	templateq=particleData.templateRun()
	templateq['runId']=runq

	if params['templateIds']:
		templateId=partdb.direct_query(data.templateImage,imgname)
	else:
		templateImgq=particleData.templateImage(templatepath=imgname)
		templateId=partdb.query(templateImgq,results=1)[0]

	# if no templates in the database, exit
	if not (templateId):
		apDisplay.printError("Template '"+imgname+"' not found in database. Use preptemplate")
	templateq['templateId']=templateId
	templateq['runId']=runq
	templateq['range_start']=float(strt)
	templateq['range_end']=float(end)
	templateq['range_incr']=float(incr)
	partdb.insert(templateq)

def insertTemplateImage(params):
	for name in params['templatelist']:
		templateq=particleData.templateImage()
		templateq['templatepath']=params['abspath']+name
		templateId=partdb.query(templateq, results=1)
	        #insert template to database if doesn't exist
		if not (templateId):
			print "Inserting",name,"into the template database"
			templateq['apix']=params['apix']
			templateq['diam']=params['diam']
			templateq['description']=params['description']
			templateq['project|projects|projectId']=params['projectId']
			partdb.insert(templateq)
	return

def insertParticlePicks(params,img,expid,manual=False):
	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=partdb.query(runq, results=1)

	# get corresponding selectionParams entry
	selexonq=particleData.selectionParams(runId=runq)
	selexonresult=partdb.query(selexonq, results=1)

	legimgid=int(img.dbid)
	legpresetid=None
	if img['preset']:
		legpresetid =int(img['preset'].dbid)

	imgname=img['filename']
	imgq = particleData.image()
	imgq['dbemdata|SessionData|session']=expid
	imgq['dbemdata|AcquisitionImageData|image']=legimgid
	imgq['dbemdata|PresetData|preset']=legpresetid
	imgids=partdb.query(imgq, results=1)

	# if no image entry, make one
	if not (imgids):
		print " ... creating new entry for",apDisplay.shortenImageName(imgname)
		partdb.insert(imgq)
		imgq=None
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session']=expid
		imgq['dbemdata|AcquisitionImageData|image']=legimgid
		imgq['dbemdata|PresetData|preset']=legpresetid
		imgids=partdb.query(imgq, results=1)

	# WRITE PARTICLES TO DATABASE
	print "Inserting particles into database for",apDisplay.shortenImageName(imgname),"..."

	
	# first open pik file, or create a temporary one if uploading a box file
	if (manual==True and params['prtltype']=='box'):
		fname="temporaryPikFileForUpload.pik"

		# read through the pik file
		boxfile=open(imgname+".box","r")
		piklist=[]
		for line in boxfile:
			elements=line.split('\t')
			xcoord=int(elements[0])
			ycoord=int(elements[1])
			xbox=int(elements[2])
			ybox=int(elements[3])
			xcenter=(xcoord + (xbox/2))*params['scale']
			ycenter=(ycoord + (ybox/2))*params['scale']
			if (xcenter < 4096 and ycenter < 4096):
				piklist.append(imgname+" "+str(xcenter)+" "+str(ycenter)+" 1.0\n")			
		boxfile.close()

		# write to the pik file
		pfile=open(fname,"w")
		pfile.writelines(piklist)
		pfile.close()
		
	elif (manual==True and params['prtltype']=='pik'):
		fname=imgname+"."+params['extension']
	else:
		if (params["crud"]==True):
			fname="pikfiles/"+imgname+".a.pik.nocrud"
		else:
			fname="pikfiles/"+imgname+".a.pik"

	# read through the pik file
	pfile=open(fname,"r")
	piklist=[]
	for line in pfile:
		if(line[0] != "#"):
			elements=line.split(' ')
			xcenter=int(elements[1])
			ycenter=int(elements[2])
			corr=float(elements[3])

			particlesq=particleData.particle()
			particlesq['runId']=runq
			particlesq['imageId']=imgids[0]
			particlesq['selectionId']=selexonresult[0]
			particlesq['xcoord']=xcenter
			particlesq['ycoord']=ycenter
			particlesq['correlation']=corr

			presult=partdb.query(particlesq)
			if not (presult):
				partdb.insert(particlesq)
	pfile.close()
	
	return
