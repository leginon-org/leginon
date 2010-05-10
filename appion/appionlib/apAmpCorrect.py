
#pythonlib
import os
import re
import sys
import time
import shutil
#appion
from appionlib import apFile
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apVolume
from appionlib import spyder
#pyami
from pyami import mrc

"""
Functions involved in amplitude correction
"""

####
# This is a low-level file with NO database connections
# Please keep it this way
####

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
	### this option always failed for me -neil
	#if mass is not None:
	#	cmd += " -molweight %d"%(mass*1000)
	cmd += " %s"%(infile)
	cmd += " %s"%(outfile)
	apParam.runCmd(cmd, package="B-factor", verbose=True, showcmd=True)

	if not apVolume.isValidVolume(outfile):
		apDisplay.printWarning("B-factor correction failed %s"%(embfactorfile))
		return infile

	return outfile

#================
def runAmpcor():
	spidercmd = "spider bat/spi @enhance_edit"
	apParam.runCmd(spidercmd, package="SPIDER", verbose=False, showcmd=True)
	apFile.removeFile('pwsc.bat')
	apFile.removeFile('enhance_edit.bat')
	return

#=====================
def spiderline(var, value, comment=None):
	"""
	do not use this function, use appionlib.apSpider.operations
	"""
	# check if var is a numeric type
	if type(var) == type(1):
		line = "x"+str(var)+"="+str(value)+" "
		while len(line) < 11:
			line += " "
		line += "; "+comment+"\n"
	else:
		line = "["+var+"]"+value+"\n"
	sys.stderr.write(line)
	return line

#================
def createAmpcorBatchFile(infile,params):
	localinfile = spyder.fileFilter(infile)

	appiondir = apParam.getAppionDirectory()
	scriptfile = os.path.join(appiondir, "appionlib/enhance.bat")
	pwscfile = os.path.join(appiondir, "appionlib/pwsc.bat")
	if not os.path.isfile(scriptfile):
		apDisplay.printError("could not find spider script: "+scriptfile)
	if not os.path.isfile(pwscfile):
		apDisplay.printError("could not find spider script: "+pwscfile)
	inf = open(scriptfile, "r")

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
				outf.write(spiderline(99,params['box'],"box size in pixels"))
			elif thr == "x98":
				outf.write(spiderline(98,params['maxfilt'],"filter limit in angstroms"))
			elif thr == "x80":
				outf.write(spiderline(80,params['apix'],"pixel size"))
			elif re.search("^\[vol\]",line):
				outf.write(spiderline("vol",localinfile,"input density file"))
			elif re.search("^\[outvol\]",line):
				outf.write(spiderline("outvol",localtmpfile,"enhanced output file"))
			elif re.search("^\[scatter\]",line):
				outf.write(spiderline("scatter",params['ampfile'],"amplitude curve file"))
			elif re.search("^\[pwsc\]",line):
				outf.write(spiderline("pwsc","pwsc","scaling script"))
			elif re.search("^\[applyfen\]",line):
				outf.write(spiderline("applyfen",os.path.join(appiondir,"lib/applyfen"),"apply curve to data script"))
			else:
				outf.write(line)
	return tmpfile

####
# This is a low-level file with NO database connections
# Please keep it this way
####


