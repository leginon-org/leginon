#!/usr/bin/env python

import os, re, sys, time
import tempfile
import cPickle
import math
import string
import shutil
import subprocess
#appion
import appionData
import apDatabase
import apParam
import apDisplay
import apEMAN
import apEulerDraw
import apChimera
import apStack
import apFile
import apUpload
try:
	import EMAN
except:
	pass
import tarfile

def createDefaults():
	# create default values for parameters
	params={}
	params['runname']='recon1'
	params['stackid']=None
	params['modelid']=None
	params['jobid']=None
	params['jobinfo']=None
	params['chimeraonly']=False
	params['path']=os.path.abspath('.')
	params['rundir']=os.path.abspath('.')
	params['volumes']=[]
	params['classavgs']=[]
	params['classvars']=[]
	params['emanavgs']=[]
	params['coranavgs']=[]
	params['msgpavgs']=[]
	params['iterations']=[]
	params['fscs']=[]
	params['package']='EMAN'
	params['tmpdir']=None
	params['commit']=True
	params['contour']=1.5
	params['oneiteration']=None
	params['zoom']=1.75
	params['description']=None
	return params

def createModelDefaults():
	params={}
	params['apix']=None
	params['boxsize']=None
	params['description']=None
	params['path']=None
	params['rundir']=None
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
	iteration['filt3d']=None
	iteration['shrink']=None
	iteration['euler2']=None
	iteration['xfiles']=None
	iteration['median']=None
	iteration['phasecls']=None
	iteration['fscls']=None
	iteration['refine']=None
	iteration['goodbad']=None
	iteration['perturb']=None
	iteration['msgpasskeep']=None
	iteration['msgpassminp']=None
	return iteration

def printHelp():
	print "\nUsage:\nuploadRecon.py stackid=<n> modelid=<n> [jobid=<cluster job id>] [package=<packagename>] [dir=/path/to/directory] [tmpdir=/path/to/dir] [contour=<n>] [zoom=<n>]\n"
	print "Example: uploadRecon.py stackid=23 modelid=20 package=EMAN\n"
	print "runname=<name>         : name assigned to this reconstruction"
	print "stackid=<n>          : stack Id in the database"
	print "modelid=<n>          : starting model id in the database"
	print "package=<package>    : reconstruction package used (EMAN by default)"
	print "dir=<path>           : directory containing the results of the reconstruction"
	print "                       (current dir is default)"
	print "tmpdir=<path>        : directory to which tmp data is extracted"
	print "                       (./temp is default)"
	print "jobid=<jobid>        : DEF_id of jobfile that was created & run"
	print "contour=<n>          : sigma level at which snapshot of density will be contoured (1.5 by default)"
	print "zoom=<n>             : zoom factor for snapshot rendering (1.75 by default)"
	print "nocommit             : don't commit to database, for testing only"
	print "oneiteration=<n>     : only upload one iteration"
	print "description=\"text\"     : description of the reconstruction - must be in quotes"
	print "\n"

	sys.exit(1)

def parseInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printHelp()

	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='runname'):
			params['runname']=elements[1]
		elif (elements[0]=='stackid'):
			params['stackid']=int(elements[1])
		elif (arg=='nocommit'):
			params['commit']=False
		elif (elements[0]=='modelid'):
			params['modelid']=int(elements[1])
		elif (elements[0]=='package'):
			params['package']=elements[1]
		elif (elements[0]=='dir'):
			params['path']=os.path.abspath(elements[1])
			params['rundir']=os.path.abspath(elements[1])
		elif (elements[0]=='jobid'):
			params['jobid']=int(elements[1])
		elif (elements[0]=='contour'):
			params['contour']=float(elements[1])
		elif (elements[0]=='zoom'):
			params['zoom']=float(elements[1])
		elif (elements[0]=='oneiteration'):
			params['oneiteration']=int(elements[1])
		elif (elements[0]=='description'):
			params['description']=elements[1]
		elif (arg=='chimeraonly'):
			params['chimeraonly']=True
			params['commit']=False
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)

def getModelData(modelid):
	modeldata = appionData.ApInitialModelData.direct_query(modelid)
	if not modeldata:
		apDisplay.printError("Initial model ID: "+str(modelid)+" does not exist in the database")
	apDisplay.printMsg("Selected initial model: "+os.path.join(modeldata['path']['path'], modeldata['name']))
	return modeldata

