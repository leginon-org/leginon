#!/usr/bin/python -O

import sys
import os
import re
import time
import glob
import shutil
import data
import apXml
import apParam
import apDisplay
import apDB
import apDatabase
import appionData
leginondb = apDB.db
appiondb = apDB.apdb

def defaults():
	params = {}
	params['numparticles']=3000
	params['numclasses']=40
	params['stackname']=None
	params['session']=None
	params['stackid']=None
	params['diam']=0
	params['bin']=1
	params['lp']=0
	params['outdir']=None
	params['mask']=None
	params['runid']=None

	return params

def cmdline(args, params):
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
		else:
			apDisplay.printError("Unknown command: "+arg)

def conflicts(params):
	if params['runid'] is None:
		apDisplay.printError("Please provide a runid, example: runid=class1")
	if params['stackid'] is None:
		apDisplay.printError("Please provide a stackid from database, example: stackid=15")
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
	stackdata = appiondb.direct_query(appionData.ApStackParamsData, params['stackid'])

	#get a stack particle params
	stackpartq = appionData.ApStackParticlesData()
	stackpartq['stackparams'] = stackdata
	stackpartdata = appiondb.query(stackpartq, results=1)[0]
	
	#get the particle normal params
	partdata = appiondb.direct_query(appionData.ApParticleData, stackpartdata['particle'].dbid)

	#get image params of the particle
	imgdata = leginondb.direct_query(data.AcquisitionImageData, partdata['dbemdata|AcquisitionImageData|image'])

	#set the parameters	
	params['session'] = imgdata['session']
	if stackdata['bin'] is not None:
		params['bin'] = stackdata['bin']
	params['apix'] = apDatabase.getPixelSize(imgdata)*params['bin']
	params['stackpath'] = os.path.abspath(stackdata['stackPath'])
	if params['outdir'] is None:
		params['outdir'] = params['stackpath']
	params['stackfile'] = os.path.join(params['stackpath'],stackdata['name'])
	params['stacktype'] = stackdata['fileType']
	params['boxsize'] = stackdata['boxSize']

	#apXml.fancyPrintDict(stackdata)
	#apXml.fancyPrintDict(stackpartdata)
	#apXml.fancyPrintDict(partdata)
	#apXml.fancyPrintDict(imgdata)

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
	emancmd += "first=1 last="+str(params['numparticles'])+" "
	emancmd += "spiderswap "
	executeEmanCmd(emancmd, verbose=True)
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
	os.chdir(params['rundir'])

def createSpiderBatchFile(params):

	scriptfile = "/ami/data07/recon_scripts/spider_scripts/norefali_3.bat"
	if not os.path.isfile(scriptfile):
		apDisplay.printError("could not find spider script: "+scriptfile)
	inf = open(scriptfile, "r")

	outfile = "noref_align3.bat"
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
				outf.write(spiderline(96,5,"first ring radii"))
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

def runSpiderClass(params reclass=False):
	spidercmd = "spider bat/spi @noref_align3"
	if reclass is False:
		apDisplay.printColor("Running spider this can take awhile","cyan")
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

def classHistogram(params):
	search = os.path.join(params['rundir'], "classes/clhc*.spi")
	files = glob.glob(search)
	lendict = {}
	maxval = 0
	minval = params['numparticles']
	print "\nClass Histogram"
	for f in files:
		inf = open(f, "r")
		count = -1
		for line in inf:
			count += 1
		inf.close()
		lendict[f] = count
		if count > maxval: maxval = count
		if count < minval: minval = count
	width = min(maxval,60)
	factor = maxval/float(width)
	for f in files:
		short = os.path.basename(f)
		short = re.sub("clhc_cls","",short)
		short = re.sub(".spi","",short)
		sys.stderr.write(short+" ")
		numpoints = int(lendict[f]*factor)
		for i in range(numpoints):
			sys.stderr.write("*")
		sys.stderr.write(" "+str(lendict[f])+"\n")

if __name__ == "__main__":
	params = defaults()
	cmdline(sys.argv[1:], params)
	conflicts(params)
	
	getStackInfo(params)
	createOutDir(params)
	
	if not os.path.isfile(os.path.join(params['rundir'], "classes_avg.spi")):
		createSpiderFile(params)
		averageTemplate(params)
		createSpiderBatchFile(params)
		runSpiderClass(params)
	else:
		runSpiderClass(params, reclass=True)
	classHistogram(params)
