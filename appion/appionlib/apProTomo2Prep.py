#!/usr/bin/env python

import math
import numpy
import os
import sys
import shutil
from appionlib import apParam
from appionlib import apTomo
from appionlib import apImod
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apProTomo


'''
This currently works with the protomo tutorial dataset only. See issue #1026 for more info.
'''


		
	#=====================
def setRefImg(self, tilts):
	# use the tilt geometry to set the reference image. Look for tilt angle closest to 0, may be off by .1 degree.	
	bestPosVal = 0.10
	bestNegVal = -0.10

	for tilt in tilts:
		if tilt <= bestPosVal and tilt > bestNegVal:
			self.refimg = tilts.index(tilt)
			if tilt >= 0:
				bestPosVal = tilt
			else:
				bestNegVal = tilt

#=====================
def parseCorrectionFactors(self, tiltfile):
	try:
		f=open(tiltfile)
		lines=f.readlines()
	except:
		apDisplay.printWarning("Failed to read the protomo2 Correction Factors file, %s" % (tiltfile, ))
	else:
		f.close()

		# Create a dictionary to store Correction Factor and rotation information for each image 
		imagedict = {}
		for n in lines:
			words = n.split()
			if len(words) is not 6:
				apDisplay.printError("The protomo2 correction factors file, %s, is not properly formatted." % (tiltfile, ))

			image_number = int(words[0])
			imagedict[image_number] = {}
			imagedict[image_number]['rotation'] = float(words[1])
			imagedict[image_number]['x'] = float(words[2])
			imagedict[image_number]['y'] = float(words[3])

		return imagedict


#=====================
def writeTiltFile(tiltfile, seriesname, imagedict, azimuth, refimg ):
	'''
	Create the geometry object (tilt angles, dir of tilt axis, origins of ROI) ---
	1. read the params from the database 
	2. write params to text file
	'''


	try:
		f = open(tiltfile,'w')
	except:
		apDisplay.printWarning("Failed to create %s for writing the protomo2 tilt geometry parameter file" % (tiltfile, ))
		raise

	f.write('\n')


	f.write ("TILT SERIES %s\n" % seriesname)
	f.write ("\n") 
	f.write ("   AXIS\n")
	f.write ("\n")
	f.write ("     TILT AZIMUTH    %g\n" % azimuth)
	f.write ("\n")

	keys = imagedict.keys()
	keys.sort()
	for n in keys:
		f.write ("   IMAGE %-5d     FILE %s       ORIGIN [ %8.3f %8.3f ]    TILT ANGLE    %8.3f    ROTATION     %8.3f\n" % (n, imagedict[n]['filename'], imagedict[n]['x'], imagedict[n]['y'], imagedict[n]['tilt'], imagedict[n]['rotation']))

	f.write ("\n")
	f.write ("   REFERENCE IMAGE %d\n" % refimg)
	f.write ("\n")
	f.write ("\n")
	f.write (" END\n")
	f.close()

#=====================
def getTiltGeom(ordered_imagelist, bin, refimg):
	# get the tilt geometry parameters
	#self.params['aligndir'],self.params['imagedir'] = apProTomo.setProtomoDir(self.params['rundir'])

	# self.params['imagedir'] when not testing with renamed images
	rawimagenames = apProTomo.linkImageFiles(ordered_imagelist, "/ami/data17/leginon/10nov10z/rawdatatest")
	shifts = apTomo.getGlobalShift(ordered_imagelist, corr_bin, refimg)

	tltparams = apProTomo.convertShiftsToParams(self.tilts, shifts, self.center, rawimagenames)
	return tltparams


	
