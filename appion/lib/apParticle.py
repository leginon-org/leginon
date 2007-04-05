#Part of the new pyappion

import particleData
import dbdatakeeper
import data


def getParticles(img,params):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=img.dbid
	partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')

	selexonrun=partdb.direct_query(data.run,params['selexonId'])
	prtlq=particleData.particle(imageId=imq,runId=selexonrun)

	particles=partdb.query(prtlq)
	shift={'shiftx':0, 'shifty':0}
	return particles,shift

def getDBparticledataImage(img,expid):
	"""
	This function queries and creates, if not found, dpparticledata.image data
	using dbemdata.AcquisitionImageData image name
	"""
	partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')

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
		print "Inserting image entry for",imgname
                partdb.insert(imgq)
		imgq=None
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session']=expid
		imgq['dbemdata|AcquisitionImageData|image']=legimgid
		imgq['dbemdata|PresetData|preset']=legpresetid
		imgids=partdb.query(imgq, results=1)

	return imgids

def insertParticlePicks(params,img,expid,manual=False):
	"""
	takes an image dict (img) and inserts particles into DB from pik file
	"""
	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=partdb.query(runq, results=1)

	# get corresponding selectionParams entry
	selexonq = particleData.selectionParams(runId=runq)
	selexonresult = partdb.query(selexonq, results=1)

        imgids=getDBparticledataImage(img,expid)

	# WRITE PARTICLES TO DATABASE
	print "Inserting",imgname,"particles into Database..."

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

def insertMakeMaskParams(params):
	partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
	maskPq=particleData.makeMaskParams()
	
	maskPq['dbemdata|SessionData|session']=params['session'].dbid
	maskPq['mask path']=params['rundir']
	maskPq['name']=params['runid']
	maskPq['mask type']=params['masktype']
	maskPq['pdiam']=params['diam']
	maskPq['region diameter']=params['cdiam']
	maskPq['edge blur']=params['cblur']
	maskPq['edge low']=params['clo']
	maskPq['edge high']=params['chi']
	maskPq['region std']=params['stdev']
	maskPq['convolve']=params['convolve']
	maskPq['convex hull']=not params['no_hull']
	maskPq['libcv']=params['cv']

	result=partdb.query(maskPq)
	if not (result):
		partdb.insert(maskPq)
		result=partdb.query(maskPq)
	return result
	
def getMaskParamsByName(params):
	partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
	maskPq=particleData.makMaskParams()
	maskPq['name']=params['runid']
	maskPq['dbemdata|SessionData|session']=params['session'].dbid

	# get corresponding makeMaskParams entry
	result = partdb.query(maskPq, results=1)
	
	return result  
	
		
def insertMaskRegion(maskrun,img,regionInfo):
	partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
	maskRq=particleData.maskRegion()
		
	maskRq['mask']=maskrun
	maskRq['imageId']=img
	maskRq['x']=regionInfo[4][1]
	maskRq['y']=regionInfo[4][0]
	maskRq['area']=regionInfo[0]
	maskRq['perimeter']=regionInfo[3]
	maskRq['mean']=regionInfo[1]
	maskRq['stdev']=regionInfo[2]
	maskRq['keep']=None

	result=partdb.query(maskRq)
	if not (result):
		partdb.insert(maskRq)
	
	return
