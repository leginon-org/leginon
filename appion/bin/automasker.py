#!/usr/bin/env python
# Will by create a "masks" directory and save png images of the mask

import sys
import os
import shutil
import numpy
ma = numpy.ma
import time
import subprocess
import scipy.misc
from PIL import Image
import scipy.ndimage as ndimage

# myami
import pyami.mrc
import pyami.numpil
from pyami import imagefun

#appion
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apCrud
from appionlib import apMask
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apParam


class AutoMasker(appionLoop2.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "mask"

	def setFunctionResultKeys(self):
		self.resultkeys = {'region':['image', 'maskrun', 'x', 'y',
			 'area', 'perimeter', 'mean', 'stdev', 'label' ],}

	#======================
	def checkConflicts(self):
		if self.params['bin'] < 1:
			apDisplay.printError("bin must be positive")
		if self.params['test'] == True:
			self.params['commit'] = False

	def insertFunctionParams(self,params):
		maskPdata = appiondata.ApMaskMakerParamsData()

		maskPdata['bin'] = params['bin']
		maskPdata.insert()

		return maskPdata

	def setupParserOptions(self):
		self.parser.add_option("-b", "--bin", dest="bin", type="int", default=1,
			help="Binning of the image", metavar="#")
		self.parser.add_option( "--downsample", dest="downsample", type="int", default=20,
			help="Downsample to reduce the size of the image prior to processessing.", metavar="#")
		self.parser.add_option("--compsizethresh", dest="compsizethresh", type="int", default=50,
			help="Component size thresholding'", metavar="#")
		self.parser.add_option("--adapthresh", dest="adapthresh", type="int", default=500,
			help="Adaptive thresholding factor", metavar="#")
		self.parser.add_option("--blur", dest="blur", type="int", default=10,
			help="Blur window size")
		self.parser.add_option("--dilation", dest="dilation", type="int", default=10,
			help="Dilation factor", metavar="#")
		self.parser.add_option("--erosion", dest="erosion", type="int", default=1,
			help="Erosion factor", metavar="#")
		self.parser.add_option("--test", dest="test", default=False,
			action="store_true", help="Flag for saving intermediate-step images and not to commit to database")

	def insertFunctionRun(self):
		if self.params is None:
			params = self.defaultparams.copy()
		if self.params['commit'] == True:
			sessionname = self.params['sessionname']
			sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)

			paramdata = self.insertFunctionParams(self.params)
			maskRdata = apMask.createMaskMakerRun(sessiondata,self.params['rundir'],self.params['runname'],paramdata)
			maskRdata.insert()
		else:
			maskRdata = apMask.createMaskMakerRun(None,None,None,None)

		return maskRdata

	def getResults(self,rundata,imgdata,infos):
		# infos is a list of information or a dictionary using non-zero index as keys
		# area,avg,stdev,length,(centerRow,centerColumn)
		if len(infos)==0:
			return
		regionlines=""
		try:
			infos.keys()
		except:
			offset=0
		else:
			offset=1
		qs = []
		for l1 in range(0,len(infos)):

			l=l1+offset
			info=infos[l]
			info.append(l1+1)
			q = apMask.createMaskRegionData(rundata,imgdata,info)
			qs.append(q)
		return qs

	def commitToDatabase(self,imgdata):
		sessiondata   = imgdata['session']
		rundir        = self.params['rundir']
		maskname      = self.params['runname']
		assessname    = self.params['runname']
		bin           = self.params['bin']
		maskdir       = os.path.join(rundir,"masks")
		
		maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
		
		if not maskrundata:
			apMask.insertManualMaskRun(sessiondata,rundir,maskname,bin)
			maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
			try:
				apParam.createDirectory(maskdir)
			except:
				apDisplay.printWarning('can not create mask directory')
		
		massessrundata,exist = apMask.insertMaskAssessmentRun(sessiondata,maskrundata,assessname)
		
		# The mask file should only exist if the em_hole_finder found a region to mask.
		# If it does not exist, do not insert anything to the DB.
		if ( os.path.exists(self.outfile) ):
			apDisplay.printMsg("Writing results to database: " + time.asctime())
			
			# Set black pixels to white and anything else to 0
			img1 = Image.open(self.outfile)
			img2 = Image.eval(img1, lambda px: 255 if px==0 else 0)

			# make sure the images have the same shape
			imgshape = numpy.asarray(imgdata['image'].shape)
			apDisplay.printMsg("MRC Image Shape:")
			print imgshape
			imgsize = imgshape[0]*imgshape[1]
			apDisplay.printMsg("MRC Image Size:")
			print imgsize

			maskshape = numpy.shape(img2)
			apDisplay.printMsg("Mask Image Shape:")
			print maskshape
			
			apDisplay.printMsg("resizing mask image with scale:")
			scaleFactorx = float(imgshape[0])/float(maskshape[0])
			scaleFactory = float(imgshape[1])/float(maskshape[1])
			scale = scaleFactorx, scaleFactory
			print scale

			img3 = imagefun.scale( img2, scale )
			maskshape = numpy.shape(img3)
			apDisplay.printMsg("Mask Image Shape:")
			print maskshape
			#img3 = numpy.resize(img2, imgshape) # not working
			img3path = self.outfile + "_tmp.jpg"
			scipy.misc.imsave(img3path, img3)			
			
			labeled_regions,clabels = ndimage.label(img3)
				
			testlog = [False,0,""]
			infos={}
			
			apDisplay.printMsg("getting mask region info.")
			infos,testlog = apCrud.getLabeledInfo( imgdata['image'], img3, labeled_regions, range(1,clabels+1), False, infos, testlog)
	
			apDisplay.printMsg("inserting mask regions to DB.")
			print len(infos)
			
			area_max = imgsize*.9
			offset = 1
			for l1 in range(0,len(infos)):
				l = l1 + offset
				info = infos[l]
				area=info[0]
				print area
				if (area > 400 and area < area_max):
					apDisplay.printMsg("saving a region of size:")
					print area
					info.append(l)
					regiondata = apMask.insertMaskRegion( maskrundata, imgdata, info )

		# Insert mask assessment regions. This keeps track of the mask regions that the user wants to reject.
		allregiondata = apMask.getMaskRegions(maskrundata,imgdata)
		
		for regiondata in allregiondata:
			apMask.insertMaskAssessment(massessrundata,regiondata,True)

