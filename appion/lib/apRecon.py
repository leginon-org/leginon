#!/usr/bin/env python
# Python functions for selexon.py

import os, re, sys
import tempfile
import cPickle
import data
import convolver
import Mrc
import numarray.nd_image
import imagefun
import peakfinder
import correlator
import math
import string
import appionData
import apDB
import EMAN
import tarfile

db = apDB.db
partdb = apDB.apdb

def createDefaults():
	# create default values for parameters
	params={}
	params['runid']='recon1'
	params['stackid']=None
	params['modelid']=None
	params['path']=os.path.abspath('.')
	params['volumes']=[]
	params['classavgs']=[]
	params['classvars']=[]
	params['iterations']=[]
	params['fscs']=[]
	params['package']='EMAN'
	params['tmpdir']='./temp'
	params['contour']=1.5
	params['zoom']=1.75
	return params

def createModelDefaults():
	params={}
	params['apix']=None
	params['boxsize']=None
	params['description']=None
	params['path']=None
	params['name']=None

def defineIteration():
	iteration={}
	iteration['num']=None
	iteration['ang']=None
	iteration['mask']=None
	iteration['imask']=None
	iteration['lpfilter']=None
	iteration['hpfilter']=None
	iteration['pad']=None
	iteration['hard']=None
	iteration['classkeep']=None
	iteration['classiter']=None
	iteration['median']=None
	iteration['phasecls']=None
	iteration['refine']=None
	return iteration
	
def printHelp():
	print "\nUsage:\nuploadRecon.py stackid=<n> modelid=<n> [package=<packagename>] [dir=/path/to/directory] [tmpdir=/path/to/dir] [contour=<n>] [zoom=<n>]\n"
	print "Example: uploadRecon.py stackid=23 modelid=20 package=EMAN\n"
	print "runid=<name>         : name assigned to this reconstruction"
	print "stackid=<n>          : stack Id in the database"
	print "modelid=<n>          : starting model id in the database"
	print "package=<package>    : reconstruction package used (EMAN by default)"
	print "dir=<path>           : directory containing the results of the reconstruction"
	print "                       (current dir is default)"
	print "tmpdir=<path>        : directory to which tmp data is extracted"
	print "                       (./temp is default)"
	print "contour=<n>          : sigma level at which snapshot of density will be contoured (1.5 by default)"
	print "zoom=<n>             : zoom factor for snapshot rendering (1.75 by default)"
	print "\n"

	sys.exit(1)

def parseInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printHelp()

	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='stackid'):
			params['stackid']=int(elements[1])
		elif (elements[0]=='modelid'):
			params['modelid']=int(elements[1])
		elif (elements[0]=='package'):
			params['package']=int(elements[1])
		elif (elements[0]=='dir'):
			params['path']=elements[1]
			if (params['path'][-1]=='/'):
				params['path']=params['path'][:-1]
		elif (elements[0]=='contour'):
			params['contour']=float(elements[1])
		elif (elements[0]=='zoom'):
			params['zoom']=float(elements[1])
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)
        
def checkStackId(params):
	stackinfo=partdb.direct_query(data.ApStackParamsData, params['stackid'])
	if not stackinfo:
		print "\nERROR: Stack ID",params['stackid'],"does not exist in the database"
		sys.exit()
	else:
		params['stack']=stackinfo
		print "Stack:",stackinfo['stackPath']+stackinfo['name']
	return
	
def checkModelId(params):
	modelinfo=partdb.direct_query(data.ApInitialModelData, params['modelid'])
	if not modelinfo:
		print "\nERROR: Initial model ID",params['modelid'],"does not exist in the database"
		sys.exit()
	else:
		params['model']=modelinfo
		print "Initial Model:",os.path.join(modelinfo['path'],modelinfo['name'])
	return

