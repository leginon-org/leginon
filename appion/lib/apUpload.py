import project
import sys
import os
import re
import apDisplay
import appionData
import apDatabase
import leginondata
import string
import apFile
from pyami import mrc


def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runname=<runname>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"
	sys.exit(1)

def parsePrtlUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printPrtlUploadHelp()
	lastarg=1
	# first get all box files
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		else:
			boxfile=arg
			if (os.path.isfile(boxfile)):
				# in case of multiple extenstions, such as pik files
				splitfname=(os.path.basename(boxfile).split('.'))
				mrcfileroot.append(splitfname[0])
				params['extension'] = string.join(splitfname[1:],'.')
				params['prtltype'] = splitfname[-1]
			else:
				apDisplay.printError("file '"+boxfile+"' does not exist \n")
		lastarg+=1
	params["imgs"]=mrcfileroot

	# save the input parameters into the "params" dictionary
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='scale'):
			params['scale']=int(elements[1])
		elif (elements[0]=='runname'):
			params['runname']=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")
	
def createDefaults():
	params={}
	params['apix']=None
	params['diam']=None
	params['bin']=None
	params['description']=None
	params['template']=None
	params['session']=None
	params['runname']=None
	params['imgs']=None
	params['rundir']=os.path.abspath('.')
	params['abspath']=os.path.abspath('.')
	params['rundir']=None
	params['scale']=None
	params['commit']=True
	params['sym']=None
	params['res']=None
	params['contour']=1.5
	params['zoom']=1.5
	params['reconid']=None
	params['rescale']=False
	params['newbox']=None
	return params

def findSymmetry(symtext):
	# find the symmetry entry in the database
	# based on the text version from EMAN
	# first convert to lower case
	symtext = string.lower(symtext)
	symdataq = appionData.ApSymmetryData(eman_name=symtext)
	symdata = symdataq.query(results=1)
	if not symdata:
		apDisplay.printWarning("No symmetry found, assuming c1 (asymmetric)")
		symdataq = appionData.ApSymmetryData(eman_name = 'c1')
		symdata = symdataq.query(results=1)
	return symdata[0]
	
def getSymmetryData(symid, msg=True):
	symdata = appionData.ApSymmetryData.direct_query(symid)
	if not symdata:
		printSymmetries()
		apDisplay.printError("no symmetry associated with this id: "+str(symid))
	if msg is True:
		apDisplay.printMsg("Selected symmetry group: "
			+apDisplay.colorString(str(symdata['symmetry']), "cyan"))
	return symdata

def compSymm(a, b):
	if a.dbid > b.dbid:
		return 1
	else:
		return -1

def printSymmetries():
	symq = appionData.ApSymmetryData()
	syms = symq.query()
	sys.stderr.write("ID   NAME         DESCRIPTION\n")
	sys.stderr.write("--   ----         -----------\n")
	syms.sort(compSymm)
	for s in syms:
		name = s['symmetry']
		name = re.sub('Icosahedral', 'Icos', name)
		sys.stderr.write( 
			apDisplay.colorString(apDisplay.rightPadString(s.dbid,3),"green")+" "
			+apDisplay.rightPadString(name,13)+" "
			+apDisplay.rightPadString(s['description'],60)+"\n"
		)

def insertModel(params):
	apDisplay.printMsg("commiting model to database")
	symdata=appionData.ApSymmetryData.direct_query(params['sym'])
	if not symdata:
		apDisplay.printError("no symmetry associated with this id\n")		
	params['syminfo'] = symdata
	modq=appionData.ApInitialModelData()
	modq['project|projects|project'] = params['projectId']
	modq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	modq['name'] = params['name']
	modq['symmetry'] = symdata
	modq['pixelsize'] = params['newapix']
	modq['boxsize'] = params['newbox']
	modq['resolution'] = params['res']
	modq['hidden'] = False
	filepath = os.path.join(params['rundir'], params['name'])
	modq['md5sum'] = apFile.md5sumfile(filepath)
	modq['description'] = params['description']
	if params['densityid'] is not None:
		modq['original density'] = appionData.Ap3dDensityData.direct_query(params['densityid'])
	if params['oldmodelid'] is not None:
		modq['original model'] = appionData.ApInitialModelData.direct_query(params['oldmodelid'])
	if params['commit'] is True:
		modq.insert()
	else:
		apDisplay.printWarning("not commiting model to database")

