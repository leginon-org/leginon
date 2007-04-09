#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import sys
import os
import data
import apLoop
import apCrud
import apParticle
import particleData

class MaskMaker:
	settingsclase = particleData.MaskMakerSettingsData
	defaultsettings = {
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
	}
	def __init__(self):
		self.settings = {}
		print "started"
	
	def prepImage(image,cutoff=5.0):
		shape=numarray.shape(image)
		garea,gavg,gstdev=maskImageStats(image)
		print 'image mean= %.1f stdev= %.1f' %(gavg,gstdev)
		cleanimage=ma.masked_outside(image,gavg-cutoff*gstdev,gavg+cutoff*gstdev)
		carea,cavg,cstdev=maskImageStats(cleanimage)
	
		image=cleanimage.filled(cavg)
		return image
		
	def getImage(self,imgname,binning):
		image = apDatabase.getImageData(imagename)['image']
		image=imagefun.bin(image,bin)
		shape=numarray.shape(image)
		cutoff=8.0
		# remove spikes in the image first
		image=self.prepImage(image,cutoff)
		return image	
	
	def makeMask(self,params,image):
		shape = numarray.shape(image)
		mask = numarray.zeros(shape)
		regioninfos = []
		return mask, regioninfos	

	def writeRegionInfo(self,imagename,path,infos):
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
		regionfile=open(path+imagename+".region",'w')
		regionfile.write(regionlines+"\n")
		regionfile.close()

	
	def writeRegionInfoToDB(self,maskrun,img,expid,infos):
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

	def writeMaskImage(self,imagename,path,mask):
		# remove old mask file if it exists
		maskfile=path+"/"+imagename+"_mask.png"
		if (os.path.exists(maskfile)):
			os.remove(maskfile)
		if mask is not None:
			apImage.arrayMaskToPngAlpha(mask,maskfile)

	def start(self,argvlist):
		data.holdImages(False)
		print argvlist
		(images,stats,params,donedict) = apLoop.startNewAppionFunction(argvlist)
		params=apCrud.modifyParams(params)
		run_dir=params["outdir"]+"/"+params["runid"]+"/"
		# create "run" directory if doesn't exist
		if not (os.path.exists(run_dir)):
			os.mkdir(run_dir)

		if params['commit']:
			maskruns=[]
			# Insertion is repeated until the query result is not empty
			# This is necessary because insertion can be slow
			maskruns=apParticle.insertMakeMaskParams(params)
			maskrun=maskruns[0]
		else:
			# create "regioninfo" directory if doesn't exist
			info_dir=run_dir+"/regions/"
			if not (os.path.exists(info_dir)):
				os.mkdir(info_dir)

			# remove region info file if it exists
			if (os.path.exists(info_dir+"*.region")):
				os.remove(info_dir+"*.region")
	
		notdone=False
		while notdone:
			while images:
				img = images.pop(0)
				imgname=img['filename']
				stats['imagesleft'] = len(images)

				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if( apLoop.startLoop(img, donedict, stats, params)==False ):
					continue
				image = self.getImage(imgname,params['bin'])
				mask,regioninfos=self.makeMask(params,image)
				if params['commit']:
					self.writeRegionInfoToDB(maskrun,img,params['session'].dbid,regioninfos)
				else:
					# remove region info file if it exists
					if (os.path.exists(info_dir+imgname+".region")):
						os.remove(info_dir+imgname+".region")
					self.writeRegionInfo(imgname,info_dir,regioninfos)
				if not params['test']:
					self.writeMaskImage(imgname,run_dir,mask)
					
				#NEED TO DO SOMETHING ELSE IF particles ARE ALREADY IN DATABASE
				apLoop.writeDoneDict(donedict,params,imgname)
				apLoop.printSummary(stats, params)
				#END LOOP OVER IMAGES
			notdone,images = apLoop.waitForMoreImages(stats, params)
			#END NOTDONE LOOP	
		apLoop.completeLoop(stats)

if __name__ == '__main__':
	print sys.argv
	function = MaskMaker()
	function.start(sys.argv)
