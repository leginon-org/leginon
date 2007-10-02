#!/usr/bin/python -O

import sys
import os
import re
import time
import glob
import shutil
import leginondata
import apXml
import apParam
import apDisplay
import apDB
import apDatabase
import apStack
import appionData
import apTemplate
leginondb = apDB.db
appiondb = apDB.apdb
functionname = "classifier"

def defaults():
	params = {}
	params['numparticles']=3000
	params['numclasses']=40
	params['stackname']=None
	params['session']=None
	params['stackid']=None
	params['diam']=None
	params['bin']=1
	params['imask']=0
	params['lp']=0
	params['outdir']=None
	params['mask']=None
	params['runid']=None
	params['description']=None
	params['commit']=False
	params['classonly']=False
	params['refid']=None
	params['xysearch']=None
	params['iter']=2
	params['csym']=1
	
	return params

def getAppionDir(params):
	params['appiondir'] = None

	trypath = os.environ.get('APPIONDIR')
	if os.path.isdir(trypath):
		params['appiondir'] = trypath
		return params['appiondir']

	user = os.environ.get('USER')
	trypath = "/home/"+user+"/pyappion"
 	if os.path.isdir(trypath):
		params['appiondir'] = trypath
		return params['appiondir']

	trypath = "/ami/sw/packages/pyappion"
 	if os.path.isdir(trypath):
		params['appiondir'] = trypath
		return params['appiondir']

	apDisplay.printError("environmental variable, APPIONDIR, is not defined.\n"+
		"Did you source useappion.sh?")

def runHelp(params):
	funcxml = os.path.join(params['appiondir'],"xml",functionname+".xml")
	xmldict = apXml.readOneXmlFile(funcxml)
	apXml.printHelp(xmldict)
	sys.exit(1)

def checkForHelpCall(args, params):
	if len(args) < 1:
		runHelp(params)
	for arg in args:
		if ('help' in arg and not '=' in arg) or arg == 'h' or arg == '-h':
			runHelp(params)

def cmdline(args, params):
	checkForHelpCall(args, params)
	for arg in args:
		elem = arg.split("=")
		if elem[0] == "numpart":
			params['numparticles'] = int(elem[1])
		elif elem[0] == "numclass":
			params['numclasses'] = int(elem[1])
		elif elem[0] == "stackname":
			params['stackname'] = elem[1]
		elif elem[0] == "session":
			params['session'] = elem[1]
		elif elem[0] == "stackid":
			params['stackid'] = int(elem[1])
		elif elem[0] == "imask":
			params['imask'] = int(elem[1])
		elif elem[0] == "lp":
			params['lp'] = int(elem[1])
		elif elem[0] == "maskdiam":
			params['mask'] = int(elem[1])
		elif elem[0] == "diam":
			params['diam'] = float(elem[1])
		elif elem[0] == "runid":
			params['runid'] = elem[1]
		elif elem[0] == "outdir":
			params['outdir'] = elem[1]
		elif arg == "commit":
			params['commit'] = True
		elif arg == "classonly":
			params['classonly'] = True
		elif elem[0] == "description":
			params['description'] = elem[1]
		elif elem[0] == "iter":
			params['iter'] = int(elem[1])
		elif elem[0] == "csym":
			params['csym'] = int(elem[1])
		elif elem[0] == "refid":
			params['refid'] = int(elem[1])
		elif elem[0] == "xysearch":
			params['xysearch'] = int(elem[1])
		else:
			apDisplay.printError(str(elem[0])+" is not recognized as a valid parameter")

def overridecmd(params):
	### create a norefRun object
	runq = appionData.ApNoRefRunData()
	runq['name'] = params['runid']
	runq['path'] = appionData.ApPathData(path=os.path.normpath(params['outdir']))
	runq['stack'] = appiondb.direct_query(appionData.ApStackData, params['stackid'])
	# ... stackId, runId and norefPath make the norefRun unique:
	uniquerun = appiondb.query(runq, results=1)[0]
	# ... continue filling non-unique variables:
	uniqueparams = uniquerun['norefParams']

	if not 'num_particles' in uniqueparams:
		apDisplay.printError("You're noref classification is too old for automatic numparticles look up\n"+\
			"please remove 'classonly' and provide numpart=\#\#\#\# as in the previous run")
	params['numparticles'] = uniqueparams['num_particles']
	params['imask'] = uniqueparams['lp_filt']
	params['mask'] = uniqueparams['mask_diam']
	params['diam'] = uniqueparams['particle_diam']
	params['description'] = uniquerun['description']