def insert3dDensity(params):
	apDisplay.printMsg("commiting density to database")
	symdata=appionData.ApSymmetryData.direct_query(params['sym'])
	if not symdata:
		apDisplay.printError("no symmetry associated with this id\n")		
	params['syminfo'] = symdata
	modq=appionData.Ap3dDensityData()
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	modq['session'] = sessiondata
	modq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	modq['name'] = params['name']
	modq['resolution'] = params['res']
	modq['symmetry'] = symdata
	modq['pixelsize'] = params['apix']
	modq['boxsize'] = params['box']
	modq['description'] = params['description']
	modq['lowpass'] = params['lp']
	modq['highpass'] = params['hp']
	modq['mask'] = params['mask']
	modq['imask'] = params['imask']
	if params['reconid'] is not None:
		iterdata = appionData.ApRefinementData.direct_query(params['reconid'])
		if not iterdata:
			apDisplay.printError("this iteration was not found in the database\n")
		modq['iterid'] = iterdata
	### if ampfile specified
	if params['ampfile'] is not None:
		(ampdir, ampname) = os.path.split(params['ampfile'])
		modq['ampPath'] = appionData.ApPathData(path=os.path.abspath(ampdir))
		modq['ampName'] = ampname
		modq['maxfilt'] = params['maxfilt']
	modq['handflip'] = params['yflip']
	modq['norm'] = params['norm']
	modq['invert'] = params['invert']
	modq['hidden'] = False
	filepath = os.path.join(params['rundir'], params['name'])
	modq['md5sum'] = apFile.md5sumfile(filepath)
	if params['commit'] is True:
		modq.insert()
	else:
		apDisplay.printWarning("not commiting model to database")

def insertTomo(params):
	apDisplay.printMsg("Commiting tomogram to database")
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(params['tiltseriesnumber'],sessiondata)
	imageq = leginondata.AcquisitionImageData()
	imageq['tilt series'] = tiltdata
	images = imageq.query()
	apix = apDatabase.getPixelSize(images[0])
	if not params['full']:
		tomoq = appionData.ApTomogramData()
		tomoq['session'] = sessiondata
		tomoq['tiltseries'] = tiltdata
		results = tomoq.query()
		tomoq['number'] = len(results)+1
		tomoq['pixelsize'] = apix * params['bin']
		alignq = appionData.ApTomoAlignmentRunData(name=params['runname'])
		fulltomoq = appionData.ApFullTomogramData()
		fulltomoq['alignment'] = alignq
		results = fulltomoq.query(results=1,readimages=False)
		tomoq['fulltomogram'] = results[0]
		tomoq['runname'] = params['volume']
		tomoq['dimension'] = {'x':params['shape'][2],'y':params['shape'][1], 'z':params['shape'][0]}
		filepath = os.path.join(params['rundir'], params['name']+".rec")
		tomoq['md5sum'] = apFile.md5sumfile(filepath)
	else:
		alignq = appionData.ApTomoAlignmentRunData()
		alignq['bin'] = params['bin']
		alignq['name'] = params['runname']
		tomoq = appionData.ApFullTomogramData()
		tomoq['alignment'] = alignq
		tomoq['session'] = sessiondata
		tomoq['tiltseries'] = tiltdata
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	tomoq['name'] = params['name']
	tomoq['description'] = params['description']
		
	if params['commit'] is True:
		tomoq.insert()
		return tomoq
	else:
		apDisplay.printWarning("not commiting tomogram to database")

def insertManualParams(params, expid):
	sessiondata = leginondata.SessionData.direct_query(expid)
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runname']
	runq['session']=sessiondata
	#runq['path'] = appionData.ApPathData(path=os.path.abspath(????????))

	manparams=appionData.ApSelectionParamsData()
	manparams['diam']=params['diam']

	selectionruns=runq.query(results=1)

	# if no run entry exists, insert new run entry into run.dbparticledata
	# then create a new selexonParam entry
	if not selectionruns:
		print "inserting manual selection run into database"
		runq['params']=manparams
		runq.insert()
	elif selectionruns[0]['params'] != manparams:
		apDisplay.printError("upload parameters not the same as last run - check diameter")



