#!/usr/bin/python -O

import pyami.quietscipy

#builtin
import sys
import os
import re
import time
import math
import random
import cPickle
#appion
import apDisplay
import apDatabase
import apImage
import apXml
import apParam
#leginon
from pyami import mem
import leginondata

class AppionLoop(object):

	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		"""
		#set the name of the function; needed for param setup
		self.setFunctionName()
		self.setProcessingDirName()
		apParam.setUmask()

		#set the resulttypes and resultkeys of the function; needed for param setup
		self.setFunctionResultKeys()

		### setup default params: output directory, etc.
		self._createDefaultParams()

		#check if user wants to print help message
		self._checkForHelpCall(sys.argv[1:])

		#check for duplicate paths in environmental variables
		self._parsePythonPath()

		### parse command line options: diam, apix, etc.
		self._checkForDuplicateCommandLineInputs(sys.argv[1:])
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
		os.chdir(self.params['rundir'])
		self.preLoopFunctions()
		### start the loop
		self.notdone=True
		self.params['badprocess'] = False
		while self.notdone:
			apDisplay.printColor("\nBeginning Main Loop", "green")
			imgnum = 0
			while imgnum < len(self.imgtree) and self.notdone is True:
				imgdata = self.imgtree[imgnum]
				imgnum += 1
			
				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if not self._startLoop(imgdata):
					continue

				### START any custom functions HERE:
				results = self.processImage(imgdata)

				### WRITE db data
				if self.params['badprocess'] is False:
	 				if self.params['commit'] is True:
						self.commitToDatabase(imgdata)
						self.commitResultsToDatabase(imgdata, results)
					else:
						apDisplay.printWarning("not committing results to database, all data will be lost")
						apDisplay.printMsg("to preserve data start script over and add 'commit' flag")
						self.writeResultsToFiles(imgdata, results)
				else:
					apDisplay.printWarning("IMAGE FAILED; nothing inserted into database")
					self.params['badprocess'] = False

				### FINISH with custom functions

	 			self._writeDoneDict(imgdata['filename'])

				if os.getloadavg()[0] > 2.0:
					apDisplay.printMsg("load average is high "+str(round(os.getloadavg()[0],2)))
					time.sleep(10)

				self._printSummary()

				if self.params['limit'] is not None and self.stats['count'] > self.params['limit']:
					apDisplay.printWarning("reached image limit of "+str(self.params['limit'])+"; now stopping")

				#END LOOP OVER IMAGES
			if self.notdone is True:
				self.notdone = self._waitForMoreImages()
			#END NOTDONE LOOP
		self.postLoopFunctions()
		self._finishLoop()

	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	def commitToDatabase(self, imgdata):
		return

	def setProcessingDirName(self):
		self.processdirname = self.functionname
			
	def reprocessImage(self, imgdata):
		"""
		Returns 
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed 
		e.g. a confidence less than 80%
		"""
		return None

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

	def processImage(self, imgdata):
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
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

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

	def setFunctionResultKeys(self):
		self.resultkeys = {}

	def insertFunctionRun(self):
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

	def setFunctionName(self, arg=None):
		"""
		Sets the name of the function
		by default takes the first variable in the argument
		"""
		if arg == None:
			arg = sys.argv[0]
		self.functionname = apParam.getFunctionName(arg)
		apDisplay.printMsg("FUNCTION:\t"+self.functionname)

	def commitResultsToDatabase(self, imgdata, results):
		if results is not None and len(results) > 0:
			resulttypes = results.keys()
			for resulttype in resulttypes:
				result = results[resulttype]
				self._writeDataToDB(result)

	def writeResultsToFiles(self, imgdata,results=None):
		if results is not None and len(results) > 0:
			for resulttype in results.keys():
				result = results[resulttype]
				try:
					resultkeys = self.resultkeys[resulttype]
				except:
					try:
						resultkeystmp = results[resulttype].keys()
					except:
						resultkeystmp = results[resulttype][0].keys()
					resultkeystmp.sort()
					resultkeys = [resultkeystmp.pop(resultkeys.index('image'))]
					resultkeys.extend(resultkeystmp)
				path = self.result_dirs[resulttype]
				imgname = imgdata['filename']
				filename = imgname+"_"+resulttype+".db"
				self._writeDataToFile(result,resultkeys,path,imgname,filename)

	def _createOutputDirs(self):
		"""
		create rundir
		"""
		if not self._createDirectory(self.params['rundir']) and self.params['continue']==False:
			apDisplay.printWarning("continue option is OFF. you WILL overwrite previous run.")
			time.sleep(10)

		self.result_dirs={}
		if self.params['background'] is False:
			apDisplay.printMsg("creating special output directories")
		self.specialCreateOutputDirs()

	def _checkParamConflicts(self):
		"""
		put in any conflicting parameters
		"""
		self.tiltoptions = ["notilt", "hightilt", "lowtilt", "minustilt", "plustilt", "all"]
		if len(self.params['mrcfileroot']) > 0 and self.params['dbimages']==True:
			apDisplay.printError("dbimages can not be specified if particular images have been specified")
		if self.params['alldbimages'] and self.params['dbimages']==True:
			apDisplay.printError("dbimages and alldbimages can not be specified at the same time")
		if self.params['runid'] is None:
			apDisplay.printError("please enter a runid, example: 'runid=run1'")
		if self.params['runid'] == 'templates':
			apDisplay.printError("templates is a reserved runid, please use another runid")
		if self.params['runid'] == 'models':
			apDisplay.printError("models is a reserved runid, please use another runid")
		if len(self.params['mrcfileroot']) > 0 and self.params['alldbimages']:
			apDisplay.printError("alldbimages can not be specified if particular images have been specified")
		if self.params['tiltangle'] is not None and self.params['tiltangle'] not in self.tiltoptions:
			apDisplay.printError("unknown tiltangle setting: "+self.params['tiltangle'])
		if self.params['background'] is False:
			apDisplay.printMsg("checking special param conflicts")
		self.specialParamConflicts()

	def _createDefaultParams(self):
		### new system, global params
		self.params = {}
		self.params['functionname'] = self.functionname
		self.params['rundir'] = "."
		self.params['appiondir'] = apParam.getAppionDirectory()
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
		self.params['session']=leginondata.SessionData(name='dummy'),
		self.params['preset']=None
		self.params['runid']=None
		self.params['dbimages']=False
		self.params['alldbimages']=False
		self.params['apix']=None
		self.params['continue']=False
		self.params['nocontinue']=False
		self.params['commit']=False
		self.params['background']=False
		self.params['description']=None
		self.params['outdir']=None
		self.params['rundir']=None
		self.params['doneDictName']=None
		self.params['functionLog']=None
		self.params['uncorrected']=False
		self.params['reprocess']=None
		self.params['nowait']=False
		self.params['norejects']=None
		self.params['bestimages']=None
		self.params['limit']=None
		self.params['shuffle']=False
		self.params['tiltangle']=None
		self.params['abspath']=os.path.abspath('.')
		### get custom default params
		apDisplay.printMsg("creating special parameter defaults")
		self.specialDefaultParams()
		### save default params separately for file saving
		self.defaultparams = self.params.copy()

	def _createDefaultStats(self):
		self.stats = {}
		self.stats['startTime']=time.time()
		self.stats['count'] = 1
		self.stats['lastcount'] = 0
		self.stats['startmem'] = mem.active()
		self.stats['memleak'] = False
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

	def _checkForHelpCall(self, args):
		if len(args) < 1:
			self._runHelp()
		for arg in args:
			if ('help' in arg and not '=' in arg) or arg == 'h' or arg == '-h':
				self._runHelp()

	def _runHelp(self):
		allxml  = os.path.join(self.params['appiondir'],"xml/allAppion.xml")
		funcxml = os.path.join(self.params['appiondir'],"xml",self.functionname+".xml")
		xmldict = apXml.readTwoXmlFiles(allxml, funcxml)
		apXml.printHelp(xmldict)
		sys.exit(1)

	def _checkForDuplicateCommandLineInputs(self, args):
		argdict = {}
		for arg in args:
			elements=arg.split('=')
			opt = elements[0].lower()
			if opt in argdict:
				apDisplay.printError("Multiple arguments were supplied for argument: "+str(opt))
			else:
				argdict[opt] = True

	def _parseCommandLineInput(self, args):
		mrcfileroot = []
		self.params['functionname'] = self.functionname
		i = 0
		while i < len(args):
			arg = args[i]
			if '.mrc' in arg and not '=' in arg:
				# add file to mrc file list minus the '.mrc' part
				mrcfile = os.path.splitext(os.path.basename(arg))[0]
				mrcfileroot.append(mrcfile)
				# remove file from list of args and backup in loop
				del args[i]
				i -= 1
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
				self.params['outdir'] = os.path.abspath(elements[1])
				#if(self.params['outdir'][0] != "/"):
				#	self.params['outdir'] = os.path.join(os.getcwd(),self.params['outdir'])
				#	self.params['outdir'] = os.path.abspath(self.params['outdir'])
			elif (elements[0]=='runid'):
				self.params['runid']=elements[1]
			elif (elements[0]=='apix'):
				self.params['apix']=float(elements[1])
			elif arg=='commit':
				self.params['commit']=True
				self.params['display']=1
			elif arg=='shuffle':
				self.params['shuffle']=True
			elif arg=='nowait':
				self.params['nowait']=True
			elif elements[0]=='tiltangle':
				self.params['tiltangle']=elements[1]
			elif arg=='norejects':
				self.params['norejects']=True
			elif arg=='bestimages':
				self.params['bestimages']=True
				self.params['norejects']=True
			elif (elements[0]=='limit'):
				self.params['limit']=int(elements[1])
			elif arg=='continue':
				self.params['continue']=True
			elif arg=='background' or arg=='bg':
				self.params['background']=True
			elif arg=='nocontinue':
				self.params['nocontinue']=True
			elif (elements[0]=='reprocess'):
				self.params['reprocess']=float(elements[1])
			elif arg=='uncorrected' or arg=='raw':
				self.params['uncorrected']=True
			elif (elements[0]=='dbimages'):
				dbinfo=elements[1].split(',')
				if len(dbinfo) == 2:
					self.params['sessionname']=dbinfo[0]
					self.params['preset']=dbinfo[1]
					self.params['dbimages']=True
				else:
					apDisplay.printError("dbimages must include both \'sessionname\' and \'preset\'"+\
						"parameters (ex: \'07feb13a,en\')\n")
			elif (elements[0]=='alldbimages'):
				self.params['sessionname']=elements[1]
				self.params['alldbimages']=True

			else:
				newargs.append(arg)

		if self.params['nocontinue'] is not True:
			if self.params['alldbimages'] is True or self.params['dbimages'] is True:
				# continue should be on for dbimages option
				self.params['continue']=True 

		sessionq=leginondata.SessionData(name=self.params['sessionname'])
		self.params['session']=sessionq.query()[0]

		if len(newargs) > 0:
			if self.params['background'] is False:
				apDisplay.printMsg("parsing special parameters")
			self.specialParseParams(newargs)

		self.params['imgdir'] = apDatabase.getImgDir(self.params['sessionname'])

		if self.params['outdir']:
			pass
		else:
			#go down one directory from img path i.e. remove 'rawdata'
			outdir = os.path.split(self.params['imgdir'])[0]
			#change leginon to appion
			outdir = re.sub('leginon','appion',outdir)
			#add the function name
			if self.processdirname is not None:
				self.params['outdir'] = os.path.join(outdir, self.processdirname)
			else:
				self.params['outdir'] = os.path.join(outdir, self.functionname)

		if self.params['runid'] is None:
			apDisplay.printError("please enter a runid, example: 'runid=run1'")
		self.params['rundir'] = os.path.join(self.params['outdir'], self.params['runid'])
		apDisplay.printMsg("RUNDIR:\t "+self.params['rundir'])

		self.params['doneDictName'] = os.path.join(self.params['rundir'] , "."+self.functionname+"donedict")

	def _shuffleTree(self, tree):
		oldtree = tree
		newtree = []
		while len(oldtree) > 0:
			j = int(len(oldtree)*random.random())
			newtree.append(oldtree[j])
			del oldtree[j]
		return newtree

	def _writeFunctionLog(self, args):
		self.params['functionLog'] = os.path.join(self.params['rundir'], self.functionname+".log")
		apParam.writeFunctionLog(args, logfile=self.params['functionLog'])

	def _setRunAndParameters(self,params):
		if params['commit'] is True:
			rundata = self.insertFunctionRun()
			self.insertPreLoopFunctionRun(rundata,params)
		
		else:
			rundata = self.insertFunctionRun()
			self.insertPreLoopFunctionRun(rundata,self.defaultparams)
		self.rundata = rundata
	
	def _writeDataToDB(self,idata):
		if idata is None:
			return
		for q in idata:
			q.insert()
		return
		
	def _writeDataToFile(self,idata,resultkeys,path,imgname, filename):
		"""
		This is used to write a list of db data that normally goes into thedatabase
		"""
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
				if infokey == 'image':
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
			if 'commit' in self.donedict:
				if self.donedict['commit'] is True and self.params['commit'] is not True:
					apDisplay.printError("Commit flag was enabled and is now disabled, create a new runid")
 				elif self.donedict['commit'] != self.params['commit']:
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
			self.donedict[imgname] = True
		self.donedict['commit'] = self.params['commit']
		doneDictName = self.params['doneDictName']
		f = open(doneDictName, 'w', 0666)
		cPickle.dump(self.donedict, f)
		f.close()

	def _createDirectory(self, path, warning=True, mode=0777):
		return apParam.createDirectory(path, warning=warning, mode=mode)

	def _getAllImages(self):
		startt = time.time()
		if 'dbimages' in self.params and self.params['dbimages']==True:
			self.imgtree = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		elif 'alldbimages' in self.params and self.params['alldbimages']==True:
			self.imgtree = apDatabase.getAllImagesFromDB(self.params['sessionname'])
		elif 'mrcfileroot' in self.params and len(self.params['mrcfileroot']) > 0:
			self.imgtree = apDatabase.getSpecificImagesFromDB(self.params["mrcfileroot"])
		else:
			print len(self.params['mrcfileroot']), self.params['mrcfileroot']
			print self.params['alldbimages'], self.params['dbimages']
			apDisplay.printError("no files specified")
		self.params['session'] = self.imgtree[0]['session']
		self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		precount = len(self.imgtree)
		apDisplay.printMsg("found "+str(precount)+" in "+apDisplay.timeString(time.time()-startt))

		### REMOVE PROCESSED IMAGES
		apDisplay.printMsg("remove processed images")
		self._removeProcessedImages()

		### SHUFFLE
		if self.params['shuffle'] is True:
			self.imgtree = self._shuffleTree(self.imgtree)
			apDisplay.printMsg("shuffling images")
		else:
			self.imgtree.sort(self._reverseSortImgTree)

		### LIMIT NUMBER
		if self.params['limit'] is not None:
			lim = int(self.params['limit'])
			if len(self.imgtree) > lim:
				apDisplay.printMsg("limiting number of images to "+str(lim))
				self.imgtree = self.imgtree[:lim]
			self.params['nowait'] = True
			
		self.stats['imagecount'] = len(self.imgtree)

	def _reverseSortImgTree(self, a, b):
		if a.dbid > b.dbid:
			return 1
		return -1

	def _alreadyProcessed(self, imgdata):
		""" 
		checks to see if image (imgname) has been done already
		"""
		imgname = imgdata['filename']
		if imgname in self.donedict:
			if not self.stats['lastimageskipped']:
				sys.stderr.write("skipping images\n")
			elif self.stats['skipcount'] % 80 == 0:
				sys.stderr.write(".\n")
			else:
				sys.stderr.write(".")
			self.stats['lastimageskipped'] = True
			self.stats['skipcount'] += 1
			return True
		else:
			self.stats['waittime'] = 0
			if self.stats['lastimageskipped']:
				apDisplay.printMsg("\nskipped"+str(self.stats['skipcount'])+" images so far")
			self.stats['lastimageskipped']=False
			return False
		return False

	def _startLoop(self, imgdata):
		"""
		initilizes several parameters for a new image
		and checks if it is okay to start processing image
		"""
		#calc images left
		self.stats['imagesleft'] = self.stats['imagecount'] - self.stats['count']

		#only if an image was processed last
		if(self.stats['lastcount'] != self.stats['count']):
			if self.params['background'] is False:
				apDisplay.printColor( "\nStarting image "+str(self.stats['count'])\
					+" ( skip:"+str(self.stats['skipcount'])+", remain:"\
					+str(self.stats['imagesleft'])+" ) file: "\
					+apDisplay.short(imgdata['filename']), "green")
			elif self.stats['count'] % 80 == 0:
				sys.stderr.write("\n")
			self.stats['lastcount'] = self.stats['count']
			self._checkMemLeak()

		# get the next image pixel size:
		self.params['apix'] = apDatabase.getPixelSize(imgdata)
		if self.params['apix'] != None and ('diam' in self.params and self.params['diam'] > 0):
			self.params['pixdiam']    = self.params['diam']/self.params['apix']
			self.params['binpixdiam'] = self.params['diam']/self.params['apix']/float(self.params['bin'])
		
		# skip if image doesn't exist:
		imgpath = os.path.join(self.params['imgdir'], imgdata['filename']+'.mrc')
		if not os.path.isfile(imgpath):
			apDisplay.printWarning(imgpath+" not found, skipping")
			return False
		
		# check to see if image has already been processed

		if imgdata['filename'] in self.donedict:
			return False
		
		self.stats['startloop'] = time.time()
		self.stats['waittime'] = 0
		
		if self.reprocessImage(imgdata) is True:
			if self.params['background'] is True:
				sys.stderr.write(",")
			else:
				"""apDisplay.printMsg("reprocessing "+apDisplay.shortenImageName(imgdata['filename']))"""
		else:
			if self.params['background'] is True:
				sys.stderr.write(".")
			else:
				"""apDisplay.printMsg("processing "+apDisplay.shortenImageName(imgdata['filename']))"""

		return True

	def _printSummary(self):
		"""
		print summary statistics on last image
		"""
		### COP OUT
		if self.params['background'] is True:
			self.stats['count'] += 1
			return

		### THIS NEEDS TO BECOME MUCH MORE GENERAL, e.g. Peaks
		tdiff = time.time()-self.stats['startloop']
		if not self.params['continue'] or tdiff > 0.1:
			count = self.stats['count']
			#if(count != self.stats['lastcount']):
			if(self.params['method'] != None):
				print "\n\tSUMMARY: using", self.params['method'], "method for",\
					self.functionname
			else:
				print "\n\tSUMMARY:"
			self._printLine()
			if(self.stats['lastpeaks'] != None):
				self.stats['peaksum'] += self.stats['lastpeaks']
				self.stats['peaksumsq'] += self.stats['lastpeaks']**2
				print "\tPEAKS:    \t",self.stats['lastpeaks'],"peaks of",self.stats['peaksum']
				if(count > 1):
					peaksum   = self.stats['peaksum']
					peaksumsq = self.stats['peaksumsq']
					peakstdev = math.sqrt(float(count*peaksumsq - peaksum**2) / float(count*(count-1)))
					peakavg = float(peaksum)/float(count)
					print "\tAVG PEAKS:\t",round(peakavg,1),"+/-",\
						round(peakstdev,1),"peaks"
					lowestpeaks = int((peakavg-peakstdev*0.5)*self.stats['imagesleft'])+peaksum
					highestpeaks = int((peakavg+peakstdev*0.5)*self.stats['imagesleft'])+peaksum
					print "\t(- ESTIMATE:",lowestpeaks,"to",highestpeaks,"total peaks -)"
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
			self.stats['count'] += 1
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
	
		if(self.stats['count'] > 15):
			memlist = self.stats['memlist'][-15:]
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
			rho   = float(n*sumxy - sumx*sumy)/float(stdx*stdy+1e-6)
			slope = float(n*sumxy - sumx*sumy)/float(n*sumxsq - sumx*sumx)
			memleak = rho*slope
			###
			if(self.stats['memleak'] and slope > 0 and memleak > 128 and gain > 256): 
				apDisplay.printError("Memory leak of "+str(round(memleak,2))+"MB")
			elif(memleak > 32):
				self.stats['memleak'] = True
				apDisplay.printWarning("substantial memory leak "+str(round(memleak,2))+"MB")
				print "(",str(n),round(slope,5),round(rho,5),round(gain,2),")"

	def _removeProcessedImages(self):
		startlen = len(self.imgtree)
		donecount = 0
		reproccount = 0
		rejectcount = 0
		tiltcount = 0
		self.stats['skipcount'] = 0
		newimgtree = []
		for imgdata in self.imgtree:
			imgname = imgdata['filename']
			skip = False

			if imgname in self.donedict:
				donecount += 1
				skip = True

			elif self.reprocessImage(imgdata) is False:
				self._writeDoneDict(imgname)
				reproccount += 1
				skip = True

			elif self.params['norejects'] is True and apDatabase.checkInspectDB(imgdata) is False:
				self._writeDoneDict(imgname)
				rejectcount += 1
				skip = True

			elif self.params['bestimages'] is True and apDatabase.checkInspectDB(imgdata) is None:
				self._writeDoneDict(imgname)
				rejectcount += 1
				skip = True

			elif ( self.params['tiltangle'] is not None or self.params['tiltangle'] != 'all' ):
				tiltangle = abs(apDatabase.getTiltAngleDeg(imgdata))
				tiltskip = False
				if (self.params['tiltangle'] == 'notilt' and abs(tiltangle) > 2.0 ):
					tiltskip = True
				elif (self.params['tiltangle'] == 'hightilt' and abs(tiltangle) < 30.0 ):
					tiltskip = True
				elif (self.params['tiltangle'] == 'lowtilt' and abs(tiltangle) > 25.0 ):
					tiltskip = True
				elif (self.params['tiltangle'] == 'minustilt' and tiltangle > 2.0 ):
					tiltskip = True
				elif (self.params['tiltangle'] == 'plustilt' and tiltangle < -2.0 ):
					tiltskip = True
				### skip this tilt?
				if tiltskip is True:
					self._writeDoneDict(imgname)
					tiltcount += 1
					skip = True

			if skip is True:
				if self.stats['skipcount'] == 0:
					sys.stderr.write("skipping images\n")
				elif self.stats['skipcount'] % 80 == 0:
					sys.stderr.write(".\n")
				else:
					sys.stderr.write(".")
				self.stats['skipcount'] += 1
			else:
				newimgtree.append(imgdata)
		if self.stats['skipcount'] > 0:
			self.imgtree = newimgtree
			sys.stderr.write("\n")
			apDisplay.printWarning("skipped "+str(self.stats['skipcount'])+" of "+str(startlen)+" images")
			apDisplay.printMsg("( "+str(reproccount)+" no reprocess "
				+" | "+str(rejectcount)+" rejected "
				+" | "+str(tiltcount)+" wrong tilt "
				+" | "+str(donecount)+" in donedict )")

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
			apDisplay.printMsg("to process them again, remove \'continue\' option and run "+self.functionname+" again.")
			self.stats['skipcount'] = 0

		#SHOULD IT WAIT?
		if self.params['nowait'] is True:
			return False
		if len(self.params["mrcfileroot"]) > 0:
			return False

		#WAIT
		if(self.stats['waittime'] > 120):
			apDisplay.printWarning("waited longer than two hours for new images with no results, so I am quitting")
			return False
		apParam.closeFunctionLog(params=self.params, msg=False, stats=self.stats)
		print "\nAll images processed. Waiting ten minutes for new images (waited",\
			self.stats['waittime'],"min so far)."
		twait0 = time.time()
		for i in range(20):
			time.sleep(20)
			#print a dot every 30 seconds
			sys.stderr.write(".")
		self.stats['waittime'] += round((time.time()-twait0)/60.0,2)
		print ""

		#GET NEW IMAGES
		self._getAllImages()
		return True

	def _finishLoop(self):
		"""
		program has finished print final stats
		"""
		ttotal= time.time()-self.stats["startTime"]
		apParam.closeFunctionLog(params=self.params)
		print apDisplay.color("COMPLETE LOOP:\t"+apDisplay.timeString(ttotal)+\
			" for "+str(self.stats["count"]-1)+" images","green")
		#for i in range(5):
		#	sys.stderr.write("\a")
		#	time.sleep(0.3)
		print "ended ",time.strftime("%a, %d %b %Y %H:%M:%S")
		if self.params['background'] is False:
			print "====================================================="
			print "====================================================="
			print "====================================================="
		print ""

	def _parsePythonPath(self):
		pythonpath = os.environ.get("PYTHONPATH")
		paths = pythonpath.split(":")
		leginons = []
		appions = []
		for p in paths:
			if "appion" in p:
				appions.append(p)
			if "leginon" in p:
				leginons.append(p)
		if len(appions) > 1:
			apDisplay.printWarning("There is more than one appion directory in your PYTHONPATH")
			print appions
		if len(leginons) > 1:
			apDisplay.printWarning("There is more than one leginon directory in your PYTHONPATH")
			print leginons

class BinLoop(AppionLoop):
	def processImage(self, imgdict):
		from pyami import mrc
		outimg = apImage.binImg(imgdict['image'], 2)
		mrc.write(outimg, imgdict['filename']+"_sm.mrc")

if __name__ == '__main__':
	print "__init__"
	imageiter = BinLoop()
	print "run"
	imageiter.run()
