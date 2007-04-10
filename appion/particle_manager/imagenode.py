#!/usr/bin/python -O
import sys
import os
import data
import numarray
import numarray.ma as ma
import apLoop
import apImage
import apDatabase
import imagefun

class ImageNode:
	defaultsettings = {}
	defaultsettings.update({
		'mrcfileroot':None,
		'sessionname':None,
		'session':None,
		'preset':None,
		'runid':"run1",
		'dbimages':False,
		'alldbimages':False,
		'apix':None,
		'diam':0,
		'bin':4,
		'continue':False,
		'commit':False,
		'description':None,
		'outdir':None,
		'rundir':None,
		'doneDictName':None,
		'functionLog':None,
		'pixdiam':None,
		'binpixdiam':None,
	})
	def __init__(self):
		self.settings = {}
		self.resulttypes = []
		self.functionname = ""
		
	def modifyParams(self,params):
		return params
		
	def prepImage(self,image,cutoff=5.0):
		shape=numarray.shape(image)
		garea,gavg,gstdev=apImage.maskImageStats(image)
		print 'image mean= %.1f stdev= %.1f' %(gavg,gstdev)
		cleanimage=ma.masked_outside(image,gavg-cutoff*gstdev,gavg+cutoff*gstdev)
		carea,cavg,cstdev=apImage.maskImageStats(cleanimage)
		image.shape = shape
		image.mean = cavg
		image.stdev = cstdev
		image=cleanimage.filled(cavg)
		return image
		
	def getImage(self,imgname,binning):
		image = apDatabase.getImageData(imgname)['image']
		image=imagefun.bin(image,binning)
		shape=numarray.shape(image)
		cutoff=8.0
		# remove spikes in the image first
		image=self.prepImage(image,cutoff)
		return image	
	
	def insertFunctionParamsToDB(self,params):
		#dummy database entry
		partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
		runIds = [1,]
		runId = runIds[0]
		return runId
		
	def function(self,params,binnedimage):
		results=['test','test2']
		shape = numarray.shape(binnedimage)
		resultimage = numarray.zeros(shape)
		return results,resultimage

	def writeResultsToDB(self,imgData,sessionId,runId,results):
		partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
		print results
		return
		
	def writeResultsToFile(self,imagename,results,path,resulttype):
		# As an example, results is a list of of information that would be inserted into the database if commited
		
		resultfile=open(path+"/"+imagename+"."+resulttype,'w')
		resultlines = '\t'.join(results)
		resultfile.write(resultlines+"\n")
		resultfile.close()

	def writeResultImageToFile(self,imagename,path,image):
		# remove old image file if it exists
		functionname = self.functionname
		filename=path+"/"+imagename+"_"+functionname+".png"
		if (os.path.exists(filename)):
			os.remove(filename)
		if image is not None:
			apImage.arrayMaskToPngAlpha(image,filename)

	def start(self,argvlist):
		functionname = self.functionname
		data.holdImages(False)
		print argvlist
		(images,stats,params,donedict) = apLoop.startNewAppionFunction(argvlist)
		params=self.modifyParams(params)
		run_dir=params["outdir"]+"/"+params["runid"]+"/"
		# create "run" directory if doesn't exist
		if not (os.path.exists(run_dir)):
			os.mkdir(run_dir)

		
		if params['commit']:
			functionrunids=[]
			runid=self.insertFunctionParamsToDB(params)
		else:
			# create "resulttypes" directory if doesn't exist
			result_dirs ={}
			for resulttype in self.resulttypes:
				result_dir=run_dir+"/"+resulttype+"s"
				if not (os.path.exists(result_dir)):
					os.mkdir(result_dir)

				# remove result file if it exists
				if (os.path.exists(result_dir+"/*."+resulttype)):
					os.remove(result_dir+"/*."+resulttype)
				result_dirs[resulttype]=result_dir

		notdone=True
		while notdone:
			while images:
				img = images.pop(0)
				imgname=img['filename']
				stats['imagesleft'] = len(images)

				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if( apLoop.startLoop(img, donedict, stats, params)==False ):
					continue
				image = self.getImage(imgname,params['bin'])
				resultData,resultImage=self.function(params,image)
				if resultData is not None:
					if params['commit']:
						self.writeResultsToDB(img,params['session'].dbid,runid,resultData)
					else:
						for resulttype in self.resulttypes:
							# remove resultdata file if it exists
							result_dir = result_dirs[resulttype]
							if (os.path.exists(result_dir+"/"+imgname+"."+resulttype)):
								os.remove(result_dir+"/"+imgname+"."+resulttype)
							self.writeResultsToFile(imgname,resultData,result_dir,resulttype)
				if resultImage is not None:
					if not params['test']:
						self.writeResultImageToFile(imgname,run_dir,resultImage)
					
				#NEED TO DO SOMETHING ELSE IF RESULTS ARE ALREADY IN DATABASE
				apLoop.writeDoneDict(donedict,params,imgname)
				apLoop.printSummary(stats, params)
				#END LOOP OVER IMAGES
			notdone,images = apLoop.waitForMoreImages(stats, params)
			#END NOTDONE LOOP	
		apLoop.completeLoop(stats)

if __name__ == '__main__':
	print sys.argv
	function = ImageNode()
	function.resulttypes = ['testtype']
	function.functionname = "test"
	
	function.start(sys.argv)
