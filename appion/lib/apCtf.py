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
import apDatabase

appiondb = apDB.apdb

def commitCtfValueToDatabase(imgdict, matlab, ctfvalue, params):
	expid = int(imgdict['session'].dbid)
	imgname = imgdict['filename']
	matfile = imgname+".mrc.mat"
	#matfilepath = os.path.join(params['matdir'], matfile)

	imfile1 = os.path.join(params['tempdir'], "im1.png")
	imfile2 = os.path.join(params['tempdir'], "im2.png")
	#MATLAB NEEDS PATH BUT DATABASE NEEDS FILENAME
	opimfile1 = imgname+".mrc1.png"
	opimfile2 = imgname+".mrc2.png"
	opimfilepath1 = os.path.join(params['opimagedir'],opimfile1)
	opimfilepath2 = os.path.join(params['opimagedir'],opimfile2)

	shutil.copy(imfile1, opimfilepath1)
	shutil.copy(imfile2, opimfilepath2)
	#pymat.eval(matlab,"im1 = imread('"+imfile1+"');")
	#pymat.eval(matlab,"im2 = imread('"+imfile2+"');")
	#pymat.eval(matlab,"imwrite(im1,'"+opimfilepath1+"');")
	#pymat.eval(matlab,"imwrite(im2,'"+opimfilepath2+"');")

	insertCtfValue(imgdict, params, matfile, expid, ctfvalue, opimfile1, opimfile2)

def commitCtfValueToDatabaseREFLEGINON(imgdata, matlab, ctfvalue, params):
	imgname = imgdata['filename']
	matfile = imgname+".mrc.mat"
	#matfilepath = os.path.join(params['matdir'], matfile)

	imfile1 = os.path.join(params['tempdir'], "im1.png")
	imfile2 = os.path.join(params['tempdir'], "im2.png")
	#MATLAB NEEDS PATH BUT DATABASE NEEDS FILENAME
	opimfile1 = imgname+".mrc1.png"
	opimfile2 = imgname+".mrc2.png"
	opimfilepath1 = os.path.join(params['opimagedir'],opimfile1)
	opimfilepath2 = os.path.join(params['opimagedir'],opimfile2)

	shutil.copy(imfile1, opimfilepath1)
	shutil.copy(imfile2, opimfilepath2)
	#pymat.eval(matlab,"im1 = imread('"+imfile1+"');")
	#pymat.eval(matlab,"im2 = imread('"+imfile2+"');")
	#pymat.eval(matlab,"imwrite(im1,'"+opimfilepath1+"');")
	#pymat.eval(matlab,"imwrite(im2,'"+opimfilepath2+"');")

	insertCtfValueREFLEGINON(imgdata, params, matfile, ctfvalue, opimfile1, opimfile2)


def printResults(params, nominal, ctfvalue):
	nom1 = float(-nominal*1e6)
	defoc1 = float(ctfvalue[0]*1e6)
	if (params['stig']==1):
		defoc2 = float(ctfvalue[1]*1e6)
	else:
		defoc2=None
	conf1 = float(ctfvalue[16])
	conf2 = float(ctfvalue[17])

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
	aceparamq = appionData.ApAceParamsData()
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
	runids = appiondb.query(runq, results=1)

	# if no run entry exists, insert new run entry into run.dbctfdata
	if not(runids):
		runq['aceparams']=aceparamq
		appiondb.insert(runq)

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

def insertAceParamsREFLEGINON(params,sessiondata):
	# first create an aceparam object
	aceparamq = appionData.ApAceParamsData()
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
	runq['session']=sessiondata

	# see if acerun already exists in the database
	runids = appiondb.query(runq, results=1)

	# if no run entry exists, insert new run entry into run.dbctfdata
	if not(runids):
		runq['aceparams']=aceparamq
		appiondb.insert(runq)

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

