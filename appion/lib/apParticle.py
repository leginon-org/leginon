#Part of the new pyappion

import particleData
#import dbdatakeeper
import data
import os
import apImage
import ImageDraw
import apDB

#partdb=dbdatakeeper.DBDataKeeper(db='dbappiondata')
partdb = apDB.apdb

def getParticles(img,params):
	"""
	returns paticles (as a list of dicts) for a given image
	ex: particles[0]['xcoord'] is the xcoord of particle 0
	"""
	
	imq=particleData.image()
	imq['dbemdata|AcquisitionImageData|image']=img.dbid

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
	particlesq=particleData.particle()
	
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
		result=[maskPq.dbid]
	return result

def getMaskParamsByName(params):
	maskPq=particleData.makeMaskParams()
	maskPq['name']=params['runid']
	maskPq['dbemdata|SessionData|session']=params['session'].dbid

	# get corresponding makeMaskParams entry
	result = partdb.query(maskPq, results=1)
	
	return result  
	
		
def insertMaskRegion(maskrun,partdbimg,regionInfo):
	maskRq=particleData.maskRegion()
		
	maskRq['mask']=maskrun
	maskRq['imageId']=partdbimg
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

def getMaskRegions(maskrun,img):
	maskRq=particleData.maskRegion()

	maskRq['mask']=maskrun
	maskRq['imageId']=img
	
	results=partdb.query(maskRq)
	
	return results	

def createPeakJpeg(img,peaks,params):
	#Does NOT use viewit
	#Resulting in a 2-fold speed up over createJPG()
	#With more features!!!

	count =   len(params['templatelist'])
	bin =     int(params["bin"])/2
	diam =    float(params["diam"])
	apix =    float(params["apix"])
	if bin < 1: 
		bin = 1
	pixrad  = diam/apix/2.0/float(bin)

	jpegdir = os.path.join(params['rundir'],"jpgs")
	if not (os.path.exists(jpegdir)):
		os.mkdir(jpegdir)

	numer = apImage.preProcessImageParams(img['image'],params)
	image = apImage.arrayToImage(numer)
	image = image.convert("RGB")

	draw = ImageDraw.Draw(image)

	drawPeaks(peaks, draw, bin, pixrad)

	outfile = os.path.join(jpegdir,img['filename']+".prtl.jpg")
	print " ... writing JPEG: ",outfile

	image.save(outfile, "JPEG", quality=95)

	del image,numer,draw

	return

def drawPeaks(peaks,draw,bin,pixrad,circmult=1.0,numcircs=2,circshape="circle"):
	"""	
	Takes peak list and draw circles around all the peaks
	"""
	circle_colors = [ \
		"#ff4040","#3df23d","#3d3df2", \
		"#f2f23d","#3df2f2","#f23df2", \
		"#f2973d","#3df297","#973df2", \
		"#97f23d","#3d97f2","#f23d97", ]
	"""	
	Order: 	Red, Green, Blue, Yellow, Cyan, Magenta,
		Orange, Teal, Purple, Lime-Green, Sky-Blue, Pink
	"""
	ps=float(circmult*pixrad) #1.5x particle radius

	#00000000 1 2 3333 44444 5555555555 666666666 777777777
	#filename x y mean stdev corr_coeff peak_size templ_num angle moment
	for p in peaks:
		x1=float(p['xcoord'])/float(bin)
		y1=float(p['ycoord'])/float(bin)

		if 'template' in p:
			#GET templ_num
			num = int(p['template'])%12
		elif 'size' in p:
			#GET templ_num
			num = int(p['size']*255)%12
		else:
			num = 0
		#Draw (numcircs) circles of size (circmult*pixrad)
		count = 0
		while(count < numcircs):
			tps = ps + count
			coord=(x1-tps, y1-tps, x1+tps, y1+tps)
			if(circshape == "square"):
				draw.rectangle(coord,outline=circle_colors[num])
			else:
				draw.ellipse(coord,outline=circle_colors[num])
			count = count + 1

	return 

