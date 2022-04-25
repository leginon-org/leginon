#!/usr/bin/env python

import math
import numpy
import os
import sys
from appionlib import apParam
from appionlib import apTomo
from appionlib import apImod
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apProTomo

try:
	noProtomo2 = False
	import protomo
except ImportError:
	noProtomo2 = True


'''
This currently works with the protomo tutorial dataset only. See issue #1026 for more info.
'''


class ApProTomo2:
	
	def __init__(self, sessiondata, seriesname, params, ordered_imagelist, refimg, center, corr_bin, processingDir, tilts):
		
		# Make sure Protomo2 is installed and the processing directory is valid
		if noProtomo2:
			apDisplay.printError("Protomo2 is not installed. Installation instructions are at http://....")
		if not os.path.isdir( processingDir ):
			apDisplay.printError("Protomo2 processing directory (%s) is not valid." % (processingDir, ))
			

		self.ordered_imagelist = ordered_imagelist
		self.processingDir     = processingDir
		self.sessiondata       = sessiondata
		self.seriesname        = seriesname
		self.params            = params
		self.refimg            = refimg
		self.center            = center
		self.corr_bin          = corr_bin
		self.tilts             = tilts
		
		# TODO: remove this when protomo is automatically creating a correctionFactors file name
		self.correctionFactorFile = "/ami/data17/appion/10nov10z/rawdata/tiltseries1/align/align1/out/correctionFactors.dat"
		
		
	#=====================
	def run(self):
		
		# use the tilt angles to set the reference image, which is the image with tilt values closest to zero.
		self.setRefImg(self.tilts)
		apDisplay.printMsg("Setting Reference image to: %d" % (self.refimg, ))
		
		
		# Write a default parameter file if it does not already exist
		self.params['protomo2paramfile'] = self.writeDefaultParamFile()
		apDisplay.printMsg("Setting Parameter file to: %s" % (self.params['protomo2paramfile'], ))
		
		# Create the parameter object
		try:
			protomo2param = protomo.param( self.params['protomo2paramfile'] )
		except Exception:
			msg = "The protomo2 config file (%s) has an error. Could not create the parameter object." % (self.params['protomo2paramfile'], )
			apDisplay.printWarning(msg)
			raise
				
		
		# Write a default tilt geometry file if it does not already exist 
		geomParamFilePath = self.writeTiltGeomFile()
		apDisplay.printMsg("Setting tilt geometry file to: %s" % (geomParamFilePath, ))
		
		# Create the protomo2 geometry object
		try:
			protomo2geom = protomo.geom( geomParamFilePath )
		except:
			apDisplay.printWarning("Failed to create the protomo2 geometry object with the geometry parameter file, %s" % (geomParamFilePath, ))
			raise
			

		# Modify the parameter object with the user input values
		self.setUserModifiedParams( protomo2param )
		

		# Create a tilt series object (contains input geometry, creates updated geometry, info to do the alignment)
		try:
			protomo2series = protomo.series(protomo2param, protomo2geom)
		except:
			apDisplay.printWarning("Failed to create the protomo2 tilt series object.")
			raise
		

		# Run the specified number of alignment iterations
		for i in range(0, self.params['max_iterations']):
			protomo2series.align()
			# correction factors, automatically generates a file name using the iteration number(? TODO: Hanspeter to implement)
			protomo2series.corr() #( self.correctionFactorFile )
			protomo2series.fit()
			protomo2series.update()
			

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
					
		# TODO: is there an error if we don't find a value between +-.1?
					
	
	#=====================
	def setUserModifiedParams(self, protomo2param):
		
		# Build and create the output and cache directories 
		cacheDir = os.path.join(self.processingDir,'cache/')
		outputDir = os.path.join(self.processingDir,'out/')
		
		if not os.path.isdir(cacheDir):
			try:
				os.makedirs(cacheDir)
				apDisplay.printMsg("Creating Protomo2 cache directory:" + cacheDir )
			except:
				apDisplay.printWarning("Could not create the cache directory for Protomo2:," + cacheDir )
				raise
		
		if not os.path.isdir(outputDir):
			try:
				os.makedirs(outputDir)
				apDisplay.printMsg("Creating Protomo2 output directory:" + outputDir )
			except:
				apDisplay.printWarning("Could not create the output directory for Protomo2:," + outputDir )
				raise
			
		# Check the input image directory
		inputImagePath = self.sessiondata['image path']			
		if not os.path.isdir( inputImagePath ):
			apDisplay.printError("Protomo2 input image path (%s) is not valid." % (inputImagePath, ))
		apDisplay.printMsg("Protomo2 input image directory:" + inputImagePath )

		# Set the parameters of the protomo2param object
		# note that boolean strings "true" and "false" should not be set with surrounding quotes as other string params are
		try:
			# hardcode the image path in the config file until Protomo2 can handle image names that start with a number
			#protomo2param.set("pathlist", '"%s"' % (inputImagePath,) )
			#protomo2param.set("outdir", outputDir)
			#protomo2param.set("cachedir", cacheDir)
			
			if self.params['sample'] is not None:
				protomo2param.set("sampling", " %g " % (self.params['sample'], ))
			
			if self.params['do_binning'] is not None:
				protomo2param.set("binning", '%s' % (self.params['do_binning'],) )
			
			if self.params['do_preprocessing'] is not None:
				protomo2param.set("preprocessing", '%s' % (self.params['do_preprocessing'],) )
			
			### Preprocess parameters ###
			if self.params['border'] is not None:
				protomo2param.set("preprocess.border", " %d " % (self.params['border'], ))
			
			if self.params['clip_low'] is not None and self.params['clip_high'] is not None:
				protomo2param.set("preprocess.clip", "{ %g %g } " % (self.params['clip_low'], self.params['clip_high']))
	
			### Window parameters ### 
			if self.params['windowsize_x'] is not None and self.params['windowsize_y'] is not None:
				protomo2param.set("window.size", "{ %d %d }" % (self.params['windowsize_x'], self.params['windowsize_y']))
			
			if self.params['reference_apodization_x'] is not None and self.params['reference_apodization_y'] is not None:
				protomo2param.set("window.mask.apodization", "{ %g %g } " % (self.params['reference_apodization_x'], self.params['reference_apodization_y']))
			
			if self.params['lowpass_diameter_x'] is not None and self.params['lowpass_diameter_y'] is not None:
				protomo2param.set("window.lowpass.diameter", "{ %g %g }" % (self.params['lowpass_diameter_x'], self.params['lowpass_diameter_y']))
			
			if self.params['highpass_diameter_x'] is not None and self.params['highpass_diameter_y'] is not None:
				protomo2param.set("window.highpass.diameter", "{ %g %g }" % (self.params['highpass_diameter_x'], self.params['highpass_diameter_y']))
	
			### Reference parameters ###
			if self.params['backprojection_bodysize'] is not None:
				protomo2param.set("reference.body", " %g " % (self.params['backprojection_bodysize'], ))
		
			### Align parameters ###
			if self.params['do_estimation'] is not None:
				protomo2param.set("align.estimate", '%s' % (self.params['do_estimation'],) )
	
			if self.params['max_correction'] is not None:
				protomo2param.set("align.maxcorrection", " %g " % (self.params['max_correction'], ))
	
			if self.params['image_apodization_x'] is not None and self.params['image_apodization_y'] is not None:
				protomo2param.set("align.mask.apodization", "{ %g %g } " % (self.params['image_apodization_x'], self.params['image_apodization_y']))
			
			if self.params['correlation_mode'] is not None:
				protomo2param.set("align.correlation.mode", '"%s"' % (self.params['correlation_mode'],) )
			
			if self.params['correlation_size_x'] is not None and self.params['correlation_size_y'] is not None:
				protomo2param.set("correlation.size", "{ %d %d }" % (self.params['correlation_size_x'], self.params['correlation_size_y']))
			
			if self.params['peak_search_radius_x'] is not None and self.params['peak_search_radius_y'] is not None:
				protomo2param.set("peaksearch.radius", "{ %g %g } " % (self.params['peak_search_radius_x'], self.params['peak_search_radius_y']))
	
			### Map parameters ###
			if self.params['map_size_x'] is not None and self.params['map_size_y'] is not None and self.params['map_size_z'] is not None:
				protomo2param.set("map.size", "{ %d %d %d }" % (self.params['map_size_x'], self.params['map_size_y'], self.params['map_size_z']))
				
			if self.params['backprojection_bodysize'] is not None:
				protomo2param.set("map.body", " %g " % (self.params['backprojection_bodysize'], ))
	
			if self.params['map_lowpass_diameter_x'] is not None and self.params['map_lowpass_diameter_y'] is not None:
				protomo2param.set("map.lowpass.diameter", "{ %g %g }" % (self.params['map_lowpass_diameter_x'], self.params['map_lowpass_diameter_y']))
		
		except protomo.error as inst:
			# TODO: figure out how to pass the exception instance to apDisplay.printError, maintaining the Traceback
			apDisplay.printWarning("%s. Could not set the protomo2 parameter values. The supplied values may not be correct. " % (inst, ))
			raise
		except:
			apDisplay.printWarning("Unexpected error: %s %s " % ( sys.exc_info()[0], sys.exc_info()[1]) )
			raise




	#=====================
	def commitResultsToDB(self):
		
		return
	
		# -- Commit Parameters --
		protomodata = apProTomo.insertProtomoParams(self.seriesname)
		alignrun = apTomo.insertTomoAlignmentRun(self.sessiondata, None, None, protomodata, None, 1, self.params['runname'],self.params['rundir'],self.params['description'])
		cycle_description = self.params['description']

		# create refinement parameter dictionary
		refinedict = apProTomo.createRefineDefaults(0, '', '', tmp='')
		refinedict['alismp'] = self.params['sample']
		refinedict['alibox_x'] = self.params['windowsize_x']
		refinedict['alibox_y'] = self.params['windowsize_y']
		refinedict['cormod'] = self.params['correlation_mode']
		refinedict['imgref'] = self.params['refimg']
		
		alignerdata = apProTomo.insertAlignIteration(alignrun, protomodata, self.params, refinedict, self.ordered_imagelist[self.refimg])
		
		# -- Commit Results --
		# Parse the results file which holds rotation and Correction Factors 
		correctionFactors = self.parseCorrectionFactors( self.correctionFactorFile )
				
		# commit the geometry parameters (psi, theta, phi, azimuth), not sure about this.
		if correctionFactors is not None:
			self.insertModel(alignerdata, correctionFactors)
		
		# insert results into ApProtomoAlignmentData for each image
		for i,imagedata in enumerate(self.ordered_imagelist):
			try:
				apProTomo.insertTiltAlignment(alignerdata,imagedata,i,correctionFactors[i],self.center)
			except:
				if i is not self.refimg :
					apDisplay.printWarning("Unable to update ApProtomoAlignmentData database table for image: %d" % i )
					# TODO: raise exception once the refimg is figured out correctly

		self.params['description'] = cycle_description


	#=====================
	# TODO: Where do we get this info from? DO we need it?
	def insertModel(self, alignerdata, results):
		# general protmo parameters
		q = appiondata.ApProtomoModelData()
		q['aligner'] = alignerdata
		q['psi'] = results[-2]['psi']
		q['theta'] = results[-2]['theta']
		q['phi'] = results[-2]['phi']
		q['azimuth'] = results[-2]['azimuth']
		modeldata = apTomo.publish(q)
		
		return modeldata

	
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
	def writeTiltGeomFile(self):
		'''
		Create the geometry object (tilt angles, dir of tilt axis, origins of ROI) ---
		1. read the params from the database 
		2. write params to text file
		'''
		
		# Try to open the tilt geometry file. If it fails (first time through), write out a default parameter file.
		geomParamFile = "/home/amber/max.tlt"
		# TODO: remove this when the rest of this function is working
		return geomParamFile;
		
		geomParamFile = "/home/amber/maxTEST.tlt"
		print "geomParamFile:"
		print geomParamFile

		# TODO: numextension is not being found
		#geomParamFile = os.path.join(self.processingDir,'protomo2.tlt') #"/home/amber/max.tlt"

		try:
			tiltGeometry = open(geomParamFile,'r')
		except:
			apDisplay.printWarning("Failed to open %s for reading the protomo2 tilt geometry parameter file. Reading Geometry from the Leginon database." % (geomParamFile, ))
			try:
				tiltGeometry = open(geomParamFile,'w')
			except:
				apDisplay.printWarning("Failed to create %s for writing the protomo2 tilt geometry parameter file" % (geomParamFile, ))
				raise

			# magic to get the tilt geometry 
			tltParams = self.getTiltGeom()		
			
			# this builds the tilt geometry file as a string
			tiltText = self.buildTiltGeomFile(tltParams[0], tltParams[1])

			# using print instead of .write so that message is converted to a string if needed 
			print >> tiltGeometry, tiltText

		# Close the tilt geometry file
		tiltGeometry.close()

		return geomParamFile;


	#=====================
	def getTiltGeom(self):
		# get the tilt geometry parameters
		self.params['aligndir'],self.params['imagedir'] =	apProTomo.setProtomoDir(self.params['rundir'])

		# self.params['imagedir'] when not testing with renamed images
		rawimagenames = apProTomo.linkImageFiles(self.ordered_imagelist, "/ami/data17/leginon/10nov10z/rawdatatest")
		shifts = apTomo.getGlobalShift(self.ordered_imagelist, self.corr_bin, self.refimg)

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
	def buildParamFile(self):
		
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

		