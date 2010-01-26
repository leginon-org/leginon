#Part of the new pyappion

#pythonlib
import math
import time
import shutil
import os
import re
import string
import subprocess
#numpy
import pyami.quietscipy
import numpy
from scipy import ndimage
from numpy import linalg
from numpy import ma
#appion
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apAlignment
from appionlib import apParam
from appionlib import apEMAN
from appionlib import spyder
from appionlib import apSymmetry
from appionlib import apFile
#pyami
from pyami import mrc
from pyami import imagefun
from pyami import convolver
from random import choice

#===========
def applyBfactor(infile, fscfile, apix, mass=None, outfile=None):
	embfactorfile = "embfactor64.exe"
	embfactorexe = apParam.getExecPath("embfactor64.exe")
	if embfactorexe is None:
		apDisplay.printWarning("Could not find %s"%(embfactorfile))
		return infile
	if outfile is None:
		outfile = os.path.splitext(infile)[0]+"-bfactor.mrc"
	cmd = embfactorexe
	cmd += " -FSC %s"%(fscfile)
	cmd += " -sampling %.3f"%(apix)
	#if mass is not None:
	#	cmd += " -molweight %d"%(mass*1000)
	cmd += " %s"%(infile)
	cmd += " %s"%(outfile)
	apDisplay.printColor(cmd, 'blue') 
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()

	if not os.path.isfile(outfile):
		apDisplay.printWarning("B-factor correction failed %s"%(embfactorfile))
		return infile
	if not isValidVolume(outfile):
		apDisplay.printWarning("B-factor correction failed %s"%(embfactorfile))
		return infile

	return outfile

#===========================
def insert3dDensity(params):
	apDisplay.printMsg("committing density to database")
	symdata=apSymmetry.findSymmetry(params['sym'])
	if not symdata:
		apDisplay.printError("no symmetry associated with this id\n")
	params['syminfo'] = symdata
	modq=appiondata.Ap3dDensityData()
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	modq['session'] = sessiondata
	modq['path'] = appiondata.ApPathData(path=os.path.abspath(params['rundir']))
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
	if params['reconiterid'] is not None:
		iterdata = appiondata.ApRefinementData.direct_query(params['reconiterid'])
		if not iterdata:
			apDisplay.printError("this iteration was not found in the database\n")
		modq['iterid'] = iterdata
	if params['reconid'] is not None:
		iterdata = appiondata.ApRefinementData.direct_query(params['reconid'])
		if not iterdata:
			apDisplay.printError("this iteration was not found in the database\n")
		modq['iterid'] = iterdata
	### if ampfile specified
	if params['ampfile'] is not None:
		(ampdir, ampname) = os.path.split(params['ampfile'])
		modq['ampPath'] = appiondata.ApPathData(path=os.path.abspath(ampdir))
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

#================
def rescaleVolume(modelId, outfile, outbox, outpix, spider=False):
	# get initial model path
	modeldata = getModelFromId(modelId)
	initmodel=os.path.join(modeldata['path']['path'],modeldata['name'])

	# check Box Size
	resize = False
	if (modeldata['boxsize'] != outbox):
		resize=True
	# check Pixel size
	scale = modeldata['pixelsize']/outpix
	if round(scale,2) != 1.:
		resize=True
	_rescaleVolume(initmodel, outfile, scale, (outbox,outbox,outbox), resize, spider)

def _rescaleVolume(infile, outfile, scale, outboxtuple, resize=False, spider=False):
	if resize is True:
		emancmd = "proc3d %s %s scale=%f clip=%d,%d,%d" % (infile, outfile, scale, outboxtuple[0], outboxtuple[1], outboxtuple[2])
		if spider is True:
			emancmd+=" spidersingle"
		apEMAN.executeEmanCmd(emancmd,verbose=True)
	else:
		if spider is True:
			emancmd = "proc3d %s %s spidersingle" % (infile,outfile)
			apEMAN.executeEmanCmd(emancmd,verbose=True)
		else:
			shutil.copy(infile,outfile)

#================
def getModelDimensions(mrcfile):
	print "calculating dimensions..."
	vol=mrc.read(mrcfile)
	(x,y,z)=vol.shape
	if x!=y!=z:
		apDisplay.printWarning("starting model is not a cube")
		return max(x,y,z)
	return x

#================
def getModelFromId(modelid):
	return appiondata.ApInitialModelData.direct_query(modelid)

