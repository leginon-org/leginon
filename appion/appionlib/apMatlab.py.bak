#Part of the new pyappion

#pythonlib
import os, pdb
import re
import sys
import math
import shutil
import time
import subprocess
#appion
from appionlib import appiondata
from appionlib import apParam
from appionlib import apDisplay
from appionlib.apCtf import ctfdb
from appionlib import apImage
from appionlib import apDBImage
from appionlib import apDatabase

try:
	import mlabraw as pymat
except:
	apDisplay.printWarning("Matlab module did not get imported")


#=====================
def printResults(params, nominal, ctfvalue):
	"""
	This is only used by ACE1
	"""
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

#=====================
def runAce(matlab, imgdata, params, showprev=True):
	imgname = imgdata['filename']

	if showprev is True:
		bestctfvalue = ctfdb.getBestCtfByResolution(imgdata)
		if bestctfvalue:
			bestconf = ctfdb.calculateConfidenceScore(bestctfvalue)
			print ( "Prev best: '"+bestctfvalue['acerun']['name']+"', conf="+
				apDisplay.colorProb(bestconf)+", defocus="+str(round(-1.0*abs(bestctfvalue['defocus1']*1.0e6),2))+
				" microns" )

	if params['uncorrected']:
		tmpname='temporaryCorrectedImage.mrc'
		imgarray = apDBImage.correctImage(imgdata)
		imgpath = os.path.join(params['rundir'],tmpname)
		apImage.arrayToMrc(imgarray, imgpath)
		print "processing", imgpath
	else:
		imgpath = os.path.join(imgdata['session']['image path'], imgname+'.mrc')

	nominal = None
	if params['nominal'] is not None:
		nominal=params['nominal']
	elif params['newnominal'] is True:
		bestctfvalue = ctfdb.getBestCtfByResolution(imgdata)
		nominal = bestctfvalue['defocus1']
	if nominal is None:
		nominal = imgdata['scope']['defocus']

	if nominal is None or nominal > 0 or nominal < -15e-6:
			apDisplay.printWarning("Nominal should be of the form nominal=-1.2e-6"+\
				" for -1.2 microns NOT:"+str(nominal))

	#Neil's Hack
	#if 'autosample' in params and params['autosample']:
	#	x = abs(nominal*1.0e6)
	#	val = 1.585 + 0.057587 * x - 0.044106 * x**2 + 0.010877 * x**3
	#	resamplefr_override = round(val,3)
	#	print "resamplefr_override=",resamplefr_override
	#	pymat.eval(matlab, "resamplefr="+str(resamplefr_override)+";")

	pymat.eval(matlab,("dforig = %e;" % nominal))

	if params['stig'] == 0:
		plist = (imgpath, params['outtextfile'], params['display'], params['stig'],\
			params['medium'], -nominal, params['tempdir']+"/")
		acecmd = makeMatlabCmd("ctfparams = ace(",");",plist)
	else:
		plist = (imgname, imgpath, params['outtextfile'], params['opimagedir'], \
			params['matdir'], params['display'], params['stig'],\
			params['medium'], -nominal, params['tempdir']+"/", params['resamplefr'])
		acecmd = makeMatlabCmd("ctfparams = measureAstigmatism(",");",plist)

	#print acecmd
	pymat.eval(matlab,acecmd)

	matfile = os.path.join(params['matdir'], imgname+".mrc.mat")
	if params['stig']==0:
		savematcmd = "save('"+matfile+"','ctfparams','scopeparams', 'dforig');"
		pymat.eval(matlab,savematcmd)

	ctfvalue = pymat.get(matlab, 'ctfparams')
	ctfvalue=ctfvalue[0]

	printResults(params, nominal, ctfvalue)

	return ctfvalue


#=====================
def runAceDrift(matlab,imgdict,params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')

	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=imgdict['scope']['defocus']

	#pdb.set_trace()
	acecommand=("measureAnisotropy('%s','%s',%d,'%s',%e,'%s','%s','%s', '%s');" % \
		( imgpath, params['outtextfile'], params['display'],\
		params['medium'], -nominal, params['tempdir']+"/", params['opimagedir'], params['matdir'], imgname))

	#~ acecommand=("mnUpCut = measureDrift('%s','%s',%d,%d,'%s',%e,'%s');" % \
		#~ ( imgpath, params['outtextfile'], params['display'], params['stig'],\
		#~ params['medium'], -nominal, params['tempdir']))

	pymat.eval(matlab,acecommand)

#=====================
def runAceCorrect(imgdict,params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')

	voltage = (imgdict['scope']['high tension'])
	apix    = apDatabase.getPixelSize(imgdict)

	ctfvalues = ctfdb.getBestCtfByResolution(imgdata)
	conf = ctfdb.calculateConfidenceScore(bestctfvalue)

	ctdimname = imgname
	ctdimpath = os.path.join(params['rundir'],ctdimname)
	print "Corrected Image written to " + ctdimpath

	#pdb.set_trace()
	acecorrectcommand=("ctfcorrect1('%s', '%s', '%.32f', '%.32f', '%f', '%f', '%f');" % \
		(imgpath, ctdimpath, ctfvalues['defocus1'], ctfvalues['defocus2'], -ctfvalues['angle_astigmatism'], voltage, apix))
	print acecorrectcommand
	try:
		matlab = pymat.open("matlab -nosplash")
	except:
		apDisplay.environmentError()
		raise
	pymat.eval(matlab, acecorrectcommand)
	pymat.close(matlab)

	return

#=====================
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

#=====================
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
		pymat.eval(matlab, acecmd)
	else:
		apDisplay.printError("Temp directory, '"+tempdir+"' not present.")
	return

#=====================
def checkMatlabPath(params=None):
	'''
	Return immediately if MATLABPATH environment variable is already set.
	Searches for ace.m and adds its directory to matlab path.
	'''
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
		#TRY sibling dir of this script
		libdir = os.path.dirname(__file__)
		libdir = os.path.abspath(libdir)
		appiondir = os.path.dirname(libdir)
		acedir = os.path.join(appiondir, 'ace')
		if os.path.isdir(acedir) and os.path.isfile(os.path.join(acedir,"ace.m")):
			updateMatlabPath(acedir)
			return
		apDisplay.environmentError()
		raise RuntimeError('Could not find ace.m.  Check MATLABPATH environment variable.')

#=====================
def updateMatlabPath(matlabpath):
	data1 = os.environ.copy()
	data1['MATLABPATH'] =  matlabpath
	os.environ.update(data1)
	#os.environ.get('MATLABPATH')
	return

#=====================
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

#=====================
def runMatlabScript(matlabscript,xvfb=True):
	waited = False
	t0 = time.time()
	if xvfb:
		cmd = "xvfb-run matlab -nodesktop < %s;" % (matlabscript)
	else:
		cmd = 'matlab -nodesktop -nosplash -nodisplay -r "run %s;exit"' % (matlabscript)
	matlabproc = subprocess.Popen(cmd, shell=True)
	out, err = matlabproc.communicate()
	### continuous check
	waittime = 2.0
	while matlabproc.poll() is None:
		if waittime > 10:
			waited = True
			sys.stderr.write(".")
			waittime *= 1.1
			time.sleep(waittime)
	
	tdiff = time.time() - t0
	if tdiff > 20:
		apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
	elif waited is True:
		print ""
	proc_code = matlabproc.returncode
	if proc_code != 0:
		apDisplay.printWarning("Matlab failed with subprocess error code %d" % proc_code)
		
