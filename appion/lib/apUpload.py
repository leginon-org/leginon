import project
import sys
import os
import apDisplay
import appionData
import apDB
import string
try:
	import pyami.mrc as mrc
except:
	import Mrc as mrc


appiondb = apDB.apdb

def printTmpltUploadHelp():
	print "\nUsage:\nuploadTemplate.py template=<name> apix=<pixel> session=<session> diam=<n> description=<'text'>\n"
	print "uploadTemplate.py template=groEL apix=1.63 session=06nov10a diam=140 description='groel templates'\n"
	print "template=<name>       : name should not have the extension, or number."
	print "                        groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>          : angstroms per pixel of the template images"
	print "diam=<n>              : approximate diameter of particle (in Angstroms)"
	print "session=<sessionId>   : session name associated with template (i.e. 06mar12a)"
	print "description=\"text\"    : description of the template - must be in quotes"
	#print "outdir=<path>         : location to copy the templates to"
	#print "                        default: /ami/data##/appion/<sessionId>/templates/"
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
	print "\nUsage:\nuploadModel.py <filename> session=<session> symmetry=<sym id> apix=<pixel> res=<resolution> [contour=<n>] [zoom=<n>] description=<\"text\"> [rescale=<model ID,scale factor>] [boxsize=<n>]\n"
	print "uploadModel.py /ami/data99/lambda.mrc symmetry=1 apix=2.02 res=25 description=\"CCMV in EMAN orientation\"\n"
	sys.exit(1)

def printMiscUploadHelp():
	print "\nUsage:\nuploadMisc.py <filename> reconid=<n> description=<\"text\">\n"
	print "uploadModel.py cpmv_cross_section.png reconid=311 description=\"cpmv cross section with pdb docked in\"\n"
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
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='commit'):
			params['commit']=True
		elif (elements[0]=='nocommit'):
			params['commit']=False
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
	# save the input parameters into the "params" dictionary
	for arg in args[2:]:
		elements=arg.split('=')
		if (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='session'):
			params['session']=elements[1]
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='nocommit'):
			params['commit']=False
		elif (elements[0]=='symmetry'):
			params['sym']=int(elements[1])
		elif (elements[0]=='res'):
			params['res']=float(elements[1])
		elif (elements[0]=='contour'):
			params['contour']=float(elements[1])
		elif (elements[0]=='zoom'):
			params['zoom']=float(elements[1])
		elif (elements[0]=='description'):
			params['description']=elements[1]
		elif (elements[0]=='boxsize'):
			params['newbox']=int(elements[1])
		elif (elements[0]=='rescale'):
			modinfo=elements[1].split(',')
			if len(modinfo) == 2:
				params['origmodel']=modinfo[0]
				params['newapix']=float(modinfo[1])
				params['rescale']=True
			else:
				apDisplay.printError("rescale must include both the original model id and a scale factor")
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")
	# if not rescaling, make sure that the input model exists
	if (os.path.isfile(mrcfile) or params['rescale'] is True):
		(params['path'], params['name']) = os.path.split(mrcfile)
		params['path'] = os.path.abspath(params['path'])
		if not params['path']:
			params['path']=params['abspath']
	else:
		apDisplay.printError("file '"+mrcfile+"' does not exist\n")
	
def parseMiscUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printMiscUploadHelp()
	# get file
	miscfile=args[1]
	if (os.path.isfile(miscfile)):
		(params['path'], params['name']) = os.path.split(miscfile)
		if not params['path']:
			params['path']=params['abspath']
	else:
		apDisplay.printError("file '"+miscfile+"' does not exist\n")
	# save the input parameters into the "params" dictionary
	for arg in args[2:]:
		elements=arg.split('=')
		if (elements[0]=='reconid'):
			params['reconid']=int(elements[1])
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
	params['rundir']=os.path.abspath('.')
	params['abspath']=os.path.abspath('.')
	params['outdir']=None
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

def checkSymInfo(params):
	symid = appiondb.direct_query(appionData.ApSymmetryData, params['sym'])
	if not symid:
		apDisplay.printError("no symmetry associated with this id\n")
	apDisplay.printMsg("Selected symmetry group: "+str(symid['symmetry']))
	params['syminfo'] = symid

def getProjectId(params):
	projectdata = project.ProjectData()
	projects = projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name'] == params['session']:
			params['projectId'] = i['projectId']
	if not params['projectId']:
		apDisplay.printError("no project associated with this session\n")
	return

def insertModel(params):
	print "inserting into database"
	symid=appiondb.direct_query(appionData.ApSymmetryData,params['sym'])
	if not symid:
		apDisplay.printError("no symmetry associated with this id\n")		
	params['syminfo']=symid
	modq=appionData.ApInitialModelData()
	modq['project|projects|project']=params['projectId']
	modq['path']= appionData.ApPathData(path=os.path.abspath(params['outdir']))
	modq['name']=params['name']
	modq['symmetry']=symid
	modq['pixelsize']=params['apix']
	modq['boxsize']=params['box']
	modq['resolution']=params['res']
	modq['hidden']=False
	modq['description']=params['description']
	appiondb.insert(modq)

def checkReconId(params):
	reconinfo=appiondb.direct_query(appionData.ApRefinementRunData, params['reconid'])
	if not reconinfo:
		print "\nERROR: Recon ID",params['reconid'],"does not exist in the database"
		sys.exit()
	else:
		params['recon']=reconinfo
		print "Associated with",reconinfo['name'],":",reconinfo['path']
	return

def insertMisc(params):
	print "inserting into database"
	miscq = appionData.ApMiscData()
	miscq['refinementRun']=params['recon']
	miscq['path'] = appionData.ApPathData(path=os.path.abspath(params['path']))
	miscq['name']=params['name']
	miscq['description']=params['description']
	appiondb.insert(miscq)

def insertManualParams(params, expid):
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	#runq['path'] = appionData.ApPathData(path=os.path.abspath(????????))

	manparams=appionData.ApSelectionParamsData()
	manparams['diam']=params['diam']

	runids=appiondb.query(runq, results=1)

	# if no run entry exists, insert new run entry into run.dbparticledata
	# then create a new selexonParam entry
	if not runids:
		print "inserting manual runId into database"
		runq['params']=manparams
		appiondb.insert(runq)
	elif runids[0]['params'] != manparams:
		apDisplay.printError("upload parameters not the same as last run - check diameter")



