#!/usr/bin/env python
# Python functions for ace

import os, sys
import cPickle
import pymat
import data
import ctfData
import dbdatakeeper

db=dbdatakeeper.DBDataKeeper()
acedb=dbdatakeeper.DBDataKeeper(db='dbctfdata')
acedonename='.acedone.py'

def printHelp():
	print "\nUsage:\npyace.py edgethcarbon=<n> edgethice=<n> pfcarbon=<n> pfice=<n> overlap=<n> fieldsize=<n> fr=<n> drange=<n> dbimages=<session>,<preset> alldbimages=<session> tempdir=<dir> [medium=carbon or medium=ice] cs=<n> outdir=<dir> runid=<runid> [display=1 or display=0] [stig=0 or stig=1] continue nominal=<n> commit reprocess=<n>\n"
	print "Example:\npyace.py dbimages=06aug30b,en medium=ice continue\n"
	print "edgethcarbon=<n>            : threshold for edge detection with medium=carbon (default=0.8)"
	print "edgethice=<n>               : threshold for edge detection with medium=ice (default=0.6)"
	print "pfcarbon=<n>                : power factor that determines the location of the upper cutoff frequency with medium=carbon (default=0.9)"
	print "pfice=<n>                   : power factor that determines the location of the upper cutoff frequency with medium=ice (default=0.3)"
	print "overlap=<n>                 : overlap of subimages for determining power spectrum (default=2)"
	print "fieldsize=<512>             : field size of subimages for determining power spectrum (default=512)"
	print "resamplefr=<n>              : resample value: increase if images have high defocus or small pixel size (default=1)"
	print "drange=0 or 1               : switch dynamic range compression on or off (default=0)"
	print "dbimages=<session>,<preset> : images to process will be queried based on session and preset"
	print "alldbimages=<session>       : images to process will be queried based on session"
	print "tempdir=<tempdir>           : temporary directory to hold intermediate files (default=./temp/)"
	print "medium=carbon or ice        : switch to determine thresholds for edge detection and power spectrum (default=carbon)"
	print "cs=<n>                      : spherical abberation (default=2.0)"
	print "outdir=<dir>                : directory into which to place the output (default=(session directory))"
	print "runid=<runid>               : subdirectory for output (default=run1)"
	print "display=0 or 1              : switch to determine whether output images will be written (default=1)"
	print "stig=0 or 1                 : switch to determine whether astigmatism will be estimated (default=0)"
	print "continue                    : if continue is specified, previously processed images for <runid> will be skipped"
	print "nominal=<n>                 : if present, the value specified by nominal will override the value returned from the database (default=None)"
	print "                              value specified should be in meters, for example: nominal=-2.0e-6"
	print "commit                      : if commit is specified, ctf parameters will be stored to the database"
	print "reprocess=<n>               : if reprocess is specified, images that have already been processed but have both confidence and confidence_d"
	print "                              values less than <n> will be reprocessed. Note: A new runid must be specified" 
	sys.exit()
	
def createDefaults():
	# create default values for parameters
	params={}
	params['edgethcarbon']=0.8
	params['edgethice']=0.6
	params['pfcarbon']=0.9
	params['pfice']=0.3
	params['overlap']=2
	params['fieldsize']=512
	params['resamplefr']=1
	params['drange']=0
	params['dbimages']=False
	params['alldbimages']=False
	params['sessionname']=None
	params['preset']=None
	params['tempdir']='./temp/'
	params['medium']='carbon'
	params['cs']=2.0
	params['outdir']=None
	params['runid']='run1'
	params['display']=1
	params['stig']=0
	params['continue']=False
	params['nominal']=None
	params['commit']=False
	params['reprocess']=None

	return(params)

