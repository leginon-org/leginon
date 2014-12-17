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
from appionlib import apDatabase

		
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
		

#=======================
def prepareTiltFile(sessionname, seriesname, tiltfilename, tiltseriesnumber, raw_path, link, coarse=True):
	'''
	Creates tlt file from basic image information and copies raw images
	'''
	
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
	tiltdata = apTomo.getImageList([tiltseriesdata])
	apDisplay.printMsg("getting imagelist")

	tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(tiltdata)
	#tilts are tilt angles, ordered_imagelist are imagedata, ordered_mrc_files are paths to files, refimg is an int
	maxtilt = max([abs(tilts[0]),abs(tilts[-1])])
	apDisplay.printMsg("highest tilt angle is %f" % maxtilt)
	
	if coarse == "True":
		azimuth = apTomo.getAverageAzimuthFromSeries(ordered_imagelist)
		
		rawexists = apParam.createDirectory(raw_path)
		
		if link == "True":
			apDisplay.printMsg("linking raw images")
		else:
			apDisplay.printMsg("copying raw images")
		newfilenames = apProTomo.getImageFiles(ordered_imagelist, raw_path, link)
	
		###create tilt file
		#get image size from the first image
		imagesizex = tiltdata[0]['image'].shape[1]
		imagesizey = tiltdata[0]['image'].shape[0]
		
		#shift half tilt series relative to eachother
		#SS I'm arbitrarily making the bin parameter here 1 because it's not necessary to sample at this point
		shifts = apTomo.getGlobalShift(ordered_imagelist, 1, refimg)
		
		#OPTION: refinement might be more robust by doing one round of IMOD aligment to prealign images before doing protomo refine
		origins = convertShiftsToOrigin(shifts, imagesizex, imagesizey)
	
		#determine azimuth
		azimuth = apTomo.getAverageAzimuthFromSeries(ordered_imagelist)
		writeTiltFile2(tiltfilename, seriesname, newfilenames, origins, tilts, azimuth, refimg)
	
	return maxtilt


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
def writeTiltFile2(tiltfile, seriesname, imagelist, origins, tilts, azimuth, refimg):
	
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
	paramdict = { 'AP_windowsize_x':params['r1_region_x'],
                'AP_windowsize_y':params['r1_region_y'],
		'APc_windowsize_x':params['region_x'],
                'APc_windowsize_y':params['region_y'],
                'AP_sampling': params['r1_sampling'],
		'APc_sampling': params['sampling'],
		'AP_map_sampling': params['map_sampling'],
		'AP_thickness': params['thickness'],
		'AP_cos_alpha': params['cos_alpha'],
		'AP_lp_diam_x': params['r1_lowpass_diameter_x'],
		'AP_lp_diam_y': params['r1_lowpass_diameter_y'],
		'AP_lp_apod_x': params['r1_lowpass_apod_x'],
                'AP_lp_apod_y': params['r1_lowpass_apod_y'],
		'AP_hp_diam_x': params['r1_highpass_diameter_x'],
		'AP_hp_diam_y': params['r1_highpass_diameter_y'],
		'AP_hp_apod_x': params['r1_highpass_apod_x'],
		'AP_hp_apod_y': params['r1_highpass_apod_y'],
		'APc_lp_diam_x': params['lowpass_diameter_x'],
		'APc_lp_diam_y': params['lowpass_diameter_y'],
		'APc_lp_apod_x': params['lowpass_apod_x'],
                'APc_lp_apod_y': params['lowpass_apod_y'],
		'APc_hp_diam_x': params['highpass_diameter_x'],
		'APc_hp_diam_y': params['highpass_diameter_y'],
		'APc_hp_apod_x': params['highpass_apod_x'],
		'APc_hp_apod_y': params['highpass_apod_y'],
		'AP_corr_mode': params['corr_mode'],
		'AP_raw_path': params['raw_path'],
		'AP_binning': params['binning'],
		'AP_preprocessing': params['preprocessing'],
		'AP_select_images': params['select_images'],
		'AP_exclude_images': params['exclude_images'],
		'AP_border': params['border'],
		'AP_clip_low': params['clip_low'],
		'AP_clip_high': params['clip_high'],
		'AP_thr_low': params['thr_low'],
		'AP_thr_high': params['thr_high'],
		'AP_gradient': params['gradient'],
		'AP_iter_gradient': params['iter_gradient'],
		'AP_filter': params['filter'],
		'AP_kernel_x': params['r1_kernel_x'],
		'AP_kernel_y': params['r1_kernel_y'],
		'APc_kernel_x': params['kernel_x'],
		'APc_kernel_y': params['kernel_y'],
		'AP_grow': params['grow'],
		'AP_window_area': params['window_area'],
		'AP_mask_apod_x': params['r1_mask_apod_x'],
		'AP_mask_apod_y': params['r1_mask_apod_y'],
		'AP_mask_width_x': params['r1_mask_width_x'],
		'AP_mask_width_y': params['r1_mask_width_y'],
		'APc_mask_apod_x': params['mask_apod_x'],
		'APc_mask_apod_y': params['mask_apod_y'],
		'APc_mask_width_x': params['mask_width_x'],
		'APc_mask_width_y': params['mask_width_y'],
		'AP_do_estimation': params['do_estimation'],
		'AP_max_correction': params['max_correction'],
		'AP_correlation_size_x': params['correlation_size_x'],
		'AP_correlation_size_y': params['correlation_size_y'],
		'AP_peak_search_radius_x': params['r1_peak_search_radius_x'],
		'AP_peak_search_radius_y': params['r1_peak_search_radius_y'],
		'APc_peak_search_radius_x': params['peak_search_radius_x'],
		'APc_peak_search_radius_y': params['peak_search_radius_y'],
		'AP_orientation': params['orientation'],
		'AP_azimuth': params['azimuth'],
		'AP_elevation': params['elevation'],
		'AP_rotation': params['rotation'],
		'AP_scale': params['scale'],
		'AP_norotations': params['norotations'],
		'AP_logging': params['logging'],
		'AP_loglevel': params['loglevel'],
		'AP_map_size_x': params['map_size_x'],
		'AP_map_size_y': params['map_size_y'],
		'AP_map_size_z': params['map_size_z'],
		'AP_filename_prefix': params['filename_prefix'],
		'AP_image_extension': params['image_file_type'],
		'AP_cachedir': params['cachedir'],
		'AP_protomo_outdir': params['protomo_outdir'],
		'AP_grid_limit': params['gridsearch_limit'],
		'AP_grid_step': params['gridsearch_step'] }
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
	#appiondir=apParam.getAppionDirectory()
	appiondir='/panfs/storage.local/imb/home/ajn10d/myami/appion'
	origparamfile=os.path.join(appiondir,'appionlib','data','protomo.param')
	coarse_origparamfile=os.path.join(appiondir,'appionlib','data','protomo_coarse_align.param')
	return coarse_origparamfile, origparamfile
		
		