#================
def rescaleModel(infile, outfile, inapix, outapix, newbox=None):
	# scale an existing model - provide an input model & output (strings)
	# an input a/pix & output a/pix (floats)
	# and the final box size (after scaling)
	# currently uses EMAN's proc3d to do this
	origbox=getModelDimensions(infile)
	if newbox is None:
		newbox = origbox
	scalefactor = float(inapix/outapix)
	apDisplay.printMsg( ("rescaling %s with boxsize %d by a factor of %.3f\n"
		+"\tand saving to %s with a boxsize %d")
		%(infile, origbox, scalefactor, outfile, newbox))
	emancmd = "proc3d %s %s " % (infile, outfile)
	if abs(scalefactor-1.0) > 0.2:
		emancmd += "scale=%.3f " % scalefactor
#	emancmd += "clip=%i,%i,%i norm=0,1" % (newbox, newbox, newbox)
	emancmd += "clip=%i,%i,%i edgenorm" % (newbox, newbox, newbox)
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	return

#================
def rescaleModelId(modelid, outfile, newapix, newbox=None):
	"""
	take an existing model id and rescale it
	"""
	modeldata = getModelFromId(modelid)
	modelapix = modeldata['pixelsize']
	modelfile = os.path.join(modeldata['path']['path'], modeldata['name'])
	rescaleModel(modelfile, outfile, modelapix, newapix, newbox)
	return

#================
def MRCtoSPI(infile,rundir):
	# convert file to spider file
	tmpspifile = randomfilename(8)+".spi"
	tmpspifile=os.path.join(rundir,tmpspifile)
	emancmd = "proc3d %s %s spidersingle" %(infile,tmpspifile)
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	return tmpspifile

#================
def createAmpcorBatchFile(infile,params):
	localinfile = spyder.fileFilter(infile)

	appiondir = apParam.getAppionDirectory()
	scriptfile = os.path.join(appiondir, "lib/enhance.bat")
	pwscfile = os.path.join(appiondir, "lib/pwsc.bat")
	if not os.path.isfile(scriptfile):
		apDisplay.printError("could not find spider script: "+scriptfile)
	if not os.path.isfile(pwscfile):
		apDisplay.printError("could not find spider script: "+pwscfile)
	inf = open(scriptfile, "r")

#	tmpfile = "out"+randomfilename(8)+".spi" ### this does not always work, and creates filenames with special characters that cannot be read
	tmpfile = "out_"+os.path.basename(infile)
	tmpfile = os.path.join(params['rundir'], tmpfile)
	localtmpfile = spyder.fileFilter(tmpfile)

	outfile = "enhance_edit.bat"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
	if os.path.isfile('pwsc.bat'):
		apDisplay.printWarning(pwscfile+" already exists; replacing it")
		time.sleep(2)
	shutil.copyfile(pwscfile, 'pwsc.bat')
	outf = open(outfile, "w")

	notdone = True
	for line in inf:
		if notdone is False:
			outf.write(line)
		else:
			thr = line[:3]
			if thr == "x99":
				outf.write(apAlignment.spiderline(99,params['box'],"box size in pixels"))
			elif thr == "x98":
				outf.write(apAlignment.spiderline(98,params['maxfilt'],"filter limit in angstroms"))
			elif thr == "x80":
				outf.write(apAlignment.spiderline(80,params['apix'],"pixel size"))
			elif re.search("^\[vol\]",line):
				outf.write(apAlignment.spiderline("vol",localinfile,"input density file"))
			elif re.search("^\[outvol\]",line):
				outf.write(apAlignment.spiderline("outvol",localtmpfile,"enhanced output file"))
			elif re.search("^\[scatter\]",line):
				outf.write(apAlignment.spiderline("scatter",params['ampfile'],"amplitude curve file"))
			elif re.search("^\[pwsc\]",line):
				outf.write(apAlignment.spiderline("pwsc","pwsc","scaling script"))
			elif re.search("^\[applyfen\]",line):
				outf.write(apAlignment.spiderline("applyfen",os.path.join(appiondir,"lib/applyfen"),"apply curve to data script"))
			else:
				outf.write(line)
	return tmpfile

#================
def runAmpcor():
	spidercmd = "spider bat/spi @enhance_edit"
	starttime = time.time()
	apAlignment.executeSpiderCmd(spidercmd)
	if os.path.isfile('pwsc.bat'):
		os.remove('pwsc.bat')
	if os.path.isfile('enhance_edit.bat'):
		os.remove('enhance_edit.bat')
	apDisplay.printColor("finished spider in "+apDisplay.timeString(time.time()-starttime),"cyan")
	return

#================
def randomfilename(num):
	# return a string of random letters and numbers of 'num' length
	f=''
	chars = string.letters + string.digits
	for i in range(num):
		f+=choice(chars)
	return f


#================
def isValidVolume(volfile):
	"""
	Checks to see if a MRC volume is valid
	"""
	if not os.path.isfile(volfile):
		return False
	volarray = mrc.read(volfile)
	if volarray.std() < 1e-6:
		apDisplay.printWarning("Volume has zero standard deviation")
		return False
	return True





