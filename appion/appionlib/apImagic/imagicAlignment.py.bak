import os
import re
import shutil
import sys
import stat
import time
import subprocess
import glob
from appionlib import apDisplay
from appionlib import apParam
from appionlib import pymagic
from appionlib import apImagicFile

#======================
def alirefs(infile, outfile=None, mask=0.99, maxshift=0.3, minrot=-180.0, maxrot=180.0, iter=5, minrad=0.0, maxrad=0.9):
	"""
	align a stack of references to each other
	"""

	fname = pymagic.fileFilter(infile)
	if outfile:
		outname = pymagic.fileFilter(outfile,exists=False)
	else:
		outname = fname+"_ali"

	myIm = pymagic.ImagicSession("align/alirefs.e")
	imagicv = myIm.version()
	myIm.toImagicQuiet("ALL") # translation & rotation
	if imagicv >= 101013:
		myIm.toImagicQuiet("ROTATION_FIRST")
	myIm.toImagicQuiet("CCF") # CCF or MCF
	myIm.toImagicQuiet("%s"%fname) # input
	myIm.toImagicQuiet("NO") # no contours on reference imgs
	myIm.toImagicQuiet("%.2f"%mask) # mask as fraction
	myIm.toImagicQuiet("%s"%outname) # output
	myIm.toImagicQuiet("-999.") # density for thresholding
	myIm.toImagicQuiet("%.2f"%maxshift) # max shift
	myIm.toImagicQuiet("%.2f,%.2f"%(minrot,maxrot)) # min max rot angle
	if imagicv >= 101013:
		myIm.toImagicQuiet("MEDIUM") # Precision for rotational alignment
		myIm.toImagicQuiet("%.2f,%.2f"%(minrad,maxrad)) # min, max radius for rot align
	myIm.toImagicQuiet("NO") # create mirrors
	myIm.toImagicQuiet("%i"%iter) # alignment iterations
	myIm.toImagicQuiet("NO") # full output of all parameters
	myIm.close()

	# check proper execution
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("alirefs.e did not execute properly")

	return outname


#======================
def alimass(infile, outfile=None, maxshift=0.2, ceniter=10, nproc=1):
	"""
	uses a rotationally averaged total sum to center particles
	default max shift is 20% of box size
	default # of centering iterations is 10
	"""
	fname = pymagic.fileFilter(infile)
	if outfile:
		outname = pymagic.fileFilter(outname)
	else:
		outname = fname+"_cen"

	if nproc > 1:
		myIm = pymagic.ImagicSession("align/alimass.e_mpi",nproc)
		myIm.toImagicQuiet("YES")
		myIm.toImagicQuiet(nproc)
	else:
		myIm = pymagic.ImagicSession("align/alimass.e")
		myIm.toImagicQuiet("NO")
	myIm.toImagicQuiet(fname)
	myIm.toImagicQuiet(outname)
	myIm.toImagicQuiet("TOTSUM")
	myIm.toImagicQuiet("CCF")
	myIm.toImagicQuiet("%.3f"%maxshift)
	myIm.toImagicQuiet("%i"%ceniter)
	myIm.toImagicQuiet("NO_FILTER")
	myIm.close()

	### check that it ran correctly
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("alimass.e did not execute properly")
		return None

	return outname


#======================
def mralign(alistack, origstack, refs, outfile=None, mask=0.8, imask=0, nproc=1):
	"""
	perform a multi-reference alignment
	"""

	aliname = pymagic.fileFilter(alistack)
	stackname = pymagic.fileFilter(origstack)
	refname = pymagic.fileFilter(refs)
	if outfile:
		outname = pymagic.fileFilter(outfile)
	else:
		outname = "mrastack"

	if nproc > 1:
		myIm = pymagic.ImagicSession("align/mralign.e_mpi",nproc)
		myIm.toImagicQuiet("YES")
		myIm.toImagicQuiet(nproc)
	else:
		myIm = pymagic.ImagicSession("align/mralign.e")
		myIm.toImagicQuiet("NO")

	## get imagic version
	imagicv = myIm.version()

	## rest of the params
	myIm.toImagicQuiet("FRESH")
	myIm.toImagicQuiet("ALL")
	# 091120 or higher version 4D options:
	if imagicv >= 91120:
		myIm.toImagicQuiet("ALIGNMENT")
		myIm.toImagicQuiet("ALL")
	myIm.toImagicQuiet("ROTATION_FIRST")
	myIm.toImagicQuiet("CCF")
	myIm.toImagicQuiet(aliname)
	myIm.toImagicQuiet(outname)
	myIm.toImagicQuiet(stackname)
	myIm.toImagicQuiet(refname)
	myIm.toImagicQuiet("NO_FILTER")
	# lower than 091120 version of imagic asks for mirrors:
	if imagicv < 91120:
		myIm.toImagicQuiet("NO")
	myIm.toImagicQuiet("0.31")
	# check if there are any rotations stored in the header
	equivRots = apImagicFile.readIndexFromHeader(aliname, 116)
	hasRots = False
	for value in equivRots:
		if value != 0:
			hasRots = True
			break

	# don't ask Max shift (during this alignment) for first iteration:
	if hasRots is True:
		myIm.toImagicQuiet("0.2")
	myIm.toImagicQuiet("-180,180")
	# don't ask rotation (during this alignment) for first iteration:
	if hasRots is True:
		myIm.toImagicQuiet("-180,180")
	myIm.toImagicQuiet("MEDIUM")
	myIm.toImagicQuiet("%.2f,%.2f"%(imask,mask))
	myIm.toImagicQuiet("2")
	myIm.toImagicQuiet("NO")
	myIm.close()

	### check that it ran correctly
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("mralign.e did not execute properly")
		return None

	return outname

#======================
def headersToFile(infile,outfile=None):
	"""
	writes out shift values to a file
	"""

	fname = pymagic.fileFilter(infile)
	if not outfile:
		outfile = "outparams.plt"

	myIm = pymagic.ImagicSession("stand/headers.e")
	if myIm.version() < 91120:
		myIm.toImagicQuiet(fname)
		myIm.toImagicQuiet("PLT")
		myIm.toImagicQuiet("SHIFT")
		myIm.toImagicQuiet(outfile)
		myIm.toImagicQuiet("*")
	else:
		myIm.toImagicQuiet("PLT")
		myIm.toImagicQuiet("SHIFT")
		myIm.toImagicQuiet(fname)
		myIm.toImagicQuiet(outfile)
	myIm.close()

	### check that it ran correctly
	if not os.path.exists(outfile):
		apDisplay.printError("headers.e did not execute properly")
		return None

	return outfile

