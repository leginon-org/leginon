#Part of the new pyappion

import particleData

def insertParticlePicks(params,img,expid,manual=False):
	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=partdb.query(runq, results=1)

	# get corresponding selectionParams entry
	selexonq = particleData.selectionParams(runId=runq)
	selexonresult = partdb.query(selexonq, results=1)

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