def listFiles(params):
	for f in os.listdir(params['path']):
		if re.match("threed\.\d+a\.mrc",f):
			params['volumes'].append(f)
		if re.match("classes\.\d+\.img",f):
			params['classavgs'].append(f)
		if re.match("fsc.eotest.\d+",f):
			params['fscs'].append(f)
			
def parseLogFile(params):
	# parse out the refine command from the .emanlog to get the parameters for each iteration
	logfile=os.path.join(params['path'],'.emanlog')
	print "parsing eman log file:",logfile
	lines=open(logfile,'r')
	for line in lines:
		# if read a refine line, get the parameters
		line=string.rstrip(line)
		if re.search("refine \d+ ", line):
			emanparams=line.split(' ')
			iteration=defineIteration()
			iteration['num']=emanparams[1]
			for p in emanparams:
				elements=p.split('=')
				if elements[0]=='ang':
					iteration['ang']=float(elements[1])
				elif elements[0]=='mask':
					iteration['mask']=int(elements[1])
				elif elements[0]=='imask':
					iteration['imask']=int(elements[1])
				elif elements[0]=='pad':
					iteration['pad']=int(elements[1])
				elif elements[0]=='hard':
					iteration['hard']=int(elements[1])
				elif elements[0]=='classkeep':
					iteration['classkeep']=float(elements[1])
				elif elements[0]=='classiter':
					iteration['classiter']=int(elements[1])
				elif elements[0]=='median':
					iteration['median']=True
				elif elements[0]=='phasecls':
					iteration['phasecls']=True
				elif elements[0]=='refine':
					iteration['refine']=True
			params['iterations'].append(iteration)
	lines.close()
				
def getEulersFromProj(params,iter):
	# get Eulers from the projection file
	eulers=[]
	projfile="proj."+iter+".txt"
	projfile=os.path.join(params['path'],projfile)
	print "reading file, "+projfile
	if not os.path.exists:
		apDisplay.printError("no projection file found for iteration "+iter)
	f = open(projfile,'r')
	for line in f:
		line=line[:-1] # remove newline at end
		i=line.split()
		angles=[i[1],i[2],i[3]]
		eulers.append(angles)
	f.close()
	return eulers
	
def getClassInfo(classes):
	# read a classes.*.img file, get # of images
	imgnum, imgtype = EMAN.fileCount(classes)
	img = EMAN.EMData()
	img.readImage(classes, 0, 1)

	# for projection images, get eulers
	projeulers=[]
	for i in range(imgnum):
		img.readImage(classes, i, 1)
		e = img.getEuler()
		alt = e.thetaMRC()*180./math.pi
		az = e.phiMRC()*180./math.pi
		phi = e.omegaMRC()*180./math.pi
		eulers=[alt,az,phi]
		if i%2==0:
			projeulers.append(eulers)
	return projeulers

def renderSnapshots(density,res,initmodel,contour,zoom):
	syms = initmodel['symmetry']['symmetry'].split()
	sym = syms[0]
	# strip digits from symmetry
	replace=re.compile('\d')
	sym=replace.sub('',sym)
			
	tmpf = density+'.tmp.mrc'
	apix = initmodel['pixelsize']
	box = initmodel['boxsize']
	halfbox = int(initmodel['boxsize']/2)

	#low pass filter the volume to .6 * reported res
	filtres = 0.6*res
	cmd = ('proc3d %s %s apix=%.3f lp=%.2f' % (density, tmpf, apix, filtres))
	os.system(cmd)
	rendercmd = ('chimera ~/pyappion/lib/apChimSnapshot.py %s %s %s %.3f %.3f' % (tmpf, density, sym, contour, zoom))
	
	os.system(rendercmd)
	os.remove(tmpf)

	if sym == 'Icosahedral':	       
		# create mrc of central slice for viruses
		tmphed = density + '.hed'
		hedcmd = ('proc3d %s %s' % (density,tmphed))
		os.system(hedcmd)
		pngslice = density + '.slice.png'
		slicecmd = ('proc2d %s %s first=%i last=%i' % (tmphed, pngslice, halfbox, halfbox))
		os.system(slicecmd)
		os.remove(tmphed)
	return
	
