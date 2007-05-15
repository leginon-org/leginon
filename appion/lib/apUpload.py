import project
import sys
import os
import apDisplay
import appionData
import apDB
import Mrc

appiondb = apDB.apdb

def printTmpltUploadHelp():
	print "\nUsage:\nuploadTemplate.py template=<name> apix=<pixel> session=<session> [commit]\n"
	print "selexon template=groEL apix=1.63 session=06nov10a commit\n"
	print "template=<name>      : name should not have the extension, or number."
	print "                       groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>         : angstroms per pixel (unbinned)"
	print "diam=<n>             : approximate diameter of particle (in Angstroms, unbinned)"
	print "session=<sessionId>  : session name associated with template (i.e. 06mar12a)"
	print "description=\"text\"   : description of the template - must be in quotes"
	print "\n"
	sys.exit(1)

def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"
	sys.exit(1)

def printModelUploadHelp():
	print "\nUsage:\nuploadModel.py <filename> session=<session> symmetry=<sym id> apix=<pixel> description=<\"text\">\n"
	print "uploadModel.py /ami/data99/lambda.mrc symmetry=1 apix=2.02 description=\"lambda in EMAN orientation\"\n"
	sys.exit(1)
	
def parseTmpltUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printTmpltUploadHelp()
	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		elif (elements[0]=='session'):
			params['session']=elements[1]
		elif (elements[0]=='description'):
			params['description']=elements[1]
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

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
		elif (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

def parseModelUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printModelUploadHelp()
	# get MRC file
	mrcfile=args[1]
	if (os.path.isfile(mrcfile)):
		(params["path"], params["name"]) = os.path.split(mrcfile)
	else:
		apDisplay.printError("file '"+mrcfile+"' does not exist\n")
	# save the input parameters into the "params" dictionary
	for arg in args[2:]:
		elements=arg.split('=')
		if (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='session'):
			params['session']=elements[1]
		elif (elements[0]=='symmetry'):
			params['sym']=int(elements[1])
		elif (elements[0]=='description'):
			params['description']=elements[1]
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
	params['runid']=None
	params['imgs']=None
	params['scale']=None
	params['sym']=None
	return params

def getProjectId(params):
	#THIS LOOKS LIKE A HACK
	projectdata = project.ProjectData()
	projects = projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name'] == params['session']:
			params['projectId'] = i['projectId']
	if not params['projectId']:
		apDisplay.printError("no project associated with this session\n")
	return

def insertManualParams(params,expid):
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	runids=appiondb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		print "inserting manual runId into database"
 		manparams=appionData.ApSelectionParamsData()
 		manparams['ApSelectionRunData']=runq
 		manparams['diam']=params['diam']
 		appiondb.insert(runq)
 	       	appiondb.insert(manparams)

def getModelDimensions(mrcfile):
	print "calculating dimensions..."
	vol=Mrc.mrc_to_numeric(mrcfile)
	(x,y,z)=vol.shape
	if x!=y!=z:
		apDisplay.printError("starting model is not a cube")
	return x
	
def insertModel(params):
	print "inserting into database"
	symid=apDB.apdb.direct_query(appionData.ApSymmetryData,params['sym'])
	if not symid:
		apDisplay.printError("no symmetry associated with this id\n")		
	modq=appionData.ApInitialModelData()
	modq['project|projects|project']=params['projectId']
	modq['path']=params['path']
	modq['name']=params['path']
	modq['symmetry']=symid
	modq['pixelsize']=params['apix']
	modq['boxsize']=params['box']
	modq['description']=params['description']
	appiondb.insert(modq)