#		if self.assess != self.assessold and self.assess is not None:
#			#imageaccessor run is always named run1
#			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		return
	
	def preLoopFunctions(self):
		# set the directory to the activate program which sets up the environment to run the em_hole_finder
		# This is needed because at the moment, the em_hole_finder uses versions of packages line numextension 
		# that the rest of appion is not compatible with. Should be something like "/opt/em_hole_finder/env/bin/activate".
		if os.environ.has_key('HOLE_FIND_ACTIVATE'):
			self.activatepath = os.path.join(os.environ['HOLE_FIND_ACTIVATE'], 'activate')
		else:
			apDisplay.printError("The environment variable 'HOLE_FIND_ACTIVATE' is not set. This is the path to the activate program which sets up the environment to run em_hole_finder. It should be 'path/to/em_hole_finder/env/bin'. For more info see http://http://emg.nysbc.org/redmine/projects/appion/wiki/Install_EM_Hole_Finder.")
		
		if ( self.params['test'] ):
			apParam.createDirectory(os.path.join(self.params['rundir'],"tests"))
								    
		apParam.createDirectory(os.path.join(self.params['rundir'],"masks"),warning=False)
		regionpath = os.path.join(self.params['rundir'],"regions")
		apParam.createDirectory(regionpath,warning=False)
		self.result_dirs = {'region':regionpath}

	def processImage(self,imgdata):
		#image     = self.getImage(imgdata, self.params['bin'])
		self.image = imgdata['image']
		
		# Check the image shape
		imgshape = numpy.asarray(imgdata['image'].shape)
		apDisplay.printMsg("MRC Image Shape prior to processing:")
		print imgshape
		
		imagepath = os.path.join(imgdata['session']['image path'],imgdata['filename']+".mrc")
		
		# Convert the MRC image to a jpg for find_mask.py
		apDisplay.printMsg("Converting mrc image to jpg.")
		jpg_dir = os.path.join( self.params['rundir'], "jpgs" )
		jpg_image = os.path.join( jpg_dir, imgdata['filename']+".jpg" )
		apParam.createDirectory( jpg_dir, warning=False )
		
		pyami.numpil.write(self.image, jpg_image)
		
		if ( self.params['test']):
			self.outfile  = os.path.join(self.params['rundir'],"tests", imgdata['filename']+"_mask.jpg" )
		else:
			self.outfile  = os.path.join(self.params['rundir'],"masks", imgdata['filename']+"_mask.jpg" )
		downsample    = str(self.params['downsample'])
		compsizethresh = str(self.params['compsizethresh'])
		adapthresh    = str(self.params['adapthresh'])
		dilation      = str(self.params['dilation'])
		erosion       = str(self.params['erosion'])
		blur         = str(self.params['blur'])
		options = " --downsample=" +  downsample + " --compsizethresh=" + compsizethresh + " --adapthresh=" + adapthresh + " --blur=" + blur + " --dilation=" + dilation + " --erosion=" + erosion;
		
		commandline = ( "source " + self.activatepath + "; python `which find_mask.py` --ifile=" + jpg_image + " --ofile=" + self.outfile + options + "\n" )
		# Test with test image
		#commandline = ( "source /opt/em_hole_finder/env/bin/activate; python /opt/em_hole_finder/find_mask_amber.py \n" )

		### run command
		apDisplay.printMsg("running em hole finder " + time.asctime())
		apDisplay.printColor(commandline, "purple")

		if True:
			proc = subprocess.Popen(commandline, shell=True)
		else:
			outf = open("automasker.out", "a")
			errf = open("automasker.err", "a")
			proc = subprocess.Popen(commandline, shell=True, stderr=errf, stdout=outf)

		proc.wait()		
		
		
		# TODO: replace the call below with similar code from apCrud.py
		# regions,maskarray = apCrud.makeMask(self.params, binnedimgarray)
