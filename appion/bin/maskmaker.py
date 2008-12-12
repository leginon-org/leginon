#!/usr/bin/env python
# Will by create a "masks" directory and save png images of the mask

import sys
import os
import shutil
import numpy
ma = numpy.ma
#appion
import appionLoop
import apImage
import apCrud
import apMask
import appionData
import apDatabase
import apDisplay
import apParam

class MaskMaker(appionLoop2.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "makemask"

	def setFunctionResultKeys(self):
		self.resultkeys = {'region':['image', 'maskrun', 'x', 'y',
			 'area', 'perimeter', 'mean', 'stdev', 'label' ],}
		
	def specialDefaultParams(self):
		self.params['masktype']='custom'
		self.params['cdiam']=0
		self.params['cblur']=3.5
		self.params['clo']=0.6
		self.params['chi']=0.95
		self.params['cschi']=1.0
		self.params['csclo']=0.0
		self.params['convolve']=0.0
		self.params['no_hull']=False
		self.params['cv']=False
		self.params['no_length_prune']=False
		self.params['stdev']=0.0
		self.params['test']=False
		self.params['bin']=4
		self.params['diam']=0

	def specialParamConflicts(self):
		if self.params['test']==True:
			self.params['commit']=False
		if self.params['masktype']=='crud':
			self.params['convolve']=0.0
			self.params['no_hull']=False
			self.params['cv']=False
			self.params['no_length_prune']=False
		elif self.params['masktype']=='aggr':
			apDisplay.printMsg("Aggregate Mask by Convolution of Particles with Disk at Particle Size")
			if float(self.params['convolve'])<=0.0:
				apDisplay.printError("Convolution Threshold not set, Won't Work")
			self.params['no_hull']=True
			self.params['cv']=False
			self.params['no_length_prune']=False
			if self.params['stdev']==0.0:
				self.params['stdev']=1.0
		elif self.params['masktype']=='edge':
			self.params['convolve']=0.0
			self.params['no_hull']=True
			self.params['cv']=True
			self.params['no_length_prune']=False


	def insertFunctionParams(self,params):
		maskPdata=appionData.ApMaskMakerParamsData()
	
		maskPdata['bin']=params['bin']
		maskPdata['mask type']=params['masktype']
		maskPdata['pdiam']=params['diam']
		maskPdata['region diameter']=params['cdiam']
		maskPdata['edge blur']=params['cblur']
		maskPdata['edge low']=params['clo']
		maskPdata['edge high']=params['chi']
		maskPdata['region std']=params['stdev']
		maskPdata['convolve']=params['convolve']
		maskPdata['convex hull']=not params['no_hull']
		maskPdata['libcv']=params['cv']

		maskPdata.insert()
		
		return maskPdata

	def setupParserOptions(self):
		self.parser.add_option("-b", "--bin", dest="bin", type="int", default=1,
			help="Binning of the image", metavar="#")
		self.parser.add_option("--masktype", dest="masktype", type="string", default='custom',
			help="Type of masking: crud, edge, aggr, or custom ", metavar="#")
		self.parser.add_option("--diam", dest="diam", type="float", default=0.0,
			help="Particle diameter", metavar="#")
		self.parser.add_option("--cruddiam", dest="cdiam", type="float", default=0.0,
			help="Mask region diameter", metavar="#")
		self.parser.add_option("--crudblur", dest="cblur", type="float", default=3.5,
			help="Gaussian bluring for edge detection", metavar="#")
		self.parser.add_option("--crudhi", dest="chi", type="float", default=0.95,
			help="High threshold for the start of edge detection", metavar="#")
		self.parser.add_option("--crudlo", dest="clo", type="float", default=0.6,
			help="Low threshold for edge extension", metavar="#")
		self.parser.add_option("--crudschi", dest="cschi", type="float", default=1.0,
			help="High threshold for the acceptable standard deviation within the crud", metavar="#")
		self.parser.add_option("--crudsclo", dest="csclo", type="float", default=0.0,
			help="Low threshold for the acceptable standard deviation within the crud", metavar="#")
		self.parser.add_option("--convolve", dest="convolve", type="float", default=0.0,
			help="Threshold for blob detection on edge image convolved with particle size, 0.0 means skip the convolution", metavar="#")
		self.parser.add_option("--no_hull", dest="no_hull", default=False,
			action="store_false", help="Flag for skipping covex hull creation")
		self.parser.add_option("--cv", dest="cv", default=False,
			action="store_false", help="Flag for using libCV region finder; False= Use canny edge detection as in Selexon")
		self.parser.add_option("--stdev", dest="stdev", type="float", default=0.0,
			help="Low threshold for the acceptable standard deviation within the crud", metavar="#")
		self.parser.add_option("--no_length_prune", dest="no_length_prune", default=False,
			action="store_false", help="Flag for not eliminating blobs by perimeter to save time")
		self.parser.add_option("--test", dest="test", default=False,
			action="store_false", help="Flag for saving intermediate-step images and not to commit to database")

	def insertFunctionRun(self):
		if self.params is None:
			params = self.defaultparams.copy()
		if self.params['commit']:
			params = self.params.copy()
			sessiondata = params['session']
		else:
			params = self.defaultparams.copy()
			sessiondata = None
			
		paramdata =self.insertFunctionParams(params)
		maskRdata=apMask.createMaskMakerRun(sessiondata,params['rundir'],params['runname'],paramdata)
		maskRdata.insert()

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

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"masks"),warning=False)
		regionpath = os.path.join(self.params['rundir'],"regions")
		self._createDirectory(regionpath,warning=False)
		self.result_dirs = {'region':regionpath}

	def processImage(self,imgdata):
		image = self.getImage(imgdata,self.params['bin'])
		results=self.function(self.rundata, imgdata, image)
		mask = results.pop('mask')
		filepathname = os.path.join(self.params['rundir'],"masks",imgdata['filename']+"_mask.png")
		if mask is not None:
			apImage.arrayMaskToPngAlpha(mask, filepathname)
		return results
		

	def prepImage(self,imgarray,cutoff=5.0):
		shape=numpy.shape(imgarray)
		garea,gavg,gstdev=apImage.maskImageStats(imgarray)
		cleanimgarray=ma.masked_outside(imgarray,gavg-cutoff*gstdev,gavg+cutoff*gstdev)
		carea,cavg,cstdev=apImage.maskImageStats(cleanimgarray)
		imgarray.shape = shape
		imgarray=cleanimgarray.filled(cavg)
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
		regions,maskarray = apCrud.makeMask(self.params, binnedimgarray)
		regionTree = self.getResults(rundata, imgdata, regions)
		return {'region':regionTree,'mask':maskarray}


if __name__ == '__main__':
	function = MaskMaker()
	function.run()
