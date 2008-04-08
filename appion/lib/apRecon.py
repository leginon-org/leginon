# Python functions for selexon.py

import os, re, sys, time
import tempfile
import cPickle
import math
import string
import appionData
import apDB
import apDatabase
import apParam
import apDisplay
import apEMAN
import apEulerDraw
try:
	import EMAN
except:
	pass
import tarfile


import subprocess

#leginondb = apDB.db
appiondb = apDB.apdb

def createDefaults():
	# create default values for parameters
	params={}
	params['runid']='recon1'
	params['stackid']=None
	params['modelid']=None
	params['jobid']=None
	params['jobinfo']=None
	params['chimeraonly']=False
	params['path']=os.path.abspath('.')
	params['outdir']=os.path.abspath('.')
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
	params['outdir']=None
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
	iteration['msgpasskeep']=None
	iteration['msgpassminp']=None
	return iteration
	
def printHelp():
	print "\nUsage:\nuploadRecon.py stackid=<n> modelid=<n> [jobid=<cluster job id>] [package=<packagename>] [dir=/path/to/directory] [tmpdir=/path/to/dir] [contour=<n>] [zoom=<n>]\n"
	print "Example: uploadRecon.py stackid=23 modelid=20 package=EMAN\n"
	print "runid=<name>         : name assigned to this reconstruction"
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
		if (elements[0]=='runid'):
			params['runid']=elements[1]
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
			params['outdir']=os.path.abspath(elements[1])
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
	modeldata = appiondb.direct_query(appionData.ApInitialModelData, modelid)
	if not modeldata:
		apDisplay.printError("Initial model ID: "+str(modelid)+" does not exist in the database")
	apDisplay.printMsg("Selected initial model: "+os.path.join(modeldata['path']['path'], modeldata['name']))
	return modeldata

def listFiles(params):
	for key in ('classavgs', 'classvars', 'volumes', 'fscs', 'emanavgs', 'msgpavgs', 'coranavgs'):
		params[key] = []
	for f in os.listdir(params['outdir']):
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
	for f in os.listdir(params['outdir']):
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
	emanJobFile = os.path.join(params['outdir'], params['jobinfo']['name']) 
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
		logfile = os.path.join(params['outdir'], params['jobinfo']['name'])
		if os.path.isfile(logfile):
			return logfile
	else:
		params['jobinfo'] = None
	logfile = os.path.join(params['outdir'], 'eman.log')
	if os.path.isfile(logfile):
		return logfile
	logfile = os.path.join(params['outdir'], '.emanlog')
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
			iteration=defineIteration()
			iteration['num']=emanparams[1]
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
				elif elements[0]=='hard':
					iteration['hard']=int(float(elements[1]))
				elif elements[0]=='classkeep':
					iteration['classkeep']=float(elements[1].strip())
				elif elements[0]=='classiter':
					iteration['classiter']=int(float(elements[1]))
				elif elements[0]=='median':
					iteration['median']=True
				elif elements[0]=='phasecls':
					iteration['phasecls']=True
				elif elements[0]=='refine':
					iteration['refine']=True
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
	projfile=os.path.join(params['outdir'], projfile)
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