#		regioninfos = []
#		test = params["test"] # test mode flag
#		lognumber = 0
#		filelog = "Log \n"
#		testlog = [test,lognumber,filelog]
		

		
#		labeled_regions,clabels = nd.label(maskPix)
#		regioninfos,testlog = getLabeledInfo( imgdata['image'], maskPix, labeled_regions, range(1,clabels+1), False, regioninfos, testlog)
#		
#		regionTree = self.getResults(self.rundata, imgdata, regioninfos)
#		return {'region':regionTree,'mask':maskarray}
		#results   = self.function(self.rundata, imgdata, image)
		
		
#		mask      = results.pop('mask')
#		pngpath   = os.path.join(self.params['rundir'],"masks")
#		
#		apParam.createDirectory(pngpath,warning=False)
#		filepathname  = os.path.join(self.params['rundir'],"masks",imgdata['filename']+"_mask.png")
#		if mask is not None:
#			# PIL alpha channel read does not work
#			#apImage.arrayMaskToPngAlpha(mask, filepathname)
#			apImage.arrayMaskToPng(mask, filepathname)
#		return results

	def prepImage(self,imgarray,cutoff=5.0):
		shape             = numpy.shape(imgarray)
		garea,gavg,gstdev = apImage.maskImageStats(imgarray)
		cleanimgarray     = ma.masked_outside( imgarray, (gavg-cutoff * gstdev), (gavg + cutoff * gstdev) )
		carea,cavg,cstdev = apImage.maskImageStats(cleanimgarray)
		imgarray.shape    = shape
		imgarray          = cleanimgarray.filled(cavg)
		return imgarray

	def getImage(self,imgdata,binning):
		imgarray = imgdata['image']
		imgarray = apImage.binImg(imgarray, binning)
		shape=numpy.shape(imgarray)
		cutoff=8.0
		# remove spikes in the image first
		imgarray=self.prepImage(imgarray,cutoff)
		return imgarray

	def function(self,rundata, imgdata, binnedimgarray):
		self.params['apix'] =  apDatabase.getPixelSize(imgdata)
		# TODO: replace the call below with similar code from apCrud.py
		# regions,maskarray = apCrud.makeMask(self.params, binnedimgarray)
		regioninfos = []
		test = params["test"] # test mode flag
		lognumber = 0
		testlog = [test,lognumber,filelog]
		
		mask = Image.open()
		
		labeled_regions,clabels = nd.label(mask)
		regioninfos,testlog = getLabeledInfo(originalimage,Henrybitmap,labeled_regions,range(1,clabels+1),False,regioninfos,testlog)
		
		
		
		regionTree = self.getResults(rundata, imgdata, regions)
		return {'region':regionTree,'mask':maskarray}


if __name__ == '__main__':
	function = AutoMasker()
	function.run()

