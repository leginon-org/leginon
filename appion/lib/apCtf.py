#Part of the new pyappion

#pythonlib
import os
import re
import sys
import math
import shutil
#appion
import appionData
import apParam
import apDisplay
import apDB
try:
	import pymat
except:
	apDisplay.matlabError()

acedb  = apDB.apdb

def runAce(matlab, imgdict, params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')

	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=imgdict['scope']['defocus']
	
	pymat.eval(matlab,("dforig = %e;" % nominal))

	expid = int(imgdict['session'].dbid)
	if params['commit']==True:
		#insert ace params into dbctfdata.ace_params table in db
		insertAceParams(params,expid)

	if params['stig']==0:
		plist = (imgpath, params['outtextfile'], params['display'], params['stig'],\
			params['medium'], -nominal, params['tempdir']+"/")
		acecmd = makeMatlabCmd("ctfparams = ace(",");",plist)
	else:
		plist = (imgname, imgpath, params['outtextfile'], params['opimagedir'], \
			params['matdir'], params['display'], params['stig'],\
			params['medium'], -nominal, params['tempdir']+"/", params['resamplefr'])
		acecmd = makeMatlabCmd("ctfparams = measureAstigmatism(",");",plist)

	pymat.eval(matlab,acecmd)
	print apDisplay.color(" done","brown")

	matfile = os.path.join(params['matdir'], imgname+".mrc.mat")
	if params['stig']==0:
		savematcmd = "save('"+matfile+"','ctfparams','scopeparams', 'dforig');"
		pymat.eval(matlab,savematcmd)

	ctfparams=pymat.get(matlab, 'ctfparams')
	printResults(params,nominal,ctfparams)

	return ctfparams

def commitAceParamToDatabase(imgdict, matlab, ctfparams, params):
	expid = int(imgdict['session'].dbid)
	imgname = imgdict['filename']
	matfile = imgname+".mrc.mat"
	#matfilepath = os.path.join(params['matdir'], matfile)

	imfile1=os.path.join(params['tempdir'], "im1.png")
	imfile2=os.path.join(params['tempdir'], "im2.png")
	#MATLAB NEEDS PATH BUT DATABASE NEEDS FILENAME
	opimfile1=imgname+".mrc1.png"
	opimfile2=imgname+".mrc2.png"
	opimfilepath1 = os.path.join(params['opimagedir'],opimfile1)
	opimfilepath2 = os.path.join(params['opimagedir'],opimfile2)

	shutil.copy(imfile1, opimfilepath1)
	shutil.copy(imfile2, opimfilepath2)
	#pymat.eval(matlab,"im1 = imread('"+imfile1+"');")
	#pymat.eval(matlab,"im2 = imread('"+imfile2+"');")
	#pymat.eval(matlab,"imwrite(im1,'"+opimfilepath1+"');")
	#pymat.eval(matlab,"imwrite(im2,'"+opimfilepath2+"');")

	insertCtfParams(imgdict, params, matfile, expid, ctfparams, opimfile1, opimfile2)

def runAceDrift(matlab,imgdict,params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')
	
	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=imgdict['scope']['defocus']
	
	expid=int(imgdict['session'].dbid)
	if params['commit']==True:
		#insert ace params into dbctfdata.ace_params table in db
		insertAceParams(params,expid)

	#pdb.set_trace()
	acecommand=("measureAnisotropy('%s','%s',%d,'%s',%e,'%s','%s','%s', '%s');" % \
		( imgpath, params['outtextfile'], params['display'],\
		params['medium'], -nominal, params['tempdir']+"/", params['opimagedir'], params['matdir'], imgname))
		
	#~ acecommand=("mnUpCut = measureDrift('%s','%s',%d,%d,'%s',%e,'%s');" % \
		#~ ( imgpath, params['outtextfile'], params['display'], params['stig'],\
		#~ params['medium'], -nominal, params['tempdir']))
		
	print " ... processing", apDisplay.shortenImageName(imgname)
	pymat.eval(matlab,acecommand)
	print "done"	

def runAceCorrect(matlab,imgdict,params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')
	
	matname=imgname+'.mrc.mat'
	matfile=os.path.join(params['matdir'],matname)
	print "Ctf params obtained from " + matfile
	
	ctdimname = imgname+'.mrc.ctf_ph'
	ctdimpath = os.path.join(params['correctedimdir'],ctdimname)

	acecorrectcommand=("ctfcorrect('%s','%s','%s','%s','%s', '%s');" % (imgpath, matfile, params['tempdir']+"/", ctdimpath, params['ctdIntmdImDir'], imgname))

	print " ... processing", apDisplay.shortenImageName(imgname)
	pymat.eval(matlab,acecorrectcommand)
	print "done"

	return

def printResults(params,nominal,ctfparams):
	nom1 = float(-nominal*1e6)
	defoc1 = float(ctfparams[0]*1e6)
	if (params['stig']==1):
		defoc2 = float(ctfparams[1]*1e6)
	else:
		defoc2=None
	conf1 = float(ctfparams[16])
	conf2 = float(ctfparams[17])

	if(conf1 > 0 and conf2 > 0):
		totconf = math.sqrt(conf1*conf2)
	else:
		totconf = 0.0
	if (params['stig']==0):
		if nom1 != 0: pererror = (nom1-defoc1)/nom1
		else: pererror = 1.0
		labellist = ["Nominal","Defocus","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	else:
		avgdefoc = (defoc1+defoc2)/2.0
		if nom1 != 0: pererror = (nom1-avgdefoc)/nom1
		else: pererror = 1.0
		labellist = ["Nominal","Defocus1","Defocus2","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,defoc2,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	return


def insertAceParams(params,expid):
	# first create an aceparam object
	aceparamq=appionData.ApAceParamsData()
	copyparamlist = ('display','stig','medium','edgethcarbon','edgethice',\
			 'pfcarbon','pfice','overlap','fieldsize','resamplefr','drange',\
			 'reprocess')
	for p in copyparamlist:
		if p in params:
			aceparamq[p] = params[p]
			
	# if nominal df is set, save override df to database, else don't set
	if params['nominal']:
		dfnom=-params['nominal']
		aceparamq['df_override']=dfnom
	
	# create an acerun object
	runq=appionData.ApAceRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	# see if acerun already exists in the database
	runids=acedb.query(runq, results=1)

	# if no run entry exists, insert new run entry into run.dbctfdata
	if not(runids):
		runq['aceparams']=aceparamq
		acedb.insert(runq)

	# if continuing a previous run, make sure that all the current
	# parameters are the same as the previous
	else:
		if not (runids[0]['aceparams'] == aceparamq):
			for i in runids[0]['aceparams']:
				if runids[0]['aceparams'][i] != aceparamq[i]:
					apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
			apDisplay.printError("All parameters for a single ACE run must be identical! \n"+\
					     "please check your parameter settings.")
	return

def insertCtfParams(imgdict,params,matfile,expid,ctfparams,opimfile1,opimfile2):
	runq=appionData.ApAceRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	acerun=acedb.query(runq,results=1)
	
	legimgid=int(imgdict.dbid)
	legpresetid=None
	if imgdict['preset']:		
		legpresetid =int(imgdict['preset'].dbid)
		
	dforig=imgdict['scope']['defocus']

	print "Committing ctf parameters for",apDisplay.short(imgdict['filename']), "to database."

	# make sure the directory paths have '/' at end
	graphpath = os.path.normpath(params['opimagedir'])+"/"
	matpath   = os.path.normpath(params['matdir'])+"/"

	ctfq=appionData.ApCtfData()
	ctfq['acerun']=acerun[0]
	ctfq['dbemdata|AcquisitionImageData|image']=legimgid
	ctfq['graphpath']=graphpath
	ctfq['graph1']=opimfile1
	ctfq['graph2']=opimfile2
	ctfq['matpath']=matpath
	ctfq['mat_file']=matfile
	ctfparamlist = ('defocus1','defocus2','defocusinit','amplitude_contrast','angle_astigmatism',\
		'noise1','noise2','noise3','noise4','envelope1','envelope2','envelope3','envelope4',\
		'lowercutoff','uppercutoff','snr','confidence','confidence_d')
	
	# test for failed ACE estimation
	# only set params if ACE was successfull
	if ctfparams[0] != -1 :
		for i in range(len(ctfparamlist)):
			ctfq[ ctfparamlist[i] ] = ctfparams[i]

	acedb.insert(ctfq)
	
	return

def mkTempDir(temppath):
	return apParam.createDirectory(temppath)

def setScopeParams(matlab,params):
	tempdir = params['tempdir']+"/"
	if os.path.isdir(tempdir):
		plist = (params['kv'],params['cs'],params['apix'],tempdir)
		acecmd1 = makeMatlabCmd("setscopeparams(",");",plist)
		pymat.eval(matlab,acecmd1)

		plist = (params['kv'],params['cs'],params['apix'])
		acecmd2 = makeMatlabCmd("scopeparams = [","];",plist)
		pymat.eval(matlab,acecmd2)
	else:
		apDisplay.printError("Temp directory, '"+params['tempdir']+"' not present.")
	return

def getCTFParamsForImage(imgdict):
	ctfq = appionData.ApCtfData()
	imgid  = imgdict.dbid
	ctfq['dbemdata|AcquisitionImageData|image'] = imgid
	return(acedb.query(ctfq))

def setAceConfig(matlab,params):
	tempdir=params['tempdir']+"/"
	if os.path.isdir(tempdir):
		pymat.eval(matlab, "edgethcarbon="+str(params['edgethcarbon'])+";")
		pymat.eval(matlab, "edgethice="+str(params['edgethice'])+";")
		pymat.eval(matlab, "pfcarbon="+str(params['pfcarbon'])+";")
		pymat.eval(matlab, "pfice="+str(params['pfice'])+";")
		pymat.eval(matlab, "overlap="+str(params['overlap'])+";")
		pymat.eval(matlab, "fieldsize="+str(params['fieldsize'])+";")
		pymat.eval(matlab, "resamplefr="+str(params['resamplefr'])+";")
		pymat.eval(matlab, "drange="+str(params['drange'])+";")

		aceconfig=os.path.join(tempdir,"aceconfig.mat")
		acecmd = "save('"+aceconfig+"','edgethcarbon','edgethice','pfcarbon','pfice',"+\
			"'overlap','fieldsize','resamplefr','drange');"
		pymat.eval(matlab,acecmd)
	else:
		apDisplay.printError("Temp directory, '"+tempdir+"' not present.")
	return

def checkMatlabPath(params=None):
	if os.environ.get("MATLABPATH") is None:
		#TRY LOCAL DIRECTORY FIRST
		matlabpath = os.path.abspath(".")
		if os.path.isfile(os.path.join(matlabpath,"ace.m")):
			updateMatlabPath(matlabpath)
			return
		#TRY APPIONDIR/ace
		if params is not None and 'appiondir' in params:
			matlabpath = os.path.join(params['appiondir'],"ace")
			if os.path.isdir(matlabpath) and os.path.isfile(os.path.join(matlabpath,"ace.m")):
				updateMatlabPath(matlabpath)
				return
		#TRY global install
		matlabpath = "/ami/sw/packages/pyappion/ace"
		if os.path.isdir(matlabpath) and os.path.isfile(os.path.join(matlabpath,"ace.m")):
			updateMatlabPath(matlabpath)
			return
		apDisplay.matlabError()

def updateMatlabPath(matlabpath):
	data1 = os.environ.copy()
	data1['MATLABPATH'] =  matlabpath
	os.environ.update(data1)
	#os.environ.get('MATLABPATH')
	return

def makeMatlabCmd(header,footer,plist):
	cmd = header
	for p in plist:
		if type(p) is str:
			cmd += "'"+p+"',"
		else:
			cmd += str(p)+","
	#remove extra comma
	n = len(cmd)
	cmd = cmd[:(n-1)]
	cmd += footer
	return cmd

def getAceValues(imgdata, params):
	# if already got ace values in a previous step,
	# don't do all this over again.
	if params['hasace'] is True:
		return
	else:
		ctfq = appionData.ApCtfData()
		ctfq['dbemdata|AcquisitionImageData|image']= imgdata.dbid
		
		ctfparams=apdb.query(ctfq)
		
		# if ctf data exist for filename
		if ctfparams is not None:
			conf_best=0
			params['kv']=(imgdata['scope']['high tension'])/1000

			# loop through each of the ace runs & get the params with highest confidence value
			for ctfp in ctfparams:
				conf1=ctfp['confidence']
				conf2=ctfp['confidence_d']
				if conf_best < conf1 :
					conf_best=conf1
					bestctfp=ctfp
				if conf_best < conf2 :
					conf_best=conf2
					bestctfp=ctfp
			if bestctfp['acerun']['aceparams']['stig']==0:
				params['hasace']=True
				params['df']=(bestctfp['defocus1'])*-1e6
				params['conf_d']=bestctfp['confidence_d']
				params['conf']=bestctfp['confidence']
			else:
				apDisplay.printWarning("Astigmatism was estimated for "+apDisplay.short(imgdict['filename'])+\
				 ". Defocus estimate may be incorrect")
				params['hasace']=True
				params['df']=( (bestctfp['defocus1'] + bestctfp['defocus2'])/2 )*-1e6
				params['conf_d']=bestctfp['confidence_d']
				params['conf']=bestctfp['confidence']
	return