def renderSnapshots(density, res=30, initmodel=None, contour=1.5, zoom=1.0, stackapix=None):
	# if eotest failed, filter to 30 
	if not res:
		res=30
	if str(res) == 'nan':
		res=100
		badres = True
	else:
		badres = False
	syms = initmodel['symmetry']['symmetry'].split()
	sym = syms[0]
	# strip digits from symmetry
	replace=re.compile('\d')
	sym=replace.sub('',sym)
			
	tmpf = density+'.tmp.mrc'
	
	if stackapix is None:
		apDisplay.printMsg("undefined stack pixelsize, using initial model pixelsize")
		apix = initmodel['pixelsize']
	else:
		apix = stackapix
	box = initmodel['boxsize']
	halfbox = int(initmodel['boxsize']/2)

	#low pass filter the volume to .6 * reported res
	filtres = 0.6*res
	lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f origin=0,0,0' % (density, tmpf, apix, filtres))
	apDisplay.printMsg("Low pass filtering model for images")
	apEMAN.executeEmanCmd(lpcmd)
	chimsnapenv = "%s,%s,%s,%.3f,%.3f" % (tmpf, density, sym, contour, zoom)
	os.environ["CHIMENV"] = chimsnapenv
	appiondir = apParam.getAppionDirectory()
	chimsnappath = os.path.join(appiondir, "bin", "apChimSnapshot.py")
	runChimeraScript(chimsnappath)
	os.remove(tmpf)

	image1 = density+".1.png"
	if not os.path.isfile(image1):
		apDisplay.printError("Chimera failed to generate images")

	# create mrc of central slice for viruses
	tmphed = density + '.hed'
	tmpimg = density + '.img'
	hedcmd = ('proc3d %s %s' % (density,tmphed))
	if sym != 'Icosahedral':
		hedcmd = hedcmd + " rot=90"
	apEMAN.executeEmanCmd(hedcmd)
	pngslice = density + '.slice.png'
	slicecmd = ('proc2d %s %s first=%i last=%i' % (tmphed, pngslice, halfbox, halfbox))
	apEMAN.executeEmanCmd(slicecmd)
	os.remove(tmphed)
	os.remove(tmpimg)
	return badres
	

def runChimeraScript(chimscript):
	apDisplay.printColor("Trying to use chimera for model imaging","cyan")
	apParam.resetVirtualFrameBuffer()
	if 'CHIMERA' in os.environ and os.path.isdir(os.environ['CHIMERA']):
		chimpath = os.environ['CHIMERA']
	else:
		chimpath = None
		apDisplay.printError("Could not find Chimera, 'CHIMERA' environmental variable is unset")
	if not os.path.isdir(chimpath):
		apDisplay.printError("Could not find chimera at: "+chimpath)
	os.environ['CHIMERA'] = chimpath
	os.environ['CHIMERAPATH'] = os.path.join(chimpath,"share")
	os.environ['LD_LIBRARY_PATH'] = os.path.join(chimpath,"lib")+":"+os.environ['LD_LIBRARY_PATH']
	chimexe = os.path.join(chimpath,"bin/chimera")
	if not os.path.isfile(chimexe):
		apDisplay.printError("Could not find chimera at: "+chimexe)
	rendercmd = (chimexe+" python:"+chimscript)
	os.popen(rendercmd)
	return

def insertRefinementRun(params):
	runq=appionData.ApRefinementRunData()
	#first two must be unique
	runq['name']=params['runid']
	runq['stack']=params['stack']

	#Recon upload can be continued
	earlyresult=appiondb.query(runq, results=1)
	if earlyresult:
		apDisplay.printWarning("Run already exists in the database.\nIdentical data will not be reinserted")

	runq['jobfile']=params['jobinfo']
	runq['initialModel']=params['model']
	runq['package']=params['package']
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	runq['description']=params['description']
	runq['initialModel']=params['model']

	result=appiondb.query(runq, results=1)

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
		#appiondb.insert(runq)
	else:
		apDisplay.printWarning("not committing results to database")

	#if we insert runq then this returns no results !!!
	# this is a workaround (annoying & bad)
	runq=appionData.ApRefinementRunData()
	runq['name']=params['runid']
	runq['stack']=params['stack']
	runq['jobfile']=params['jobinfo']
	runq['initialModel']=params['model']
	runq['package']=params['package']
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	runq['description']=params['description']
	runq['package']=params['package']
	runq['initialModel']=params['model']

	result = appiondb.query(runq, results=1)

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
	fscfile = os.path.join(params['outdir'],fsc)

	if not os.path.isfile(fscfile):
		apDisplay.printWarning("Could not find FSC file: "+fscfile)
 
	iteration['fscfile'] = fscfile
	if fsc in params['fscs']:
		resq=appionData.ApResolutionData()

		# calculate the resolution:
		halfres = calcRes(fscfile, params['model']['boxsize'], params['apix'])
		
		# save to database
		resq['half'] = halfres
		resq['fscfile'] = fsc

		apDisplay.printMsg("inserting FSC resolution data into database")
		if params['commit'] is True:
			appiondb.insert(resq)
		else:
			apDisplay.printWarning("not committing results to database")

		return resq

