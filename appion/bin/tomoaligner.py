#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import shutil
import re
import subprocess
import math
#pyami
from pyami import mrc
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apTomo
from appionlib import apProTomo
# don't import protomo2 until we have moved to Python 2.6
#from appionlib import apProTomo2
from appionlib import apImod
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apStack
try:
	no_wx = False
	import wx
except ImportError:
	no_wx = True

#=====================
#=====================
class protomoAligner(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")

		### strings
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")

		### integers
		self.parser.add_option("--tiltseriesnumber", dest="tiltseriesnumber", type="int",
			help="tilt series number in the session", metavar="int")
		self.parser.add_option("--othertilt", dest="othertilt", type="int",
			help="2nd tilt group series number if needed", metavar="int")
		self.alignmethods = ( "imod-shift", "protomo", "protomo2", "leginon" )
		self.parser.add_option("--alignmethod", dest="alignmethod",
			help="aligning method, e.g. --alignmethod=protomo or imod-shift", metavar="Method",
			type="choice", choices=self.alignmethods, default="protomo" )
		self.parser.add_option("--goodaligner", dest="goodalignerid", type="int",
			help="Protomo only: Reset to Aligner Parameter Id. This will set tiltseries info automatically, e.g. --goodaligner=1", metavar="int")
		self.parser.add_option("--cycle", dest="cycle", default=1, type="int",
			help="Protomo only: Align cycle, e.g. --cycle=1", metavar="int")
		self.parser.add_option("--refimg", dest="refimg", type="int",
			help="Protomo only: custom reference image number, e.g. --refimg=20", metavar="int")
		self.parser.add_option("--sample", dest="sample", default=4.0, type="float",
			help="Protomo only: Align sample rate, e.g. --sample=2.0", metavar="float")
		self.parser.add_option("--region", dest="region", default=50, type="int",
			help="Protomo only: Percentage of image used in alignment, e.g. --region=80", metavar="int")
		self.parser.add_option("--goodcycle", dest="goodcycle", type="int",
			help="Protomo only: Reset to image origin to that of this align cycle, e.g. --goodcycle=1", metavar="int")
		self.parser.add_option("--goodstart", dest="goodstart",  type="int",
			help="Protomo only: Reset beginning image origin and rotation before this image number, e.g. --goodstart=1", metavar="int")
		self.parser.add_option("--goodend", dest="goodend",  type="int",
			help="Protomo only: Reset ending image origin and rotation after this image number, e.g. --goodend=50", metavar="int")

		# Read options related to protomo2
		self.parser.add_option("--windowsize_x", dest="windowsize_x",  type="int",
			help="Protomo2 only: Region of interest in the x dimension used for alignmnet (in pixels), e.g. --windowsize_x=1024", metavar="int")
		
		self.parser.add_option("--windowsize_y", dest="windowsize_y",  type="int",
			help="Protomo2 only: Region of interest in the y dimension used for alignmnet (in pixels), e.g. --windowsize_y=1024", metavar="int")
		
		self.parser.add_option("--lowpass_diameter_x", dest="lowpass_diameter_x",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_diameter_y", dest="lowpass_diameter_y",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--highpass_diameter_x", dest="highpass_diameter_x",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_diameter_y", dest="highpass_diameter_y",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--backprojection_bodysize", dest="backprojection_bodysize",  type="float",
			help="Protomo2 only: Back projection body size for the reconstruction (in pixels), e.g. --backprojection_bodysize=80.0", metavar="float")
		
		self.parser.add_option("--protomo2paramfile", dest="protomo2paramfile",
			help="Protomo2 only: Path and filename of the protomo2 parameter file, e.g. --protomo2paramfile=/path/to/max.param", metavar="FILE")

		self.parser.add_option("--max_iterations", dest="max_iterations",  type="int",
			help="Protomo2 only: Number of alignment and geometry refinement iterations, e.g. --max_iterations=4", metavar="int")

		self.parser.add_option("--do_binning", dest="do_binning",  default="true", action="store_true",
			help="Protomo2 only: Binning of raw data if sampling factor is greater or equal to 2, e.g. --binning")
		
		self.parser.add_option("--do_preprocessing", dest="do_preprocessing",  default="true", action="store_true",
			help="Protomo2 only: Remove density outliers from the images prior to processing, e.g. --do_preprocessing")
		
		self.parser.add_option("--border", dest="border",  type="int",
			help="Protomo2 only: Width of area at the image edge to exclude from image statistics, e.g. --border=100", metavar="int")
		
		self.parser.add_option("--clip_low", dest="clip_low",  type="float",
			help="Protomo2 only: Lower threshold specified as a multiple of the standard deviation, e.g. --clip_low=3.5", metavar="float")

		self.parser.add_option("--clip_high", dest="clip_high",  type="float",
			help="Protomo2 only: Upper threshold specified as a multiple of the standard deviation, e.g. --clip_high=3.5", metavar="float")

		self.parser.add_option("--do_estimation", dest="do_estimation",  default="true", action="store_true",
			help="Protomo2 only: Enables alignment parameter prediction, e.g. --do_estimation")

		self.parser.add_option("--max_correction", dest="max_correction",  type="float",
			help="Protomo2 only: TODO, e.g. --max_correction=0.04", metavar="float")

		self.parser.add_option("--image_apodization_x", dest="image_apodization_x",  type="float",
			help="Protomo2 only: TODO, e.g. --image_apodization_x=10.0", metavar="float")

		self.parser.add_option("--image_apodization_y", dest="image_apodization_y",  type="float",
			help="Protomo2 only: TODO, e.g. --image_apodization_y=10.0", metavar="float")

		self.parser.add_option("--reference_apodization_x", dest="reference_apodization_x",  type="float",
			help="Protomo2 only: TODO, e.g. --reference_apodization_x=10.0", metavar="float")

		self.parser.add_option("--reference_apodization_y", dest="reference_apodization_y",  type="float",
			help="Protomo2 only: TODO, e.g. --reference_apodization_y=10.0", metavar="float")

		self.correlation_modes = ( "xcf", "mcf", "pcf", "dbl" )
		self.parser.add_option("--correlation_mode", dest="correlation_mode",
			help="Protomo2 only: Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--correlation_size_x", dest="correlation_size_x",  type="int",
			help="Protomo2 only: X size of cross correlation peak image, e.g. --correlation_size_x=128", metavar="int")

		self.parser.add_option("--correlation_size_y", dest="correlation_size_y",  type="int",
			help="Protomo2 only: Y size of cross correlation peak image, e.g. --correlation_size_y=128", metavar="int")
		
		self.parser.add_option("--peak_search_radius_x", dest="peak_search_radius_x",  type="float",
			help="Protomo2 only: TODO, e.g. --peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--peak_search_radius_y", dest="peak_search_radius_y",  type="float",
			help="Protomo2 only: TODO, e.g. --peak_search_radius_y=19.0", metavar="float")

		self.parser.add_option("--map_size_x", dest="map_size_x",  type="int",
			help="Protomo2 only: Size of the reconstructed tomogram in the X direction, e.g. --map_size_x=256", metavar="int")

		self.parser.add_option("--map_size_y", dest="map_size_y",  type="int",
			help="Protomo2 only: Size of the reconstructed tomogram in the Y direction, e.g. --map_size_y=256", metavar="int")

		self.parser.add_option("--map_size_z", dest="map_size_z",  type="int",
			help="Protomo2 only: Size of the reconstructed tomogram in the Z direction, e.g. --map_size_z=128", metavar="int")
		
		self.parser.add_option("--map_lowpass_diameter_x", dest="map_lowpass_diameter_x",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --map_lowpass_diameter_x=0.5", metavar="float")
		
		self.parser.add_option("--map_lowpass_diameter_y", dest="map_lowpass_diameter_y",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --map_lowpass_diameter_y=0.5", metavar="float")
		
		return

	#=====================
	def checkConflicts(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		self.sessiondata = sessiondata
		if self.params['goodalignerid'] is None:
			if self.params['tiltseriesnumber'] is None :
				apDisplay.printError("There is no tilt series specified")
			if self.params['runname'] is None:
				apDisplay.printError("enter a run name")
			if self.params['description'] is None:
				apDisplay.printError("enter a description, e.g. --description='awesome data'")
			tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
			self.params['tiltseries'] = tiltdata
			if self.params['othertilt'] is not None:
				othertiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['othertilt'],sessiondata)
				self.params['othertiltseries'] = othertiltdata
			else:
				self.params['othertiltseries'] = None
			if self.params['alignmethod'] == 'leginon':
				self.params['cycle'] = 0
				self.params['region'] = 100
		else:
			self.createParamsFromGoodAligner(self.params['goodalignerid'])
			if self.params['goodcycle'] is None:
				if self.params['goodstart'] or self.params['goodend']:
						apDisplay.printError("Cannot specify reseting image range without knowing the cycle number to reset to")
			elif self.params['goodcycle'] >= self.params['cycle']:
				apDisplay.printError("Only older cycle can be used as the base to reset image origin to")

		# Sampling is needed for protomo1 and 2, not imod
		if self.params['sample'] is not None:
			if self.params['sample'] < 1:
				apDisplay.printError("Sampling factor (--sample) must be greater or equal to 1.")

	def setProcessingDirName(self):
		self.setTiltSeriesDir()
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.processdirname = "tomo/"+tiltseriespath+'/align'

	def onInit(self):
		pieces = self.params['rundir'].split('/')
		self.params['tiltseriesdir'] = '/'.join(pieces[:-2])

	def createParamsFromGoodAligner(self,alignerid):
		q = appiondata.ApTomoAlignerParamsData()
		alignerdata = q.direct_query(alignerid)
		self.params['goodcycle'] = alignerdata['refine_cycle']['cycle']
		alignrundata = alignerdata['alignrun']
		if self.params['runname'] is None:
			self.params['runname'] = alignrundata['name']
		else:
			if self.params['runname'] != alignrundata['name']:
				apDisplay.printError("Alignment run name can not be changed between cycles")
		if self.params['description'] is None:
				self.params['description'] = alignrundata['description']
		q = appiondata.ApTiltsInAlignRunData(alignrun=alignrundata)
		results = q.query()
		if results:
			if len(results) == 1:
				tiltdata = results[0]['tiltseries']
				self.params['tiltseries'] = tiltdata
				self.params['tiltseriesnumber'] = tiltdata['number']
				self.params['othertiltseries'] = None
			else:
				runpathdata = alignrundata['path']
				for tiltdata in results:
					pathdata = tiltdata['path']
					if pathdata.dbid == runpathdata.dbid:
						self.params['tiltseries'] = tiltdata
						self.params['tiltseriesnumber'] = tiltdata['number']
					else:
						self.params['othertiltseries'] = tiltdata
						self.params['othertilt'] = tiltdata['number']


	def setTiltSeriesDir(self):
		path = os.path.abspath(self.sessiondata['image path'])
		pieces = path.split('leginon')
		path = 'leginon'.join(pieces[:-1]) + 'appion' + pieces[-1]
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" %  self.params['tiltseriesnumber']
		self.params['tiltseriesdir'] = os.path.join(path,tiltseriespath)

	#=====================
	def runProjalign(self,paramfile):
		"""
		Uses Hans Peters' projalign
		takes individual MRC files not an MRC stack
		"""
	#	while "transmation matrices are inconsistent":
		if True:
			#run tomo-refine.sh which iteratively run projalign
			### changes origin and rotation for each image
			tomorefineexe = apParam.getExecPath("tomo-refine.sh", die=True)
			cmd = ( tomorefineexe
				+" "+paramfile
			)
			print cmd
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
			### results got to runname-iter-numimgs.tlt
			#run tomofit.sh
			tomofitexe = apParam.getExecPath("tomo-fit.sh", die=True)
			cmd = ( tomofitexe
				+" "+paramfile
			)
			print cmd
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
			## refines geometric parameters: inplane rotation and tilt axis angle

			### repeat tomo-refine.sh
			### stop when the transmation matrices are consistent, less than 1% difference

	#=====================
	def runProtomo2(self, sessiondata, processingDir,  seriesname, ordered_imagelist, refimg, center, corr_bin, commit, tilts):
		"""
		Uses Hanspeters' protomo2
		takes individual MRC files or MRC stack, tiff, spider, imagic, suprim
		"""
		
		# TODO: not sure the ordered_imagelist, and refimg were found correctly. May need to look into geometry file to get it.
		
		if not os.path.isdir( processingDir ):
			apDisplay.printError("Protomo2 processing directory (%s) is not valid." % (processingDir, ))
		
		# Create an instance of the Protomo2 class 	
		apProtomo2 = apProTomo2.ApProTomo2( sessiondata, seriesname, self.params, ordered_imagelist, refimg, center, corr_bin, processingDir, tilts )
		
		# Run protomo2
		apProtomo2.run()

		# Write input parameters and results to DB
		if commit:
			apProtomo2.commitResultsToDB()

	#=====================
	def start(self):
		commit = self.params['commit']
		tiltdatalist = apTomo.getTiltdataList(self.params['tiltseries'],self.params['othertiltseries'])
		sessiondata = tiltdatalist[0]['session']
		description = self.params['description']
		alignsample = self.params['sample']
		cycle = self.params['cycle']
		alignmethod = self.params['alignmethod']
		apDisplay.printMsg("getting imagelist")
		imagelist = apTomo.getImageList(tiltdatalist)
		tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(imagelist)
		
		# This parameter is needed for protomo, but not protomo2
		if self.params['refimg']:
			refimg = self.params['refimg']

		if alignmethod != 'protomo2':
			for file in ordered_mrc_files:
				# protomo can not function with a negative origin
				# protomo2 CAN function with negative origin
				apImage.shiftMRCStartToZero(file)
				
			apDisplay.printMsg("getting pixelsize")
			pixelsize = apTomo.getTomoPixelSize(ordered_imagelist[refimg])
			if pixelsize is None:
				apDisplay.printError('Pixel Size not retrieved. Invalid tilt series for processing')

		imgshape = apTomo.getTomoImageShape(ordered_imagelist[refimg])
		corr_bin = apTomo.getCorrelatorBinning(imgshape)
		center = {'x':imgshape[1]/2,'y':imgshape[0]/2}
		default_azimuth = apTomo.getDefaultAzimuthFromLeginon(ordered_imagelist[refimg])

		processdir = os.path.abspath(self.params['rundir'])
		imodseriesname = apTomo.getFilename(tiltdatalist)
		
		# protomo2 does not write out text files, intermediate info is in memory and the final result is binary
		seriesname = 'tomo'+ imodseriesname
		# Write tilt series stack images and tilt angles, not needed for protomo2
		if alignmethod != 'protomo2':
			stackdir = self.params['tiltseriesdir']
			stackname = imodseriesname+".st"
			apTomo.writeTiltSeriesStack(stackdir,stackname,ordered_mrc_files,1e10*pixelsize)
			apImod.writeRawtltFile(stackdir,imodseriesname,tilts)
		
		leginonxcorrlist = []
		for tiltdata in tiltdatalist:
			settingsdata = apTomo.getTomographySettings(sessiondata,tiltdata)
			leginonxcorrlist.append(settingsdata)
			
		# Run protomo2 
		if alignmethod == 'protomo2':
			self.runProtomo2(sessiondata, processdir, seriesname, ordered_imagelist, refimg, center, corr_bin, commit, tilts)
			
			# protomo2 does not need anything beyond this point, so exit
			return
			
		if cycle != 1 or alignmethod != 'protomo':
			cycles=[cycle,]
		else:
			# also process and commit protomo cycle 0 if doing cycle 1
			cycles=[0,1]
		for cycle in cycles:
			if alignmethod == 'protomo' or alignmethod == 'leginon':
				self.params['aligndir'],self.params['imagedir'] =	apProTomo.setProtomoDir(self.params['rundir'],cycle)
				aligndir = self.params['aligndir']
				# Link images into rundir/raw
				rawimagenames = apProTomo.linkImageFiles(ordered_imagelist,self.params['imagedir'])
				tltfile = os.path.join(aligndir,seriesname+'-%02d-itr.tlt' % (cycle,))
				if cycle == 0:
					# get initial shift alignment from leginon tiltcorrelator
					# Assume all tiltdata have the same tomography settings
					shifts = apTomo.getGlobalShift(ordered_imagelist, corr_bin, refimg)
					tltparams = apProTomo.convertShiftsToParams(tilts,shifts,center,default_azimuth,rawimagenames)
					apProTomo.writeTiltFile(tltfile,seriesname, tltparams[0], tltparams[1])
					refineparamdict=apProTomo.createRefineDefaults(len(tilts),
							os.path.join(processdir,'raw'),os.path.join(processdir,'out'))
					refineparamdict = apProTomo.updateRefineParams(refineparamdict,imgshape,alignsample,100,refimg)
				else:
					lasttltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (cycle-1,))
					if self.params['goodcycle']:
						if (self.params['goodstart'] == 0 and self.params['goodend'] == len(ordered_imagelist) - 1):
							# revert goodcycle related params since nothing will be reset
							self.params['goodcycle'] = None
							self.params['goodstart'] = None
							self.params['goodend'] = None
					if not self.params['goodcycle']:
						#default uses last cycle
						shutil.copy(lasttltfile,tltfile)
					else:
						if not (self.params['goodstart'] or self.params['goodend']):
							shutil.copy(lasttltfile,tltfile)
						else:
							# Reset bad ending tilts before alignment cycle
							goodtltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (self.params['goodcycle'],))
							goodtltparams = apProTomo.parseTilt(goodtltfile)
							lasttltparams = apProTomo.parseTilt(lasttltfile)
							tltparams = apProTomo.resetTiltParams(lasttltparams,goodtltparams,self.params['goodstart'],self.params['goodend'])
							apProTomo.writeTiltFile(tltfile,seriesname, tltparams[0], tltparams[1])
					lastrefineparamfile = os.path.join(aligndir,seriesname+'-%02d.param' % (cycle-1,))
					refineparamdict = apProTomo.parseRefineParamFile(lastrefineparamfile)
					refineparamdict = apProTomo.updateRefineParams(refineparamdict,imgshape,alignsample,self.params['region'],refimg)
				# Write param file in rundir/align
				paramfilepath = os.path.join(seriesname+'-%02d.param' % (cycle))
				fullparamfilepath = os.path.join(aligndir,paramfilepath)
				apProTomo.writeRefineParamFile(refineparamdict,fullparamfilepath)
				# run porjalign script
				os.chdir(aligndir)
				if cycle > 0:
					self.runProjalign(paramfilepath)
				else:
					lasttltfile = os.path.join(aligndir,seriesname+'-%02d-itr.tlt' % (cycle,))
					newtltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (cycle,))
					shutil.copy(lasttltfile,newtltfile)
				# convert to imod alignment
				alignpathprefix = os.path.join(processdir, seriesname)
				centertuple = (center['x'],center['y'])
				apProTomo.convertGlobalTransformProtomoToImod(seriesname+'-%02d' %(cycle),imodseriesname, centertuple)
			elif alignmethod == 'imod-shift':
				# Correlation by Coarse correlation in IMOD
				aligndir = processdir
				imodxcorrdata = apImod.coarseAlignment(stackdir, processdir, imodseriesname, commit)
				# Global Transformation
				gtransforms = apImod.convertToGlobalAlignment(processdir, imodseriesname)
			# Create Aligned Stack for record
			bin = int(math.ceil(min(imgshape) / 512.0))
			apImod.createAlignedStack(stackdir, aligndir, imodseriesname,bin)
			if alignmethod == 'protomo' or alignmethod == 'leginon':
				alifilename = imodseriesname+'-%02d.ali' % cycle
				os.rename(imodseriesname+'.ali',alifilename)
			else:
				alifilename = imodseriesname+'.ali'
			alifilepath = os.path.join(aligndir,alifilename)
			# commit to database
			if commit:
				if alignmethod == 'protomo' or alignmethod == 'leginon':
					# -- Commit Parameters --
					protomodata = apProTomo.insertProtomoParams(seriesname)
					alignrun = apTomo.insertTomoAlignmentRun(sessiondata,leginonxcorrlist[0],None,protomodata,None,1,self.params['runname'],self.params['rundir'],self.params['description'])
					self.cycle_description = self.params['description']
					self.params['cycle'] = cycle
					if cycle == 0:
						# temporarily change aligner description on the initial 0 cycle
						self.params['description'] = 'leginon correlation results'
					# insert sample and window size and all the other user defined params into ApProtomoRefinementParamsData
					alignerdata = apProTomo.insertAlignIteration(alignrun, protomodata, self.params, refineparamdict,ordered_imagelist[refimg])
					# -- Commit Results --
					resulttltfile = os.path.join(aligndir,seriesname+'-%02d-fitted.tlt' % (cycle,))
					resulttltparams = apProTomo.parseTilt(resulttltfile)
					if resulttltparams:
						# commit the geometry parameters (psi, theta, phi, azimuth)
						modeldata = apProTomo.insertModel(alignerdata, resulttltparams)
						# insert results into ApProtomoAlignmentData (also used by imod) for each image
						for i,imagedata in enumerate(ordered_imagelist):
							apProTomo.insertTiltAlignment(alignerdata,imagedata,i,resulttltparams[0][i],center)
					self.params['description'] = self.cycle_description
				else:
					alignrun = apTomo.insertTomoAlignmentRun(sessiondata,None,imodxcorrdata,None,None,1,self.params['runname'],self.params['rundir'],self.params['description'])
					alignerdata = apTomo.insertAlignerParams(alignrun,self.params)
					#results
					prexgfile = os.path.join(aligndir,imodseriesname+'.prexg')
					shifts = apImod.readShiftPrexgFile(aligndir, imodseriesname)
					resulttltparams = apProTomo.convertShiftsToParams(tilts,shifts,center,default_azimuth)
					if resulttltparams:
						modeldata = apProTomo.insertModel(alignerdata, resulttltparams)
						for i,imagedata in enumerate(ordered_imagelist):
							apProTomo.insertTiltAlignment(alignerdata,imagedata,i,resulttltparams[0][i],center)
				# multiple tilt series in one alignrun
				for i in range(0,len(tiltdatalist)):
					if i == 0:
						primary = True
					else:
						primary = False
					apTomo.insertTiltsInAlignRun(alignrun, tiltdatalist[i],leginonxcorrlist[i],primary)
			apTomo.makeAlignStackMovie(alifilepath)
			os.chdir(processdir)

#=====================
if __name__ == '__main__':
	app = protomoAligner()
	app.start()
	app.close()



