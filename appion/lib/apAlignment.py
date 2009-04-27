#!/usr/bin/python -O

import sys
import os
import re
import time
import glob
import shutil
import math
import subprocess
import leginondata
import apXml
import apParam
import apDisplay
import apDatabase
import apStack
import apImage
import appionData
import apTemplate
import apEMAN

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
	params['rundir']=None
	params['mask']=None
	params['runname']=None
	params['description']=None
	params['commit']=False
	params['classonly']=False
	params['refids']=None
	params['xysearch']=None
	params['iter']=2
	params['csym']=1
	params['staticref']=False
	params['runtime']=None

	return params

def getAppionDir(params):
	params['appiondir'] = apParam.getAppionDirectory()
	return params['appiondir']

def runHelp(params):
	functionname = os.path.basename(sys.argv[0]).split(".")[0]
	#funcxml = os.path.join(params['appiondir'],"xml",functionname+".xml")
	#xmldict = apXml.readOneXmlFile(funcxml)
	#apXml.printHelp(xmldict)
	print "no help for ",functionname
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
		elif elem[0] == "runname":
			params['runname'] = elem[1]
		elif elem[0] == "rundir":
			params['rundir'] = elem[1]
		elif arg == "commit":
			params['commit'] = True
		elif arg == "staticref":
			params['staticref'] = True
		elif arg == "classonly":
			params['classonly'] = True
		elif elem[0] == "description":
			params['description'] = elem[1]
		elif elem[0] == "iter":
			params['iter'] = int(elem[1])
		elif elem[0] == "csym":
			params['csym'] = int(elem[1])
		elif elem[0] == "refids":
			if not ',' in elem[1]:
				params['refids'] = [ int(elem[1]) ]
			else:
				params['refids'] = elem[1].split(',')
		elif elem[0] == "xysearch":
			params['xysearch'] = int(elem[1])
		else:
			apDisplay.printError(str(elem[0])+" is not recognized as a valid parameter")

def overridecmd(params):
	### create a norefRun object
	runq = appionData.ApNoRefRunData()
	runq['name'] = params['runname']
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	runq['stack'] = appionData.ApStackData.direct_query(params['stackid'])
	# ... stackId, runname and norefPath make the norefRun unique:
	uniquerun = runq.query(results=1)[0]
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
	if params['runname'] is None:
		apDisplay.printError("Please provide a runname, example: runname=run1")
	if params['stackid'] is None:
		apDisplay.printError("Please provide a stackid from database, example: stackid=15")
	if params['numclasses'] > 999:
		apDisplay.printError("The number of classes is too large (> 999), please provide a smaller number")
	maxparticles = 150000
	if params['numparticles'] > maxparticles:
		apDisplay.printError("The number of particles is too large (> %d), please provide a smaller number" % (maxparticles,))
	return

def refconflicts(params):
	if params['refids'] is None:
		apDisplay.printError("Please provide a template reference id, example: refids=28")
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
	elif partdata['selectionrun']['tiltparams'] is not None:
		selectdata = partdata['selectionrun']['tiltparams']
	else:
		apDisplay.printWarning("Failed to get particle selection params")
		selectdata = {}

	#get image params of the particle (dereference keep image from loading as would partdata['image'])
	imageref = partdata.special_getitem('image', dereference = False)
	imgdata = leginondata.AcquisitionImageData.direct_query(imageref.dbid, readimages=False)

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
		params['bin']     = stackparamdata['bin']
	params['apix']      = apDatabase.getPixelSize(imgdata)*params['bin']
	params['stackpath'] = os.path.abspath(stackdata['path']['path'])
	if params['rundir'] is None:
		params['rundir']  = params['stackpath']
	params['stackfile'] = os.path.join(params['stackpath'],stackdata['name'])
	params['stacktype'] = stackparamdata['fileType']
	params['boxsize']   = int(stackparamdata['boxSize']/params['bin'])
	params['classfile'] = "classes_avg%03d" % params['numclasses']
	params['varfile']   = "classes_var%03d" % params['numclasses']

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
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime),"cyan")
	return

