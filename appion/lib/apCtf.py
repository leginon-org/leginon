#Part of the new pyappion

import os,re,sys
#import aceFunctions as af
import ctfData
import math
import apLoop,apDisplay
import dbdatakeeper
try:
	import pymat
except:
	apDisplay.printError("MATLAB connection failed! try typing 'usematlab73'")

acedb  = dbdatakeeper.DBDataKeeper(db='dbctfdata')

def runAce(matlab,img,params):
	imgname = img['filename']
	imgpath = os.path.join(img['session']['image path'], imgname+'.mrc')

	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=img['scope']['defocus']
	
	pymat.eval(matlab,("dforig = %e;" % nominal))

	expid=int(img['session'].dbid)
	if params['commit']==True:
		#insert ace params into dbctfdata.ace_params table in db
		insertAceParams(params,expid)

	plist = (imgpath, params['outtextfile'], params['display'], params['stig'],\
		params['medium'], -nominal, params['tempdir']+"/")
	acecmd = makeMatlabCmd("ctfparams = ace(",");",plist)

	pymat.eval(matlab,acecmd)
	print apDisplay.color(" done","brown")

	matfile = os.path.join(params['matdir'],imgname+'.mrc.mat')
	savematcmd = "save('"+str(matfile)+"','ctfparams','scopeparams','dforig');"
	pymat.eval(matlab,savematcmd)

	ctfparams=pymat.get(matlab,'ctfparams')
	printResults(params,nominal,ctfparams)

	#display must be on to be able to commit ctf results to db 	
	if (params['display']):
		imfile1=os.path.join(params['tempdir'],'im1.png')
		imfile2=os.path.join(params['tempdir'],'im2.png')
		opimfile1=os.path.join(params['opimagedir'],imgname+'.mrc1.png')
		opimfile2=os.path.join(params['opimagedir'],imgname+'.mrc2.png')
		pymat.eval(matlab,"im1 = imread('"+imfile1+"');")
		pymat.eval(matlab,"im2 = imread('"+imfile2+"');")
		pymat.eval(matlab,"imwrite(im1,'"+opimfile1+"');")
		pymat.eval(matlab,"imwrite(im2,'"+opimfile2+"');")
		#insert ctf params into dbctfdata.ctf table in db
		if (params['commit']==True):
			insertCtfParams(img,params,imgname,matfile,expid,ctfparams,opimfile1,opimfile2)
	return


def printResults(params,nominal,ctfparams):
	nom1 = float(-nominal*1e6)
	defoc1 = float(ctfparams[0]*1e6)
	if (params['stig']==0):
		defoc2 = float(ctfparams[0]*1e6)
	else:
		defoc2=None
	conf1 = float(ctfparams[16])
	conf2 = float(ctfparams[17])

	if(conf1 > 0 and conf2 > 0):
		totconf = math.sqrt(conf1*conf2)
	else:
		totconf = 0.0
	if (params['stig']==0):
		pererror = (nom1-defoc1)/defoc1
		labellist = ["Nominal","Defocus","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	else:
		avgdefoc = (defoc1+defoc2)/2.0
		pererror = (nom1-avgdefoc)/avgdefoc
		labellist = ["Nominal","Defocus1","Defocus2","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,defoc2,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
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

		copyparamlist = ('display','stig','medium','edgethcarbon','edgethice',\
			'pfcarbon','pfice','overlap','fieldsize','resamplefr','drange',\
			'reprocess')
		for p in copyparamlist:
			if p in params:
				aceparams[p] = params[p]
		# if nominal df is set, save override df to database, else don't set
		if params['nominal']:
			aceparams['df_override']=dfnom

		acedb.insert(runq)
	       	acedb.insert(aceparams)
		
	# if continuing a previous run, make sure that all the current
	# parameters are the same as the previous
	else:
		aceq=ctfData.ace_params(runId=runq)
		aceresults=acedb.query(aceq, results=1)
		acelist=aceresults[0]
		mustretain = ('display','stig','medium','edgethcarbon','edgethice',\
			'pfcarbon','pfice','overlap','fieldsize','resamplefr','drange',\
			'reprocess')
		for p in mustretain:
			if acelist[p] != params[p]:
				apDisplay.printError("All parameters for a single ACE run must be identical! \n"+\
					"please check your parameter settings.")
		if (str(acelist['df_override'])!=str(dfnom)):
			apDisplay.printError("All parameters for a single ACE run must be identical! \n"+\
					"please check your parameter settings.")
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

	print "Committing ctf parameters for",apDisplay.shortenImageName(imgname), "to database."

	ctfq=ctfData.ctf()
	ctfq['runId']=runq
	ctfq['aceId']=acevals[0]
	ctfq['imageId']=procimgq
	ctfq['graph1']=opimfile1
	ctfq['graph2']=opimfile2
	ctfq['mat_file']=matfile
	ctfparamlist = ('defocus1','defocus2','defocusinit','amplitude_contrast','angle_astigmatism',\
		'noise1','noise2','noise3','noise4','envelope1','envelope2','envelope3','envelope4',\
		'lowercutoff','uppercutoff','snr','confidence','confidence_d')
	for i in range(len(ctfparamlist)):
		ctfq[ ctfparamlist[i] ] = ctfparams[i]

	if ctfq['defocus1']==-1:
		ctf_failedq=ctfData.ctf(runId=runq, aceId=acevals[0], imageId=procimgq,\
			mat_file=ctfq['mat_file'], graph1=ctfq['graph1'], graph2=ctfq['graph2'])
		acedb.insert(ctf_failedq)
	else:
		acedb.insert(ctfq)
	
	return

def mkTempDir(temppath):
	if os.path.exists(temppath):
		apDisplay.printWarning("temporary directory, '"+temppath+"' already exists\n")
	else:
		try:
			os.makedirs(temppath,0777)
		except:
			apDisplay.printError("Could not create temp directory, '"+
				temppath+"'\nCheck the folder write permissions")

	return

def setScopeParams(matlab,params):
	tempdir = params['tempdir']+"/"
	if os.path.exists(tempdir):
		plist = (params['kv'],params['cs'],params['apix'],tempdir)
		acecmd1 = makeMatlabCmd("setscopeparams(",");",plist)
		pymat.eval(matlab,acecmd1)

		plist = (params['kv'],params['cs'],params['apix'])
		acecmd2 = makeMatlabCmd("scopeparams = [","];",plist)
		pymat.eval(matlab,acecmd2)
	else:
		apDisplay.printError("Temp directory, '"+params['tempdir']+"' not present.")
	return

def getCTFParamsForImage(imagedata):
	imagename = imagedata['filename']+'.mrc'
	ctfq = ctfData.ctf()
	imq  = ctfData.image(imagename=imagename)
	ctfq['imageId'] = imq
	return(acedb.query(ctfq))

def setAceConfig(matlab,params):
	tempdir=params['tempdir']+"/"
	if os.path.exists(tempdir):
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