def conflicts(params):
	if params['runid'] is None:
		apDisplay.printError("Please provide a runid, example: runid=run1")
	if params['stackid'] is None:
		apDisplay.printError("Please provide a stackid from database, example: stackid=15")
	if params['numclasses'] > 999:
		apDisplay.printError("The number of classes is too large (> 999), please provide a smaller number")
	if params['numparticles'] > 9999:
		apDisplay.printError("The number of particles is too large (> 9999), please provide a smaller number")
	return

def refconflicts(params):
	if params['refid'] is None:
		apDisplay.printError("Please provide a reference id, example: refid=28")
	if params['description'] is None:
		apDisplay.printError("Please provide a description")
		
def getStackId(params):
	if params['stackid'] is not None:
		return params['stackid']
	if params['session'] is None and params['stackname'] is None:
		apDisplay.printError("stack and session name undefined, please provide stack and session name."+\
			"\nexample: stackname=stack1 session=07jun05a")		
	if params['session'] is None:
		apDisplay.printError("session name undefined, please provide session name.\nexample: session=07jun05a")		
	if params['stackname'] is None:
		apDisplay.printError("stack name undefined, please provide stack name.\nexample: stackname=stack1")

	#checks done; find stackid
	stackq = appionData.ApStackParamsData()
	stackq['name'] = params['stackname']
	sessionid = apDatabase.getExpIdFromSessionName(params['session'])

def getStackInfo(params):
	#get the stack params
	stackpartdata = apStack.getStackParticle(params['stackid'], 1)

	#separate out data
	stackdata = stackpartdata['stack']
	stackrundata = stackpartdata['stackRun']
	stackparamdata = stackrundata['stackParams']
	partdata = stackpartdata['particle']
	if partdata['selectionrun']['params'] is not None:
		selectdata = partdata['selectionrun']['params']
	elif partdata['selectionrun']['dogparams'] is not None:
		selectdata = partdata['selectionrun']['dogparams']
	elif partdata['selectionrun']['manparams'] is not None:
		selectdata = partdata['selectionrun']['manparams']
	else:
		apDisplay.printWarning("Failed to get particle selection params")
		selectdata = {}

	#get image params of the particle
	imgdata = leginondb.direct_query(leginondata.AcquisitionImageData,
		partdata['dbemdata|AcquisitionImageData|image'], readimages=False)

	#apXml.fancyPrintDict(stackrundata)
	#apXml.fancyPrintDict(stackparamdata)
	#apXml.fancyPrintDict(stackpartdata)
	#apXml.fancyPrintDict(partdata)
	#apXml.fancyPrintDict(selectdata)
	#apXml.fancyPrintDict(imgdata)
	#sys.exit(1)

	#set the parameters	
	params['session']   = imgdata['session']
	if stackparamdata['bin'] is not None:
		params['bin']    = stackparamdata['bin']
	params['apix']      = apDatabase.getPixelSize(imgdata)*params['bin']
	params['stackpath'] = os.path.abspath(stackdata['path']['path'])
	if params['outdir'] is None:
		params['outdir'] = params['stackpath']
	params['stackfile'] = os.path.join(params['stackpath'],stackdata['name'])
	params['stacktype'] = stackparamdata['fileType']
	params['boxsize']   = int(stackparamdata['boxSize']/params['bin'])
	params['classfile'] = "classes_avg%03d" % params['numclasses']

	if 'diam' in selectdata and not params['classonly']:
		if params['diam'] is None:
			apDisplay.printWarning("particle diameter not specified using value from database")
			params['diam'] = selectdata['diam']
		if params['mask'] is None:
			apDisplay.printWarning("mask diameter not specified using value from database")
			params['mask'] = selectdata['diam']

	if params['imask'] == 0 and 'lp_filt' in selectdata and not params['classonly']:
		apDisplay.printWarning("lowpass not specified using value from database for 'first ring diam'")
		params['imask'] = selectdata['lp_filt']

	if not params['xysearch']:
		params['xysearch'] = int(params['boxsize']*0.1)*params['apix']

	# if first ring radii is not set, set one (in angstroms)
	if params['imask'] == 0:
		params['imask']= int(max(params['boxsize']/16-2,1)*params['apix'])
	return