#=====================
def buildTiltGeomFile(self, imagedict, parameterdict=False):

	tiltText = "TILT SERIES %s\n" % self.seriesname
	tiltText += "\n" 
	tiltText += "   AXIS\n"
	tiltText += "\n"
	tiltText += "     TILT AZIMUTH    %g\n" % parameterdict['azimuth']
	tiltText += "\n"

	# Loop through the images to format the tilt geometry for each one
	# TODO: check this...not sure if it is getting the right filenames
	keys = imagedict.keys()
	keys.sort()
	for n in keys:
		tiltText += "   IMAGE %-5d     FILE %s       ORIGIN [ %8.3f %8.3f ]    TILT ANGLE    %8.3f    ROTATION     %8.3f\n" % (n, imagedict[n]['filename'], imagedict[n]['x'], imagedict[n]['y'], imagedict[n]['tilt'], imagedict[n]['rotation'])

	tiltText += "\n"
	tiltText += "   REFERENCE IMAGE %d\n" % self.refimg
	tiltText += "\n"
	tiltText += "\n"
	tiltText += " END\n"

	return tiltText



#=====================
def writeDefaultParamFile(self):

	# Set the default protomo2 parameter file location if it is not provided by the user
	if self.params['protomo2paramfile'] is None:
		self.params['protomo2paramfile'] = os.path.join(self.processingDir,'protomo2.param')

	# Try to open the param file. If it fails (first time through), write out a default parameter file.
	try:
		protomo2params = open(self.params['protomo2paramfile'],'r')
	except:
		try:
			protomo2params = open(self.params['protomo2paramfile'],'w')
		except:
			apDisplay.printWarning("Failed to create %s for writing the default protomo2 parameter file" % (self.params['protomo2paramfile'], ))
			raise
		paramtext = self.buildParamFile()
		# using print instead of .write so that message is converted to a string if needed 
		print >> protomo2params, paramtext

	# Close the parameter file
	protomo2params.close()

	return self.params['protomo2paramfile']

#=====================
def getPrototypeParamFile(outparamfile):
	
	#TODO: expand on this later
	appiondir=apParam.getAppionDirectory()
	origparamfile=os.path.join(appiondir,'appionlib','data','protomo.param')
	newparamfile=os.path.join(os.getcwd(),outparamfile)
	shutil.copyfile(origparamfile,newparamfile)
	
