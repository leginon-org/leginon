#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import sys
import os
import data
import apLoop
import apCrudFinder
import apParticle
import particleData
import apDatabase
import numarray
import apImage
import numarray.ma as ma
import imagenode

class MaskMaker(imagenode.ImageNode):
	settingsclase = particleData.MaskMakerSettingsData
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
		imagenode.ImageNode.__init__
		self.functionname = 'mask'
		self.resulttypes = ['region']
		print "started"
	
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

	def makeMask(self,params,image):
		shape = numarray.shape(image)
		mask = numarray.zeros(shape)
		regioninfos = [[10,20,30,40,(50,60)],]
		return regioninfos, mask	

	def writeResultsToFile(self,imagename,infos,path,resulttype='region'):
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
		for l1 in range(0,len(infos)):
		
			l=l1+offset
			info=infos[l]
			regionline=" %s.mrc %d %d %.1f %.1f %.1f %d\n" %(imagename,int(info[4][1]),int(info[4][0]),info[0],info[1],info[2],int(info[3]))
			regionlines=regionlines+regionline
		regionfile=open(path+"/"+imagename+".region",'w')
		regionfile.write(regionlines+"\n")
		regionfile.close()

	
	def writeResultsToDB(self,img,expid,maskrun,infos):
		# infos is a list of information or a dictionary using non-zero index as keys
		# area,avg,stdev,length,(centerRow,centerColumn)
		imgids=apParticle.getDBparticledataImage(img,expid)
		if len(infos)==0:
			return
		regionlines=""
		try:
			infos.keys()
		except:
			offset=0
		else:
			offset=1
		for l1 in range(0,len(infos)):
		
			l=l1+offset
			info=infos[l]
			apParticle.insertMaskRegion(maskrun,imgids[0],info)

	def writeResultImageToFile(self,imagename,path,mask):
		maskfile=path+"/"+imagename+"_mask.png"
		if (os.path.exists(maskfile)):
			os.remove(maskfile)
		apImage.arrayMaskToPngAlpha(mask,maskfile)
			
	def outputTestImage(self,array,name,description,testlog):
		width=25
		if testlog[0]:
			jpgname="tests/%02d%s.jpg" %(testlog[1],name)
			space=(width-len(jpgname))*' '
			testlog[2]+= "%s:%s%s\n" % (jpgname,space,description)
			testlog[1] += 1
		else:
			return testlog
		apImage.arrayToJpeg(array,jpgname)
		return testlog

	def function(self,params,binnedimage):
		results,resultimage = apCrudFinder.makeMask(params,binnedimage)
		return results,resultimage


if __name__ == '__main__':
	print sys.argv
	function = MaskMaker()
	function.start(sys.argv)