def createSpiderFile(params):
	"""
	takes the stack file and create a spider file ready for processing
	"""
	emancmd  = "proc2d "
	if not os.path.isfile(params['stackfile']):
		apDisplay.printError("stackfile does not exist: "+params['stackfile'])
	emancmd += params['stackfile']+" "

	outfile = "start.spi"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	emancmd += outfile+" "
	emancmd += "apix="+str(params['apix'])+" "
	if params['lp'] > 0:
		emancmd += "lp="+str(params['lp'])+" "
	emancmd += "last="+str(params['numparticles']-1)+" "
	emancmd += "spiderswap "
	starttime = time.time()
	apDisplay.printColor("Running stack conversion this can take a while","cyan")
	executeEmanCmd(emancmd, verbose=True)
	apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime),"cyan")
	return

def createSpiderRefFile(params):
	"""
	takes the reference template file and creates a spider file with same pixel size and box size
	"""
	templatedata = apTemplate.getTemplateFromId(params['refid'])
	reffile = os.path.join(templatedata['path']['path'],templatedata['templatename'])

	scalefactor = round(templatedata['apix'],5)/round(params['apix'],5)
	refarray = apImage.mrcToArray(reffile)
	scaleRefArray = apTemplate.scaleTemplate(refarray, scalefactor, params['boxsize'])
	tmpreffile = os.path.join(params['rundir'],'tmpreferencefile.mrc')
	apImage.arrayToMrc(scaleRefArray, tmpreffile)

	emancmd  = "proc2d "
	emancmd += tmpreffile+" "

	outfile = "reference.spi"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	emancmd += outfile+" "
	emancmd += "apix="+str(params['apix'])+" "
	if params['lp'] > 0:
		emancmd += "lp="+str(params['lp'])+" "
	emancmd += "spiderswap "
	apDisplay.printColor("converting reference to spider format","cyan")
	executeEmanCmd(emancmd, verbose=True)
	os.remove(tmpreffile)
	
	return

def averageTemplate(params):
	"""
	takes the spider file and creates an average template of all particles and masks it
	"""
	emancmd  = "proc2d start.spi template.mrc average"
	executeEmanCmd(emancmd)
	emancmd  = "proc2d template.mrc template.mrc center"
	executeEmanCmd(emancmd)
	pixrad = int(float(params['mask'])/params['apix']/2.0)
	apDisplay.printMsg("using mask radius of "+str(pixrad)+" pixels ("+str(params['mask'])+" angstroms)")
	emancmd  = "proc2d template.mrc template.mrc mask="+str(pixrad)
	executeEmanCmd(emancmd)
	outfile = "template.spi"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	emancmd  = "proc2d template.mrc template.spi spiderswap"
	executeEmanCmd(emancmd)

	time.sleep(2)
	return

def executeEmanCmd(emancmd, verbose=False):
	sys.stderr.write("EMAN: "+emancmd+"\n")
	try:
		if verbose is False:
			os.popen(emancmd)
		else:
			os.system(emancmd)
	except:
		apDisplay.printError("could not run eman command: "+emancmd)

def createOutDir(params):
	params['rundir'] = os.path.join(params['outdir'], params['runid'])
	apDisplay.printMsg("creating run directory: "+params['rundir'])
	apParam.createDirectory(params['rundir'],remove=True)
	apParam.writeFunctionLog(sys.argv, logfile=os.path.join(params['rundir'],"classifier.log"))
	os.chdir(params['rundir'])

