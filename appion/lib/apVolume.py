#Part of the new pyappion

#pythonlib
import math
import time
#numpy
import numpy
from scipy import ndimage
from numpy import linalg
from numpy import ma
#appion
import os
import re
import string
import apDisplay
import appionData
import apAlignment
import apEMAN
import apDB
#pyami
from pyami import mrc
from pyami import imagefun
from pyami import convolver
from whrandom import choice

appiondb = apDB.apdb

def getModelDimensions(mrcfile):
	print "calculating dimensions..."
	vol=mrc.read(mrcfile)
	(x,y,z)=vol.shape
	if x!=y!=z:
		apDisplay.printError("starting model is not a cube")
	return x

def getModelFromId(modelid):
	return appiondb.direct_query(appionData.ApInitialModelData, modelid)
	
def rescaleModel(infile,outfile,inapix,outapix,newbox=None):
	# scale an existing model - provide an input model & output (strings)
	# an input a/pix & output a/pix (floats)
	# and the final box size (after scaling)
	# currently uses EMAN's proc3d to do this
	origbox=getModelDimensions(infile)
	if newbox is None:
		newbox=origbox
	scalefactor = float(inapix/outapix)
	print "rescaling",infile,"with boxsize:",origbox
	print "by a factor of",scalefactor
	print "saving to",outfile,"with a boxsize:",newbox
	emancmd = "proc3d %s %s " % (infile, outfile)
	emancmd += "scale=%s " % scalefactor
	emancmd += "clip=%i,%i,%i edgenorm" % (newbox, newbox, newbox)
	apEMAN.executeEmanCmd(emancmd, verbose=True)

def MRCtoSPI(infile,outdir):
	# convert file to spider file
	tmpspifile = randomfilename(8)+".spi"
	tmpspifile=os.path.join(outdir,tmpspifile)
	emancmd = "proc3d %s %s spidersingle" %(infile,tmpspifile)
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	return tmpspifile

def createAmpcorBatchFile(infile,params):
	scriptfile = os.path.join(params['appiondir'],"lib/enhance.bat")
	if not os.path.isfile(scriptfile):
		apDisplay.printError("could not find spider script: "+scriptfile)
	inf = open(scriptfile, "r")

	tmpfile="out"+randomfilename(8)+".spi"
	tmpfile=os.path.join(params['outdir'],tmpfile)
	
	outfile = "enhance_edit.bat"
	if os.path.isfile(outfile):
		apDisplay.printWarning(outfile+" already exists; removing it")
		time.sleep(2)
		os.remove(outfile)
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
				outf.write(apAlignment.spiderline("vol",infile,"input density file"))
			elif re.search("^\[outvol\]",line):
				outf.write(apAlignment.spiderline("outvol",tmpfile,"enhanced output file"))
			elif re.search("^\[scatter\]",line):
				outf.write(apAlignment.spiderline("scatter",params['ampfile'],"amplitude curve file"))
			elif re.search("^\[pwsc\]",line):
				outf.write(apAlignment.spiderline("pwsc",os.path.join(params['appiondir'],"lib/pwsc"),"scaling script"))
			elif re.search("^\[applyfen\]",line):
				outf.write(apAlignment.spiderline("applyfen",os.path.join(params['appiondir'],"lib/applyfen"),"scaling script"))
			else:
				outf.write(line)
	return tmpfile

def runAmpcor():
	spidercmd = "spider bat/spi @enhance_edit"
	starttime = time.time()
	apAlignment.executeSpiderCmd(spidercmd)
	apDisplay.printColor("finished spider in "+apDisplay.timeString(time.time()-starttime),"cyan")
	
def randomfilename(num):
	# return a string of random letters and numbers of 'num' length
	f=''
	chars = string.letters + string.digits
	for i in range(num):
		f+=choice(chars)
	return f