def listFiles(params):
	for key in ('classavgs', 'classvars', 'volumes', 'fscs', 'emanavgs', 'msgpavgs', 'coranavgs'):
		params[key] = []
	for f in os.listdir(params['rundir']):
		if re.match("threed\.\d+a\.mrc",f):
			params['volumes'].append(f)
		if re.match("classes\.\d+\.img",f):
			params['classavgs'].append(f)
		if re.match("fsc.eotest.\d+",f):
			params['fscs'].append(f)
		if re.match("classes_eman\.\d+\.img",f):
			params['emanavgs'].append(f)
		if re.match("classes_msgp\.\d+\.img",f):
			params['msgpavgs'].append(f)
		if re.match("classes_coran\.\d+\.img",f):
			params['coranavgs'].append(f)

def convertClassAvgFiles(params):
	files_classavg = []
	files_classold = []
	files_classgood = []
	for f in os.listdir(params['rundir']):
		if re.match("classes_eman\.\d+\.img",f):
			return
		if re.match("classes_coran\.\d+\.img",f):
			return
		if re.match("classes_msgp\.\d+\.img",f):
			return
		if re.match("classes\.\d+\.img",f):
			files_classavg.append(f)
		if re.match("classes\.\d+\.old\.img",f):
			files_classold.append(f)
		if re.match("goodavgs\.\d+\.img",f):
			files_classgood.append(f)
	if params['package']=='EMAN':
		for f in files_classavg:
			for ext in ['.img','.hed']:
				oldf = f.replace('.img',ext)
				newf = oldf.replace('classes','classes_eman')
				os.rename(oldf,newf)
				os.symlink(newf,oldf)
	if params['package']=='EMAN/SpiCoran':
		for f in files_classavg:
			for ext in ['.img','.hed']:
				oldf = f.replace('.img',ext)
				newf = oldf.replace('classes','classes_coran')
				os.rename(oldf,newf)
				os.symlink(newf,oldf)
		for f in files_classold:
			for ext in ['.img','.hed']:
				oldf = f.replace('.img',ext)
				newf = oldf.replace('classes','classes_eman')
				new2f = newf.replace('old.','')
				os.rename(oldf,new2f)
	if params['package']=='EMAN/MsgP':
		for f in files_classgood:
			for ext in ['.img','.hed']:
				oldf = f.replace('.img',ext)
				newf = oldf.replace('goodavgs','classes_msgp')
				os.rename(oldf,newf)
				os.symlink(newf,oldf)
		for f in files_classavg:
			for ext in ['.img','.hed']:
				oldf = f.replace('.img',ext)
				newf = oldf.replace('classes','classes_eman')
				os.rename(oldf,newf)

# Parse MsgPassing params through EMAN jobfile
def parseMsgPassingParams(params):
	emanJobFile = os.path.join(params['rundir'], params['jobinfo']['name'])
	if os.path.isfile(emanJobFile):
		lines=open(emanJobFile,'r')
		j=0
		for i,line in enumerate(lines):
			line=string.rstrip(line)
			if re.search("^msgPassing_subClassification.py", line):
				msgpassparams=line.split()
				iteration = params['iterations'][j]
				for p in msgpassparams:
					elements=p.split('=')
					if elements[0]=='corCutOff':
						iteration['msgpasskeep']=float(elements[1])
					elif elements[0]=='minNumOfPtcls':
						iteration['msgpassminp']=int(elements[1])
				j+=1
		lines.close()
	else:
		apDisplay.printError("EMAN Job file: "+emanJobFile+" does not exist!")

def findEmanJobFile(params):
	# first find the job file, if it doesn't exist, use the .eman log file
	if 'jobinfo' in params and params['jobinfo'] is not None:
		logfile = os.path.join(params['rundir'], params['jobinfo']['name'])
		if os.path.isfile(logfile):
			return logfile
	else:
		params['jobinfo'] = None
	logfile = os.path.join(params['rundir'], 'eman.log')
	if os.path.isfile(logfile):
		return logfile
	logfile = os.path.join(params['rundir'], '.emanlog')
	if os.path.isfile(logfile):
		return logfile
	apDisplay.printError("Could not find eman job or log file")