def insertRefinementRun(params):
	runq=appionData.ApRefinementRunData()
	runq['name']=params['runid']
	runq['stack']=params['stack']
	runq['initialModel']=params['model']
	runq['package']=params['package']
	runq['path']=params['path']
	result=partdb.query(runq, results=1)

## 	if result:
## 		print "\nERROR: run already exists in the database\n"
## 		sys.exit()	        

## 	else:

	if not result:
		print "inserting reconstruction run into database"
		partdb.insert(runq)

		runq=appionData.ApRefinementRunData()
		runq['name']=params['runid']
		runq['stack']=params['stack']
		runq['initialModel']=params['model']
		runq['package']=params['package']
		runq['path']=params['path']
		result=partdb.query(runq, results=1)
		
	# save run entry in the parameters
	params['refinementRun']=result[0]

	return

def insertResolutionData(params,iteration):
	fsc='fsc.eotest.'+iteration['num']
	if fsc in params['fscs']:
		resq=appionData.ApResolutionData()

		#fsc file with path:
		fscfile=os.path.join(params['path'],fsc)

		# calculate the resolution:
		halfres=calcRes(fscfile, params['model'])

		# save to database
		resq['half']=halfres
		resq['fscfile']=fsc

		partdb.insert(resq)

		return resq

def insertIteration(iteration,params):
	refineparamsq=appionData.ApRefinementParamsData()
	refineparamsq['ang']=iteration['ang']
	refineparamsq['mask']=iteration['mask']
	refineparamsq['imask']=iteration['imask']
	refineparamsq['lpfilter']=iteration['lpfilter']
	refineparamsq['hpfilter']=iteration['hpfilter']
	refineparamsq['pad']=iteration['pad']
	refineparamsq['EMAN_hard']=iteration['hard']
	refineparamsq['EMAN_classkeep']=iteration['classkeep']
	refineparamsq['EMAN_classiter']=iteration['classiter']
	refineparamsq['EMAN_median']=iteration['median']
	refineparamsq['EMAN_phasecls']=iteration['phasecls']
	refineparamsq['EMAN_refine']=iteration['refine']

	# insert resolution data
	resData=insertResolutionData(params,iteration)

	classavg='classes.'+iteration['num']+'.img'
	
	# insert refinement results
	refineq=appionData.ApRefinementData()
	refineq['refinementRun']=params['refinementRun']
	refineq['refinementParams']=refineparamsq
	refineq['iteration']=iteration['num']
	refineq['resolution']=resData
	classvar='classes.'+iteration['num']+'.var.img'
	volumeDensity='threed.'+iteration['num']+'a.mrc'
	if classavg in params['classavgs']:
		refineq['classAverage']=classavg
	if classvar in params['classvars']:
		refineq['classVariance']=classvar
	if volumeDensity in params['volumes']:
		refineq['volumeDensity']=volumeDensity
	result=partdb.query(refineq, results=1)
	if not result:
		partdb.insert(refineq)

	renderSnapshots(volumeDensity,resData['half'],params['model'],params['contour'],params['zoom'])
		
	# get projections eulers for iteration:
	iteration['eulers']=getEulersFromProj(params,iteration['num'])
	
	# get # of class averages and # kept