def parseInput(args):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printHelp()

	# create params dictionary & set defaults
	params=createDefaults()
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='edgethcarbon'):
			params["edgethcarbon"]=float(elements[1])
		elif (elements[0]=='edgethice'):
			params["edgethice"]=float(elements[1])
		elif (elements[0]=='pfcarbon'):
			params["pfcarbon"]=float(elements[1])
		elif (elements[0]=='pfice'):
			params["pfice"]=float(elements[1])
		elif (elements[0]=='overlap'):
			params["overlap"]=int(elements[1])
		elif (elements[0]=='fieldsize'):
			params["fieldsize"]=int(elements[1])
		elif (elements[0]=='resamplefr'):
			params["resamplefr"]=float(elements[1])
		elif (elements[0]=='drange'):
			drange=int(elements[1])
			if drange == 1 or drange== 0:
				params["drange"]=drange
			else:
				print "Error: drange should only be 0 or 1"
				sys.exit()
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo)==2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
				params['dbimages']=True
				params['continue']=True
			else:
				print "dbimages must include both sessionname and preset parameters"
				sys.exit()
		elif (elements[0]=='alldbimages'):
			params['sessionname']=elements[1]
			params['alldbimages']=True
		elif (elements[0]=='tempdir'):
			params['tempdir']=elements[1]
		elif (elements[0]=='medium'):
			medium=elements[1]
			if medium=='carbon' or medium=='ice':
				params['medium']=medium
			else:
				print "medium can only be 'carbon' or 'ice'"
				sys.exit()
		elif (elements[0]=='cs'):
			params['cs']=float(elements[1])
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='display'):
			display=int(elements[1])
			if display==0 or display==1:
				params['display']=display
			else:
				print "display must be 0 or 1"
				sys.exit()		
		elif (elements[0]=='stig'):
			stig=int(elements[1])
			if stig==0 or stig==1:
				params['stig']=stig
			else:
				print "stig must be 0 or 1"
				sys.exit()
		elif arg=='continue':
			params['continue']=True
		elif (elements[0]=='nominal'):
			params['nominal']=float(elements[1])
		elif arg=='commit':
			params['commit']=True
			params['display']=1
		elif (elements[0]=='reprocess'):
			params['reprocess']=float(elements[1])
		else:
			print "undefined parameter", arg
			sys.exit()
		
	return(params)	

def getImagesFromDB(session,preset):
	# returns list of image names from DB
	print "Querying database for images"
	sessionq = data.SessionData(name=session)
	presetq=data.PresetData(name=preset)
	imageq=data.AcquisitionImageData()
	imageq['preset'] = presetq
	imageq['session'] = sessionq
	# readimages=False to keep db from returning actual image
	# readimages=True could be used for doing processing w/i this script
	imagelist=db.query(imageq, readimages=False)
	return (imagelist)

def getAllImagesFromDB(session):
	# returns list of image data based on session name
	print "Querying database for images"
	sessionq= data.SessionData(name=session)
	imageq=data.AcquisitionImageData()
	imageq['session']=sessionq
	imagelist=db.query(imageq, readimages=False)
	return (imagelist)
	
def getImagesToReprocess(params):
	session=params['sessionname']
	preset=params['preset']
	threshold=params['reprocess']
	images=getImagesFromDB(session,preset)
	imagelist=[]
	for n in images:
		imagename=n['filename']+'.mrc'
		ctfq=ctfData.ctf()
		imq=ctfData.image(imagename=imagename)
		ctfq['imageId']=imq
		ctfparams=acedb.query(ctfq)
		if ctfparams:
			if ctfparams[0]['confidence'] > threshold and ctfparams[0]['confidence_d'] > threshold:
				print imagename, 'has confidence and confidence_d <', threshold
				imagelist.append(n)
		else:
			#print imagename, 'not processed yet. Will process now with current ACE parameters.'
			imagelist.append(n)
	return (imagelist)

def getCTFParamsForImage(imagedata):
	imagename=imagedata['filename']+'.mrc'
	ctfq=ctfData.ctf()
	imq=ctfData.image(imagename=imagename)
	ctfq['imageId']=imq
	return(acedb.query(ctfq))
	
