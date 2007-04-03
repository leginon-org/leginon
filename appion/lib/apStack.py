#! /usr/bin/env python
# Will create a stack file based on a set of input parameters using EMAN's batchboxer

import os, re, sys, math
import string
import data
import ctfData
import dbdatakeeper
import particleData

partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
acedb =dbdatakeeper.DBDataKeeper(db='dbctfdata')
db    =dbdatakeeper.DBDataKeeper(db='dbemdata')

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

def checkInspectFile(img):
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
		return (True)
	return (False)

def checkInspectDB(img):
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=img.dbid
	imgresult=partdb.query(imq, results=1)
	if imgresult:
		if imgresult[0]['keep']==True:
			return(True)
	return(False)

def checkPairInspectDB(img,params):
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=params['sibpairs'][img.dbid]
	imgresult=partdb.query(imq, results=1)
	if imgresult:
		if imgresult[0]['keep']==True:
			return(True)
	return(False)

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
	print "\nprocessing:",img['filename']
	input=os.path.join(params["filepath"],(img['filename']+'.mrc'))
	output=os.path.join(params["outdir"],(img['filename']+'.hed'))

	# create output directory if it does not exist
	if not os.path.exists(params["outdir"]):
		print "creating directory:",params['outdir']
		os.makedirs(params['outdir'])
           
	# if getting particles from database, a temporary
	# box file will be created
	if params['selexonId']:
		dbbox=os.path.join(params['outdir'],"temporaryParticlesFromDB.box")
		if params['defocpair']:
			particles,shift=getDefocPairParticles(img,params)
		else:
			particles,shift=getParticles(img)
		if len(particles)>0:			
			###apply limits
			if params['selexonmin'] or params['selexonmax']:
				particles=eliminateMinMaxCCParticles(particles,params)
			
			###save particles
			if len(particles)>0:
				hasparticles=True
				saveParticles(particles,shift,dbbox,params,img)
			else:
				hasparticles=False
		else:
			hasparticles=False
	else:
		dbbox=img['filename']+'.box'
		hasparticles=True
	
	if hasparticles:
		#count number of particles in box file
		f=open(dbbox,'r')
		lines=f.readlines()
		f.close
		nptcls=len(lines)
		# write batchboxer command
		if params["selexonId"]:
			cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i" %(input, dbbox, output, params["boxsize"])
		elif params["boxsize"]:
			cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i insideonly" %(input, dbbox, output, params["boxsize"])
		else: 
	 		cmd="batchboxer input=%s dbbox=%s output=%s insideonly" %(input, dbbox, output)
	
		print "boxing particles"
		f=os.popen(cmd)
		f.close()
		return(nptcls)
	else:
		return(0)		

def getParticles(img):
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=img.dbid
	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	
	prtlq=particleData.particle(imageId=imq,runId=selexonrun)
	particles=partdb.query(prtlq)
	shift={'shiftx':0, 'shifty':0}
	return(particles,shift)
		
def getDefocPairParticles(img,params):
	imq=particleData.image()
	print "finding pair for", img['filename'] 
	imq['dbemdata|AcquisitionImageData|image']=params['sibpairs'][img.dbid]
	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	
	prtlq=particleData.particle(imageId=imq,runId=selexonrun)
	particles=partdb.query(prtlq)
	
	shiftq=particleData.shift()
	shiftq['dbemdata|AcquisitionImageData|image1']=params['sibpairs'][img.dbid]
	shiftdata=partdb.query(shiftq,readimages=False)[0]
	shiftx=shiftdata['shiftx']*shiftdata['scale']
	shifty=shiftdata['shifty']*shiftdata['scale']
	shift={}
	shift['shiftx']=shiftx
	shift['shifty']=shifty
	print "shifting particles by", shiftx, shifty
	return(particles,shift)

def eliminateMinMaxCCParticles(particles,params):
	newparticles=[]
	eliminated=0
	for prtl in particles:
		keep=False
		if params['selexonmin']:
			if params['selexonmin']<prtl['correlation']:
				keep=True
		if params['selexonmax']:
			if params['selexonmax']>prtl['correlation']:
				keep=True
		if keep:
			newparticles.append(prtl)
		else:
			eliminated+=1
	print eliminated,"particles eliminated due to selexonmin or selexonmax"
	return(newparticles)

def saveParticles(particles,shift,dbbox,params,img):
	plist=[]
	box=params['boxsize']
	imgxy=img['camera']['dimension']
	eliminated=0
	for prtl in particles:
		# save the particles to the database
		xcoord=int(math.floor(prtl['xcoord']-(box/2)-shift['shiftx']+0.5))
		ycoord=int(math.floor(prtl['ycoord']-(box/2)-shift['shifty']+0.5))
		if (xcoord>0 and xcoord+box <= imgxy['x'] and ycoord>0 and ycoord+box <= imgxy['y']):
			plist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
			if params['commit']:
				stackpq=particleData.stackParticles()
				stackpq['stackId']=params['stackId']
				stackpq['particleId']=prtl
				stackres=partdb.query(stackpq)
				if not stackres:
					params['particleNumber']=params['particleNumber']+1
					stackpq['particleNumber']=params['particleNumber']
					partdb.insert(stackpq)
		else:
			eliminated+=1
	if eliminated>0:
		print eliminated, "particles eliminated because out of bounds"
	#write boxfile
	boxfile=open(dbbox,'w')
	boxfile.writelines(plist)
	boxfile.close()
	