def parseLogFile(params):
	# parse out the refine command from the .emanlog to get the parameters for each iteration
	logfile = findEmanJobFile(params)
	apDisplay.printMsg("parsing eman log file: "+logfile)
	lines=open(logfile,'r')
	params['iterations'] = []
	for line in lines:
		# if read a refine line, get the parameters
		line=string.rstrip(line)
		if re.search("refine \d+ ", line):
			emanparams=line.split(' ')
			if emanparams[0] is "#":
				emanparams.pop(0)
			# get rid of first "refine"
			emanparams.pop(0)
			iteration=defineIteration()
			iteration['num']=emanparams[0]
			iteration['sym']=''
			for p in emanparams:
				elements=p.strip().split('=')
				if elements[0]=='ang':
					iteration['ang']=float(elements[1])
				elif elements[0]=='mask':
					iteration['mask']=int(float(elements[1]))
				elif elements[0]=='imask':
					iteration['imask']=int(float(elements[1]))
				elif elements[0]=='pad':
					iteration['pad']=int(float(elements[1]))
				elif elements[0]=='sym':
					iteration['sym'] = apUpload.findSymmetry(elements[1])
				elif elements[0]=='hard':
					iteration['hard']=int(float(elements[1]))
				elif elements[0]=='classkeep':
					iteration['classkeep']=float(elements[1].strip())
				elif elements[0]=='classiter':
					iteration['classiter']=int(float(elements[1]))
				elif elements[0]=='filt3d':
					iteration['filt3d']=int(float(elements[1]))
				elif elements[0]=='shrink':
					iteration['shrink']=int(float(elements[1]))
				elif elements[0]=='euler2':
					iteration['euler2']=int(float(elements[1]))
				elif elements[0]=='xfiles':
					## trying to extract "xfiles" as entered into emanJobGen.php
					values = elements[1]
					apix,mass,alito = values.split(',')
					iteration['xfiles']=float(mass)
				elif elements[0]=='amask1':
					iteration['amask1']=float(elements[1])
				elif elements[0]=='amask2':
					iteration['amask2']=float(elements[1])
				elif elements[0]=='amask3':
					iteration['amask3']=float(elements[1])
				elif elements[0]=='median':
					iteration['median']=True
				elif elements[0]=='phasecls':
					iteration['phasecls']=True
				elif elements[0]=='fscls':
					iteration['fscls']=True
				elif elements[0]=='refine':
					iteration['refine']=True
				elif elements[0]=='goodbad':
					iteration['goodbad']=True
				elif elements[0]=='perturb':
					iteration['perturb']=True
			params['iterations'].append(iteration)
		if re.search("coran_for_cls.py \d+ ", line):
				params['package']='EMAN/SpiCoran'
		if re.search("msgPassing_subClassification.py \d+ ", line):
				params['package']='EMAN/MsgP'
	apDisplay.printColor("Found "+str(len(params['iterations']))+" iterations", "green")
	lines.close()

def getEulersFromProj(params,iter):
	# get Eulers from the projection file
	eulers=[]
	projfile="proj."+iter+".txt"
	projfile=os.path.join(params['rundir'], projfile)
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

def renderSnapshots(density, res=30, initmodel=None, contour=1.5, zoom=1.0,
		apix=None, sym=None, box=None):
	if sym is None:
		sym = initmodel['symmetry']['eman_name']
	if apix is None:
		apix = initmodel['pixelsize']
	if box is None:
		box = initmodel['boxsize']
	badres = apChimera.filterAndChimera(density, res, apix, box, 'snapshot', contour, zoom, sym)
	return badres