#      	params['eulers']=getClassInfo(os.path.join(params['path'],classavg))

        # get list of bad particles for this iteration
	plogf=os.path.join(params['path'],"particle.log")
	if not os.path.exists(plogf):
		apDisplay.printError("no particle.log file found")
	f=open(plogf,'r')
	iteration['badprtls']=[]
	n=str(int(iteration['num'])+1)
	for line in f:
		line=string.rstrip(line)
		if re.search("X\t\d+\t"+iteration['num']+"$",line):
			bits=line.split()
			iteration['badprtls'].append(bits[1])
		# break out of into the next iteration
	        elif re.search("X\t\d+\t"+n+"$",line):
			break
		
	# expand cls.*.tar into temp file
	clsf=os.path.join(params['path'],"cls."+iteration['num']+".tar")
	print "reading",clsf
	clstar=tarfile.open(clsf)
	clslist=clstar.getmembers()
	clsnames=clstar.getnames()
	print "extracting",clsf,"into temp directory"
	for clsfile in clslist:
		clstar.extract(clsfile,params['tmpdir'])
	clstar.close()

	iteration['numclasses']=len(clsnames)
		
	# for each class, insert particle alignment info into database
	prtlaliq=appionData.ApParticleClassificationData()
	for cls in clsnames:
		insertParticleClassificationData(params,cls,iteration,refineq)
	return

def insertParticleClassificationData(params,cls,iteration,refineq):
	clsfilename=os.path.join(params['tmpdir'],cls)
	f=open(clsfilename)

	# get the corresponding proj number & eulers from filename
	replace=re.compile('\D')
	projnum=int(replace.sub('',cls))

	eulq=appionData.ApEulerData()
	eulq['euler1']=iteration['eulers'][projnum][0]
	eulq['euler2']=iteration['eulers'][projnum][1]
	eulq['euler3']=iteration['eulers'][projnum][2]

	print "\tinserting",(len(f.readlines())-2),"particles from class",(projnum+1),"/",iteration['numclasses']
	f.close()
			
	# for each cls file get alignments for particles
	f=open(clsfilename)
	for line in f:
		# skip line if not a particle
		if re.search("start",line):
			prtlaliq=appionData.ApParticleClassificationData()

			# gather alignment data from line
			ali=line.split()
			prtlnum=int(ali[0])

			# check if bad particle
			if str(prtlnum) in iteration['badprtls']:
				prtlaliq['thrown_out']=True

				prtlnum+=1 # offset for EMAN
				qualf=float(ali[2].strip(','))
				other=ali[3].split(',')
				rot=float(other[0])*180./math.pi
				shx=float(other[1])
				shy=float(other[2])
				if (other[3]=='1') :
					prtlaliq['mirror']=True

				# find particle in stack database
				stackpq=appionData.ApStackParticlesData()
				stackpq['stackparams']=params['stack']
				stackpq['particleNumber']=prtlnum
				stackp=partdb.query(stackpq, results=1)[0]

				if not stackp:
					apDisplay.printError("particle "+prtlnum+" not in stack")
						
				# insert classification info
				prtlaliq['refinement']=refineq
				prtlaliq['particle']=stackp
				prtlaliq['eulers']=eulq
				prtlaliq['shiftx']=shx
				prtlaliq['shifty']=shy
				prtlaliq['inplane_rotation']=rot
				prtlaliq['quality_factor']=qualf
				partdb.insert(prtlaliq)
	f.close()
	return

def calcRes(fscfile, model):
	# calculate the resolution at 0.5

	# get box size and pixel size from model
	boxsize=int(model['boxsize'])
	apix=float(model['pixelsize'])
	
	lastx = 0
	lasty = 0
	f=open(fscfile,'r')
	for line in f:
		line=string.rstrip(line)
		bits=line.split('\t')
		x=float(bits[0])
		y=float(bits[1])
		if float(y)>0.5:
			lastx=x
			lasty=y
		else:
			# get difference of fsc points
			diffy=lasty-y
			# get distance from 0.5
			distfsc=(0.5-y)/diffy
			#get interpolated spatial frequency
			intfsc=x-(distfsc*(x-lastx))

			res=boxsize*apix/intfsc
			return res
	f.close()
	return
	
def writeReconLog(commandline):
        f=open('.reconlog','a')
        out=""
        for n in commandline:
                out=out+n+" "
        f.write(out)
        f.write("\n")
        f.close()
