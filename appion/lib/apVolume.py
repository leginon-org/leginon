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
import apDisplay
import appionData
import apAlignment
import apEMAN
import apDB
#pyami
from pyami import mrc
from pyami import imagefun
from pyami import convolver

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