def insertCtfValue(imgdict, params, matfile, expid, ctfvalue, opimfile1, opimfile2):
	runq=appionData.ApAceRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	acerun=appiondb.query(runq,results=1)
	
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
	ctfvaluelist = ('defocus1','defocus2','defocusinit','amplitude_contrast','angle_astigmatism',\
		'noise1','noise2','noise3','noise4','envelope1','envelope2','envelope3','envelope4',\
		'lowercutoff','uppercutoff','snr','confidence','confidence_d')
	
	# test for failed ACE estimation
	# only set params if ACE was successfull
	if ctfvalue[0] != -1 :
		for i in range(len(ctfvaluelist)):
			ctfq[ ctfvaluelist[i] ] = ctfvalue[i]

	appiondb.insert(ctfq)
	
	return

def insertCtfValueREFLEGINON(imgdata, params, matfile, ctfvalue, opimfile1, opimfile2):
	runq=appionData.ApAceRunData()
	runq['name']=params['runid']
	runq['session']=imgdata['session']

	acerun=appiondb.query(runq,results=1)
	
	dforig=imgdata['scope']['defocus']

	print "Committing ctf parameters for",apDisplay.short(imgdict['filename']), "to database."

	# make sure the directory paths have '/' at end
	graphpath = os.path.normpath(params['opimagedir'])+"/"
	matpath   = os.path.normpath(params['matdir'])+"/"

	ctfq=appionData.ApCtfData()
	ctfq['acerun']=acerun[0]
	ctfq['image']=imgdata
	ctfq['graphpath']=graphpath
	ctfq['graph1']=opimfile1
	ctfq['graph2']=opimfile2
	ctfq['matpath']=matpath
	ctfq['mat_file']=matfile
	ctfvaluelist = ('defocus1','defocus2','defocusinit','amplitude_contrast','angle_astigmatism',\
		'noise1','noise2','noise3','noise4','envelope1','envelope2','envelope3','envelope4',\
		'lowercutoff','uppercutoff','snr','confidence','confidence_d')
	
	# test for failed ACE estimation
	# only set params if ACE was successfull
	if ctfvalue[0] != -1 :
		for i in range(len(ctfvaluelist)):
			ctfq[ ctfvaluelist[i] ] = ctfvalue[i]

	appiondb.insert(ctfq)
	
	return

def mkTempDir(temppath):
	return apParam.createDirectory(temppath)

def getBestDefocusForImage(imgdata, display=False):
	"""
	takes an image and get the best defocus for that image
	"""
	ctfvalue, conf = getBestCtfValueForImage(imgdata)
#	ctfvalue, conf = getBestCtfValueForImageREFLEGINON(imgdata)
	if ctfvalue['acerun']['aceparams']['stig'] == 1:
		apDisplay.printWarning("astigmatism was estimated for "+apDisplay.short(imgdata['filename'])+\
		 " and average defocus estimate may be incorrect")
		avgdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		return -avgdf

	#### the following was confusing for makestack, so I commented it out #######
	if display is True:
		print "Best ACE run info: '"+ctfvalue['acerun']['name']+"', confidence="+\
			str(round(conf,4))+", defocus="+str(round(-1.0*abs(ctfvalue['defocus1']*1.0e6),4))+\
			" microns, resamplefr="+str(ctfvalue['acerun']['aceparams']['resamplefr'])

	return -ctfvalue['defocus1']

def getBestCtfValueForImage(imgdata):
	"""
	takes an image and get the best ctfvalues for that image
	"""
	### get all ctf values
	ctfq = appionData.ApCtfData()
	ctfq['dbemdata|AcquisitionImageData|image'] = imgdata.dbid
	ctfvalues = appiondb.query(ctfq)

	### check if it has values
	if ctfvalues is None:
		return None, None

	### find the best values
	bestconf = 0.0
	bestctfvalue = None
	for ctfvalue in ctfvalues:
		conf1 = ctfvalue['confidence']
		conf2 = ctfvalue['confidence_d']
		if conf1 > 0 and conf2 > 0:
			#conf = max(conf1,conf2)
			conf = math.sqrt(conf1*conf2)
			if conf > bestconf:
				bestconf = conf
				bestctfvalue = ctfvalue

	return bestctfvalue, bestconf

