
## python
import time
import os
import subprocess
import cPickle
import sys
import math
from string import lowercase
import random
## PIL
#import Image
## spider
import spyder
## appion
import apImage
import apEMAN
import apParam
import apDisplay
import apFile

"""
A large collection of SPIDER functions

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

neil
"""

#===============================
def reconstructRct(stackfile, eulerdocfile, volfile, numpart, pixrad, dataext=".spi"):
	"""
	inputs:
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### setup
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	if dataext in eulerdocfile:
		eulerdocfile = eulerdocfile[:-4]
	if dataext in volfile:
		volfile = volfile[:-4]
	t0 = time.time()
	rundir = "volumes"
	apParam.createDirectory(rundir)

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("BP CG", 
		stackfile+"@*****", #stack file
		"1-%d"%(numpart), #number of particles
		str(pixrad), #particle radius
		eulerdocfile, #angle doc file
		"N", #has symmetry?, does not work
		volfile, #filename for volume
 		"%.1e,%.1f" % (1.0e-5, 0.0), #error, chi^2 limits
 		"%d,%d" % (25,1), #iterations, 1st derivative mode
 		"2000", #lambda - higher=less sensitive to noise
	)
	mySpider.close()
	return



