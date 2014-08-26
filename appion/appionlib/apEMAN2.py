import os
import re
import sys
import time
import math
import random
import subprocess
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apImagicFile

try:
	import EMAN2
except:
	apDisplay.printError("EMAN2 not found")

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#=====================
def stackToHDF(infile,outfile,apix,pinfo=None):
	"""
	convert stack to an hdf stack
	pinfo contains CTF information from apFrealign.getPerParticleCTF
	pinfo may also contain helical information
	"""
	from utilities import generate_ctf

	a = EMAN2.EMData()
	imn = EMAN2.EMUtil.get_image_count(infile)

	if pinfo is not None:
		if len(pinfo) != imn:
			apDisplay.printError("insufficient particle info for stack")

	# output must end with hdf
	outf,ext = os.path.splitext(outfile)
	if ext != '.hdf':
		outstack = outf+".hdf"

	apDisplay.printMsg("Generating '%s' with %i particles"%(outstack,imn))

	for i in xrange(imn):
		a.read_image(infile,i)
		a.set_attr_dict({'active':1})
		t2 = EMAN2.Transform({"type":"spider","phi":0,"theta":0,"psi":0})
		a.set_attr("xform.projection", t2)
		a.set_attr("apix_x",apix)

		if pinfo is not None:
			pdata = pinfo[i+1]
			df1 = pdata['df1']
			df2 = pdata['df2']
			astig = pdata['angastig']
			kv = pdata['kev']
			cs = pdata['cs']
			ampc = pdata['ampc']*100

			# save CTF dict (bfactor is hard coded to 0.0)
			df=(float(df1)+float(df2))/2
			ctfgen = generate_ctf([df,cs,kv,apix,0.0,ampc])
			a.set_attr("ctf",ctfgen)

			# if helical info is present
			if pdata['hnum'] is not None:
				a.set_attr("h_angle",pdata['hangle'])
		a.write_image(outstack,i)

	return outstack

#=====================
def stackHDFToIMAGIC(hdfFile, imagicFile=None):
	"""
	convert HDF stack back into an IMAGIC stack
	"""
	numPart = EMAN2.EMUtil.get_image_count(hdfFile)
	
	# output must end with hdf
	root, ext = os.path.splitext(hdfFile)	
	if imagicFile is None or ext != ".hed":
		imagicFile = root+".hed"
	apFile.removeFile(imagicFile)
	apFile.removeFile(root+".img")
	apDisplay.printMsg("Creating IMAGIC file '%s' with %d particles"%(imagicFile,numPart))

	headerOnly = False
	for i in range(numPart):
		imgData = EMAN2.EMData.read_images(hdfFile, [i], headerOnly)[0]
		imgData.write_image(imagicFile, i)

	return imagicFile