def createSpiderRefFile(params):
	"""
	takes the reference template file and
	creates a spider file with same pixel size and box size
	"""
	for i,refid in enumerate(params['refids']):
		templatedata= apTemplate.getTemplateFromId(int(refid))
		#convert template data
		reffile = os.path.join(templatedata['path']['path'], templatedata['templatename'])
		scalefactor = round(templatedata['apix'],5)/round(params['apix'],5)
		refarray = apImage.mrcToArray(reffile)
		scaleRefArray = apTemplate.scaleTemplate(refarray, scalefactor, params['boxsize'])

		#write to file
		tmpreffile = os.path.join(params['rundir'], "tempref%03d.spi" % (i+1))
		if os.path.isfile(tmpreffile):
			apDisplay.printWarning(tmpreffile+" already exists; removing it")
			time.sleep(2)
			os.remove(tmpreffile)
		apImage.arrayToMrc(scaleRefArray, tmpreffile)

		#set outfile name
		outfile = os.path.join(params['rundir'], "reference%03d.spi" % (i+1))
		if os.path.isfile(outfile):
			apDisplay.printWarning(outfile+" already exists; removing it")
			time.sleep(2)
			os.remove(outfile)

		#low pass filter
		emancmd  = "proc2d "
		emancmd += tmpreffile+" "
		emancmd += outfile+" "
		emancmd += "apix="+str(params['apix'])+" "
		if params['lp'] > 0:
			emancmd += "lp="+str(params['lp'])+" "
		emancmd += "spider-single "
		apDisplay.printColor("Converting reference "+str(i+1)+" to spider format for template="+str(refid),"cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		if len(params['refids']) == 1:
			#don't break for single template case
			oldreffile = os.path.join(params['rundir'], "oldreference.spi")
			shutil.copyfile(outfile, oldreffile)
	return

def averageTemplate(params):
	"""
	takes the spider file and creates an average template of all particles and masks it
	"""
	emancmd  = "proc2d start.spi template.mrc average"
	apEMAN.executeEmanCmd(emancmd)
	emancmd  = "proc2d template.mrc template.mrc"
	apEMAN.executeEmanCmd(emancmd)
	pixrad = int(float(params['mask'])/params['apix']/2.0)
	apDisplay.printMsg("using mask radius of "+str(pixrad)+" pixels ("+str(params['mask'])+" angstroms)")
	emancmd  = "proc2d template.mrc template.mrc mask="+str(pixrad)
	apEMAN.executeEmanCmd(emancmd)
	outfile = "template.spi"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	emancmd  = "proc2d template.mrc template.spi spiderswap"
	apEMAN.executeEmanCmd(emancmd)

	time.sleep(2)
	return

def createRunDir(params):
	apDisplay.printMsg("creating run directory: "+params['rundir'])
	apParam.createDirectory(params['rundir'])
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
				if firstring == 0:
					firstring = 2
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
			thr = line[:3]
			if re.search("^x99",line):
				outf.write(spiderline(99,params['numparticles'],"number of particles in stack"))
			elif re.search("^x98",line):
				outf.write(spiderline(98,len(params['refids']),"number of reference images"))
			elif re.search("^x97",line):
				outf.write(spiderline(97,imaskpixrad,"first ring radii"))
			elif re.search("^x96",line):
				outf.write(spiderline(96,maskpixrad,"last ring radii"))
			elif re.search("^x95",line):
				xysearch = int(float(params['xysearch'])/params['apix'])
				outf.write(spiderline(95,params['xysearch'],"translational search range (in pixels)"))
			elif re.search("^x93",line):
				outf.write(spiderline(93,params['csym'],"c-symmetry (rotational symmetry to be applied, 1 if none)"))
			elif re.search("^x92",line):
				outf.write(spiderline(92,iteration,"refinement iteration"))
			elif re.search("^\[stack\]",line):
				outf.write(spiderline("stack",os.path.join(params['rundir'],'start')))
			elif re.search("^\[aligned\]",line):
				outf.write(spiderline("aligned",os.path.join(params['iterdir'],'aligned')))
			elif re.search("^\[alistack\]",line):
				# get aligned stack from previous iteration
				if iteration == 1:
					outf.write(spiderline("alistack",os.path.join(params['rundir'],'start')))
				else:
					previter = iteration - 1
					previtername = 'refine%d' %previter
					previterdir = os.path.join(params['rundir'],previtername)
					outf.write(spiderline("alistack",os.path.join(previterdir,'aligned')))
			elif re.search("^\[prevaliparams\]",line):
				# get alignment parameters from previous iteration
				previter = iteration - 1
				previtername = 'refine%d' %previter
				previterdir = os.path.join(params['rundir'],previtername)
				if iteration == 1:
					outf.write(spiderline("prevaliparams",os.path.join(params['iterdir'],'apmq')))
				elif iteration == 2:
					outf.write(spiderline("prevaliparams",os.path.join(previterdir,'apmq')))
				else:
					outf.write(spiderline("prevaliparams",os.path.join(previterdir,'apmqSUM')))
			elif re.search("^\[ref\]",line):
				# get reference template - if first iteration, get original, else get from previous iteration
				if iteration == 1:
					outf.write(spiderline("ref",os.path.join(params['rundir'],'reference')))
				elif params['staticref'] is True:
					staticrefdir = os.path.join(params['rundir'],'refine1')
					outf.write(spiderline("ref",os.path.join(staticrefdir,'refstack')))
				else:
					previter = iteration - 1
					previtername = 'refine%d' % previter
					previterdir = os.path.join(params['rundir'],previtername)
					outf.write(spiderline("ref",os.path.join(previterdir,'refali')))
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

def estimateTime(numparts, maskpixrad=None):
	#min time 60 sec vs. 289 from model
	#linear time 0 sec vs. -1.1587 from model
	"""
	esttime = ( 60.0
		+ 0.0 * numparts
		+ 1.6642e-3 * numparts**2
		+ 5.6333e-7 * numparts**3
		+ 6.7367e-11 * numparts**4 )
	"""
	#quadradic time March 14, 2008
	x = float(maskpixrad*numparts*2.0)
	esttime = ( 26.83 + 0.001809 * x + 1.8542e-09 * x**2 )
	#ln(y) = -13.182 + 1.531 * ln(x) ==>
	#esttime = 1.884e-6 * (x**1.531) + 26.0
	return esttime

def runSpiderClass(params, reclass=False):
	spidercmd = "spider bat/spi @norefalign_edit"
	if reclass is False:
		maskpixrad = int(float(params['mask'])/params['apix']/2.0)
		esttime = estimateTime(params['numparticles'], maskpixrad)
		apDisplay.printColor("Running spider this can take awhile, estimated time: "+\
			apDisplay.timeString(esttime),"cyan")
	starttime = time.time()
	executeSpiderCmd(spidercmd)
	convertClasslistToEMANlist(params)

	runtime = time.time()-starttime
	apDisplay.printColor("finished spider in "+apDisplay.timeString(runtime),"cyan")
	shutil.copyfile(os.path.join(params['rundir'],"classes_avg.spi"),
		os.path.join(params['rundir'],params['classfile']+".spi") )
	shutil.copyfile(os.path.join(params['rundir'],"classes_var.spi"),
		os.path.join(params['rundir'],params['varfile']+".spi") )
	params['runtime'] = runtime

def runSpiderRefAli(params):
	spidercmd = "spider bat/spi @refalign_edit"
	starttime = time.time()
	executeSpiderCmd(spidercmd)
	apDisplay.printColor("finished spider in "+apDisplay.timeString(time.time()-starttime),"cyan")

def executeSpiderCmd(spidercmd, verbose=True):
	sys.stderr.write("SPIDER: "+spidercmd+"\n")
	try:
		if verbose is False:
			proc = subprocess.Popen(spidercmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		else:
			proc = subprocess.Popen(spidercmd, shell=True)
		proc.wait()
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

def makeRefImagic(params):
	apDisplay.printColor("converting spider stacks to imagic","cyan")
	convertStackToIMAGIC(params['iterdir'],'ref.spi')
	convertStackToIMAGIC(params['iterdir'],'refali.spi')
	convertStackToIMAGIC(params['iterdir'],'varali.spi')
	#MRCs are for the web viewer
	convertStackToMrcs(params['iterdir'],'refali.spi', len(params['refids']))
	convertStackToMrcs(params['iterdir'],'varali.spi', len(params['refids']))
	if params['csym']>1:
		convertStackToIMAGIC(params['iterdir'],'refali_nosym.spi')
		convertStackToIMAGIC(params['iterdir'],'varali_nosym.spi')
		convertStackToMrcs(params['iterdir'],'refali_nosym.spi', len(params['refids']))
		convertStackToMrcs(params['iterdir'],'varali_nosym.spi', len(params['refids']))

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
	apEMAN.executeEmanCmd(emancmd)

def convertStackToMrcs(path, filename, numimg=10):
	"""
	takes spider stack file and converts to single mrc files
	"""
	stackroot = os.path.splitext(filename)[0]
	filepath = os.path.join(path, filename)
	#numimg = apEMAN.getNumParticlesInStack(filepath)
	for i in range(numimg):
		num = ("%03d" % (i+1) )
		refstackname = stackroot+num+".mrc"
		emancmd = ("proc2d "+filepath+" "+refstackname
			+" first="+str(i)+" last="+str(i))
		apEMAN.executeEmanCmd(emancmd)

def convertStackToIMAGIC(path,filename):
	"""
	takes spider stack file and converts to imagic stack
	"""
	stackroot = os.path.splitext(filename)[0]
	refstackname = stackroot+".hed"
	emancmd = "proc2d "+os.path.join(path,filename)+" "+refstackname
	apEMAN.executeEmanCmd(emancmd)

def convertClassfileToImagic(params):
	"""
	takes the final spider file and converts it to imagic
	"""
	classroot = os.path.join(params['rundir'], params['classfile'])
	emancmd  = "proc2d "+classroot+".spi "+classroot+".hed"
	apEMAN.executeEmanCmd(emancmd)
	varroot = os.path.join(params['rundir'], params['varfile'])
	emancmd  = "proc2d "+varroot+".spi "+varroot+".hed"
	apEMAN.executeEmanCmd(emancmd)

def convertClasslistToEMANlist(params):
	"""
	takes list files for each class and convert to eman list reference to the imagic stack
	"""
	classroot = 'clhc_cls'
	search = os.path.join(params['rundir'], "classes/"+classroot+"*.spi")
	files = glob.glob(search)
	for infile in files:
		filename = os.path.basename(infile)
		fileroot = filename.split(".")
		splitn = fileroot[0].split(classroot)
		n = int(splitn[1])
		num = ("%04d" % (n-1) )
		outfile = os.path.join(params['rundir'], "classes/"+classroot+num+".lst")
		convertSpiDocToEMANlist(infile,outfile,params['stackfile'])

def convertSpiDocToEMANlist(infile,outfile,stackfile):
	inlines = open(infile, "r")
	out = open(outfile, "w")
	out.write('#LST\n')
	for line in inlines:
		if line.strip()[0]!=';':
			words = line.split()
			ptcl = math.floor(float(words[2]))
			out.write('%d\t%s\n' % (ptcl-1, stackfile))
	out.close()
	inlines.close()

def insertNoRefRun(params, insert=False):
	# create a norefParam object
	paramq = appionData.ApNoRefParamsData()
	paramq['num_particles'] = params['numparticles']
	paramq['particle_diam'] = params['diam']
	paramq['mask_diam'] = params['mask']
	paramq['lp_filt'] = params['imask']
	paramsdata = paramq.query(results=1)

	### create a norefRun object
	runq = appionData.ApNoRefRunData()
	runq['name'] = params['runname']
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	runq['stack'] = appionData.ApStackData.direct_query(params['stackid'])
	# ... stackId, runname and norefPath make the norefRun unique:
	uniquerun = runq.query(results=1)
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
				apDisplay.printError("Run name '"+params['runname']+"' for stackid="+\
					str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))
	#else:
	#	apDisplay.printWarning("Run name '"+params['runname']+"' already exists in database")
	runq['run_seconds'] = params['runtime']

	### create a classRun object
	classq = appionData.ApNoRefClassRunData()
	classq['num_classes'] = params['numclasses']
	norefrun = runq.query(results=1)
	if params['classonly']:
		classq['norefRun'] = uniquerun[0]
	elif norefrun:
		classq['norefRun'] = norefrun[0]
	elif not params['classonly']:
		classq['norefRun'] = runq
	else:
		apDisplay.printError("parameters have changed for run name '"+params['runname']+\
			"', specify 'classonly' to re-average classes")
	# ... numclasses and norefRun make the class unique:
	uniqueclass = classq.query(results=1)
	# ... continue filling non-unique variables:
	classq['classFile'] = params['classfile']
	classq['varFile'] = params['varfile']
	# ... check if params associated with unique classRun are consistent:
	if uniqueclass:
		for i in classq:
			apXml.fancyPrintDict(uniqueclass[0])
			apXml.fancyPrintDict(classq)
			if uniqueclass[0][i] != classq[i]:
				apDisplay.printError("NoRefRun name '"+params['runname']+"' for numclasses="+\
					str(params['numclasses'])+"\nis already in the database with different parameter: "+str(i))

	classdata = classq.query(results=1)

	norefrun = runq.query(results=1)
	if not classdata and insert is True:
		# ideal case nothing pre-exists
		apDisplay.printMsg("inserting noref run parameters into database")
		classq.insert()

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
	runq['name'] = params['runname']
	runq['stack'] = appionData.ApStackData.direct_query(params['stackid'])
	runq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	# ... stackId, runname and refPath make the refRun unique:
	uniquerun = runq.query(results=1)
	# ... continue filling non-unique variables:
	runq['refParams'] = paramq
	runq['description'] = params['description']

	# ... check if params associated with unique refRun are consistent:
	if uniquerun:
		for i in runq:
			if uniquerun[0][i] != runq[i]:
				apDisplay.printError("Run name '"+params['runname']+"' for stackid="+\
					str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))
	else:
		apDisplay.printWarning("Run name '"+params['runname']+"' already exists in database")

	if insert is True:
		# ideal case nothing pre-exists
		apDisplay.printMsg("inserting ref run parameters into database")
		params['runq']=runq
		runq.insert()

	for refid in params['refids']:
		reftempq = appionData.ApRefTemplateRunData()
		reftempq['refTemplate'] = appionData.ApTemplateImageData.direct_query(refid)
		reftempq['refRun'] = runq
		if insert is True:
			reftempq.insert()

