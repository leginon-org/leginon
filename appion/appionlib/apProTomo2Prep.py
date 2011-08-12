#!/usr/bin/env python

import math
import numpy
import os
import sys
import shutil
import re
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

#=======================
def convertShiftsToOrigin(shifts,imagesize_x, imagesize_y):
	newshift=[]
	origin_x=imagesize_x/2.0
	origin_y=imagesize_y/2.0
	for shift in shifts:
		newx=origin_x+shift['x']
		newy=origin_y+shift['y']
		newshift.append({'x':newx,'y':newy})
	return newshift
		

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

#====================
# This function duplicates the one above. Should migrate to this one in the future. 
def writeTileFile2(tiltfile, seriesname, imagelist, origins, tilts, azimuth, refimg):
	
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
	for n in range(len(imagelist)):
		imagename=os.path.splitext(os.path.basename(imagelist[n]))[0] #strip off path and extension from mrc file
		f.write ("   IMAGE %-5d     FILE %s       ORIGIN [ %8.3f %8.3f ]    TILT ANGLE    %8.3f    ROTATION     %8.3f\n" % (n+1, imagename, origins[n]['x'], origins[n]['y'], tilts[n], 0))

	f.write ("\n")
	f.write ("   REFERENCE IMAGE %d\n" % refimg)
	f.write ("\n")
	f.write ("\n")
	f.write (" END\n")
	f.close()

#=====================
def modifyParamFile(filein, fileout, paramdict):
	f = open(filein, 'r')
	filestring = f.read()
	f.close()
        
	for key, value in paramdict.iteritems():
		filestring = re.sub(key, str(value), filestring)
        
	f = open(fileout, 'w')
	f.write(filestring)
	f.close()
            
#=====================
def createParamDict(params):
	paramdict = { 'AP_windowsize_x':params['region_x'],
                'AP_windowsize_y':params['region_y'],
                'AP_sampling': params['sampling'],
		'AP_thickness': params['thickness'],
		'AP_cos_alpha': params['cos_alpha'],
		'AP_lp_diam_x': params['lowpass_diameter_x'],
		'AP_lp_diam_y': params['lowpass_diameter_y'],
		'AP_lp_apod_x': params['lowpass_apod_x'],
                'AP_lp_apod_y': params['lowpass_apod_y'],
		'AP_hp_diam_x': params['highpass_diameter_x'],
		'AP_hp_diam_y': params['highpass_diameter_y'],
		'AP_hp_apod_x': params['highpass_apod_x'],
		'AP_hp_apod_y': params['highpass_apod_y'], 
		'AP_corr_mode': params['corr_mode'],
		'AP_raw_path': params['raw_path'] }

	return paramdict				
	
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

def getPrototypeParamPath():
	appiondir=apParam.getAppionDirectory()
	origparamfile=os.path.join(appiondir,'appionlib','data','protomo.param')
	return origparamfile
		
		