def getPixelSize(imagedata):
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=imagedata['scope']['magnification']
	pixelsizeq['tem']=imagedata['scope']['tem']
	pixelsizeq['ccdcamera'] = imagedata['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	binning=imagedata['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	return(pixelsize*1e10)

def getDoneDict(params):
	#write done dict to rundir
	params['acedonepath']=os.path.join(params['rundir'],acedonename)
	if os.path.exists(params['acedonepath']):
		# unpickle previously modified dictionary
		f=open(params['acedonepath'],'r')
		donedict=cPickle.load(f)
		f.close()
	else:
		#set up dictionary
		donedict={}
	return (params,donedict)

def writeDoneDict(donedict,params):
	f=open(params['acedonepath'],'w')
	cPickle.dump(donedict,f)
	f.close()
	return
	
def doneCheck(donedict,im):
	# check to see if image has been processed yet and
	# append dictionary if it hasn't
	# this may not be the best way to do this
	if donedict.has_key(im):
		pass
	else:
		donedict[im]=None
	return

def mkTempDir(temppath):
	if os.path.exists(temppath):
		print "\nWarning: temporary directory,", temppath, "already exists\n"
	else:
		os.mkdir(temppath)
	return

def setScopeParams(matlab,params):
	if os.path.exists(params['tempdir']):
		acecommand=("setscopeparams(%d,%f,%f,'%s');" % (params['kv'],params['cs'],params['apix'],params['tempdir']))
#		print acecommand
		pymat.eval(matlab,acecommand)
		pymat.eval(matlab,("scopeparams = [%d, %f, %f];" % (params['kv'],params['cs'],params['apix'])))
	else:
		print "Temp directory not present."
		sys.exit()
	return

def setAceConfig(matlab,params):
	tempdir=params['tempdir']
	if os.path.exists(tempdir):
		aceconfig=tempdir+'aceconfig.mat'
		pymat.eval(matlab, ("edgethcarbon=%f;" % params['edgethcarbon']))
		pymat.eval(matlab, ("edgethice=%f;" % params['edgethice']))
		pymat.eval(matlab, ("pfcarbon=%f;" % params['pfcarbon']))
		pymat.eval(matlab, ("pfice=%f;" % params['pfice']))
		pymat.eval(matlab, ("overlap=%d;" % params['overlap']))
		pymat.eval(matlab, ("fieldsize=%d;" % params['fieldsize']))
		pymat.eval(matlab, ("resamplefr=%f;" % params['resamplefr']))
		pymat.eval(matlab, ("drange=%d;" % params['drange']))
		acecommand=("save('%s','edgethcarbon','edgethice','pfcarbon','pfice','overlap','fieldsize','resamplefr','drange');" % aceconfig )
#		print acecommand
		pymat.eval(matlab,acecommand)
	else:
		print "Temp directory not present."
		sys.exit()
	return

def writePyAceLog(commandline):
	f=open('.pyacelog', 'a')
	out=""
	for n in commandline:
		out=out+n+" "
	f.write(out)
	f.write("\n")
	f.close()

def runAce(matlab,img,params):
	imgpath=img['session']['image path']
	imgname=img['filename']
	imgpath=imgpath + '/' + imgname + '.mrc'
	
	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=img['scope']['defocus']
	
	pymat.eval(matlab,("dforig = %e;" % nominal))

	expid=int(img['session'].dbid)
	if params['commit']==True:
		#insert ace params into dbctfdata.ace_params table in db
		insertAceParams(params,expid)

	acecommand=("ctfparams = ace('%s','%s',%d,%d,'%s',%e,'%s');" % (imgpath, params['outtextfile'], params['display'], params['stig'], params['medium'], -nominal, params['tempdir']))
#	print acecommand
	print "Processing", imgname
	pymat.eval(matlab,acecommand)

	matname=imgname+'.mrc.mat'
	matfile=os.path.join(params['matdir'],matname)
	savematcommand=("save('%s','ctfparams','scopeparams','dforig');" % (matfile))
#	print savematcommand
	pymat.eval(matlab,savematcommand)
	ctfparams=pymat.get(matlab,'ctfparams')
	if (params['stig']==0):
		print " +---------+---------+-------+-------+ "
		print " | Nominal | Defocus | Conf1 | Conf2 | "
		print(" | %1.3f   |  %1.3f  | %1.3f | %1.3f | " % \
			(float(-nominal*1e6), float(ctfparams[0]*1e6), ctfparams[16], ctfparams[17]))
		print " +---------+---------+-------+-------+ "
	else:
		print " +---------+----------+----------+-------+-------+ "
		print " | Nominal | Defocus1 | Defocus2 | Conf1 | Conf2 | "
		print(" |  %1.3f  |   %1.3f  |  %1.3f   | %1.3f | %1.3f | " % \
			(float(-nominal*1e6), float(ctfparams[0]*1e6), float(ctfparams[1]*1e6), ctfparams[16], ctfparams[17]))
		print " +---------+----------+----------+-------+-------+ "
	#display must be on to be able to commit ctf results to db 	
	if (params['display']):
		imfile1=params['tempdir']+'im1.png'
		imfile2=params['tempdir']+'im2.png'
		opimname1=imgname+'.mrc1.png'
		opimname2=imgname+'.mrc2.png'
		opimfile1=os.path.join(params['opimagedir'],opimname1)
		opimfile2=os.path.join(params['opimagedir'],opimname2)
		
		pymat.eval(matlab,("im1 = imread('%s');" % (imfile1)))
		pymat.eval(matlab,("im2 = imread('%s');" % (imfile2))) 
		pymat.eval(matlab,("imwrite(im1,'%s');" % (opimfile1)))
		pymat.eval(matlab,("imwrite(im2,'%s');" % (opimfile2)))

		#insert ctf params into dbctfdata.ctf table in db
		if (params['commit']==True):
			insertCtfParams(img,params,imgname,matfile,expid,ctfparams,opimfile1,opimfile2)

	return

def insertAceParams(params,expid):
	runq=ctfData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=acedb.query(runq, results=1)

	dfnom='None'
	if params['nominal']:
		dfnom=-params['nominal']
		
	# if no run entry exists, insert new run entry into run.dbctfdata
	# then create a new ace_param entry
	if not(runids):
		aceparams=ctfData.ace_params()
		aceparams['runId']=runq
		aceparams['display']=params['display']
		aceparams['stig']=params['stig']
		aceparams['medium']=params['medium']
		aceparams['edgethcarbon']=params['edgethcarbon']
		aceparams['edgethice']=params['edgethice']
		aceparams['pfcarbon']=params['pfcarbon']
		aceparams['pfice']=params['pfice']
		aceparams['overlap']=params['overlap']
		aceparams['fieldsize']=params['fieldsize']
		aceparams['resamplefr']=params['resamplefr']
		aceparams['drange']=params['drange']
		# if nominal df is set, save override df to database, else don't set
		if params['nominal']:
			aceparams['df_override']=dfnom
		if params['reprocess']:
			aceparams['reprocess']=params['reprocess']
		acedb.insert(runq)
	       	acedb.insert(aceparams)
		
	# if continuing a previous run, make sure that all the current
	# parameters are the same as the previous
	else:
		aceq=ctfData.ace_params(runId=runq)
		aceresults=acedb.query(aceq, results=1)
		acelist=aceresults[0]
		if (acelist['display']!=params['display'] or
		    acelist['stig']!=params['stig'] or
		    acelist['medium']!=params['medium'] or
		    acelist['edgethcarbon']!=params['edgethcarbon'] or
		    acelist['edgethice']!=params['edgethice'] or
		    acelist['pfcarbon']!=params['pfcarbon'] or
		    acelist['pfice']!=params['pfice'] or
		    acelist['overlap']!=params['overlap'] or
		    acelist['fieldsize']!=params['fieldsize'] or
		    acelist['resamplefr']!=params['resamplefr'] or
		    acelist['drange']!=params['drange'] or
		    acelist['reprocess']!=params['reprocess'] or
		    str(acelist['df_override'])!=str(dfnom)):
			print "All parameters for a single ACE run must be identical!"
			print "please check your parameter settings."
			sys.exit()
	return

def insertCtfParams(img,params,imgname,matfile,expid,ctfparams,opimfile1,opimfile2):
	runq=ctfData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	# get corresponding ace_params entry
	aceq=ctfData.ace_params(runId=runq)
	acevals=acedb.query(aceq, results=1)

	legimgid=int(img.dbid)
	legpresetid=None
	if img['preset']:		
		legpresetid =int(img['preset'].dbid)
		
	dforig=img['scope']['defocus']

	procimgq = ctfData.image(imagename=imgname + '.mrc')
	procimgq['dbemdata|SessionData|session']=expid
	procimgq['dbemdata|AcquisitionImageData|image']=legimgid
	procimgq['dbemdata|PresetData|preset']=legpresetid
	procimgq['dbemdata|ScopeEMData|defocus']=dforig

	imgids=acedb.query(procimgq)

	# if no image entry, make one
	if not (imgids):
		acedb.insert(procimgq)
			
	print "Committing ctf parameters for", imgname, "to database."
	ctfq=ctfData.ctf()
	ctfq['runId']=runq
	ctfq['aceId']=acevals[0]
	ctfq['imageId']=procimgq
	ctfq['defocus1']=ctfparams[0]
	ctfq['defocus2']=ctfparams[1]
	ctfq['defocusinit']=ctfparams[2]
	ctfq['amplitude_contrast']=ctfparams[3]
	ctfq['angle_astigmatism']=ctfparams[4]
	ctfq['noise1']=ctfparams[5]
	ctfq['noise2']=ctfparams[6]
	ctfq['noise3']=ctfparams[7]
	ctfq['noise4']=ctfparams[8]
	ctfq['envelope1']=ctfparams[9]
	ctfq['envelope2']=ctfparams[10]
	ctfq['envelope3']=ctfparams[11]
	ctfq['envelope4']=ctfparams[12]
	ctfq['lowercutoff']=ctfparams[13]
	ctfq['uppercutoff']=ctfparams[14]
	ctfq['graph1']=opimfile1
	ctfq['graph2']=opimfile2
	ctfq['mat_file']=matfile
	ctfq['snr']=ctfparams[15]
	ctfq['confidence']=ctfparams[16]
	ctfq['confidence_d']=ctfparams[17]

	if ctfq['defocus1']==-1:
		ctf_failedq=ctfData.ctf(runId=runq, aceId=acevals[0], imageId=procimgq, mat_file=ctfq['mat_file'], graph1=ctfq['graph1'], graph2=ctfq['graph2'])
		acedb.insert(ctf_failedq)
	else:
		acedb.insert(ctfq)
	
	return

def getOutDirs(params):
	sessionq=data.SessionData(name=params['sessionname'])
	sessiondata=db.query(sessionq)
	impath=sessiondata[0]['image path']
	print impath,sessiondata,sessionq
	params['imgdir']=impath+'/'

	if params['outdir']:
		pass
	else:
		outdir=os.path.split(impath)[0]
		outdir=os.path.join(outdir,'ctf_ace/')
		params['outdir']=outdir

	params['rundir']=os.path.join(params['outdir'],params['runid'])
	params['matdir']=os.path.join(params['rundir'],'matfiles')
	params['opimagedir']=os.path.join(params['rundir'],'opimages')
#	print params['rundir']
	
	if os.path.exists(params['outdir']):
		if os.path.exists(params['rundir']):
			print "\nWarning: run directory for", params['runid'],"already exists. Make sure continue option is on if you don't want to overwrite previous run.\n"
		else:
			os.makedirs(params['matdir'])
			os.makedirs(params['opimagedir'])
	else:
		os.makedirs(params['matdir'])
		os.makedirs(params['opimagedir'])
	
	return(params)

def getOutTextFile(params):
	session=params['sessionname']
	rundir=params['rundir']
	outtextfile=os.path.join(rundir,(session+'.txt'))
	params['outtextfile']=outtextfile
	return(params)