def createNoRefSpiderBatchFile(params):
	scriptfile = os.path.join(params['appiondir'],"lib/norefalign.bat")
	maskpixrad = int(float(params['mask'])/params['apix']/2.0)
	if not os.path.isfile(scriptfile):
		apDisplay.printError("could not find spider script: "+scriptfile)
	inf = open(scriptfile, "r")

	outfile = "norefalign_edit.bat"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	outf = open(outfile, "w")

	notdone = True
	for line in inf:
		if notdone is False:
			outf.write(line)
		else:
			thr = line[:3]
			if thr == "x99":
				outf.write(spiderline(99,params['numparticles'],"number of particles in stack"))
			elif thr == "x98":
				outf.write(spiderline(98,params['boxsize'],"box size"))
			elif thr == "x97":
				pixdiam = int(float(params['diam'])/params['apix'])
				outf.write(spiderline(97,pixdiam,"expected diameter of particle (in pixels)"))		
			elif thr == "x96":
				firstring = int(float(params['imask'])/params['apix'])
				outf.write(spiderline(96,firstring,"first ring radii"))
			elif thr == "x95":
				#lastring = params['boxsize']/2 - 2
				lastring = maskpixrad - 2
				outf.write(spiderline(95,lastring,"last ring radii"))
			elif thr == "x94":
				outf.write(spiderline(94,maskpixrad,"mask radius (in pixels)"))
			elif thr == "x93":
				outf.write(spiderline(93,params['numclasses'],"num classes (will get as close as possible)"))
			elif thr == "x92":
				outf.write(spiderline(92,10,"additive constant for hierarchical clustering"))
				notdone = False
			else:
				outf.write(line)

def createRefSpiderBatchFile(params,iteration):
	scriptfile = os.path.join(params['appiondir'],"lib/refbasedali.bat")
	maskpixrad = int(float(params['mask'])/params['apix']/2.0)
	imaskpixrad = int(float(params['imask'])/params['apix']/2.0)
	if not os.path.isfile(scriptfile):
		apDisplay.printError("could not find spider script: "+scriptfile)
	inf = open(scriptfile, "r")

	outfile = "refalign_edit.bat"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	outf = open(outfile, "w")

	notdone = True
	for line in inf:
		if notdone is False:
			outf.write(line)
		else:
			if re.search("^x99",line):
				outf.write(spiderline(99,params['numparticles'],"number of particles in stack"))
 			elif re.search("^x98",line):
				outf.write(spiderline(98,1,"number of reference images"))
			elif re.search("^x97",line):
				outf.write(spiderline(97,imaskpixrad,"first ring radii"))
			elif re.search("^x96",line):
				outf.write(spiderline(96,maskpixrad,"last ring radii"))
			elif re.search("^x95",line):
				xysearch = int(float(params['xysearch'])/params['apix'])
				outf.write(spiderline(95,params['xysearch'],"translational search range (in pixels)"))
			elif re.search("^x93",line):
				outf.write(spiderline(93,params['csym'],"c-symmetry (rotational symmetry to be applied, 1 if none)"))
			elif re.search("^\[stack\]",line):
				outf.write(spiderline("stack",os.path.join(params['rundir'],'start')))
			elif re.search("^\[aligned\]",line):
				outf.write(spiderline("aligned",os.path.join(params['rundir'],'aligned')))
			elif re.search("^\[ref\]",line):
				# get reference template - if first iteration, get original, else get from previous iteration
				if iteration == 1:
					outf.write(spiderline("ref",os.path.join(params['rundir'],'reference')))
				else:
					previter = iteration - 1
					previtername = 'refine%d' % previter
					previterdir = os.path.join(params['rundir'],previtername)
					outf.write(spiderline("ref",os.path.join(previterdir,'refali001.spi')))
				notdone = False
			else:
				outf.write(line)

def spiderline(var, value, comment=None):
	# check if var is a numeric type
	if type(var) == type(1):
		line = "x"+str(var)+"="+str(value)+" "
		while len(line) < 11:
			line += " "
		line += "; "+comment+"\n"
	else:
	      	line = "["+var+"]"+value+"\n"
	sys.stderr.write(line)
	return line

