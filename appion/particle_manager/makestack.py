#! /usr/bin/env python
# Will create a stack file based on a set of input parameters using EMAN's batchboxer

import os, re, sys
import string
import data
import ctfData
import dbdatakeeper
import particleData

partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
acedb=dbdatakeeper.DBDataKeeper(db='dbctfdata')
db=dbdatakeeper.DBDataKeeper(db='dbemdata')

def printHelp():
	print "\nUsage:\nmakestack.py <boxfile> [single=<stackfile>] [outdir=<path>] [ace=<n>] [boxsize=<n>] [inspected or inspectfile=<file>] [phaseflip] [noinvert] [spider] mindefocus=<n> maxdefocus=<n>\n"
	print "Examples:\nmakestack.py extract/001ma.box single=stacks/start.hed ace=0.8 boxsize=180 inspected"
	print "makestack.py extract/*.box outdir=stacks/noctf/ ace=0.8 boxsize=180\n"
	print "* Supports wildcards - By default a stack file of the same name as the box file"
	print "  will be created in the current directory *\n"
	print "<boxfile>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>        : subdirectory for output (default=stack1)"
	print "                       do not use this option if you are specifying particular images"
	print "outdir=<path>        : Directory in which to create the stack"
	print "single=<file>        : Create a single stack containing all the boxed particles"
	print "                       (density will be inverted)"
	print "ace=<n>              : Only use micrographs with this ACE confidence value and higher"
	print "selexoncutoff=<n>    : Only use particles of this correlation value and higher"
	print "boxsize=<n>          : Make stacks with this box size"
	print "inspected            : Use only manually inspected images from database"
	print "inspectfile=<file>   : Text file containing results of manually checked images"
	print "phaseflip            : Stack will be phase flipped using best ACE value in database"
	print "noinvert             : If writing to a single stack, images will NOT be inverted"
	print "                       (stack images are inverted by default)"
	print "spider               : Single output stack will be in SPIDER format"
	print "mindefocus=<n>       : Limit the defocus to values above what is specified ( no limits by default )"
	print "                       Example <mindefocus = -1.0e-6>"
	print "maxdefocus=<n>       : Limit the defocus to values below what is specified ( no limits by default )"
	print "                       Example <maxdefocus = -3.0e-6>"
	print "description=\"text\"   : description of the stack being created- surround text with double quotes"
	print "prtlrunId=<n>        : use particles from database corresponding to selexon run id"
	print "commit               : store particles to database"
	print "\n"

	sys.exit(1)
    
def createDefaults():
	# create default values for parameters
	params={}
	params["imgs"]=''
	params["outdir"]=os.path.abspath('.')+'/'
	params["runid"]=None
	params["single"]=None
	params["ace"]=None
	params["boxsize"]=None
	params["inspected"]=None
	params['inspectfile']=None
	params["phaseflip"]=None
	params["hasace"]=False
	params["apix"]=0
	params["kv"]=0
	params["noinvert"]=False
	params["spider"]=False
	params["df"]=0.0
	params['mindefocus']=None
	params['maxdefocus']=None
	params['description']=None
	params['selexonId']=None
	params['selexoncutoff']=None
	params['commit']=False
	params['outdir']=os.path.abspath('.')+'/'
	params['particleNumber']=0
	return params

