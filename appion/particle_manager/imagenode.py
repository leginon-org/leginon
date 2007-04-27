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
	# These are default parameters that are used to create the default database run and parameter
	# entries
	defaultsettings.update({
		'mrcfileroot':None,
		'sessionname':None,
		'session':data.SessionData(name='dummy'),
		'preset':None,
		'runid':"dummy",
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
		self.dbsavetypes = {'pik':'txt','region':'txt'}	#possible resulttypes that commit to db and their file extension if saved to file
		self.filesavetypes = {'mask':'png','cc':'jpg','test':'jpg'}	#possible resulttypes never commited to db and their file extension

		# redefine the followings for the actual function in the subclass
		# in this test function, it output two results. 'pik' is saved to db if commited and has four columns of entry. 'cc' is a jpg file
		# that is always saved in the run directory
		self.functionname = "test"
		self.resulttypes = ('pik','cc')
		self.resultkeys = {'pik':['dbemdata|AcquisitionImageData|image','testrun','x','y'],'cc':None}
		
	
	def modifyParams(self,params):
		# This can go in apLoop.py as specialParamConclicts()
		return params
		
	def prepImage(self,image,cutoff=5.0):
		shape=numarray.shape(image)
		garea,gavg,gstdev=apImage.maskImageStats(image)
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
	
	def insertFunctionParams(self,params):
		testPdata = appionData.ApTestParamsData()
		testPdata['bin']=params['bin']
		
		self.partdb.insert(testPdata)
		return testPdata

	def insertFunctionRun(self,params):

		rundata = appionData.ApTestRunData()
		rundata['name'] = params['runid']
		rundata['dbemdata|SessionData|session'] = params['session'].dbid
		rundata['path'] = params['outdir']
		rundata['params'] = self.insertFunctionParams(params)		

		self.partdb.insert(rundata)
		
		return rundata
		
	def function(self,params,rundata,imgdata,binnedimage):	
		
		def createResultData(rundata,imgdata,info):
			testresultdata=appionData.ApTestResultData()
			testresultdata['testrun']=rundata
			testresultdata['dbemdata|AcquisitionImageData|image']=imgdata.dbid
			testresultdata['x']=info[0]
			testresultdata['y']=info[1]
			
			return testresultdata
			
		infos = [(0.2,1*params['bin']),(0.5,2.2*params['bin'])]
		pikresults = []
		for info in infos:
			pikresults.append(createResultData(rundata,imgdata,info))
		
		shape = numarray.shape(binnedimage)
		ccimage = numarray.zeros(shape)
		
		return {'pik':pikresults,'cc':ccimage}

	def writeResultsToDB(self,idata):
		if idata is None:
			return
		for q in idata:
			self.partdb.insert(q)
		return
		
	def writeResultsToFile(self,imagename,idata,path,resulttype,result_ext):
		
		filename = path+"/"+imagename+"_"+resulttype+"."+result_ext
		if os.path.exists(filename):
			os.remove(filename)
		if idata is None:
			return
		else:
			print filename
			if result_ext == 'png':
				apImage.arrayMaskToPngAlpha(idata,filename)
			else:
				if result_ext == 'jpg':
					arrayToJpeg(idata,filename,normalize=True)	
				else:
				# As an example, results is a list of several dictionary of of information that would be inserted into the database if commited
				# For example: [{'dbemdata|AcquisitionImageData|image': imagedata,run:rundata,'x':0.5,'y':1,3},{'run':rundata,'x':2.5,'y':3,3}]
					resultfile=open(filename,'w')
					resultlines=[]
					for info in idata:
						resultline = ''
						for infokey in self.resultkeys[resulttype]:
							try:
								# For data object, save in file as its dbid
								result = info[infokey].dbid
							except:
								result = info[infokey]

							# For image, save in file as its filename
							if infokey == 'dbemdata|AcquisitionImageData|image':
								result=imagename
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

		expid = params['session'].dbid
		
		if params['commit']:
			rundata = self.insertFunctionRun(params)
		
		else:
			rundata = self.insertFunctionRun(self.defaultsettings)
			
		# create "result" directory if doesn't exist
		result_dirs ={}
		for resulttype in self.resulttypes:
			if resulttype in self.filesavetypes.keys() or (resulttype in self.dbsavetypes.keys() and params['commit'] == False):
				result_dir=run_dir+resulttype+"s"
				if not (os.path.exists(result_dir)):
					os.mkdir(result_dir)

				# remove result file if it exists
				if not params['continue'] and os.path.exists(result_dir+"/*"):
					os.remove(result_dir+"/*")
				
				result_dirs[resulttype]=result_dir
			else:
				result_dirs[resulttype]=None
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
				
				resulttypes = self.resulttypes
				for resulttype in resulttypes:
					try:
						resultData = results[resulttype]
					except KeyError:
						print "EMPTY %s RESULT" % resulttype
					result_dir=result_dirs[resulttype]
					
					if resulttype in self.dbsavetypes.keys():
						result_ext = self.dbsavetypes[resulttype]
						if params['commit']:
							self.writeResultsToDB(resultData)
						else:
							self.writeResultsToFile(imgname,resultData,result_dir,resulttype,result_ext)
					else:
						if resulttype in self.filesavetypes.keys():
							result_ext = self.filesavetypes[resulttype]
							self.writeResultsToFile(imgname,resultData,result_dir,resulttype,result_ext)
						else:
							print "RESULT %s NOT SAVED IN ANY WAY" % resulttype
						
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
	function.start(sys.argv)