def insertRMeasureData(params, iteration):
	volumeDensity='threed.'+iteration['num']+'a.mrc'

	volPath = os.path.join(params['outdir'], volumeDensity)
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
		appiondb.insert(resq)
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
	refineparamsq['EMAN_hard']=iteration['hard']
	refineparamsq['EMAN_classkeep']=iteration['classkeep']
	refineparamsq['EMAN_classiter']=iteration['classiter']
	refineparamsq['EMAN_median']=iteration['median']
	refineparamsq['EMAN_phasecls']=iteration['phasecls']
	refineparamsq['EMAN_refine']=iteration['refine']
	refineparamsq['MsgP_cckeep']=iteration['msgpasskeep']
	refineparamsq['MsgP_minptls']=iteration['msgpassminp']

	#create Chimera snapshots
	fscfile = os.path.join(params['outdir'], "fsc.eotest."+iteration['num'])
	halfres = calcRes(fscfile, params['model']['boxsize'], params['apix'])
	volumeDensity = 'threed.'+iteration['num']+'a.mrc'
	volDensPath = os.path.join(params['outdir'], volumeDensity)
	badres = renderSnapshots(volDensPath, halfres, params['model'], 
		params['contour'], params['zoom'], params['apix'])

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
		appiondb.insert(refineq)
	else:
		apDisplay.printWarning("not committing results to database")

	#insert FSC data
	fscfile = os.path.join(params['outdir'], "fsc.eotest."+iteration['num'])
	insertFSC(fscfile, refineq, params['commit'])
	halfres = calcRes(fscfile, params['model']['boxsize'], params['apix'])
	apDisplay.printColor("FSC 0.5 Resolution: "+str(halfres), "cyan")

	# get projections eulers for iteration:
	eulers = getEulersFromProj(params,iteration['num'])	
	
	# get # of class averages and # kept
	#params['eulers']=getClassInfo(os.path.join(params['outdir'],classavg))

	# get list of bad particles for this iteration
	badprtls = readParticleLog(params['outdir'], iteration['num'])

	# expand cls.*.tar into temp file
	clsf=os.path.join(params['outdir'], "cls."+iteration['num']+".tar")
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
	apEulerDraw.createEulerImages(refrunid, iternum, path=params['outdir'])

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

def insertParticleClassificationData(params,cls,iteration,eulers,badprtls,refineq,numcls):
	# get the corresponding proj number & eulers from filename
	replace=re.compile('\D')
	projnum=int(replace.sub('',cls))

	eulq=appionData.ApEulerData()
	eulq['euler1']=eulers[projnum][0]
	eulq['euler2']=eulers[projnum][1]
	eulq['euler3']=eulers[projnum][2]

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
			if params['package']== 'EMAN/MsgP':
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
			prtlaliq['eulers']=eulq
			prtlaliq['shiftx']=shx
			prtlaliq['shifty']=shy
			prtlaliq['inplane_rotation']=rot
			prtlaliq['quality_factor']=qualf
			prtlaliq['msgp_keep']=msgk
			prtlaliq['coran_keep']=corank

			#apDisplay.printMsg("inserting Particle Classification Data into database")
			if params['commit'] is True:
				appiondb.insert(prtlaliq)

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
			appiondb.insert(fscq)
	apDisplay.printMsg("inserted "+str(numinserts)+" rows of FSC data into database")
	f.close()


def runRMeasure(apix, volpath):
	t0 = time.time()

	apDisplay.printMsg("R Measure, processing volume: "+volpath)
	fin,fout = os.popen2("rmeasure")
	fin.write(volpath+"\n"+str(apix)+"\n")
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
	return appiondb.direct_query(appionData.ApRefinementRunData, refinerunid) 

def getNumIterationsFromRefineRunID(refinerunid):
	refrundata = appiondb.direct_query(appionData.ApRefinementRunData, refinerunid) 
	refq = appionData.ApRefinementData()
	refq['refinementRun'] = refrundata
	return len(refq.query())

def getClusterJobDataFromID(jobid):
	return appiondb.direct_query(appionData.ApClusterJobData, jobid)

def getRefinementsFromRun(refinerundata):
	refineitq=appionData.ApRefinementData()
	refineitq['refinementRun'] = refinerundata
	return appiondb.query(refineitq)

if __name__ == '__main__':
	r = runRMeasure(6.52,'threed.1a.mrc')
	print r