def insertIterRun(params, iternum, itername, insert=False):
	### create the RefIteration objects
	iterq = appionData.ApRefIterationData()
	iterq['refRun'] = params['runq']
	iterq['iteration'] = iternum
	iterq['name'] = itername

	##############################################
	## Need to code for upload of particle data ##
	##############################################

	if insert is True:
		# ideal case nothing pre-exists
		apDisplay.printMsg("inserting ref iterations parameters into database")
		iterq.insert()
	return

def getAlignParticle(stackpdata,alignstackdata):
	oldstack = stackpdata['stack']['oldstack']
	particledata = stackpdata['particle']
	oldstackpdata = appionData.ApStackParticlesData(stack=oldstack,particle=particledata)
	q = appionData.ApAlignParticlesData(alignstack=alignstackdata,stackpart=oldstackpdata)
	results = q.query(readimages=False)
	if results:
		return results[0]

def getAlignShift(alignpdata,package):
	shift = None
	if package == 'Spider':
		angle = alignpdata['rotation']*math.pi/180.0
		shift = {'x':alignpdata['xshift']*math.cos(-angle)-alignpdata['yshift']*math.sin(-angle),
				'y':alignpdata['xshift']*math.sin(-angle)+alignpdata['yshift']*math.cos(-angle)}
	elif package == 'Xmipp':
		shift = {'x':alignpdata['xshift'],'y':alignpdata['yshift']}
	return shift

def getAlignPackage(alignrundata):
	aligntypedict = {
		'norefrun':'Spider',
		'refbasedrun':'Spider',
		'maxlikerun':'Xmipp',
		'imagicMRA':'Imagic'
	}
	for type in aligntypedict.keys():
		if alignrundata[type]:
			alignpackage = aligntypedict[type]
			break
	return alignpackage
