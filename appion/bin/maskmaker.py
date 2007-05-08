#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import sys
import os
import data
import apLoop
import apCrudFinder
import apParticle
import appionData
import apDatabase
import numarray
import apImage
import numarray.ma as ma
import imagenode
import apDB

class MaskMaker(imagenode.ImageNode):
	defaultsettings = dict(imagenode.ImageNode.defaultsettings)
	defaultsettings.update({
		'masktype':'custom',
		'cdiam':0,
		'cblur':3.5,
		'clo':0.6,
		'chi':0.95,
		'cstd':1.0,
		'cschi':1.0,
		'csclo':0.0,
		'convolve':0.0,
		'no_hull':False,
		'cv':False,
		'no_length_prune':False,
		'stdev':0.0,
		'test':False
	})
	def __init__(self):
		imagenode.ImageNode.__init__(self)
		
		self.functionname = 'mask'
		self.resulttypes = ['region','mask']

		# Two options for creating resultkeys of dbsavetype result: (1) get from db and sort (2) define directly
		# option (1) Pro: don't have to decide which goes first. Con:may not in any logical order and is sensitive to name change
		# option (2) Pro: can be made logical and gives a record stays the same if name changed. Con: need to define for the function and change if more or less results are outputted
		
		# Option (1) is shown here
		regionData = appionData.ApMaskRegionData()
		regionkeys = regionData.keys()
		regionkeys.sort()
		newregionkeys = [regionkeys.pop(regionkeys.index('dbemdata|AcquisitionImageData|image'))]
		newregionkeys.extend(regionkeys)

		self.resultkeys = {'region':newregionkeys,'mask':None}
	
	def modifyParams(self,params):
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
		return params	


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
			q = apParticle.createMaskRegionData(rundata,imgdata,info)
			qs.append(q)
		return qs

	def function(self,params,rundata,imgdata,binnedimgarray):
		regions,maskarray = apCrudFinder.makeMask(params,binnedimgarray)
		regionTree = self.getResults(rundata,imgdata,regions)
		return {'region':regionTree,'mask':maskarray}


if __name__ == '__main__':
	print sys.argv
	function = MaskMaker()
	function.start(sys.argv)