#=====================
def buildParamFile(self):
	"""This function may disappear in the future and be replaced by 
	a prototypical param file that lives somewhere in myami"""
	paramtext =  '(* Parameters for MAX tilt series *)\n'
	paramtext +=  '\n'
	paramtext +=  '(* Units are pixels for real space quantities, or reciprocal pixels    *)\n'
	paramtext +=  '(* for reciprocal space quantities, unless otherwise stated. The units *)\n'
	paramtext +=  '(* refer to the sampled image. The spatial frequencies for filters are *)\n'
	paramtext +=  '(* multiplied by the sampling factor and thus refer to the unsampled,  *)\n'
	paramtext +=  '(* raw image.                                                          *)\n'
	paramtext +=  '\n'
	paramtext +=  '\n'
	paramtext +=  'tiltseries {\n'
	paramtext +=  '\n'
	paramtext +=  '  N = { 512, 512 }  (* window size at sampling S *)\n'
	paramtext +=  '\n'
	paramtext +=  '  T = 40            (* thickness at sampling S *)\n'
	paramtext +=  '\n'
	paramtext +=  '  S = 2             (* sampling *)\n'
	paramtext +=  '\n'
	paramtext +=  '  F = 0.4848        (* cos( highest tilt angle ) *)\n'
	paramtext +=  '\n'
	paramtext +=  '  sampling: S\n'
	paramtext +=  '\n'
	paramtext +=  '  binning: true\n'
	paramtext +=  '\n'
	paramtext +=  '  preprocessing: true\n'
	paramtext +=  '\n'
	paramtext +=  '  preprocess {\n'
	paramtext +=  '\n'
	paramtext +=  '    logging: false\n'
	paramtext +=  '\n'
	paramtext +=  '    border: 100\n'
	paramtext +=  '\n'
	paramtext +=  '    clip: { 3.5, 3.5 }   (* specified as a multiple of the standard deviation *)\n'
	paramtext +=  '\n'
	paramtext +=  '    mask {\n'
	paramtext +=  '      gradient: true\n'
	paramtext +=  '      iter: true\n'
	paramtext +=  '      filter: "median"\n'
	paramtext +=  '      kernel: { 5, 5 }\n'
	paramtext +=  '      clip: { 3.0, 3.0 }\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '  }\n'
	paramtext +=  '\n'
	paramtext +=  '  window {\n'
	paramtext +=  '\n'
	paramtext +=  '    size: N\n'
	paramtext +=  '\n'
	paramtext +=  '    mask {\n'
	paramtext +=  '      apodization: { 10, 10 }\n'
	paramtext +=  '      width: N - 2.5 * apodization\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '    lowpass {\n'
	paramtext +=  '      diameter:    { 0.40, 0.40 } * S\n'
	paramtext +=  '      apodization: { 0.01, 0.01 } * S\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '    highpass {\n'
	paramtext +=  '      diameter:    { 0.04, 0.04 } * S\n'
	paramtext +=  '      apodization: { 0.02, 0.02 } * S\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '  }\n'
	paramtext +=  '\n'
	paramtext +=  '\n'
	paramtext +=  '  reference {\n'
	paramtext +=  '\n'
	paramtext +=  '    body: T / F\n'
	paramtext +=  '\n'
	paramtext +=  '  }\n'
	paramtext +=  '\n'
	paramtext +=  '\n'
	paramtext +=  '  align {\n'
	paramtext +=  '\n'
	paramtext +=  '    estimate: true\n'
	paramtext +=  '\n'
	paramtext +=  '    maxcorrection: 0.04\n'
	paramtext +=  '\n'
	paramtext +=  '    mask {\n'
	paramtext +=  '      apodization: { 10, 10 }\n'
	paramtext +=  '      width: N - 2.5 * apodization\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '    correlation {\n'
	paramtext +=  '      mode: "mcf"\n'
	paramtext +=  '      size: { 128, 128 }\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '    peaksearch {\n'
	paramtext +=  '      radius: { 49, 49 }\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '  }\n'
	paramtext +=  '\n'
	paramtext +=  '\n'
	paramtext +=  '  fit {\n'
	paramtext +=  '\n'
	paramtext +=  '    orientation: true\n'
	paramtext +=  '    azimuth: true\n'
	paramtext +=  '    rotation: true\n'
	paramtext +=  '\n'
	paramtext +=  '    logging: true\n'
	paramtext +=  '\n'
	paramtext +=  '  }\n'
	paramtext +=  '\n'
	paramtext +=  '\n'
	paramtext +=  '  map {\n'
	paramtext +=  '\n'
	paramtext +=  '    size: { 256, 256, 128 }\n' 
	paramtext +=  '    body: T / F\n'
	paramtext +=  '\n'
	paramtext +=  '    lowpass {\n'
	paramtext +=  '      diameter:    { 0.50, 0.50 } * S\n'
	paramtext +=  '      apodization: { 0.02, 0.02 } * S\n'
	paramtext +=  '    }\n'
	paramtext +=  '\n'
	paramtext +=  '    logging: true\n'
	paramtext +=  '\n'
	paramtext +=  '  }\n'
	paramtext +=  '\n'
	paramtext +=  '  suffix: ".mrc"\n'
	paramtext +=  '\n'
	paramtext +=  '  pathlist: "/ami/data17/leginon/10nov10z/rawdatatest"\n'
	paramtext +=  '\n'
	paramtext +=  '  cachedir: "/ami/data17/appion/10nov10z/rawdata/tiltseries1/align/align1/cache/"\n'
	paramtext +=  '\n'
	paramtext +=  '  outdir: "/ami/data17/appion/10nov10z/rawdata/tiltseries1/align/align1/out/"\n'
	paramtext +=  '\n'
	paramtext +=  '  logging: true\n'
	paramtext +=  '\n'
	paramtext +=  '  restart: false\n'
	paramtext +=  '\n'
	paramtext +=  '}\n'

	return paramtext

		
