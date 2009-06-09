#Part of the new pyappion

#pythonlib
import math
import time
import shutil
import os
import re
import string
#numpy
import pyami.quietscipy
import numpy
from scipy import ndimage
from numpy import linalg
from numpy import ma
#appion
import apDisplay
import appionData
import apAlignment
import apParam
import apEMAN
import spyder
#pyami
from pyami import mrc
from pyami import imagefun
from pyami import convolver
from random import choice

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

	if resize is True:
		emancmd = "proc3d %s %s scale=%f clip=%d,%d,%d" % (initmodel, outfile, scale, outbox, outbox, outbox)
		if spider is True:
			emancmd+=" spidersingle"
		apEMAN.executeEmanCmd(emancmd,verbose=True)
	else:
		if spider is True:
			emancmd = "proc3d %s %s spidersingle" % (initmodel,outfile)
		else:
			shutil.copy(initmodel,outfile)

#================
def getModelDimensions(mrcfile):
	print "calculating dimensions..."
	vol=mrc.read(mrcfile)
	(x,y,z)=vol.shape
	if x!=y!=z:
		apDisplay.printError("starting model is not a cube")
	return x

#================
def getModelFromId(modelid):
	return appionData.ApInitialModelData.direct_query(modelid)

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