def insertRefinementRun(params):
	runq=appionData.ApRefinementRunData()
	#first two must be unique
	runq['name']=params['runname']
	runq['stack']=params['stack']

	#Recon upload can be continued
	earlyresult=runq.query(results=1)
	if earlyresult:
		apDisplay.printWarning("Run already exists in the database.\nIdentical data will not be reinserted")

	runq['jobfile']=params['jobinfo']
	runq['initialModel']=params['model']
	runq['package']=params['package']
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	runq['description']=params['description']
	runq['initialModel']=params['model']

	result=runq.query(results=1)

	if earlyresult and not result:
		if params['commit'] is True:
			apDisplay.printError("Refinement Run parameters have changed")
		else:
			apDisplay.printWarning("Refinement Run parameters have changed")

	# get stack apix
	params['apix'] = apDatabase.getApixFromStackData(params['stack'])

	apDisplay.printMsg("inserting Refinement Run into database")
	if params['commit'] is True:
		runq.insert()
	else:
		apDisplay.printWarning("not committing results to database")

	#if we insert runq then this returns no results !!!
	# this is a workaround (annoying & bad)
	runq=appionData.ApRefinementRunData()
	runq['name']=params['runname']
	runq['stack']=params['stack']
	runq['jobfile']=params['jobinfo']
	runq['initialModel']=params['model']
	runq['package']=params['package']
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	runq['description']=params['description']
	runq['package']=params['package']
	runq['initialModel']=params['model']

	result = runq.query(results=1)

	# save run entry in the parameters
	if result:
		params['refinementRun'] = result[0]
	elif params['commit'] is True:
		apDisplay.printWarning("Refinement Run was not found, setting to inserted values")
		params['refinementRun'] = runq
	else:
		apDisplay.printWarning("Refinement Run was not found, setting to 'None'")
		params['refinementRun'] = None
	return True

def insertResolutionData(params,iteration):
	fsc = 'fsc.eotest.'+iteration['num']
	fscfile = os.path.join(params['rundir'],fsc)

	if not os.path.isfile(fscfile):
		apDisplay.printWarning("Could not find FSC file: "+fscfile)

	iteration['fscfile'] = fscfile
	if fsc in params['fscs']:
		resq=appionData.ApResolutionData()

		# calculate the resolution:
		halfres = calcRes(fscfile, params['boxsize'], params['apix'])

		# save to database
		resq['half'] = halfres
		resq['fscfile'] = fsc

		apDisplay.printMsg("inserting FSC resolution data into database")
		if params['commit'] is True:
			resq.insert()
		else:
			apDisplay.printWarning("not committing results to database")

		return resq

def insertRMeasureData(params, iteration):
	volumeDensity='threed.'+iteration['num']+'a.mrc'

	volPath = os.path.join(params['rundir'], volumeDensity)
	if not os.path.exists(volPath):
		apDisplay.printWarning("R Measure failed, volume density not found: "+volPath)
		return None

	resolution = runRMeasure(params['apix'], volPath)

	if resolution is None:
		return None

	resq=appionData.ApRMeasureData()
	resq['volume']=volumeDensity
	resq['rMeasure']=resolution

	apDisplay.printMsg("inserting R Measure Data into database")
	if params['commit'] is True:
		resq.insert()
	else:
		apDisplay.printWarning("not committing results to database")

	return resq