def phaseFlip(params,img):
	input=os.path.join(params["outdir"],(img['filename']+'.hed'))
	output=os.path.join(params["outdir"],(img['filename']+'.ctf.hed'))

	cmd="applyctf %s %s parm=%f,200,1,0.1,0,17.4,9,1.53,%i,2,%f setparm flipphase" %(input,output,params["df"],params["kv"],params["apix"])
	print "phaseflipping particles"

	f=os.popen(cmd)
	f.close()
    
def singleStack(params,img):
 	if (params["phaseflip"]==True):
		input=os.path.join(params["outdir"],(img['filename']+'.ctf.hed'))
	else:
		input=os.path.join(params["outdir"],(img['filename']+'.hed'))
	output=os.path.join(params["outdir"],params["single"])
    
	singlepath=os.path.split(output)[0]

	# create output directory if it does not exist
	if (not os.path.exists(singlepath)):
		os.mkdir(singlepath)
           
	cmd="proc2d %s %s norm=0.0,1.0" %(input, output)

	# bin images is specified
	if params['bin']:
		cmd=cmd+" shrink=%i" %params['bin']
		
	# unless specified, invert the images
	if (params["noinvert"]==False):
		cmd=cmd+" invert"

	# if specified, create spider stack
	if (params["spider"]==True):
		cmd=cmd+" spiderswap"
    
 	print "writing to: %s" %output
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
	
	os.remove(os.path.join(params["outdir"],(img['filename']+".hed")))
	os.remove(os.path.join(params["outdir"],(img['filename']+".img")))
	if (params["phaseflip"]==True):
		os.remove(os.path.join(params["outdir"],(img['filename']+".ctf.hed")))
		os.remove(os.path.join(params["outdir"],(img['filename']+".ctf.img")))

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

	# get selection run id
	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	if not (selexonrun):
		print "\nError: specified runId '"+str(params['selexonId'])+"' not in database\n"
		sys.exit()
	
	# from id get the session
	sessionid=db.direct_query(data.SessionData,selexonrun['dbemdata|SessionData|session'])
	# get all images from session
	dbimgq=data.AcquisitionImageData(session=sessionid)
	dbimginfo=db.query(dbimgq,readimages=False)
	if not (dbimginfo):
		print "\nError: no images associated with this runId\n"
		sys.exit()

	# for every image, find corresponding image entry in the particle database
	dbimglist=[]
	for img in dbimginfo:
		pimgq=particleData.image()
		pimgq['dbemdata|AcquisitionImageData|image']=img.dbid
		pimg=partdb.query(pimgq)
		if pimg:
			dbimglist.append(img)
	return (dbimglist)

def getImgsDefocPairFromSelexonId(params):
	print "finding Leginon image defocus pairs that have particles for selexon run:", params['selexonId']

	# get selection run id
	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	if not (selexonrun):
		print "\nError: specified runId '"+str(params['selexonId'])+"' not in database\n"
		sys.exit()
	
	# from id get the session
	sessionid=db.direct_query(data.SessionData,selexonrun['dbemdata|SessionData|session'])
	# get all images from session
	dbimgq=data.AcquisitionImageData(session=sessionid)
	dbimginfo=db.query(dbimgq,readimages=False)
	if not (dbimginfo):
		print "\nError: no images associated with this runId\n"
		sys.exit()

	# for every image, find corresponding image entry in the shift table
	dbimglist=[]
	params['sibpairs']={}
	for img in dbimginfo:
		pimgq=particleData.image()
		pimgq['dbemdata|AcquisitionImageData|image']=img.dbid
		pimg=partdb.query(pimgq)
		if pimg:
			simgq=particleData.shift()
			simgq['dbemdata|AcquisitionImageData|image1']=img.dbid
			simgdata=partdb.query(simgq,readimages=False)
			if simgdata:
				simg=simgdata[0]
				siblingimage=db.direct_query(data.AcquisitionImageData,simg['dbemdata|AcquisitionImageData|image2'],readimages=False)
				#create a dictionary for keeping the dbids of image pairs so we don't have to query later
				params['sibpairs'][simg['dbemdata|AcquisitionImageData|image2']]=simg['dbemdata|AcquisitionImageData|image1']
				dbimglist.append(siblingimage)
			else:
				print "Warning: No shift data for ",img['filename']
			
			
	return (dbimglist)

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
		if params['bin']:
			stparamq['bin']=params['bin']
		if params['phaseflip']==True:
			stparamq['phaseFlipped']=True
		if params['ace']:
			stparamq['aceCutoff']=params['ace']
		if params['selexonmin']:
			stparamq['selexonCutoff']=params['selexonmin']
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
		    stackparams['bin']!=params['bin'] or
		    stackparams['phaseFlipped']!=params['phaseflip'] or
		    stackparams['aceCutoff']!=params['ace'] or
		    stackparams['selexonCutoff']!=params['selexonmin'] or
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
