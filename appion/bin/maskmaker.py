#!/usr/bin/python -O
# Will by create a "masks" directory and save png images of the mask

import sys
import os
import data
import appionLoop
import apCrud
import apParticle
import appionData
import apDatabase
import numarray
import apImage
import numarray.ma as ma
import apDB
import imagefun

class MaskMaker(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "makemask"

	def setFunctionResultKeys(self):
		self.resultkeys = {'region':['dbemdata|AcquisitionImageData|image','maskrun','x','y','area','perimeter','mean','stdev','label'],}
		
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
		params = self.params
		if params['masktype']=='crud':
			params['convolve']=0.0
			params['no_hull']=False
			params['cv']=False
			params['no_length_prune']=False

		else:
			if params['masktype']=='aggr':
				print "----Aggregate Mask by Convolution of Particles with Disk at Particle Size----"
				if float(params['binpixdiam']) < 20 :
					print "----Particle too small, Probably Won't Work----"
				else:
					if float(params['convolve'])<=0.0:
						print "----Convolution Threshold not set, Won't Work----"
						sys.exit()
			
				params['no_hull']=True
				params['cv']=False
				params['no_length_prune']=False
				if params['stdev']==0.0:
					params['stdev']=1.0
			else:
				if params['masktype']=='edge':
					params['convolve']=0.0
					params['no_hull']=True
					params['cv']=True
					params['no_length_prune']=False
		if params['test']==True:
			params['commit']=False
		self.params = params


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

		self.partdb.insert(maskPdata)
		
		return maskPdata

	def specialParseParams(self,args):
		params = self.params
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='masktype'):
				params['masktype']=elements[1]
			elif (elements[0]=='cruddiam'):
				params['cdiam']=float(elements[1])
			elif (elements[0]=='crudblur'):
				params['cblur']=float(elements[1])
			elif (elements[0]=='crudlo'):
				params['clo']=float(elements[1])
			elif (elements[0]=='crudhi'):
				params['chi']=float(elements[1])
			elif (elements[0]=='crudstd'):
				params['cstd']=float(elements[1])
			elif (elements[0]=='crudschi'):
				params['cschi']=float(elements[1])
			elif (elements[0]=='crudsclo'):
				params['csclo']=float(elements[1])
			elif (elements[0]=='convolve'):
				params['convolve']=float(elements[1])
			elif (elements[0]=='stdev'):
				params['stdev']=float(elements[1])
			elif (arg=='no_hull'):
				params['no_hull']=True
			elif (arg=='cv'):
				params['cv']=True
				params['no_hull']=True
			elif (arg=='no_length_prune'):
				params['no_length_prune']=True
			elif (arg=='test'):
				params['test']=True
				
		self.params = params
	
	def insertFunctionRun(self,params):
		maskRdata=appionData.ApMaskMakerRunData()
		maskRdata['dbemdata|SessionData|session'] = params['session'].dbid
		maskRdata['path']=params['rundir']
		maskRdata['name']=params['runid']
		maskRdata['params']=self.insertFunctionParams(params)
		self.partdb.insert(maskRdata)

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
		results=self.function(self.params,self.rundata,imgdata,image)
		mask = results.pop('mask')
		filepathname = self.params['rundir']+"/masks/"+imgdata['filename']+"_mask.png"
		apImage.arrayMaskToPngAlpha(mask,filepathname)
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
		imgarray=imagefun.bin(imgarray,binning)
		shape=numarray.shape(imgarray)
		cutoff=8.0
		# remove spikes in the image first
		imgarray=self.prepImage(imgarray,cutoff)
		return imgarray	
	
	def function(self,params,rundata,imgdata,binnedimgarray):
		regions,maskarray = apCrud.makeMask(params,binnedimgarray)
		regionTree = self.getResults(rundata,imgdata,regions)
		return {'region':regionTree,'mask':maskarray}


if __name__ == '__main__':
	function = MaskMaker()
	function.run()
