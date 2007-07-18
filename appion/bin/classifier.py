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
	params['lp']=0
	params['outdir']=None
	params['mask']=None
	params['runid']=None
	params['description']=None
	params['commit']=False

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
		elif elem[0] == "description":
			params['description'] = elem[1]
		else:
			apDisplay.printError(str(elem[0])+" is not recognized as a valid parameter")

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
	params['stackpath'] = os.path.abspath(stackdata['stackPath'])
	if params['outdir'] is None:
		params['outdir'] = params['stackpath']
	params['stackfile'] = os.path.join(params['stackpath'],stackdata['name'])
	params['stacktype'] = stackparamdata['fileType']
	params['boxsize']   = int(stackparamdata['boxSize']/params['bin'])
	params['classfile'] = "classes_avg%03d" % params['numclasses']

	if 'diam' in selectdata:
		if params['diam'] is None:
			apDisplay.printWarning("particle diameter not specified using value from database")
			params['diam'] = selectdata['diam']
		if params['mask'] is None:
			apDisplay.printWarning("mask diameter not specified using value from database")
			params['mask'] = selectdata['diam']

	if params['lp'] == 0 and 'lp_filt' in selectdata:
		apDisplay.printWarning("lowpass not specified using value from database for 'first ring diam'")
		params['lp'] = selectdata['lp_filt']


def createSpiderFile(params):
	"""
	takes the stack file and create a spider file ready for processing
	"""
	emancmd  = "proc2d "
	if not os.path.isfile(params['stackfile']):
		apDisplay.printError("stackfile does not exist: "+params['stackfile'])
	emancmd += params['stackfile']+" "

	outfile = "startswapnorm.spi"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	emancmd += outfile+" "
	emancmd += "apix="+str(params['apix'])+" "
	if params['lp'] > 0:
		emancmd += "lp="+str(params['lp'])+" "
	emancmd += "last="+str(params['numparticles'])+" "
	emancmd += "spiderswap "
	starttime = time.time()
	apDisplay.printColor("Running stack conversion this can take awhile","cyan")
	executeEmanCmd(emancmd, verbose=True)
	apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime),"cyan")
	return

def averageTemplate(params):
	"""
	takes the spider file and creates an average template of all particles and masks it
	"""
	emancmd  = "proc2d startswapnorm.spi template.mrc average"
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
	apParam.createDirectory(params['rundir'])
	apParam.writeFunctionLog(sys.argv, logfile=os.path.join(params['rundir'],"classifier.log"))
	os.chdir(params['rundir'])

def createSpiderBatchFile(params):
	scriptfile = os.path.join(params['appiondir'],"lib/norefalign.bat")
	#scriptfile = "/ami/data07/recon_scripts/spider_scripts/norefali_3.bat"
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
				if params['lp'] != 0:
					firstring = int(float(params['lp'])/params['apix'])
				else: 
					firstring = int(max(params['boxsize']/16-2,1))
				outf.write(spiderline(96,firstring,"first ring radii"))
			elif thr == "x95":
				lastring = params['boxsize']/2 - 2
				outf.write(spiderline(95,lastring,"last ring radii"))
			elif thr == "x94":
				pixrad = int(float(params['mask'])/params['apix']/2.0)
				outf.write(spiderline(94,pixrad,"mask radius (in pixels)"))
			elif thr == "x93":
				outf.write(spiderline(93,params['numclasses'],"num classes (will get as close as possible)"))
			elif thr == "x92":
				outf.write(spiderline(92,10,"additive constant for hierarchical clustering"))
				notdone = False
			else:
				outf.write(line)

def spiderline(num, value, comment):
	line = "x"+str(num)+"="+str(value)+" "
	while len(line) < 11:
		line += " "
	line += "; "+comment+"\n"
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

def executeSpiderCmd(spidercmd, verbose=True):
	sys.stderr.write("SPIDER: "+spidercmd+"\n")
	try:
		if verbose is False:
			os.popen(spidercmd)
		else:
			os.system(spidercmd)
	except:
		apDisplay.printError("could not run spider command: "+spidercmd)

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
	paramq['particle_diam'] = params['diam']
	paramq['mask_diam'] = params['mask']
	paramq['lp_filt'] = params['lp']
	paramsdata = appiondb.query(paramq, results=1)

	### create a norefRun object
	runq = appionData.ApNoRefRunData()
	runq['name'] = params['runid']
	runq['norefPath'] = params['outdir']
	runq['stack'] = appiondb.direct_query(appionData.ApStackData, params['stackid'])
	# ... stackId, runId and norefPath make the norefRun unique:
	uniquerun = appiondb.query(runq, results=1)
	# ... continue filling non-unique variables:
	runq['description'] = params['description']

	if paramsdata:
		runq['norefParams'] = paramsdata
	else:
		runq['norefParams'] = paramq
	# ... check if params associated with unique norefRun are consistent:
	if uniquerun:
		for i in runq:
			if uniquerun[0][i] != runq[i]:
				apDisplay.printError("Run name '"+params['runid']+"' for stackid="+\
					str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))

	### create a classRun object
	classq = appionData.ApNoRefClassRunData()
	classq['num_classes'] = params['numclasses']
	norefrun = appiondb.query(runq, results=1)
	if norefrun:
		classq['norefRun'] = norefrun
	else:
		classq['norefRun'] = runq
	# ... numclasses and norefRun make the class unique:
	uniqueclass = appiondb.query(runq, results=1)
	# ... continue filling non-unique variables:
	classq['classFile'] = params['classfile']
	# ... check if params associated with unique classRun are consistent:
	if uniqueclass:
		for i in classq:
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

if __name__ == "__main__":
	params = defaults()
	getAppionDir(params)
	cmdline(sys.argv[1:], params)
	conflicts(params)
	
	getStackInfo(params)
	createOutDir(params)

	if params['commit']is True:
		insertNoRefRun(params, insert=False)

	classfile = os.path.join(params['rundir'], "classes_avg.spi")
	if not os.path.isfile(classfile):
		createSpiderFile(params)
		averageTemplate(params)
		createSpiderBatchFile(params)
		runSpiderClass(params)
	else:
		apDisplay.printWarning("particles were already aligned for this runid, only redoing clustering") 
		createSpiderBatchFile(params)
		runSpiderClass(params, reclass=True)

	classfile = os.path.join(params['rundir'],params['classfile']+".spi")
	if not os.path.isfile(classfile):
		apDisplay.printError("failed to write classfile, "+classfile)

	convertClassfileToImagic(params)

	if params['commit']is True:
		insertNoRefRun(params, insert=True)
	if params['numclasses'] <= 80:
		classHistogram(params)
	apDisplay.printMsg("SUCCESS: classfile located at:\n"+classfile)
