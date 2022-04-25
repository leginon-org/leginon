
## python
import os
import time
import numpy
import subprocess
import math
## appion
from appionlib import spyder
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apFile
from pyami import spider

"""
A large collection of SPIDER functions for 2D WHOLE IMAGE FILTERS purposes only

I try to keep the trend
image file:
	*****img.spi
image stack file:
	*****stack.spi
doc/keep/reject file:
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is
"""

#===============================
def phaseFlipImage(img,cs,df,hightension,imgsize,apix):
	"""
	computes the phase contrast transfer function,
	then multiplies it by the fourier transform of an image,
	then does a reverse FFT
	"""

	imgname,ext = os.path.splitext(img)
	if ext != ".spi":
		apDisplay.printError("Input file for SPIDER phaseflipping is not in spider format")

	# SPIDER can't handle really long file names,
	# so remove path portion of file
	inname = os.path.basename(imgname)
	tfname = os.path.basename(imgname)+"_tf"
	outname = os.path.basename(imgname)+"_out"

	# calculate wavelength of electron at approprate kv:
	h = 6.626068e-34 # planck's constant
	m = 9.10938188e-31 # mass of electron
	eV = 1.6e-19*hightension # ev in joules
	c = float(2.998e+8) # speed of light
	# calculate wavelength
	lam = h/math.sqrt(2*m*eV*(1+(eV/(2*m*c*c))))
	# convert to angstroms
	lam *= 10e9

	mySpider = spyder.SpiderSession(dataext='spi', logo=False, nproc=1)
	# set up TF CT command
	apDisplay.printMsg("calculating transfer function using 'TF CT'")
	mySpider.toSpiderQuiet("TF CT")
	mySpider.toSpiderQuiet(tfname)
	mySpider.toSpider("%.3f      ; cs"%cs)
	mySpider.toSpider("%i,%.8f ; defocus,lambda"%(df,lam))
	mySpider.toSpider("%i       ; img size"%imgsize)
	mySpider.toSpider("%.8f ; max sp.fr. 1/(2*%.5f)"%(1/(2*apix),apix))
	mySpider.toSpider("0.0047,100 ; src size, df spread")
	mySpider.toSpider("0.0,0.0    ; astig, azi")
	mySpider.toSpider("0.057,0.15 ; amp contr, gauss")
	mySpider.toSpider("-1         ; sign")
	mySpider.close()

	# apply the tranform
	mySpider = spyder.SpiderSession(dataext='spi', logo=False, nproc=1)
	mySpider.toSpiderQuiet("FT",inname+"@1","_1")
	mySpider.toSpiderQuiet("MU","_1",tfname,"_2","*")
	mySpider.toSpiderQuiet("FT","_2",outname)
	apDisplay.printMsg("applying transfer function to image")
	mySpider.close()

	if not os.path.exists(outname+".spi"):
		apDisplay.printError("corrected SPIDER image was not generated")

	return os.path.abspath(outname+".spi")

#===============================
def fermiLowPassFilter(imgarray, pixrad=2.0, dataext="spi", nproc=None):
	if dataext[0] == '.': dataext = dataext[1:]
	if nproc is None:
		nproc = apParam.getNumProcessors(msg=False)
	### save array to spider file
	spider.write(imgarray, "rawimg."+dataext)
	### run the filter
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, nproc=nproc)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpiderQuiet("FQ", "rawimg", "filtimg", "5", str(1.0/pixrad), "0.04")
	mySpider.close()
	### read array from spider file
	filtarray = spider.read("filtimg."+dataext)
	### clean up
	apFile.removeFile("rawimg."+dataext)
	apFile.removeFile("filtimg."+dataext)
	return filtarray

#===============================
def fermiHighPassFilter(imgarray, pixrad=200.0, dataext="spi", nproc=None):
	if dataext[0] == '.': dataext = dataext[1:]
	if nproc is None:
		nproc = apParam.getNumProcessors(msg=False)
	### save array to spider file
	spider.write(imgarray, "rawimg."+dataext)
	### run the filter
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, nproc=nproc)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpiderQuiet("FQ", "rawimg", "filtimg", "6", str(1.0/pixrad), "0.04")
	mySpider.close()
	### read array from spider file
	filtarray = spider.read("filtimg."+dataext)
	### clean up
	apFile.removeFile("temp001."+dataext)
	apFile.removeFile("filtimg."+dataext)
	return filtarray



