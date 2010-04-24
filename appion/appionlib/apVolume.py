#pythonlib
import os
import re
import time
import random
import shutil
import string
import subprocess
#numpy
import numpy
#appion
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apParam
from appionlib import apDisplay
#pyami
from pyami import mrc

"""
Functions to manipulate volumes
"""

####
# This is a low-level file with NO database connections
# Please keep it this way
####


#================
def getModelDimensions(mrcfile):
	print "calculating dimensions..."
	vol=mrc.read(mrcfile)
	(x,y,z)=vol.shape
	if x!=y!=z:
		apDisplay.printWarning("starting model is not a cube")
		return max(x,y,z)
	return x

#=====================
def getPDBDimensions(pdbfile):
	"""
	Measure the size of the particle and determine a boxsize
	"""
	f = open(pdbfile, "r")
	limits = numpy.array([100,100,100,-100,-100,-100], dtype=numpy.float32)
	count = 0
	for line in f:
		### only look at atom lines
		if line.startswith("ATOM  ") or line.startswith("HETATM"):
			count += 1
			x = float(line[30:38])
			y = float(line[38:46])
			z = float(line[46:54])
			## x limits
			if x < limits[0]:
				limits[0] = x
			elif x > limits[3]:
				limits[3] = x
			## y limits
			if y < limits[1]:
				limits[1] = y
			elif y > limits[4]:
				limits[4] = y
			## z limits
			if z < limits[2]:
				limits[2] = z
			elif z > limits[5]:
				limits[5] = z
	f.close()
	if count == 0:
		apDisplay.printError("No atoms were found in PDB file")
	apDisplay.printMsg("Found %d atoms in PDB file"%(count))
	apDisplay.printMsg("x limits: %.2f - %.2f = %.2f"%(limits[3],limits[0],limits[3]-limits[0]))
	apDisplay.printMsg("y limits: %.2f - %.2f = %.2f"%(limits[4],limits[1],limits[4]-limits[1]))
	apDisplay.printMsg("z limits: %.2f - %.2f = %.2f"%(limits[5],limits[2],limits[5]-limits[2]))
	limitsize = max(limits[3]-limits[0], limits[4]-limits[1], limits[5]-limits[2])
	return limitsize

#================
def MRCtoSPI(infile, rundir):
	# convert file to spider file
	tmpspifile = apParam.randomString(8)+".spi"
	tmpspifile = os.path.join(rundir,tmpspifile)
	emancmd = "proc3d %s %s spidersingle" %(infile,tmpspifile)
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	return tmpspifile

#================
def isValidVolume(volfile):
	"""
	Checks to see if a MRC volume is valid
	"""
	if not os.path.isfile(volfile):
		return False
	volarray = mrc.read(volfile)
	if abs(volarray.min() - volarray.max()) < 1e-6:
		apDisplay.printWarning("Volume has zero standard deviation")
		return False
	return True

#================
def rescaleVolume(infile, outfile, inapix, outapix=None, newbox=None, spider=False):
	"""
	scale an existing model - provide an input model & output (strings)
	an input a/pix & output a/pix (floats)
	and the final box size (after scaling)
	currently uses EMAN's proc3d to do this
	"""

	origbox = getModelDimensions(infile)
	if newbox is None:
		newbox = origbox

	if outapix is None:
		outapix = inapix

	apDisplay.printMsg( ("rescaling %s with boxsize %d by a factor of %.3f\n"
		+"\tand saving to %s with a boxsize %d")
		%(infile, origbox, scalefactor, outfile, newbox))

	emancmd = "proc3d %s %s " % (infile, outfile)

	scalefactor = float(inapix/outapix)
	# only do it if it is bigger than 10%
	if abs(scalefactor-1.0) > 0.1:
		emancmd += "scale=%.3f " % scalefactor

	emancmd += "clip=%i,%i,%i norm=0,1 " % (newbox, newbox, newbox)
	apEMAN.executeEmanCmd(emancmd, verbose=True)

	if spider is True:
		emancmd += "spidersingle "
	return

#================
def viper2eman(infile, outfile, apix=None):
	"""
	apix is requested so it puts it into the MRC file
	sometimes yflip is needed, but I am worried this mirrors the structure
	"""
	### rotate 90 degrees about z
	rotatecmd = "proc3d %s rotated.mrc rot=0,0,90"%(infile)
	apEMAN.executeEmanCmd(rotatecmd, verbose=True)

	### move 2fold facing z to 5fold facing z
	composecmd = "proc3d rotated.mrc composed.mrc icos2fTo5f"
	apEMAN.executeEmanCmd(composecmd, verbose=True)

	### set origin and apix
	finalcmd = "proc3d composed.mrc %s origin=0,0,0 "%(outfile)
	if apix is not None:
		finalcmd += "apix=%.3f "%(apix)
	apEMAN.executeEmanCmd(finalcmd, verbose=True)

	return outfile

#================
def eman2viper(infile, outfile, apix=None):
	"""
	apix is requested so it puts it into the MRC file
	"""
	### move 5fold facing z to 2fold facing z
	rotatecmd = "proc3d %s composed.mrc icos5fTo2f"%(infile)
	apEMAN.executeEmanCmd(rotatecmd, verbose=True)

	### rotate 90 degrees about z
	composecmd = "proc3d composed.mrc rotated.mrc rot=0,0,90"
	apEMAN.executeEmanCmd(composecmd, verbose=True)

	### set origin and apix
	finalcmd = "proc3d rotated.mrc %s origin=0,0,0 "%(outfile)
	if apix is not None:
		finalcmd += "apix=%.3f "%(apix)
	apEMAN.executeEmanCmd(finalcmd, verbose=True)

	return outfile

####
# This is a low-level file with NO database connections
# Please keep it this way
####


