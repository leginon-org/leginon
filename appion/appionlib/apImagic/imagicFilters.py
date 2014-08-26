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

#======================
def takeoverHeaders(filename, numpart, boxsize):
	### better workaround than copyFile ... still a workaround though

	fname = pymagic.fileFilter(filename)
	
	## output temporary file to same directory as original file
	outpath = os.path.split(fname)[0]
	outfile = os.path.join(outpath,"tempimg")
	myIm = pymagic.ImagicSession("stand/testim.e")
	myIm.toImagicQuiet("%s,1,%d" % (outfile,numpart))
	myIm.toImagicQuiet("%d,%d" % (boxsize, boxsize))
	myIm.toImagicQuiet("REAL")
	myIm.toImagicQuiet("BLOBS")
	myIm.close()
	
	if not os.path.exists(outfile+".hed"):
		apDisplay.printError("header rewrite failed")
	apDisplay.printMsg("replacing '%s' with '%s'"%(fname+".hed",outfile+".hed"))
	shutil.move(outfile+".hed", fname+".hed")
	os.remove(outfile+".img")


#======================
def convertFilteringParameters(hpfilt, lpfilt, apix):
	### CONVERT FILTERING PARAMETERS TO IMAGIC FORMAT BETWEEN 0-1
	if lpfilt is not "" and apix is not "":
		lpfilt_imagic = 2 * float(apix) / int(lpfilt)
	else:
		lpfilt_imagic = 1
	if float(lpfilt_imagic) > 1 or float(lpfilt_imagic) < 0:
		lpfilt_imagic = 1	# imagic cannot perform job when lowpass > 1

	if hpfilt is not "" and apix is not "":
		hpfilt_imagic = 2 * float(apix) / int(hpfilt)
	else:
		hpfilt_imagic = 0.01
	if float(hpfilt_imagic) > 1 or float(hpfilt_imagic) < 0:
		hpfilt_imagic = 0.01

	return hpfilt_imagic, lpfilt_imagic


#======================
def softMask(infile, outfile=None, mask=0.8, falloff=0.1):
	"""
	applies a soft mask to images in a stack
	"""
	fname = pymagic.fileFilter(infile)
	if outfile:
		outname = pymagic.fileFilter(outname)
	else:
		outname = fname+"_mask"

	## output temporary file to same directory as original file
	outfile = fname+"_mask"
	myIm = pymagic.ImagicSession("stand/arithm.e")
	myIm.toImagicQuiet("%s"%fname) # input
	myIm.toImagicQuiet("%s"%outname) # output
	myIm.toImagicQuiet("SOFT") # soft mask
	myIm.toImagicQuiet("%.2f"%mask) # mask as a fraction
	myIm.toImagicQuiet("%.2f"%falloff) # falloff as a fraction
	myIm.close()

	### check that it ran correctly
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("arithm.e did not execute properly")
		return None

	return outname


#======================
def mask2D(boxsz, mask, infile=False, maskfile="mask2Dimgfile"):
	"""
	creates a 2d circular mask
	if infile is specified, mask is applied to stack & then mask is deleted
	boxsz is the box size in pixels
	mask is the size of the mask to apply as a fraction
	"""

	### generate a 2D mask
#	f=open(batchfile,"w")
#	f.write("#!/bin/csh -f\n")
#	f.write("setenv IMAGIC_BATCH 1\n")
	apDisplay.printMsg("creating 2D mask")
	myIm = pymagic.ImagicSession("stand/testim.e")
	myIm.toImagicQuiet("%s"%maskfile)
	myIm.toImagicQuiet("%i,%i"%(boxsz,boxsz))
	myIm.toImagicQuiet("real")
	myIm.toImagicQuiet("disc")
	myIm.toImagicQuiet("%.3f"%mask)
	myIm.close()

	if not infile:
		# check proper execution
		if not os.path.exists(maskfile+".hed"):
			apDisplay.printError("mask generation did not execute properly")
		return maskfile

	### if infile is specified, apply mask to images
	fname = pymagic.fileFilter(infile)
	file_ma=fname+"_ma"

	apDisplay.printMsg("applying 2D mask")
	myIm = pymagic.ImagicSession("stand/twoimag.e")
	myIm.toImagicQuiet("mul")
	myIm.toImagicQuiet("%s"%fname)
	myIm.toImagicQuiet("%s"%maskfile)
	myIm.toImagicQuiet("%s"%file_ma)
	myIm.close()

	# check proper execution
	if not os.path.exists(file_ma+".hed"):
		apDisplay.printError("masking did not execute properly")

	return file_ma


#======================
def normalize(infile, outfile=None, sigma=10.0, path=os.path.abspath('.'), keepfiles=False):
	"""
	normalize images in a stack
	"""

	fname = pymagic.fileFilter(infile)
	if outfile:
		outname = pymagic.fileFilter(outfile)
	else:
		outname=fname+"_norm"

	myIm = pymagic.ImagicSession("stand/pretreat.e")
	imagicv = myIm.version()
	myIm.toImagicQuiet(fname) # input
	myIm.toImagicQuiet(outname) # output
	myIm.toImagicQuiet("NORM_VARIANCE") # mode
	myIm.toImagicQuiet("WHOLE") # mask to be used
	myIm.toImagicQuiet("%.2f"%sigma) # desired sigma
	myIm.toImagicQuiet("NO") # remove dust outliers
	if imagicv >= 110119:
		myIm.toImagicQuiet("NO")
	myIm.close()

	# check proper execution
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("normalization did not execute properly")

	return outname