def parseInput(args):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printHelp()

	# create params dictionary & set defaults
	params=createDefaults()

	lastarg=1

	# first get all images
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		elif (arg=='phaseflip' or arg=='commit' or arg=='noinvert' or arg=='spider'):
			break
		else:
			boxfile=arg
			if (os.path.exists(boxfile)):
				mrcfileroot.append(os.path.splitext(boxfile)[0])
			else:
				print ("file '%s' does not exist \n" % boxfile)
				sys.exit()
		lastarg+=1
	params["imgs"]=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='outdir'):
			outputdir=elements[1]
			# if user has not specified a full path:
			if not outputdir[0]=='/':
				params['outdir']=params['outdir']+outputdir
			else:
				params['outdir']=outputdir
			# make sure the directory path has '/' at end
			if not(params["outdir"][-1]=='/'):
				params["outdir"]=params["outdir"]+'/'
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (elements[0]=='single'):
			params["single"]=elements[1]
		elif (elements[0]=='ace'):
			params["ace"]=float(elements[1])
		elif (elements[0]=='selexoncutoff'):
			params["selexoncutoff"]=float(elements[1])
		elif (elements[0]=='boxsize'):
			params["boxsize"]=int(elements[1])
		elif (elements[0]=='inspectfile'):
			params["inspectfile"]=elements[1]
		elif (arg=='inspected'):
			params["inspected"]=True
		elif (arg=='phaseflip'):
			params["phaseflip"]=True
		elif (arg=='noinvert'):
			params["noinvert"]=True
		elif (arg=='spider'):
			params["spider"]=True
		elif (arg=='commit'):
			params['commit']=True
			# if commit is set, must have a runid:
			if not params['runid']:
				params['runid']='stack1'
		elif (elements[0]=='mindefocus'):
			mindf=float(elements[1])
			if mindf > 0:
				print "mindefocus must be negative and specified in meters"
				sys.exit()
			else:
				params['mindefocus']=mindf*1e6
		elif (elements[0]=='maxdefocus'):
			maxdf=float(elements[1])
			if maxdf > 0:
				print "maxdefocus must be negative and specified in meters" 
				sys.exit()
			else:
				params['maxdefocus']=maxdf*1e6
		elif (elements[0]=='description'):
			params["description"]=elements[1]
		elif (elements[0]=='prtlrunId'):
			params["selexonId"]=int(elements[1])
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)
	return params
    
def getFilePath(img):
	session=img.split('_')[0] # get session from beginning of file name
	f=os.popen('dbemgetpath %s' % session)
	result=f.readlines()
	f.close()
	if (result==[]):
		print "rawdata directory does not exist!\n"
		sys.exit(1)
	else:
		words=result[0].split('\t')
		path=string.rstrip(words[1])
	return path

def checkInspected(img):
	filename=img['filename']+'.mrc'
	f=open(params["inspectfile"],'r')
	results=f.readlines()
	status=''
	for line in results:
		words=line.split('\t')
		if (string.find(words[0],filename)==0):
			status=words[1]
			status.rstrip('\n')
			break
	if (status.rstrip('\n')=='keep'):
		return 'TRUE'
	return 'FALSE'

def getAceValues(params,img):
	# if already got ace values in a previous step,
	# don't do all this over again.
	if params['hasace']==True:
		return
	else:
		filename=img['filename']+'.mrc'
		
		### TEMPORARY WORKAROUND ###
		### data.run & data.image coming up as particleData.run & image,
		### have to reset to ctfData for this to work.
		############################
		data.image=ctfData.image
		data.run=ctfData.run
		############################

		imq=ctfData.image(imagename=filename)
		imparams=acedb.query(imq)

		runq=ctfData.run()
		aceq=ctfData.ace_params()

		ctfq=ctfData.ctf()
		ctfq['imageId']=imq
		ctfq['runId']=runq
		ctfq['aceId']=aceq
		
		ctfparams=acedb.query(ctfq)

		# if ctf data exist for filename
		if ctfparams:
			conf_best=0
			params['kv']=(img['scope']['high tension'])/1000

			# loop through each of the ace runs & get the params with highest confidence value
			for ctfp in ctfparams:
				if (ctfp['aceId']['stig']==0):
					conf1=ctfp['confidence']
					conf2=ctfp['confidence_d']
					if conf_best < conf1 :
						conf_best=conf1
						params['hasace']=True
						params['df']=(ctfp['defocus1'])*-1e6
						params['conf_d']=ctfp['confidence_d']
						params['conf']=ctfp['confidence']
					if conf_best < conf2 :
						conf_best=conf2
						params['hasace']=True
						params['df']=(ctfp['defocus1'])*-1e6
						params['conf_d']=ctfp['confidence_d']
						params['conf']=ctfp['confidence']
				else:
					print "Skipping ace run:", filename, ": ", ctfp['runId']['name'], "because astigmatism was turned on"
					params['hasace']=False
		# set db data back to particle
		############################
		data.image=particleData.image
		data.run=particleData.run
		############################
        return
            
