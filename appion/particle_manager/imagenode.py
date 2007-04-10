#!/usr/bin/python -O
import sys
import numarray

class ImageNode:
	def __init__(self):
		self.settings = {}
		self.resulttypes = []
		
		print "started"
		
	def modifyParams(self,params):
		return params
		
	def insertFunctionParamsToDB(self,params):
		runIds = [1,]
		runId = runIds[0]
		return runId
		
	def function(self,params,binnedimage):
		results={}
		shape = numarray.shape(binnedimage)
		resultimage = numarray.zeros(shape)
		return results,resultimage

	def writeResultsToDB(self,function,runId,imgData,sessionId,results):
		partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
		print results
		return
		
	def writeResultsToFile(self,imagename,resulttype,path,results):
		# resultdata is a list of of information that would be inserted into the database if commited
		
		resultfile=open(path+imagename+"."+resulttype,'w')
		resultlines = ''.join(results)
		resultfile.write(regionlines+"\n")
		regionfile.close()

	def writeResultImageToFile(self,function,imagename,path,image):
		# remove old image file if it exists
		filename=path+"/"+imagename+"_"+function+".png"
		if (os.path.exists(filename)):
			os.remove(filename)
		if image is not None:
			apImage.arrayMaskToPngAlpha(image,filename)

	def start(self,argvlist):
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
			# create "infotypes" directory if doesn't exist
			result_dirs ={}
			for reulttype in self.resulttypes:
				result_dir=run_dir+"s/"+resulttype
				if not (os.path.exists(result_dir)):
					os.mkdir(result_dir)

				# remove info file if it exists
				if (os.path.exists(result_dir+"*."+resulttype)):
				os.remove(result_dir+"*."+resulttype)
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
				if params['commit']:
					self.writeResultsToDB(function,runid,img,params['session'].dbid,results)
				else:
					for resulttype in resulttypes:
						# remove resultdata file if it exists
						result_dir = result_dirs[resulttype]
						if (os.path.exists(result_dir+imgname+"."+resulttype)):
							os.remove(result_dir+imgname+","+resulttype)
						self.writeResultsToFile(imgname,resulttype,result_dir,results)
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
	function.start(sys.argv)
