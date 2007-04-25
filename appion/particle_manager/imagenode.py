#!/usr/bin/python -O
import sys
import os
import data
import dbdatakeeper
import numarray
import numarray.ma as ma
import apLoop
import apImage
import apDatabase
import apParticle
import imagefun
import apDB
import appionData

class ImageNode:
	defaultsettings = {}
	# These are just a copy from Leginon, They are not called in the class anywhere yet.
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
		self.partdb=apDB.apdb
		self.db=apDB.db
		self.settings = {}
		self.dbsavetypes = {'pik':'txt','region':'txt'}	#possible resulttypes that commit to db and their file extension
		self.filesavetypes = {'mask':'png','ccmap':'jpg','test':'jpg'}	#possible resulttypes never comit to db and their file extension
		self.functionname = ""
		self.resulttypes = []
		self.resultkeys = {}
		
	
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
	
	def insertFunctionParams(self):
		testPdata = appionData.ApTestParamsData()
		testPdata.update({
		'name': 'testparam',
		'bin': 4,
		'param1': 1,
		'param2': 2,
		})
		self.partdb.insert(testPdata)
		return testPdata

	def insertFunctionParamsDummy(self):
		testPdata = appionData.ApTestParamsData()
		testPdata.update({
		'name': 'testparam',
		'bin': 4,
		'param1': 1,
		'param2': 2,
		})
		self.partdb.insert(testPdata)
		return testPdata

	def insertFunctionRun(self,params):

		rundata = appionData.ApTestRunData()
		rundata['name'] = params['runid']
		sessiondata = data.SessionData(name=params['session'])
		print sessiondata.dbid
		rundata['dbemdata|SessionData|session'] = sessiondata.dbid
		rundata['path'] = params['outdir']
		rundata['params'] = self.insertFunctionParams()		

		self.partdb.insert(rundata)
		
		return rundata
		
	def insertFunctionRunDummy(self,params):

		''' A dummy run and parameters are inserted into the database
		the first time when the user does not want to commit the data.
		The later non-commit run won't insert because the values will
		be identical.
		
		This way the result object would be uniform
		'''
		
		testRdata = appionData.ApTestRunData()
		testRdata['name'] = 'dummy'
		testRdata['dbemdata|SessionData|session'] = 0
		testRdata['path'] = ''
		testRdata['params'] = self.insertFunctionParams()		

		self.partdb.insert(testRdata)
		
		return testRdata
		
	def function(self,params,rundata,imgdata,binnedimage):	
		self.resulttypes = ['pik','cc']
		self.resultkeys = {'pik':['dbemdata|AcquisitionImageData|image','run','x','y'],'cc':None}
		
		pikresults=[{'dbemdata|AcquisitionImageData|image':imgdata.dbid,'run':'test1','x':0.2,'y':1},{'dbemdata|AcquisitionImageData|image':imgdata.dbid,'run':'test2','x':5.2,'y':4}]
		
		shape = numarray.shape(binnedimage)
		ccimage = numarray.zeros(shape)
		
		return [pikresults,ccimage]

	def writeResultsToDB(self,idata):
		result=self.partdb.query(idata)
		self.partdb.insert(idata)
		return
		
	def writeResultsToFile(self,idata,path,resulttype,result_ext):
		imageid = idata[0]['dbemdata|AcquisitionImageData|image']
		imagedata = self.db.direct_query(data.AcquisitionImageData, imageid, False)
		imagename = imagedata['filename']
		
		filename = path+"/"+imagename+"_"+resulttype+"."+result_ext
		print filename
		if result_ext == 'png':
			apImage.arrayMaskToPngAlpha(image,filename)
		else:
			if result_ext == 'jpg':
				print "need your idea here, I don't know what you want"	
			else:
		# As an example, results is a list of several dictionary of of information that would be inserted into the database if commited
		# For example: [{runname:'text1',x:0.5,y:1,3},{runname:'text2',x:2.5,y:3,3}]
				resultfile=open(filename,'w')
				resultlines=[]
				for info in idata:
					resultline = ''
					for infokey in self.resultkeys[resulttype]:
						if infokey == 'dbemdata|AcquisitionImageData|image':
							info[infokey]=imagename
						try:
							result = info[infokey].dbid
						except:
							result = info[infokey]
						try:
							resultline += str(result) + '\t'
						except:
							resultline += '\t'
					resultlines.append(resultline)
				resultlinestxt = '\n'.join(resultlines) +"\n"
				resultfile.write(resultlinestxt)
				resultfile.close()
		
	def start(self,argvlist):
		functionname = self.functionname
		data.holdImages(False)
		(images,stats,params,donedict) = apLoop.startNewAppionFunction(argvlist)
		params=self.modifyParams(params)
		run_dir=params["outdir"]+"/"+params["runid"]+"/"
		# create "run" directory if doesn't exist
		if not (os.path.exists(run_dir)):
			os.mkdir(run_dir)

		expid = data.SessionData(name=params['session']).dbid
		print expid
		
		if params['commit']:
			rundata = self.insertFunctionRun(params)
		
		else:
			rundata = self.insertFunctionRunDummy(params)
			
			# create "result" directory if doesn't exist
			result_dirs ={}
			for resulttype in self.resulttypes:
				result_dir=run_dir+"/"+resulttype+"s"
				if not (os.path.exists(result_dir)):
					os.mkdir(result_dir)

				# remove result file if it exists
				if not params['continue'] and os.path.exists(result_dir+"/*"):
					os.remove(result_dir+"/*")
				result_dirs[resulttype]=result_dir

		notdone=True
		while notdone:
			while images:
				imgdata = images.pop(0)
				imgname=imgdata['filename']
				stats['imagesleft'] = len(images)

				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if( apLoop.startLoop(imgdata, donedict, stats, params)==False ):
					continue
				image = self.getImage(imgname,params['bin'])

				results=self.function(params,rundata,imgdata,image)
				
				i =0
				resulttypes = self.resulttypes
				for resulttype in resulttypes:
					resultData = results[i]
					result_dir=result_dirs[resulttype]
					if resultData is not None:
						if resulttype in self.dbsavetypes.keys():
							result_ext = self.dbsavetypes[resulttype]
							if params['commit']:
								self.writeResultsToDB(resultData)
							else:
								self.writeResultsToFile(resultData,result_dir,resulttype,result_ext)
					else:
						for resulttype in self.filesavetypes.keys():
							result_ext = self.filesavetypes[resulttype]
							self.writeResultsToFile(resultData,result_dir,resulttype,result_ext)
					
				#NEED TO DO SOMETHING ELSE IF RESULTS ARE ALREADY IN DATABASE
				apLoop.writeDoneDict(donedict,params,imgname)
				apLoop.printSummary(stats, params)
				#END LOOP OVER IMAGES
			notdone,images = apLoop.waitForMoreImages(stats, params)
			#END NOTDONE LOOP	
		apLoop.completeLoop(stats)

if __name__ == '__main__':
	function = ImageNode()
	function.functionname = "test"
	function.resulttypes = ['pik','cc']
	function.resultkeys = {'pik':['dbemdata|AcquisitionImageData|image','run','x','y'],'cc':None}
	function.start(sys.argv)
