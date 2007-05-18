#!/usr/bin/python -O
# Will by create a "masks" directory and save png images of the mask

import sys
import os
import numarray
import numarray.ma as ma
#appion
import appionLoop
import apImage
import apCrud
import apParticle
import appionData
import apDatabase
import apDisplay

class MaskMaker(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "makemask"

	def setFunctionResultKeys(self):
		self.resultkeys = {'region':['dbemdata|AcquisitionImageData|image', 'maskrun', 'x', 'y',
			 'area', 'perimeter', 'mean', 'stdev', 'label' ],}
		
	def specialDefaultParams(self):
		self.params['masktype']='custom'
		self.params['cdiam']=0
		self.params['cblur']=3.5
		self.params['clo']=0.6
		self.params['chi']=0.95
		self.params['cstd']=1.0
		self.params['cschi']=1.0
		self.params['csclo']=0.0
		self.params['convolve']=0.0
		self.params['no_hull']=False
		self.params['cv']=False
		self.params['no_length_prune']=False
		self.params['stdev']=0.0
		self.params['test']=False

	def specialParamConflicts(self):
		if self.params['masktype']=='crud':
			self.params['convolve']=0.0
			self.params['no_hull']=False
			self.params['cv']=False
			self.params['no_length_prune']=False
		elif self.params['masktype']=='aggr':
			apDisplay.printMsg("Aggregate Mask by Convolution of Particles with Disk at Particle Size")
			if float(self.params['binpixdiam']) < 20 :
				apDisplay.printWarning("Particle too small, Probably Won't Work")
			elif float(self.params['convolve'])<=0.0:
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

		self.appiondb.insert(maskPdata)
		
		return maskPdata

	def specialParseParams(self, args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='masktype'):
				self.params['masktype']=elements[1]
			elif (elements[0]=='cruddiam'):
				self.params['cdiam']=float(elements[1])
			elif (elements[0]=='crudblur'):
				self.params['cblur']=float(elements[1])
			elif (elements[0]=='crudlo'):
				self.params['clo']=float(elements[1])
			elif (elements[0]=='crudhi'):
				self.params['chi']=float(elements[1])
			elif (elements[0]=='crudstd'):
				self.params['cstd']=float(elements[1])
			elif (elements[0]=='crudschi'):
				self.params['cschi']=float(elements[1])
			elif (elements[0]=='crudsclo'):
				self.params['csclo']=float(elements[1])
			elif (elements[0]=='convolve'):
				self.params['convolve']=float(elements[1])
			elif (elements[0]=='stdev'):
				self.params['stdev']=float(elements[1])
			elif (arg=='no_hull'):
				self.params['no_hull']=True
			elif (arg=='cv'):
				self.params['cv']=True
				self.params['no_hull']=True
			elif (arg=='no_length_prune'):
				self.params['no_length_prune']=True
			elif (arg=='test'):
				self.params['test']=True
		if self.params['test']==True:
			self.params['commit']=False			
	
	def insertFunctionRun(self):
		params = self.params
		if params is None:
			params = self.defaultparams
		maskRdata=appionData.ApMaskMakerRunData()
		maskRdata['dbemdata|SessionData|session'] = params['session'].dbid
		maskRdata['path']=params['rundir']
		maskRdata['name']=params['runid']
		maskRdata['params']=self.insertFunctionParams(params)
		self.appiondb.insert(maskRdata)

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
			info.append(l+1)
			q = apParticle.createMaskRegionData(rundata,imgdata,info)
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
		apImage.arrayMaskToPngAlpha(mask, filepathname)
		return results
		

	def prepImage(self,imgarray,cutoff=5.0):
		shape=numarray.shape(imgarray)
		garea,gavg,gstdev=apImage.maskImageStats(imgarray)
		cleanimgarray=ma.masked_outside(imgarray,gavg-cutoff*gstdev,gavg+cutoff*gstdev)
		carea,cavg,cstdev=apImage.maskImageStats(cleanimgarray)
		imgarray.shape = shape
		imgarray.mean = cavg
		imgarray.stdev = cstdev
		imgarray=cleanimgarray.filled(cavg)
		return imgarray
		
	def getImage(self,imgdata,binning):
		imgarray = imgdata['image']
		imgarray = apImage.binImg(imgarray, binning)
		shape=numarray.shape(imgarray)
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
