#!/usr/bin/env python

#builtin
import sys
import os
import re
import time
import math
import cPickle
#appion
import apDisplay
import apDatabase
import apDB
import apImage
import apXml
#leginon
import data
try:
	import mem
except:
	apDisplay.printError("Please load 'usepythoncvs' for CVS leginon code,"
		+" which includes 'mem.py'")

class AppionLoop(object):
	partdb=apDB.apdb
	db=apDB.db

	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		"""
				
		#set the name of the function; needed for param setup
		self.setFunctionName()

		#set the resulttypes and resultkeys of the function; needed for param setup
		self.setFunctionResultKeys()

		### setup default params: output directory, etc.
		self._createDefaultParams()

		### parse command line options: diam, apix, etc.
		self._parseCommandLineInput(sys.argv[1:])

		### check for conflicts
		self._checkParamConflicts()

		### insert run and parameters
		self._setRunAndParameters(self.params)

		### setup default stats: timing variables, etc.
		self._createDefaultStats()

		### create output directories
		self._createOutputDirs()

		### write log of command line options
		self._writeFunctionLog(sys.argv)

		### read/create dictionary to keep track of processed images
		self._readDoneDict()

		###A insert run and param to db

	def run(self):
		"""
		processes all images
		"""
		### get images from database
		self._getAllImages()
		self.preLoopFunctions()
		### start the loop
		notdone=True
		while notdone:
			self._removeProcessedImages()
			for imgdata in self.imgtree:
				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if not self._startLoop(imgdata):
					continue

				### START any custom functions HERE:
				results = self.processImage(imgdata)

				### WRITE db data
 				if self.params['commit'] == True:
					if results is None:
						self.commitToDatabase(imgdata)
					else:
						self.commitToDatabase(imgdata,results)
				else:
					self.writeResultsToFiles(imgdata,results)
				
				### FINISH with custom functions

	 			self._writeDoneDict(imgdata['filename'])
				self._printSummary()
				#END LOOP OVER IMAGES
			notdone = self._waitForMoreImages()
			#END NOTDONE LOOP
		self.postLoopFunctions()
		self._finishLoop()

	def commitToDatabase(self, imgdict,results=None):
		if results is None:
			return
		else:
			if len(results) > 0:
				resulttypes = results.keys()
				for resulttype in resulttypes:
					result = results[resulttype]
					self._writeDataToDB(result)

	def writeResultsToFiles(self, imgdict,results=None):
		if results is None:
			return
		else:
			if len(results) > 0:
				resulttypes = results.keys()
				for resulttype in resulttypes:
					result = results[resulttype]
					try:
						resultkeys = self.resultkeys[resulttype]
					except:
                				try:
							resultkeystmp = results[resulttype].keys()
						except:
							resultkeystmp = results[resulttype][0].keys()
						resultkeystmp.sort()
                				resultkeys = [resultkeystmp.pop(resultkeys.index('dbemdata|AcquisitionImageData|image'))]
               					resultkeys.extend(resultkeystmp)
					path = self.result_dirs[resulttype]
					imgname = imgdict['filename']
					filename = imgdict['filename']+"_"+resulttype+".db"
					self._writeDataToFile(result,resultkeys,path,imgname,filename)

	def setFunctionName(self, arg=None):
		"""
		Sets the name of the function
		by default takes the first variable in the argument
		"""
		if arg == None:
			arg = sys.argv[0]
		self.functionname = os.path.basename(arg.strip())
		#remove all letters after a dot, e.g. "func.py" -> "func"
		self.functionname = os.path.splitext(self.functionname)[0]
		#self.functionname = re.sub("\.[a-zA-Z]+$","",self.functionname)
		apDisplay.printMsg("FUNCTION:\t"+self.functionname)

	def setFunctionResultKeys(self):
		self.resultkeys = {}
			
	def reprocessImage(self, imgdict):
		"""
		Returns True if an image should be reprocess
		e.g. a confidence less than 80%
		"""
		return False

	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		return

	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		return

	def processImage(self, imgdict):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		raise NotImplementedError()

	def specialDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		return

	def specialParseParams(self, args):
		"""
		put in any additional parameters to parse
		"""
		return

	def specialParamConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		return

	def specialCreateOutputDirs(self):
		"""
		put in any additional directories to create
		"""
		return	

	def insertFunctionRun(self,params):
		"""
		put in run and param insertion to db here
		"""
		self.rundata = {}
		return	

	def insertPreLoopFunctionRun(self,rundata,params):
		"""
		put in run and param insertion to db here
		"""
		return	

	#################################################
	#### ITEMS BELOW ARE NOT USUALLY OVERWRITTEN ####
	#################################################

	def _createOutputDirs(self):
		"""
		create rundir
		"""
		if not self._createDirectory(self.params['rundir']) and self.params['continue']==False:
			apDisplay.printWarning("continue option is OFF. you WILL overwrite previous run.")
			time.sleep(10)

		self.result_dirs={}
		
		print "creating special output directories"
		self.specialCreateOutputDirs()

	def _checkParamConflicts(self):
		"""
		put in any conflicting parameters
		"""
		if len(self.params['mrcfileroot']) > 0 and self.params['dbimages']==True:
			apDisplay.printError("dbimages can not be specified if particular images have been specified")
		if self.params['alldbimages'] and self.params['dbimages']==True:
			apDisplay.printError("dbimages and alldbimages can not be specified at the same time")
		if len(self.params['mrcfileroot']) > 0 and self.params['alldbimages']:
			apDisplay.printError("alldbimages can not be specified if particular images have been specified")

		print "checking special param conflicts"
		self.specialParamConflicts()

	def _getAppionDir(self):
		self.params['appiondir'] = os.environ.get('APPIONDIR')
		if self.params['appiondir'] is None:
			user = os.environ.get('USER')
			trypath = "/home/"+user+"/pyappion"
		 	if os.path.isdir(trypath):
				self.params['appiondir'] = trypath
		if self.params['appiondir'] is None:
			trypath = "/ami/sw/packages/pyappion"
		 	if os.path.isdir(trypath):
				self.params['appiondir'] = trypath
		if self.params['appiondir'] is None:
			apDisplay.printError("environmental variable, APPIONDIR, is not defined.\n"+
				"Did you source useappion.sh?")
		apDisplay.printMsg("APPIONDIR:\t"+self.params['appiondir'])
		return self.params['appiondir']

	def _createDefaultParams(self):
		### new system, global params
		self.params = {}
		self.params['functionname'] = self.functionname
		self.params['rundir'] = "."
		self._getAppionDir()
		self.params['method'] = "updated"
		"""
		### XML parameters
		self.params['xmlglobfile'] = os.path.join(self.params['appiondir'],"xml","allAppion.xml")
		print "XML global parameter file:",self.params['xmlglobfile']
		self.params['xmlfuncfile'] = os.path.join(self.params['appiondir'],"xml",self.functionname+".xml")
		print "XML function parameter file:",self.params['xmlfuncfile']
		self.params = apXml.readTwoXmlFiles(self.params['xmlglobfile'], self.params['xmlfuncfile'])
		"""
		### classic methods
		self.params['mrcfileroot']=[]
		self.params['sessionname']=None
		self.params['session']=data.SessionData(name='dummy'),
		self.params['preset']=None
		self.params['runid']="dummy"
		self.params['dbimages']=False
		self.params['alldbimages']=False
		self.params['apix']=None
		self.params['diam']=0
		self.params['bin']=4
		self.params['continue']=False
		self.params['commit']=False
		self.params['description']=None
		self.params['outdir']=None
		self.params['rundir']=None
		self.params['doneDictName']=None
		self.params['functionLog']=None
		self.params['pixdiam']=None
		self.params['binpixdiam']=None
		self.params['nowait']=False
		self.params['abspath']=os.path.abspath('.')
		### get custom default params
		apDisplay.printMsg("creating special parameter defaults")
		self.specialDefaultParams()
		### save default params separately for file saving
		self.defaultparams = self.params.copy()

		### revert default runid params to run1 as in previous
		self.params['runid']="run1"

	def _createDefaultStats(self):
		self.stats = {}
		self.stats['startTime']=time.time()
		self.stats['count']  = 1
		self.stats['skipcount'] = 1
		self.stats['lastcount'] = 0
		self.stats['startmem'] = mem.active()
		self.stats['peaksum'] = 0
		self.stats['lastpeaks'] = None
		self.stats['imagesleft'] = 1
		self.stats['peaksumsq'] = 0
		self.stats['timesum'] = 0
		self.stats['timesumsq'] = 0
		self.stats['skipcount'] = 0
		self.stats['waittime'] = 0
		self.stats['lastimageskipped'] = False
		self.stats['notpair'] = 0
		self.stats['memlist'] = [mem.active()]

	def _parseCommandLineInput(self, args):
		mrcfileroot = []
		self.params['functionname'] = self.functionname
		i = 0
		while i < len(args):
			arg = args[i]
			if '.mrc' in arg and not '=' in arg:
				# add file to mrc file list minus the '.mrc' part
				mrcfile = os.path.splitext(arg)[0]
				mrcfileroot.append(mrcfile)
				# remove file from list of args and backup in loop
				del args[i]
				i -= 1
			elif ('help' in arg and not '=' in arg) or arg == 'h' or arg == '-h':
				allxml = os.path.join(self.params['appiondir'],"xml/allAppion.xml")
				funcxml = os.path.join(self.params['appiondir'],"xml",self.functionname+".xml")
				xmldict = apXml.readTwoXmlFiles(allxml, funcxml)
				apXml.printHelp(xmldict)
			i += 1

		self.params['mrcfileroot']=mrcfileroot
		if(len(self.params['mrcfileroot']) > 0):
			imgname = self.params['mrcfileroot'][0]
			sessionname = apDatabase.getSessionName(imgname)
			#sessionname = re.sub("^(?P<ses>[0-9]+[a-z]+[0-9]+[^_]+)_.+$", "\g<ses>", imgname)
			self.params['sessionname'] = sessionname
			apDisplay.printMsg("SESSIONNAME:\t'"+self.params['sessionname']+"'")

		newargs = []
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#if (elements[0] is 'help' or elements[0] is '--help' or elements[0] is '-h'):
			if (elements[0]=='outdir'):
				self.params['outdir']=os.path.abspath(elements[1])
				#if(self.params['outdir'][0] != "/"):
				#	self.params['outdir'] = os.path.join(os.getcwd(),self.params['outdir'])
				#	self.params['outdir'] = os.path.abspath(self.params['outdir'])
			elif (elements[0]=='runid'):
				self.params['runid']=elements[1]
			elif (elements[0]=='apix'):
				self.params['apix']=float(elements[1])
			elif (elements[0]=='diam'):
				self.params['diam']=float(elements[1])
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif arg=='commit':
				self.params['commit']=True
				self.params['display']=1
			elif arg=='continue':
				self.params['continue']=True
			elif (elements[0]=='dbimages'):
				dbinfo=elements[1].split(',')
				if len(dbinfo) == 2:
					self.params['sessionname']=dbinfo[0]
					self.params['preset']=dbinfo[1]
					self.params['dbimages']=True
					self.params['continue']=True # continue should be on for dbimages option
				else:
					print "\nERROR: dbimages must include both \'sessionname\' and \'preset\'"+\
						"parameters (ex: \'07feb13a,en\')\n"
					sys.exit(1)
			elif (elements[0]=='alldbimages'):
				self.params['sessionname']=elements[1]
				self.params['alldbimages']=True
			else:
				newargs.append(arg)

		apDisplay.printMsg("parsing special parameters")
		self.specialParseParams(args)

		self.params['imgdir'] = apDatabase.getImgDir(self.params['sessionname'])

		if self.params['outdir']:
			pass
		else:
			#go down one directory from img path i.e. remove 'rawdata'
			outdir = os.path.split(self.params['imgdir'])[0]
			#change leginon to appion
			outdir = re.sub('leginon','appion',outdir)
			#add the function name
			self.params['outdir'] = os.path.join(outdir, self.functionname)

		self.params['rundir'] = os.path.join(self.params['outdir'], self.params['runid'])
		apDisplay.printMsg("RUNDIR:\t "+self.params['rundir'])

		self.params['doneDictName'] = os.path.join(self.params['rundir'] , "."+self.functionname+"donedict")

		if(self.params['apix'] != None and self.params['diam'] > 0):
			self.params['pixdiam']    = self.params['diam']/self.params['apix']
			self.params['binpixdiam'] = self.params['diam']/self.params['apix']/float(self.params['bin'])

	def _writeFunctionLog(self, args):
		file = os.path.join(self.params['rundir'], self.functionname+".log")
		out=""
		for arg in args:
			out += arg+" "
		f=open(file,'aw')
		f.write(out)
		f.write("\n")
		f.close()

	def _setRunAndParameters(self,params):
		if params['commit']:
			rundata = self.insertFunctionRun(params)
			self.insertPreLoopFunctionRun(rundata,params)
		
		else:
			rundata = self.insertFunctionRun(self.defaultparams)
			self.insertPreLoopFunctionRun(rundata,self.defaultparams)
		self.rundata = rundata
	

	def _writeDataToDB(self,idata):
		if idata is None:
			return
		for q in idata:
			self.partdb.insert(q)
		return
		
	def _writeDataToFile(self,idata,resultkeys,path,imgname,filename):
		''' This is used to write a list of db data that normally goes into the	database
		'''
		filepathname = path+'/'+filename
		if os.path.exists(filepathname):
			os.remove(filepathname)
		if idata is None:
			return
		resultfile=open(filepathname,'w')
		resultlines=[]
		for info in idata:
			resultline = ''
			for infokey in resultkeys:
				try:
					# For data object, save in file as its dbid
					result = info[infokey].dbid
				except:
					result = info[infokey]

				# For image, save in file as its filename
				if infokey == 'dbemdata|AcquisitionImageData|image':
					result=imgname

				# Separate the results by tabs
				try:
					resultline += str(result) + '\t'
				except:
					resultline += '\t'
			resultlines.append(resultline)
		resultlinestxt = '\n'.join(resultlines) +"\n"
		resultfile.write(resultlinestxt)
		resultfile.close()
		

	def _readDoneDict(self):
		"""
		reads or creates a done dictionary
		"""
		doneDictName = self.params['doneDictName']
		if os.path.isfile(doneDictName) and self.params['continue'] == True:
			apDisplay.printMsg("reading old done dictionary:\n"+doneDictName)
			# unpickle previously modified dictionary
			f = open(doneDictName,'r')
			self.donedict = cPickle.load(f)
			f.close()
			if 'commit' in self.donedict  and not self.donedict['commit'] and self.params['commit']:
				apDisplay.printWarning("'commit' flag was changed, creating new done dictionary")
				self.donedict = {}
				self.donedict['commit'] = self.params['commit']
			else:
				apDisplay.printMsg("found "+str(len(self.donedict))+" dictionary entries")
		else:
			#set up dictionary
			self.donedict = {}
			self.donedict['commit'] = self.params['commit']
			apDisplay.printMsg("creating new done dictionary:\n"+doneDictName)

	def _writeDoneDict(self, imgname=None):
		"""
		write finished image (imgname) to done dictionary
		"""
		if imgname != None:
			self.donedict[imgname]=True
		self.donedict['commit'] = self.params['commit']
		doneDictName = self.params['doneDictName']
		f = open(doneDictName, 'w', 0666)
		cPickle.dump(self.donedict, f)
		f.close()

	def _createDirectory(self, path, warning=True, mode=0777):
		if os.path.exists(path):
			if warning:
				apDisplay.printWarning("directory \'"+path+"\' already exists.")
			return False
		os.makedirs(path,mode)
	
		return True

	def _getAllImages(self):
		startt = time.time()
		if 'dbimages' in self.params and self.params['dbimages']==True:
			self.imgtree = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		elif 'alldbimages' in self.params and self.params['alldbimages']==True:
			self.imgtree = apDatabase.getAllImagesFromDB(self.params['sessionname'])
		elif 'mrcfileroot' in self.params and len(self.params['mrcfileroot']) > 0:
			self.imgtree = apDatabase.getSpecificImagesFromDB(self.params["mrcfileroot"])
		else:
			print len(self.params['mrcfileroot']),self.params['alldbimages'],self.params['dbimages'],self.params['mrcfileroot']
			apDisplay.printError("no files specified")
		self.params['session']   = self.imgtree[0]['session']
		self.stats['imagecount'] = len(self.imgtree)
		self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		print " ... found",self.stats['imagecount'],"in",apDisplay.timeString(time.time()-startt)

	def _alreadyProcessed(self, imgdict):
		""" 
		checks to see if image (imgname) has been done already
		"""
		imgname = imgdict['filename']
		if imgname in self.donedict:
			if not self.stats['lastimageskipped']:
				sys.stderr.write("skipping images")
			else:
				sys.stderr.write(".")
			self.stats['lastimageskipped'] = True
			self.stats['skipcount'] += 1
			return True
		else:
			self.donedict[imgname]=None
			self.stats['waittime'] = 0
			if self.stats['lastimageskipped']:
				print "\nskipped",self.stats['skipcount'],"images so far"
			self.stats['lastimageskipped']=False
			return False
		return False

	def _startLoop(self, imgdict):
		"""
		initilizes several parameters for a new image
		and checks if it is okay to start processing image
		"""
		#calc images left
		self.stats['imagesleft'] = self.stats['imagecount'] - self.stats['count'] - self.stats['skipcount']

		#only if an image was processed last
		if(self.stats['lastcount'] != self.stats['count']):
			print "\nStarting new image", self.stats['count'], "( skip:",self.stats['skipcount'],\
				", left:", self.stats['imagesleft'],")", apDisplay.short(imgdict['filename'])
			self.stats['lastcount'] = self.stats['count']
			self._checkMemLeak()

		# get the next image pixel size:
		self.params['apix'] = apDatabase.getPixelSize(imgdict)

		# skip if image doesn't exist:
		imgpath = os.path.join(self.params['imgdir'],imgdict['filename']+'.mrc')
		if not os.path.isfile(imgpath):
			apDisplay.printWarning(imgpath+" not found, skipping")
			return False

		# check to see if image has already been processed
		#if self._alreadyProcessed(imgdict):
		#	return False

		self.stats['startloop'] = time.time()
		apDisplay.printMsg("processing "+apDisplay.shortenImageName(imgdict['filename']))
		return True

	def _printSummary(self):
		"""
		print summary statistics on last image
		"""
		### THIS NEEDS TO BECOME MUCH MORE GENERAL, e.g. Peaks
		tdiff = time.time()-self.stats['startloop']
		if not self.params['continue'] or tdiff > 0.3:
			count = self.stats['count']
			#if(count != self.stats['lastcount']):
			if(self.params['method'] != None):
				print "\n\tSUMMARY: using", self.params['method'], "method for",\
					self.functionname
			else:
				print "\n\tSUMMARY:"
			self._printLine()
			if(self.stats['lastpeaks'] != None):
				print "\tPEAKS:    \t",self.stats['lastpeaks'],"peaks"
				if(count > 1):
					peaksum   = self.stats['peaksum']
					peaksumsq = self.stats['peaksumsq']
					peakstdev = math.sqrt(float(count*peaksumsq - peaksum**2) / float(count*(count-1)))
					print "\tAVG PEAKS:\t",round(float(peaksum)/float(count),1),"+/-",\
						round(peakstdev,1),"peaks"
					print "\t(- TOTAL:",peaksum,"peaks for",count,"images -)"
				self._printLine()
	
			print "\tTIME:     \t",apDisplay.timeString(tdiff)
			self.stats['timesum'] = self.stats['timesum'] + tdiff
			self.stats['timesumsq'] = self.stats['timesumsq'] + (tdiff**2)
			timesum = self.stats['timesum']
			timesumsq = self.stats['timesumsq']
			if(count > 1):
				timeavg = float(timesum)/float(count)
				timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
				timeremain = (float(timeavg)+float(timestdev))*self.stats['imagesleft']
				print "\tAVG TIME: \t",apDisplay.timeString(timeavg,timestdev)
				#print "\t(- TOTAL:",apDisplay.timeString(timesum)," -)"
				if(self.stats['imagesleft'] > 0):
					print "\t(- REMAINING TIME:",apDisplay.timeString(timeremain),"for",self.stats['imagesleft'],"images -)"
			#print "\tMEM: ",(mem.active()-startmem)/1024,"M (",(mem.active()-startmem)/(1024*count),"M)"
			self.stats['count'] = self.stats['count'] + 1
			self._printLine()

	def _checkMemLeak(self):
		"""
		unnecessary code for determining if the program is eating memory over time
		"""
		### Memory leak code:
		self.stats['memlist'].append(mem.active())
		memfree = mem.free()
		swapfree = mem.swapfree()
		minavailmem = 64*1024; # 64 MB, size of one image
		if(memfree < minavailmem):
			apDisplay.printError("Memory is low ("+str(int(memfree/1024))+"MB): there is probably a memory leak")
	
		if(self.stats['count'] > 5):
			memlist = self.stats['memlist']
			n       = len(memlist)
			gain    = (memlist[n-1] - memlist[0])/1024.0
			sumx    = n*(n-1.0)/2.0
			sumxsq  = n*(n-1.0)*(2.0*n-1.0)/6.0
			sumy = 0.0; sumxy = 0.0; sumysq = 0.0
			for i in range(n):
				value  = float(memlist[i])/1024.0
				sumxy  += float(i)*value
				sumy   += value
				sumysq += value**2
			###
			stdx  = math.sqrt(n*sumxsq - sumx**2)
			stdy  = math.sqrt(n*sumysq - sumy**2)
			rho   = float(n*sumxy - sumx*sumy)/float(stdx*stdy)
			slope = float(n*sumxy - sumx*sumy)/float(n*sumxsq - sumx*sumx)
			memleak = rho*slope
			###
			if(slope > 0 and memleak > 32 and gain > 128): 
				printError("Memory leak of "+str(round(memleak,2))+"MB")
			elif(memleak > 16):
				print apDisplay.color(" ... substantial memory leak "+str(round(memleak,2))+"MB","brown"),\
					"(",n,round(slope,5),round(rho,5),round(gain,2),")"

	def _removeProcessedImages(self):
		startlen = len(self.imgtree)
		i = 0
		while i < len(self.imgtree):
			imgdict = self.imgtree[i]
			if self._alreadyProcessed(imgdict):
				if self.reprocessImage(imgdict):
					apDisplay.printMsg("reprocessing image "+apDisplay.short(imgdict['filename']))
				else:
					apDisplay.printMsg("skipping image "+apDisplay.short(imgdict['filename']))
					del self.imgtree[i]
					i -= 1
			i += 1

	def _printLine(self):
		print "\t------------------------------------------"

	def _waitForMoreImages(self):
		"""
		pauses 10 mins and then checks for more images to process
		"""
		#SKIP MESSAGE
		if(self.stats['skipcount'] > 0):
			apDisplay.printWarning("Images already processed and were therefore skipped (total "+\
				str(self.stats['skipcount'])+" skipped).")
			apDisplay.printMsg("to them process again, remove \'continue\' option and run selexon again.")
			self.stats['skipcount'] = 0

		#SHOULD IT WAIT?
		if self.params['nowait']:
			return False
		if not self.params["dbimages"]:
			return False
		self.stats['waittime'] = self.stats['waittime'] + 10
		if(self.stats['waittime'] > 120):
			print "Waited longer than two hours, so I am quitting"
			return False

		#WAIT
		print "\nAll images processed. Waiting ten minutes for new images (waited",\
			self.stats['waittime'],"min so far)."
		for i in range(20):
			time.sleep(30)
			#print a dot every 30 seconds
			sys.stderr.write(".")
		print ""

		#GET NEW IMAGES
		self.imgtree = self.getAllImages()
		return True

	def _finishLoop(self):
		"""
		program has finished print final stats
		"""
		ttotal= time.time()-self.stats["startTime"]
		print apDisplay.color("COMPLETE LOOP:\t"+apDisplay.timeString(ttotal)+\
			" for "+str(self.stats["count"]-1)+" images","green")
		print "ended ",time.strftime("%a, %d %b %Y %H:%M:%S")
		print "====================================================="
		print "====================================================="
		print "====================================================="
		print "====================================================="
		print ""

class BinLoop(AppionLoop):
	def processImage(self, imgdict):
		import imagefun
		imagefun.bin(imgdict['image'], 2)

if __name__ == '__main__':
	print "__init__"
	imageiter = BinLoop()
	print "run"
	imageiter.run()