def getPixelSize(imagedata):
	# use image data object to get pixel size
	# multiplies by binning and also by 1e10 to return image pixel size in angstroms
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=imagedata['scope']['magnification']
	pixelsizeq['tem']=imagedata['scope']['tem']
	pixelsizeq['ccdcamera'] = imagedata['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	
	binning=imagedata['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	
	return(pixelsize*1e10)

        
def checkAce():
	conf_d=params["conf_d"]
	conf=params["conf"]
	thresh=params["ace"]
	# if either conf_d or confidence are above threshold, use this image
	if (conf_d>=thresh or conf>=thresh):
		return 'TRUE'
	return 'FALSE'

def batchBox(params, img):
	input=params["filepath"]+'/'+img['filename']+'.mrc'
	output=params["outdir"]+img['filename']+'.hed'

	# create output directory if it does not exist
	if not os.path.exists(params["outdir"]):
		print "creating directory:",params['outdir']
		os.makedirs(params['outdir'])
           
	# if getting particles from database, a temporary
	# box file will be created
	if params['selexonId']:
		dbbox=params['outdir']+"temporaryParticlesFromDB.box"
		writeParticleBoxfile(img,dbbox)
	else:
		dbbox=img['filename']+'.box'

	# write batchboxer command
	if params["boxsize"]:
		cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i insideonly" %(input, dbbox, output, params["boxsize"])
	else: 
 		cmd="batchboxer input=%s dbbox=%s output=%s insideonly" %(input, dbbox, output)

	print "boxing",input
	f=os.popen(cmd)
	f.close()
    
def writeParticleBoxfile(img,dbbox):
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=img.dbid
	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	
	prtlq=particleData.particle(imageId=imq,runId=selexonrun)
	particles=partdb.query(prtlq)

	if (particles):
		#write the tmp box file
		plist=[]
		box=params['boxsize']	
		for prtl in particles:
			if (params['selexoncutoff']):
				if params['selexoncutoff']>prtl['correlation']:
					continue
			# save the particles to the database
			if params['commit']:
				stackpq=particleData.stackParticles()
				stackpq['stackId']=params['stackId']
				stackpq['particleId']=prtl
				stackres=partdb.query(stackpq)
				if not stackres:
					params['particleNumber']=params['particleNumber']+1
					stackpq['particleNumber']=params['particleNumber']
					partdb.insert(stackpq)
			xcoord=prtl['xcoord']-int(box/2)
			ycoord=prtl['ycoord']-int(box/2)
			if (xcoord>0 and ycoord>0):
				plist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
		boxfile=open(dbbox,'w')
		boxfile.writelines(plist)
		boxfile.close()
		
	print img['filename']
	
def phaseFlip(params,img):
	input=params["outdir"]+img['filename']+'.hed'
	output=params["outdir"]+img['filename']+'.ctf.hed'

	cmd="applyctf %s %s parm=%f,200,1,0.1,0,17.4,9,1.53,%i,2,%f setparm flipphase" %(input,output,params["df"],params["kv"],params["apix"])
	print "phaseflipping",input

	f=os.popen(cmd)
	f.close()
    
def singleStack(params,img):
 	if (params["phaseflip"]==True):
		input=params["outdir"]+img['filename']+'.ctf.hed'
	else:
		input=params["outdir"]+img['filename']+'.hed'
	output=params["outdir"]+params["single"]
    
	singlepath=os.path.split(output)[0]

	# create output directory if it does not exist
	if (not os.path.exists(singlepath)):
		os.mkdir(singlepath)
           
	cmd="proc2d %s %s norm=0.0,1.0" %(input, output)
    
	# unless specified, invert the images
	if (params["noinvert"]==False):
		cmd=cmd+" invert"

	# if specified, create spider stack
	if (params["spider"]==True):
		cmd=cmd+" spiderswap"
    
 	print "writing particles to stackfile: %s" %output
	# run proc2d & get number of particles
	f=os.popen(cmd)
 	lines=f.readlines()
	f.close()
	for n in lines:
		words=n.split()
		if 'images' in words:
			count=int(words[-2])

	# create particle log file
	f=open(singlepath+'/.particlelog','a')
	out=''
	for n in range(count-params["particle"]):
		particlenum=str(1+n+params["particle"])
		line=str(particlenum)+'\t'+params["filepath"]+'/'+img['filename']+'.mrc'
		f.write(line+"\n")
	f.close()
	params["particle"]=count
	
	os.remove(params["outdir"]+img['filename']+".hed")
	os.remove(params["outdir"]+img['filename']+".img")
	if (params["phaseflip"]==True):
		os.remove(params["outdir"]+img['filename']+".ctf.hed")
		os.remove(params["outdir"]+img['filename']+".ctf.img")

def writeBoxLog(commandline):
	f=open('.makestacklog','a')
	out=""
	for n in commandline:
		out=out+n+" "
	f.write(out)
	f.write("\n")
	f.close()

# since we're using a batchboxer approach, we must first get a list of
# images that contain particles
def getImgsFromSelexonId(params):
	print "finding Leginon Images that have particles for selexon run:", params['selexonId']

	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	if not (selexonrun):
		print "\nError: specified runId '"+str(params['selexonId'])+"' not in database\n"
		sys.exit()

	imgq=particleData.image()
	prtlq=particleData.particle(runId=selexonrun, imageId=imgq)
	prtllist=partdb.query(prtlq)
	if not (prtllist):
		print "\nError: no particles for run '"+str(params['selexonId'])+"'\n"
		sys.exit()

	# for every particle, get image it came from and create a single list of unique images
	imageIdlist={}
	for prtl in prtllist:
		dbimg=prtl['imageId']
		imgkey=dbimg.dbid
		imgval=dbimg['dbemdata|AcquisitionImageData|image']
		imageIdlist[imgkey]=imgval

	# create a list of image objects that contain particles
	imagelist=[]
	for img in imageIdlist:
		imginfo=db.direct_query(data.AcquisitionImageData,imageIdlist[img],readimages=False)
		imagelist.append(imginfo)

	return(imagelist)

def insertStackParams(params):
	if params['spider']==True:
		fileType='spider'
	else:
		fileType='imagic'

	if params['noinvert']==True:
		inverted=None
	else:
		inverted=True

	# get stack parameters if they already exist in table
	stparamq=particleData.stackParams()
	stparamq['stackPath']=params['outdir']
	stparamq['name']=params['single']

	stackparams=partdb.query(stparamq,results=1)

	# if not in the database, insert new stack parameters
	if not stackparams:
		print "Inserting stack parameters into DB"
		stparamq['description']=params['description']
		stparamq['boxSize']=params['boxsize']
		stparamq['fileType']=fileType
		stparamq['inverted']=inverted
		if params['phaseflip']==True:
			stparamq['phaseFlipped']=True
		if params['ace']:
			stparamq['aceCutoff']=params['ace']
		if params['selexoncutoff']:
			stparamq['selexonCutoff']=params['selexoncutoff']
		if params['inspected']:
			stparamq['checkImage']=True
		if params['mindefocus']:
			stparamq['minDefocus']=params['mindefocus']
		if params['maxdefocus']:
			stparamq['maxDefocus']=params['maxdefocus']
       		partdb.insert(stparamq)
		stp=particleData.stackParams(stackPath=params['outdir'],name=params['single'])
		stackparams=partdb.query(stp,results=1)[0]
	else:
		stackparams=stackparams[0]
		if (stackparams['description']!=params['description'] or
		    stackparams['boxSize']!=params['boxsize'] or
		    stackparams['phaseFlipped']!=params['phaseflip'] or
		    stackparams['aceCutoff']!=params['ace'] or
		    stackparams['selexonCutoff']!=params['selexoncutoff'] or
		    stackparams['checkImage']!=params['inspected'] or
		    stackparams['minDefocus']!=params['mindefocus'] or
		    stackparams['maxDefocus']!=params['maxdefocus'] or
		    stackparams['fileType']!=fileType or
		    stackparams['inverted']!=inverted):
			print "ERROR: All parameters for a particular stack must be identical!"
			print "please check your parameter settings."
			sys.exit()
	# get the stack Id
	params['stackId']=stackparams

#-----------------------------------------------------------------------

if __name__ == '__main__':
	# record command line
	writeBoxLog(sys.argv)

	# parse command line input
	params=parseInput(sys.argv)

	# stack must have a description
	if not params['description']:
		print "\nERROR: Stack must have a description\n"
		sys.exit()
		
	# if a runId is specified, outdir will have a subdirectory named runId
	if params['runid']:
		params['outdir']=params['outdir']+params['runid']+'/'

	# if saving to the database, stack must be a single file
	if params['commit'] and not params['single']:
		print "\nERROR: When committing to database, stack must be a single file."
		print "use the single=filename option"
		sys.exit()

	# if getting particles from db or committing, a box size must be set
	if (params['commit'] or params['selexonId']) and not params['boxsize']:
		print "\nERROR: specify a box size\n"
		sys.exit()

	# if making a single stack, remove existing stack if exists
	if params["single"]:
		stackfile=params["outdir"]+os.path.splitext(params["single"])[0]
		# if saving to the database, store the stack parameters
		if (params['commit']==True):
			insertStackParams(params)
		if (params["spider"]==True):
			if (os.path.exists(stackfile+".spi")):
				os.remove(stackfile+".spi")
    		if (os.path.exists(stackfile+".hed")):
			os.remove(stackfile+".hed")
		if (os.path.exists(stackfile+".img")):
			os.remove(stackfile+".img")
			
		# set up counter for particle log
		p_logfile=params["outdir"]+'.particlelog'

 		if (os.path.exists(p_logfile)):
			os.remove(p_logfile)
		params["particle"]=0
            
	# get images from database if using a selexon runId
	if params['selexonId']:
		images=getImgsFromSelexonId(params)
		
	# get list of input images, since wildcards are supported
	else:
		if not params['imgs']:
			print "\nERROR: enter particle images to box or use a particles selection runId\n"
			sys.exit()
		imglist=params["imgs"]
		images=[]
		for img in imglist:
			imageq=data.AcquisitionImageData(filename=img)
			imageresult=db.query(imageq, readimages=False)
			images=images+imageresult
		params['session']=images[0]['session']['name']
			
	# box particles
	# if any restrictions are set, check the image
	while images:
		img = images.pop(0)

		params['apix']=getPixelSize(img)

 		# get session ID
		params['session']=img['session']['name']
		params['filepath']=img['session']['image path']
		
		# first remove any existing boxed files
		stackfile=params["outdir"]+img['filename']
	
		if (os.path.exists(stackfile+".hed") or os.path.exists(stackfile+".img")):
			os.remove(stackfile+".hed")
			os.remove(stackfile+".img")

		params["hasace"]=False

		# check if the image has been marked as good
		if params["inspectfile"]:
			goodimg=checkInspected(img)
			if (goodimg=='FALSE'):
				print img['filename']+".mrc has been rejected upon inspection"
				continue

		# check that ACE estimation is above confidence threshold
 		if params["ace"]:
			# find ace values in database
 			getAceValues(params,img)
			if (params["hasace"]==False): 
				print img['filename']+".mrc has no ACE values"
				continue
			# if has ace values, see if above threshold
			goodimg=checkAce()
			if (goodimg=='FALSE'):
				print img['filename']+".mrc is below ACE threshold"
				continue

		# skip micrograph that have defocus above or below min/max defocus levels
		if params['mindefocus']:
			getAceValues(params,img) # find ace values in database
			print params['mindefocus'],params['df']
			if params['df'] > params['mindefocus']:
				print img['filename']+".mrc rejected because defocus(",params['df'],") is less than specified in mindefocus (",params['mindefocus'],")"
				continue
	
		if params['maxdefocus']:
			if params['df'] < params['maxdefocus']:
				print img['filename']+".mrc rejected because defocus(",params['df'],") greater than specified in maxdefocus (",params['maxdefocus'],")"
				continue

		# box the particles
		batchBox(params,img)
		if not(os.path.exists(params["outdir"]+img['filename']+".hed")):
			print "no particles were boxed from "+img['filename']+".mrc"
			continue
        
		# phase flip boxed particles if requested
		if (params["phaseflip"]==True):
			getAceValues(params,img) # find ace values in database
			if (params["hasace"]==False): 
				print img['filename']+".mrc has no ACE values"
				continue
			phaseFlip(params,img) # phase flip stack file

		# add boxed particles to a single stack
		if params["single"]:
			singleStack(params,img)

		if os.path.exists(params['outdir']+'temporaryParticlesFromDB.box'):
			os.remove(params['outdir']+'temporaryParticlesFromDB.box')

	print "Done!"
