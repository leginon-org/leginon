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
import apCtf
try:
	import pymat
except:
	apDisplay.matlabError()

appiondb = apDB.apdb

def runAce(matlab, imgdict, params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')

	nominal = None
	if params['nominal'] is not None:
		nominal=params['nominal']
	elif params['newnominal'] is True:
		nominal = apCtf.getBestDefocusForImage(imgdict)
	if nominal is None:
		nominal = imgdict['scope']['defocus']

	if nominal is None or nominal > 0 or nominal < -15e-6:
			apDisplay.printWarning("Nominal should be of the form nominal=-1.2e-6"+\
				" for -1.2 microns NOT:"+str(nominal))

	#Neil's Hack
	#resamplefr_override = round(2.0*(math.sqrt(abs(nominal*1.0e6)+1.0)-1.0),3)
	#print "resamplefr_override=",resamplefr_override
	#pymat.eval(matlab, "resamplefr="+str(resamplefr_override)+";")

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

	pymat.eval(matlab,acecmd)

	matfile = os.path.join(params['matdir'], imgname+".mrc.mat")
	if params['stig']==0:
		savematcmd = "save('"+matfile+"','ctfparams','scopeparams', 'dforig');"
		pymat.eval(matlab,savematcmd)

	ctfvalue = pymat.get(matlab, 'ctfparams')
	apCtf.printResults(params, nominal, ctfvalue)

	return ctfvalue


def runAceDrift(matlab,imgdict,params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')
	
	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=imgdict['scope']['defocus']
	
	expid=int(imgdict['session'].dbid)

	#pdb.set_trace()
	acecommand=("measureAnisotropy('%s','%s',%d,'%s',%e,'%s','%s','%s', '%s');" % \
		( imgpath, params['outtextfile'], params['display'],\
		params['medium'], -nominal, params['tempdir']+"/", params['opimagedir'], params['matdir'], imgname))
		
	#~ acecommand=("mnUpCut = measureDrift('%s','%s',%d,%d,'%s',%e,'%s');" % \
		#~ ( imgpath, params['outtextfile'], params['display'], params['stig'],\
		#~ params['medium'], -nominal, params['tempdir']))
		
	pymat.eval(matlab,acecommand)

def runAceCorrect(matlab,imgdict,params):
	imgname = imgdict['filename']
	imgpath = os.path.join(imgdict['session']['image path'], imgname+'.mrc')
	
	matname=imgname+'.mrc.mat'
	matfile=os.path.join(params['matdir'],matname)
	print "Ctf params obtained from " + matfile
	
	ctdimname = imgname+'.mrc.ctf_ph'
	ctdimpath = os.path.join(params['correctedimdir'],ctdimname)

	acecorrectcommand=("ctfcorrect('%s','%s','%s','%s','%s', '%s');" % (imgpath,\
		matfile, params['tempdir']+"/", ctdimpath, params['ctdIntmdImDir'], imgname))

	pymat.eval(matlab,acecorrectcommand)

	return


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