def runSpiderClass(params, reclass=False):
	spidercmd = "spider bat/spi @norefalign_edit"
	if reclass is False:
		esttime = 3*60*(params['numparticles']/500)**2
		apDisplay.printColor("Running spider this can take awhile, estimated time: "+\
			apDisplay.timeString(esttime),"cyan")
	starttime = time.time()
	executeSpiderCmd(spidercmd)
	apDisplay.printColor("finished spider in "+apDisplay.timeString(time.time()-starttime),"cyan")
	shutil.copy(os.path.join(params['rundir'],"classes_avg.spi"),
		os.path.join(params['rundir'],params['classfile']+".spi") )

def runSpiderRefAli(params):
	spidercmd = "spider bat/spi @refalign_edit"
	starttime = time.time()
	executeSpiderCmd(spidercmd)
	apDisplay.printColor("finished spider in "+apDisplay.timeString(time.time()-starttime),"cyan")

def executeSpiderCmd(spidercmd, verbose=True):
	sys.stderr.write("SPIDER: "+spidercmd+"\n")
	try:
		if verbose is False:
			os.popen(spidercmd)
		else:
			os.system(spidercmd)
	except:
		apDisplay.printError("could not run spider command: "+spidercmd)

def makeRefMrc(params):
	apDisplay.printColor("converting spider files to mrc","cyan")
	convertFileToMRC(params['iterdir'],'ref001.spi')
	convertFileToMRC(params['iterdir'],'refali001.spi')
	convertFileToMRC(params['iterdir'],'varali001.spi')
	if params['csym']>1:
		convertFileToMRC(params['iterdir'],'refali001_nosym.spi')
		convertFileToMRC(params['iterdir'],'varali001_nosym.spi')
	
	
def classHistogram(params):
	search = os.path.join(params['rundir'], "classes/clhc*.spi")
	files = glob.glob(search)
	lendict = {}
	maxval = 0
	minval = params['numparticles']

	for f in files:
		inf = open(f, "r")
		count = -1.0
		for line in inf:
			count += 1.0
		inf.close()
		lendict[f] = count
		if count > maxval: maxval = count
		if count < minval: minval = count

	width = 60.0
	if maxval < width:
		factor = 1.0
	else:
		factor = width/maxval

	print "\nClass Histogram"
	for f in files:
		short = os.path.basename(f)
		short = re.sub("clhc_cls","",short)
		short = re.sub(".spi","",short)
		sys.stderr.write(short+" ")
		numpoints = int(lendict[f]*factor)
		for i in range(numpoints):
			sys.stderr.write("*")
		sys.stderr.write(" "+str(int(lendict[f]))+"\n")

def convertFileToMRC(path,filename):
	"""
	takes any single spider or imagic-formatted file and converts to mrc
	"""
	fileroot=os.path.splitext(filename)[0]
	mrcfile=fileroot+".mrc"
	emancmd = "proc2d "+os.path.join(path,filename)+" "+mrcfile
	executeEmanCmd(emancmd)
	
def convertClassfileToImagic(params):
	"""
	takes the final spider file and converts it to imagic
	"""
	classroot = os.path.join(params['rundir'],params['classfile'])
	emancmd  = "proc2d "+classroot+".spi "+classroot+".hed"
	executeEmanCmd(emancmd)