def insertIteration(iteration, params):
	refineparamsq=appionData.ApRefinementParamsData()
	refineparamsq['ang']=iteration['ang']
	refineparamsq['mask']=iteration['mask']
	refineparamsq['imask']=iteration['imask']
	refineparamsq['lpfilter']=iteration['lpfilter']
	refineparamsq['hpfilter']=iteration['hpfilter']
	refineparamsq['pad']=iteration['pad']
	refineparamsq['symmetry']=iteration['sym']
	refineparamsq['EMAN_hard']=iteration['hard']
	refineparamsq['EMAN_classkeep']=iteration['classkeep']
	refineparamsq['EMAN_classiter']=iteration['classiter']
	refineparamsq['EMAN_filt3d']=iteration['filt3d']
	refineparamsq['EMAN_shrink']=iteration['shrink']
	refineparamsq['EMAN_euler2']=iteration['euler2']
	refineparamsq['EMAN_xfiles']=iteration['xfiles']
	refineparamsq['EMAN_median']=iteration['median']
	refineparamsq['EMAN_phasecls']=iteration['phasecls']
	refineparamsq['EMAN_fscls']=iteration['fscls']
	refineparamsq['EMAN_refine']=iteration['refine']
	refineparamsq['EMAN_goodbad']=iteration['goodbad']
	refineparamsq['EMAN_perturb']=iteration['perturb']
	refineparamsq['MsgP_cckeep']=iteration['msgpasskeep']
	refineparamsq['MsgP_minptls']=iteration['msgpassminp']

	#create Chimera snapshots
	fscfile = os.path.join(params['rundir'], "fsc.eotest."+iteration['num'])
	halfres = calcRes(fscfile, params['boxsize'], params['apix'])
	volumeDensity = 'threed.'+iteration['num']+'a.mrc'
	volDensPath = os.path.join(params['rundir'], volumeDensity)
	badres = renderSnapshots(volDensPath, halfres, params['model'],
		params['contour'], params['zoom'], params['apix'], box=params['boxsize'])

	## uncommment this for chimera image only runs...
	if params['chimeraonly'] is True:
		return

	# insert resolution data
	if badres != True:
		resData = insertResolutionData(params, iteration)
	else:
		apDisplay.printWarning("resolution reported as nan, not committing results to database")
		return
	RmeasureData = insertRMeasureData(params, iteration)

	classavg='classes.'+iteration['num']+'.img'

	if params['package']== 'EMAN':
		emanclassavg='classes_eman.'+iteration['num']+'.img'
		coranclassavg=None
		msgpassclassavg=None
	elif params['package']== 'EMAN/SpiCoran':
		emanclassavg='classes_eman.'+iteration['num']+'.img'
		coranclassavg='classes_coran.'+iteration['num']+'.img'
		msgpassclassavg=None
	elif params['package']== 'EMAN/MsgP':
		emanclassavg='classes_eman.'+iteration['num']+'.img'
		coranclassavg=None
		msgpassclassavg='classes_msgp.'+iteration['num']+'.img'
	else:
		apDisplay.printError("Refinement Package Not Valid")

	# insert refinement results
	refineq = appionData.ApRefinementData()
	refineq['refinementRun'] = params['refinementRun']
	refineq['refinementParams'] = refineparamsq
	refineq['iteration'] = iteration['num']
	refineq['resolution'] = resData
	refineq['rMeasure'] = RmeasureData
	classvar = 'classes.'+iteration['num']+'.var.img'
	if classavg in params['classavgs']:
		refineq['classAverage'] = classavg
	if classvar in params['classvars']:
		refineq['classVariance'] = classvar
	if volumeDensity in params['volumes']:
		refineq['volumeDensity'] = volumeDensity
	if emanclassavg in params['emanavgs']:
		refineq['emanClassAvg'] = emanclassavg
	if msgpassclassavg in params['msgpavgs']:
		refineq['MsgPGoodClassAvg'] = msgpassclassavg
	if coranclassavg in params['coranavgs']:
		refineq['SpiCoranGoodClassAvg'] = coranclassavg
	apDisplay.printMsg("inserting Refinement Data into database")
	if params['commit'] is True:
		refineq.insert()
	else:
		apDisplay.printWarning("not committing results to database")

	#insert FSC data
	fscfile = os.path.join(params['rundir'], "fsc.eotest."+iteration['num'])
	insertFSC(fscfile, refineq, params['commit'])
	halfres = calcRes(fscfile, params['boxsize'], params['apix'])
	apDisplay.printColor("FSC 0.5 Resolution: "+str(halfres), "cyan")

	# get projections eulers for iteration:
	eulers = getEulersFromProj(params,iteration['num'])

	# get list of bad particles for this iteration
	badprtls = readParticleLog(params['rundir'], iteration['num'])

	# expand cls.*.tar into temp file
	clsf=os.path.join(params['rundir'], "cls."+iteration['num']+".tar")
	print "reading",clsf
	clstar=tarfile.open(clsf)
	clslist=clstar.getmembers()
	clsnames=clstar.getnames()
	print "extracting",clsf,"into temp directory"
	for clsfile in clslist:
		clstar.extract(clsfile,params['tmpdir'])
	clstar.close()

	# for each class, insert particle alignment info into database
	apDisplay.printColor("Inserting Particle Classification Data for "
		+str(len(clsnames))+" classes", "magenta")
	t0 = time.time()
	for cls in clsnames:
		insertParticleClassificationData(params, cls, iteration, eulers, badprtls, refineq, len(clsnames))
	apDisplay.printColor("\nFinished in "+apDisplay.timeString(time.time()-t0), "magenta")

	# remove temp directory
	for file in os.listdir(params['tmpdir']):
		os.remove(os.path.join(params['tmpdir'],file))
	os.rmdir(params['tmpdir'])

	#create euler freq map
	apDisplay.printMsg("creating euler frequency map")
	refrunid = int(params['refinementRun'].dbid)
	iternum = int(iteration['num'])
	if params['package'] == 'EMAN/SpiCoran':
		coran = True
	else:
		coran = False

	apEulerDraw.createEulerImages(refrunid, iternum, path=params['rundir'], coran=coran)

	return


