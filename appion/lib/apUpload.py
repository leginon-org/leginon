import project
import sys
import os
import re
import apDisplay
import appionData
import apDatabase
import leginondata
import apDB
import string
import apFile
try:
	import pyami.mrc as mrc
except:
	import Mrc as mrc

appiondb = apDB.apdb

def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"
	sys.exit(1)

def printMiscUploadHelp():
	print "\nUsage:\nuploadMisc.py <filename> reconid=<n> session=<session> description=<\"text\">\n"
	print "uploadMisc.py cpmv_cross_section.png reconid=311 description=\"cpmv cross section with pdb docked in\"\n"
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
		elif (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

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
		elif (elements[0]=='session'):
			params['session']=elements[1]
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

def getSymmetryData(symid, msg=True):
	symdata = appiondb.direct_query(appionData.ApSymmetryData, symid)
	if not symdata:
		printSymmetries()
		apDisplay.printError("no symmetry associated with this id: "+str(symid))
	if msg is True:
		apDisplay.printMsg("Selected symmetry group: "
			+apDisplay.colorString(str(symdata['symmetry']), "cyan"))
	return symdata

def getProjectId(params):
	projectdata = project.ProjectData()
	projects = projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name'] == params['session']:
			params['projectId'] = i['projectId']
	print params['session'], params['projectId']
	if not params['projectId']:
		apDisplay.printError("no project associated with this session\n")
	return

def compSymm(a, b):
	if a.dbid > b.dbid:
		return 1
	else:
		return -1

def printSymmetries():
	symq = appionData.ApSymmetryData()
	syms = appiondb.query(symq)
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
	symdata=appiondb.direct_query(appionData.ApSymmetryData, params['sym'])
	if not symdata:
		apDisplay.printError("no symmetry associated with this id\n")		
	params['syminfo'] = symdata
	modq=appionData.ApInitialModelData()
	modq['project|projects|project'] = params['projectId']
	modq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	modq['name'] = params['name']
	modq['symmetry'] = symdata
	modq['pixelsize'] = params['newapix']
	modq['boxsize'] = params['oldbox']
	modq['resolution'] = params['res']
	modq['hidden'] = False
	filepath = os.path.join(params['outdir'], params['name'])
	modq['md5sum'] = apFile.md5sumfile(filepath)
	modq['description'] = params['description']
	if params['commit'] is True:
		appiondb.insert(modq)
	else:
		apDisplay.printWarning("not commiting model to database")

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
	if params['reconid'] is not None:
		miscq['refinementRun']= params['recon']
	if params['projectId'] is not None:
		miscq['project|projects|project']= params['projectId']
	miscq['path'] = appionData.ApPathData(path=os.path.abspath(params['path']))
	miscq['name']= params['name']
	miscq['description']=params['description']
	appiondb.insert(miscq)

def insertManualParams(params, expid):
	sessiondata = appiondb.direct_query(leginondata.SessionData, expid)
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['session']=sessiondata
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