def insertNoRefRun(params, insert=False):
	# create a norefParam object
	paramq = appionData.ApNoRefParamsData()
	paramq['num_particles'] = params['numparticles']
	paramq['particle_diam'] = params['diam']
	paramq['mask_diam'] = params['mask']
	paramq['lp_filt'] = params['imask']
	paramsdata = appiondb.query(paramq, results=1)

	### create a norefRun object
	runq = appionData.ApNoRefRunData()
	runq['name'] = params['runid']
	runq['path'] = appionData.ApPathData(path=os.path.normpath(params['outdir']))
	runq['stack'] = appiondb.direct_query(appionData.ApStackData, params['stackid'])
	# ... stackId, runId and norefPath make the norefRun unique:
	uniquerun = appiondb.query(runq, results=1)
	# ... continue filling non-unique variables:
	runq['description'] = params['description']

	if paramsdata:
		runq['norefParams'] = paramsdata[0]
	else:
		runq['norefParams'] = paramq
	# ... check if params associated with unique norefRun are consistent:
	if uniquerun and not params['classonly']:
		for i in runq:
			if uniquerun[0][i] != runq[i]:
				apDisplay.printError("Run name '"+params['runid']+"' for stackid="+\
					str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))
	#else:
	#	apDisplay.printWarning("Run name '"+params['runid']+"' already exists in database")

	### create a classRun object
	classq = appionData.ApNoRefClassRunData()
	classq['num_classes'] = params['numclasses']
	norefrun = appiondb.query(runq, results=1)
	if params['classonly']:
		classq['norefRun'] = uniquerun[0]
	elif norefrun:
		classq['norefRun'] = norefrun[0]
	elif not params['classonly']:
		classq['norefRun'] = runq
	else:
		apDisplay.printError("parameters have changed for run name '"+params['runid']+\
			"', specify 'classonly' to re-average classes")
	# ... numclasses and norefRun make the class unique:
	uniqueclass = appiondb.query(classq, results=1)
	# ... continue filling non-unique variables:
	classq['classFile'] = params['classfile']
	# ... check if params associated with unique classRun are consistent:
	if uniqueclass:
		for i in classq:
			apXml.fancyPrintDict(uniqueclass[0])
			apXml.fancyPrintDict(classq)
			if uniqueclass[0][i] != classq[i]:
				apDisplay.printError("NoRefRun name '"+params['runid']+"' for numclasses="+\
					str(params['numclasses'])+"\nis already in the database with different parameter: "+str(i))

	classdata = appiondb.query(classq, results=1)

	norefrun = appiondb.query(runq, results=1)
	if not classdata and insert is True:
		# ideal case nothing pre-exists
		apDisplay.printMsg("inserting noref run parameters into database")
		appiondb.insert(classq)

	return

def insertRefRun(params, insert=False):
	# create a refParam object
	paramq = appionData.ApRefParamsData()
	paramq['mask_diam'] = params['mask']
	paramq['imask_diam'] = params['imask']
	paramq['lp'] = params['lp']
	paramq['xysearch'] = params['xysearch']
	paramq['csym'] = params['csym']
	paramq['num_particles'] = params['numparticles']

	### create a refRun object
	runq = appionData.ApRefRunData()
	runq['name'] = params['runid']
	runq['stack'] = appiondb.direct_query(appionData.ApStackData, params['stackid'])
	runq['path'] = appionData.ApPathData(path=os.path.normpath(params['outdir']))
	# ... stackId, runId and refPath make the refRun unique:
	uniquerun = appiondb.query(runq, results=1)
	# ... continue filling non-unique variables:
	runq['refParams'] = paramq
	runq['refTemplate'] = appiondb.direct_query(appionData.ApTemplateImageData, params['refid'])
	runq['description'] = params['description']

	# ... check if params associated with unique refRun are consistent:
	if uniquerun:
		for i in runq:
			if uniquerun[0][i] != runq[i]:
				apDisplay.printError("Run name '"+params['runid']+"' for stackid="+\
					str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))
	else:
		apDisplay.printWarning("Run name '"+params['runid']+"' already exists in database")

	if insert is True:
		# ideal case nothing pre-exists
		apDisplay.printMsg("inserting ref run parameters into database")
		params['runq']=runq
		appiondb.insert(runq)

def insertIterRun(params, iter, itername, insert=False):
	### create the RefIteration objects
	iterq = appionData.ApRefIterationData()
	iterq['refRun'] = params['runq']
	iterq['iteration'] = iter
	iterq['name'] = itername

	##############################################
	## Need to code for upload of particle data ##
	##############################################

	if insert is True:
		# ideal case nothing pre-exists
		apDisplay.printMsg("inserting ref iterations parameters into database")
		appiondb.insert(iterq)
	return