def readParticleLog(path, iternum):
	plogf = os.path.join(path,"particle.log")
	if not os.path.isfile(plogf):
		apDisplay.printError("no particle.log file found")

	f=open(plogf,'r')
	badprtls=[]
	n=str(int(iternum)+1)
	for line in f:
		line=string.rstrip(line)
		if re.search("X\t\d+\t"+str(iternum)+"$",line):
			bits=line.split()
			badprtls.append(bits[1])
		# break out of into the next iteration
		elif re.search("X\t\d+\t"+n+"$",line):
			break
	f.close()
	return badprtls

def insertParticleClassificationData(params,cls,iteration,eulers,badprtls,refineq,numcls,euler_convention='zxz'):
	# get the corresponding proj number & eulers from filename
	replace=re.compile('\D')
	projnum=int(replace.sub('',cls))

	clsfilename=os.path.join(params['tmpdir'],cls)
	sys.stderr.write(".")
	#f=open(clsfilename)
	#apDisplay.printMsg("Class "+str(projnum+1)+" of "+str(numcls)+": inserting "
	#	+str(len(f.readlines())-2)+" particles")
	#f.close()

	# for each cls file get alignments for particles
	f=open(clsfilename)
	for line in f:
		# skip line if not a particle
		if re.search("start",line):
			prtlaliq=appionData.ApParticleClassificationData()

			# gather alignment data from line
			ali=line.split()
			prtlnum = int(ali[0])

			# check if bad particle
			if str(prtlnum) in badprtls:
				prtlaliq['thrown_out']=True

			prtlnum+=1 # offset for EMAN
			qualf=float(ali[2].strip(','))
			other=ali[3].split(',')
			rot=float(other[0])*180./math.pi
			shx=float(other[1])
			shy=float(other[2])
			if (other[3]=='1') :
				prtlaliq['mirror']=True

			# SPIDER coran kept particle
			if params['package']== 'EMAN/SpiCoran':
				corank=bool(int(other[4]))
			else:
				corank=None

			# message passing kept particle
			if params['package']== 'EMAN/MsgP' and len(ali) > 4:
				msgk=bool(int(ali[4]))
			else:
				msgk=None
			# find particle in stack database
			stackpq = appionData.ApStackParticlesData()
			stackpq['stack'] = params['stack']
			stackpq['particleNumber'] = prtlnum
			stackpartdatas = stackpq.query(results=1)

			if not stackpartdatas:
				apDisplay.printError("particle "+str(prtlnum)+" not in stack id="+str(params['stack'].dbid))
			stackp = stackpartdatas[0]

			# insert classification info
			prtlaliq['refinement']=refineq
			prtlaliq['particle']=stackp
			prtlaliq['shiftx']=shx
			prtlaliq['shifty']=shy
			prtlaliq['euler1']=eulers[projnum][0]
			prtlaliq['euler2']=eulers[projnum][1]
			prtlaliq['euler3']=rot
			prtlaliq['quality_factor']=qualf
			prtlaliq['msgp_keep']=msgk
			prtlaliq['coran_keep']=corank
			prtlaliq['euler_convention']=euler_convention

			#apDisplay.printMsg("inserting Particle Classification Data into database")
			if params['commit'] is True:
				prtlaliq.insert()

	f.close()
	return

def calcRes(fscfile, boxsize, apix):
	# calculate the resolution at 0.5

	lastx = 0
	lasty = 0
	f=open(fscfile,'r')
	for line in f:
		line=string.rstrip(line)
		bits=line.split('\t')
		x=float(bits[0])
		y=float(bits[1])
		if isinstance(y,(int,long,float,complex)):
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