def getBestCtfValueForImageREFLEGINON(imgdata):
	"""
	takes an image and get the best ctfvalues for that image
	"""
	### get all ctf values
	ctfq = appionData.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = appiondb.query(ctfq)

	### check if it has values
	if ctfvalues is None:
		return None, None

	### find the best values
	bestconf = 0.0
	bestctfvalue = None
	for ctfvalue in ctfvalues:
		conf1 = ctfvalue['confidence']
		conf2 = ctfvalue['confidence_d']
		if conf1 > 0 and conf2 > 0:
			#conf = max(conf1,conf2)
			conf = math.sqrt(conf1*conf2)
			if conf > bestconf:
				bestconf = conf
				bestctfvalue = ctfvalue

	return bestctfvalue, bestconf

def ctfValuesToParams(ctfvalue, params):
	if ctfvalue['acerun']['aceparams']['stig'] == 1:
		apDisplay.printWarning("astigmatism was estimated for this image"+\
		 " and average defocus estimate may be incorrect")
		params['hasace'] = True
		avgdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		params['df']     = avgdf*-1.0e6
		params['conf_d'] = ctfvalue['confidence_d']
		params['conf']   = ctfvalue['confidence']
		return -avgdf
	else:
		params['hasace'] = True
		params['df']     = ctfvalue['defocus1']*-1.0e6
		params['conf_d'] = ctfvalue['confidence_d']
		params['conf']   = ctfvalue['confidence']
		return -ctfvalue['defocus1']
	return None


def printCtfSummary(params):
	"""
	prints a histogram of the best ctfvalues for the session
	"""
	sys.stderr.write("processing CTF histogram...\n")
	### get all images
	imgtree = apDatabase.getAllImages({}, params)

	### get best ctf values for each image
	ctfhistconf = []
	ctfhistval = []
	for imgdata in imgtree:
		if params['norejects'] is True and apDatabase.getSiblingImgAssessmentStatus(imgdata) is False:
			continue

		ctfq = appionData.ApCtfData()
		ctfq['dbemdata|AcquisitionImageData|image'] = imgdata.dbid
		ctfvalues = appiondb.query(ctfq)

		### check if it has values
		if ctfvalues is None:
			continue

		### find the best values
		bestconf = 0.0
		bestctfvalue = None
		for ctfvalue in ctfvalues:
			conf1 = ctfvalue['confidence']
			conf2 = ctfvalue['confidence_d']
			if conf1 > 0 and conf2 > 0:
				#conf = max(conf1,conf2)
				conf = math.sqrt(conf1*conf2)
				if conf > bestconf:
					bestconf = conf
					bestctfvalue = ctfvalue
		ctfhistconf.append(bestconf)
		ctfhistval.append(bestctfvalue)

	ctfhistconf.sort()
	confhist = {}
	yspan = 20.0
	minconf = ctfhistconf[0]
	maxconf = ctfhistconf[len(ctfhistconf)-1]
	maxcount = 0
	for conf in ctfhistconf:
		c2 = round(conf*yspan,0)/yspan
		if c2 in confhist:
			confhist[c2] += 1
			if confhist[c2] > maxcount:
				maxcount = confhist[c2]
		else:
			confhist[c2] = 1
	if maxcount > 70:
		scale = 70.0/float(maxcount)
		sys.stderr.write(" * = "+str(round(scale,1))+" images\n")
	else:
		scale = 1.0

	colorstr = {}
	for i in range(int(yspan+1)):
		j = float(i)/yspan
		if j < 0.5:
			colorstr[j] = "red"
		elif j < 0.8:
			colorstr[j] = "yellow"
		else:
			colorstr[j] = "green"

	sys.stderr.write("Confidence histogram:\n")
	for i in range(int(yspan+1)):
		j = float(i)/yspan
		if j < minconf-1.0/yspan:
			continue
		jstr = "%1.2f" % j
		jstr = apDisplay.rightPadString(jstr,5)
		sys.stderr.write(jstr+"> ")
		if j in confhist:
			for k in range(int(confhist[j]*scale)):
				sys.stderr.write(apDisplay.color("*",colorstr[j]))
		sys.stderr.write("\n")