#===========
def insertFSC(fscfile, refineData, commit=True):
	if not os.path.isfile(fscfile):
		apDisplay.printWarning("Could not open FSC file: "+fscfile)

	f = open(fscfile,'r')
	apDisplay.printMsg("inserting FSC Data into database")
	numinserts = 0
	for line in f:
		fscq = appionData.ApFSCData()
		fscq['refinementData'] = refineData
		line = string.rstrip(line)
		bits = line.split('\t')
		fscq['pix'] = int(bits[0])
		fscq['value'] = float(bits[1])

		numinserts+=1
		if commit is True:
			fscq.insert()
	apDisplay.printMsg("inserted "+str(numinserts)+" rows of FSC data into database")
	f.close()


#===========
def getRMeasurePath():
	unames = os.uname()
	if unames[-1].find('64') >= 0:
		exename = 'rmeasure64.exe'
	else:
		exename = 'rmeasure32.exe'
	rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		rmeasexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(rmeasexe):
		exename = "rmeasure.exe"
		rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		exename = "rmeasure"
		rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return rmeasexe

#===========
def runRMeasure(apix, volpath, imask=0):
	t0 = time.time()

	apDisplay.printMsg("R Measure, processing volume: "+volpath)
	rmeasexe = getRMeasurePath()
	rmeasproc = subprocess.Popen(rmeasexe, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	fin = rmeasproc.stdin
	fout = rmeasproc.stdout
	fin.write(volpath+"\n"+str(apix)+"\n"+"0,0\n")
	fin.flush()
	fin.close()
	output = fout.readlines()
	fout.close()

	flog = open("rmeasure.log", "a")
	for line in output:
		flog.write(line.rstrip()+"\n")
	flog.close()

	if output is None:
		apDisplay.printWarning("R Measure, FAILED: no output found")
		return None

	resolution = None
	key = "Resolution at FSC = 0.5:"
	keylen = len(key)
	for line in output:
		sline = line.strip()
		if sline[0:keylen] == key:
			#print sline
			blocks = sline.split(key)
			resolution = float(blocks[1])
			break

	apDisplay.printColor("R Measure, resolution: "+str(resolution)+" Angstroms", "cyan")
	apDisplay.printMsg("R Measure, completed in: "+apDisplay.timeString(time.time()-t0))

	return resolution

def getRefineRunDataFromID(refinerunid):
	return appionData.ApRefinementRunData.direct_query(refinerunid)

def getNumIterationsFromRefineRunID(refinerunid):
	refrundata = appionData.ApRefinementRunData.direct_query(refinerunid)
	refq = appionData.ApRefinementData()
	refq['refinementRun'] = refrundata
	refdatas = refq.query()
	if not refdatas:
		return 0
	maxiter = 0
	for refdata in refdatas:
		iternum = refdata['iteration']
		if iternum > maxiter:
			maxiter = iternum
	return maxiter

def getClusterJobDataFromID(jobid):
	return appionData.ApClusterJobData.direct_query(jobid)

def getRefinementsFromRun(refinerundata):
	refineitq=appionData.ApRefinementData()
	refineitq['refinementRun'] = refinerundata
	return refineitq.query()

def getResolutionFromFSCFile(fscfile, boxsize, apix, msg=False):
	if not os.path.isfile(fscfile):
		apDisplay.printError("fsc file does not exist")
	if msg is True:
		apDisplay.printMsg("box: %d, apix: %.3f, file: %s"%(boxsize, apix, fscfile))
	f = open(fscfile, 'r')
	lastx=0
	lasty=0
	for line in f:
		xy = line.strip().split()
		x = float(xy[0])
		y = float(xy[1])
		if x != 0.0 and x < 0.9:
			apDisplay.printWarning("FSC is wrong data format")
		if y > 0.5:
			#store values for later
			lastx = x
			lasty = y
		else:
			# get difference of fsc
			diffy = lasty-y
			# get distance from 0.5
			distfsc = (0.5-y) / diffy
			# get interpolated spatial freq
			intfsc = x - distfsc * (x-lastx)
			# convert to Angstroms
			res = boxsize * apix / intfsc
			f.close()
			return res

def getSessionDataFromReconId(reconid):
	stackid = apStack.getStackIdFromRecon(reconid)
	partdata = apStack.getOneParticleFromStackId(stackid, msg=False)
	sessiondata = partdata['particle']['selectionrun']['session']
	return sessiondata


if __name__ == '__main__':
	r = runRMeasure(1.63,"/ami/data15/appion/08may09b/recon/recon1/threed.20a.mrc",'0,0')
	print r

