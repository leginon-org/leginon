#!/usr/bin/env python

#builtin
import sys
import os
import time
import math
import random
import cPickle
#appion
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParam
from appionlib import apProject
#leginon
from appionlib import appionScript
from pyami import mem

class AppionTiltSeriesLoop(appionScript.AppionScript):
	#=====================
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		overrides appionScript
		"""
		appionScript.AppionScript.__init__(self)
		self.rundata = {}
		### extra appionLoop functions:
		self._addDefaultParams()
		self.setFunctionResultKeys()
		self._setRunAndParameters()
		#self.specialCreateOutputDirs()
		self._initializeDoneDict()
		self.result_dirs={}

	def createDefaultStats(self):
		super(AppionTiltSeriesLoop,self).createDefaultStats()
		self.stats['lastseries_skipped'] = False
		self.stats['seriesleft'] = 1
	#=====================
	def run(self):
		"""
		processes all series
		"""
		### get tilt series from database
		self._getAllSeries()
		os.chdir(self.params['rundir'])
		self.preLoopFunctions()
		### start the loop
		self.notdone=True
		self.badprocess = False
		self.stats['startloop'] = time.time()
		while self.notdone:
			apDisplay.printColor("\nBeginning Main Loop", "green")
			seriesnum = 0
			while seriesnum < len(self.seriestree) and self.notdone is True:
				self.stats['startseries'] = time.time()
				tiltseriesdata = self.seriestree[seriesnum]
				seriesnum += 1

				### CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if not self._startLoop(tiltseriesdata):
					continue

				### set the pixel size
				imgtree = apDatabase.getImagesFromTiltSeries(tiltseriesdata,False)
				self.params['apix'] = apDatabase.getPixelSize(imgtree[0])
				if not self.params['background']:
					apDisplay.printMsg("Pixel size: "+str(self.params['apix']))

				### START any custom functions HERE:
				results = self.loopProcessTiltSeries(tiltseriesdata)

				### WRITE db data
				if self.badprocess is False:
					if self.params['commit'] is True:
						if not self.params['background']:
							apDisplay.printColor(" ==== Committing data to database ==== ", "blue")
						self.loopCommitToDatabase(tiltseriesdata)
						self.commitResultsToDatabase(tiltseriesdata, results)
					else:
						apDisplay.printWarning("not committing results to database, all data will be lost")
						apDisplay.printMsg("to preserve data start script over and add 'commit' flag")
						self.writeResultsToFiles(tiltseriesdata, results)
				else:
					apDisplay.printWarning("IMAGE FAILED; nothing inserted into database")
					self.badprocess = False
					self.stats['lastpeaks'] = 0

				### FINISH with custom functions
				seriesname = "series%3d" % (tiltseriesdata['number'])
				self._writeDoneDict(seriesname)

				loadavg = os.getloadavg()[0]
				if loadavg > 2.0:
					apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))
					loadsquared = loadavg*loadavg
					time.sleep(loadsquared)
					apDisplay.printMsg("New load average "+str(round(os.getloadavg()[0],2)))

				self._printSummary()

				if self.params['limit'] is not None and self.stats['count'] > self.params['limit']:
					apDisplay.printWarning("reached series limit of "+str(self.params['limit'])+"; now stopping")

				#END LOOP OVER IMAGES
			if self.notdone is True:
				self.notdone = self._waitForMoreSeries(timeout_min=self.params['timeout'])
			#END NOTDONE LOOP
		self.postLoopFunctions()
		self.close()

	#=====================
	def loopProcessTiltSeries(self, tiltseriesdata):
		"""
		setup like this to override things
		"""
		return self.processTiltSeries(tiltseriesdata)

	#=====================
	def loopCommitToDatabase(self, tiltseriesdata):
		"""
		setup like this to override things
		"""
		return self.commitToDatabase(tiltseriesdata)

	#######################################################
	#### ITEMS BELOW SHOULD BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def setupParserOptions(self):
		"""
		put in any additional parser options
		"""
		apDisplay.printError("you did not create a 'setupParserOptions' function in your script")
		raise NotImplementedError()

	#=====================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		apDisplay.printError("you did not create a 'checkConflicts' function in your script")
		raise NotImplementedError()

	#=====================
	def reprocessSeries(self, tiltseriesdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		return None

	#=====================
	def preLoopFunctions(self):
		"""
		do something before starting the loop
		"""
		return

	#=====================
	#def insertPreLoopFunctionRun(self,rundata,params):
	#	"""
	#	put in run and param insertion to db here
	#	"""
	#	return

	#=====================
	def __isShortTiltSeries(self, tiltseriesdata):
		imgtree = apDatabase.getImagesFromTiltSeries(tiltseriesdata,False)
		imagelimit = self.params['imagelimit']
		is_short = len(imgtree) < imagelimit
		if is_short:
			apDisplay.printWarning("Tilt series has less than %d images" % imagelimit)
		return is_short

	def isBadTiltSeries(self, tiltseriesdata):
		"""
		use this function to skip bad tilt series before processing
		return True if bad
		"""
		apDisplay.printError("you did not create a 'isBadTiltSeries' function in your script")
		raise NotImplementedError()

	def processTiltSeries(self, tiltseriesdata):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		apDisplay.printError("you did not create a 'processTiltSeries' function in your script")
		raise NotImplementedError()

	#=====================
	def commitToDatabase(self, tiltseriesdata):
		"""
		put in any additional commit parameters
		"""
		apDisplay.printError("you did not create a 'commitToDatabase' function in your script")
		raise NotImplementedError()

	#=====================
	def setFunctionResultKeys(self):
		self.resultkeys = {}

	#=====================
	def insertFunctionRun(self):
		"""
		put in run and param insertion to db here for insertion during instance initialization if you want to use self.rundata during the run
		"""
		return

	#=====================
	def postLoopFunctions(self):
		"""
		do something after finishing the loop
		"""
		return


	#################################################
	#### ITEMS BELOW ARE NOT USUALLY OVERWRITTEN ####
	#################################################

	#=====================
	def commitResultsToDatabase(self, tiltseriesdata, results):
		if results is not None and len(results) > 0:
			resulttypes = results.keys()
			for resulttype in resulttypes:
				result = results[resulttype]
				self._writeDataToDB(result)

	#=====================
	def writeResultsToFiles(self, tiltseriesdata,results=None):
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
					resultkeys = [resultkeystmp.pop(resultkeys.index('tiltseries'))]
					resultkeys.extend(resultkeystmp)
				path = self.result_dirs[resulttype]
				seriesname = "series%3d" % (tiltseriesdata['number'])
				imgname = "fake_image"
				filename = seriesname +"_"+resulttype+".db"
				self._writeDataToFile(result,resultkeys,path,imgname,filename)

	#=====================
	def checkGlobalConflicts(self):
		"""
		put in any conflicting parameters
		"""
		appionScript.AppionScript.checkGlobalConflicts(self)

		if self.params['runname'] is None:
			apDisplay.printError("please enter a runname, example: 'runname=run1'")
		if self.params['runname'] == 'templates':
			apDisplay.printError("templates is a reserved runname, please use another runname")
		if self.params['runname'] == 'models':
			apDisplay.printError("models is a reserved runname, please use another runname")
		if self.params['rundir']is not None and self.params['runname'] != os.path.basename(self.params['rundir']):
			apDisplay.printError("runname and rundir basename are different: "
				+self.params['runname']+" vs. "+os.path.basename(self.params['rundir']))
		if self.params['mrcnames'] and self.params['preset']:
			apDisplay.printError("preset can not be specified if particular images have been specified")
		if self.params['sessionname'] is None and self.params['mrcnames'] is None:
			apDisplay.printError("please specify an mrc name or session")
		if self.params['sessionname'] is not None and self.params['projectid'] is not None:
			### Check that project and tilt series are in sync
			seriesproject = apProject.getProjectIdFromSessionName(self.params['sessionname'])
			if seriesproject and seriesproject != self.params['projectid']:
				apDisplay.printError("project id and session do not correlate")

	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		appionScript.AppionScript.setupGlobalParserOptions(self)

		### Set usage
		self.parser.set_usage("Usage: %prog --projectid=## --runname=<runname> --session=<session> "
			+" --description='<text>' --commit [options]")
		### Input value options
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("--preset", dest="preset",
			help="Image preset associated with processing run, e.g. --preset=en", metavar="PRESET")
		self.parser.add_option("-m", "--mrclist", dest="mrcnames",
			help="List of mrc files to process, e.g. --mrclist=..003en,..002en,..006en", metavar="MRCNAME")
		self.parser.add_option("--reprocess", dest="reprocess", type="float",
			help="Only process series that pass this reprocess criteria")
		self.parser.add_option("--limit", dest="limit", type="int",
			help="Only process <limit> number of series")

		### True / False options
		self.parser.add_option("--continue", dest="continue", default=True,
			action="store_true", help="Continue processing run from last tilt series")
		self.parser.add_option("--no-continue", dest="continue", default=True,
			action="store_false", help="Do not continue processing run from last series")
		self.parser.add_option("--background", dest="background", default=False,
			action="store_true", help="Run in background mode, i.e. reduce the number of messages printed")
		self.parser.add_option("--no-wait", dest="wait", default=True,
			action="store_false", help="Do not wait for more tilt series after completing loop")
		self.parser.add_option("--timeout", dest="timeout", type="int", default=180,
			help="Waiting time out in minutes")
		self.parser.add_option("--imagelimit", dest="imagelimit", type="int", default=50,
			help="Minimum number of images in tilt for processing")
		self.parser.add_option("--no-rejects", dest="norejects", default=False,
			action="store_true", help="Do not process hidden or rejected images")
		self.parser.add_option("--best-series", dest="bestseries", default=False,
			action="store_true", help="Only process exemplar or keep images")
		self.parser.add_option("--reverse", dest="reverse", default=False,
			action="store_true", help="Process the images from newest to oldest")

	#=====================
	def _addDefaultParams(self):
		### new system, global params
		self.params['functionname'] = self.functionname
		self.params['appiondir'] = apParam.getAppionDirectory()
		### classic methods
		self.params['functionLog']=None
		self.defaultparams = {}

	#=====================
	def _shuffleTree(self, tree):
		random.shuffle(tree)
		return tree

	#=====================
	def _writeFunctionLog(self, args):
		self.params['functionLog'] = os.path.join(self.params['rundir'], self.functionname+".log")
		apParam.writeFunctionLog(args, logfile=self.params['functionLog'])

	#=====================
	def _setRunAndParameters(self):
		rundata = self.insertFunctionRun()
		# replace existing rundata only if it is not empty
		if rundata:
			self.rundata = rundata

	#=====================
	def _writeDataToDB(self,idata):
		if idata is None:
			return
		for q in idata:
			q.insert()
		return

	#=====================
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

	#=====================
	def _initializeDoneDict(self):
		"""
		reads or creates a done dictionary
		"""
		self.donedictfile = os.path.join(self.params['rundir'] , self.functionname+".donedict")
		if os.path.isfile(self.donedictfile) and self.params['continue'] == True:
			### unpickle previously done dictionary
			apDisplay.printMsg("Reading old done dictionary: "+os.path.basename(self.donedictfile))
			f = open(self.donedictfile,'r')
			self.donedict = cPickle.load(f)
			f.close()
			if not 'commit' in self.donedict or self.donedict['commit'] == self.params['commit']:
				### all is well
				apDisplay.printMsg("Found "+str(len(self.donedict))+" done dictionary entries")
				return
			elif self.donedict['commit'] is True and self.params['commit'] is not True:
				### die
				apDisplay.printError("Commit flag was enabled and is now disabled, create a new runname")
			else:
				### set up fresh dictionary
				apDisplay.printWarning("'--commit' flag was changed, creating new done dictionary")

		### set up fresh dictionary
		self.donedict = {}
		self.donedict['commit'] = self.params['commit']
		apDisplay.printMsg("Creating new done dictionary: "+os.path.basename(self.donedictfile))

		### write donedict to file
		f = open(self.donedictfile, 'w', 0666)
		cPickle.dump(self.donedict, f)
		f.close()
		return

	#=====================
	def _reloadDoneDict(self):
		"""
		reloads done dictionary
		"""
		f = open(self.donedictfile,'r')
		self.donedict = cPickle.load(f)
		f.close()

	#=====================
	def _writeDoneDict(self, seriesname=None):
		"""
		write finished series (seriesname) to done dictionary
		"""
		### reload donedict from file just in case two runs are running
		f = open(self.donedictfile,'r')
		self.donedict = cPickle.load(f)
		f.close()

		### set new parameters
		if seriesname != None:
			self.donedict[seriesname] = True
		self.donedict['commit'] = self.params['commit']

		### write donedict to file
		f = open(self.donedictfile, 'w', 0666)
		cPickle.dump(self.donedict, f)
		f.close()

	#=====================
	def _getAllSeries(self):
		startt = time.time()
		self.seriestree = []
		if self.params['mrcnames'] is not None:
			mrcfileroot = self.params['mrcnames'].split(",")
			if self.params['sessionname'] is not None:
				images = apDatabase.getSpecificImagesFromSession(mrcfileroot, self.params['sessionname'])
			else:
				images = apDatabase.getSpecificImagesFromDB(mrcfileroot)
		elif self.params['sessionname'] is not None:
			if self.params['preset'] is not None:
				images = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
			else:
				self.seriestree = apDatabase.getAllTiltSeriesFromSessionName(self.params['sessionname'])
		else:
			if self.params['mrcnames'] is not None:
				apDisplay.printMsg("MRC List: "+str(len(self.params['mrcnames']))+" : "+str(self.params['mrcnames']))
			apDisplay.printMsg("Session: "+str(self.params['sessionname'])+" : "+str(self.params['preset']))
			apDisplay.printError("no files specified")
		# Only use finished tilt series
		if len(self.seriestree) > 0:
			indices_to_pop = []
			for tiltseriesdata in self.seriestree:
				if not apDatabase.getTiltSeriesDoneStatus(tiltseriesdata):
					indices_to_pop.append(self.seriestree.index(tiltseriesdata))
			indices_to_pop.sort()
			indices_to_pop.reverse()
			for index in indices_to_pop:	
				self.seriestree.pop(index)
		else:
			for image in images:
				tiltseriesdata = image['tilt series']
				if tiltseriesdata and tiltseriesdata not in self.seriestree and apDatabase.getTiltSeriesDoneStatus(tiltseriesdata):
					self.seriestree.append(tiltseriesdata)
		precount = len(self.seriestree)
		apDisplay.printMsg("Found "+str(precount)+" tilt series in "+apDisplay.timeString(time.time()-startt))

		### REMOVE PROCESSED IMAGES
		apDisplay.printMsg("Remove processed series")
		self._removeProcessedSeries()

		### SET SERIES ORDER
		if self.params['reverse'] is True:
			apDisplay.printMsg("Process series new to old")
		else:
			# by default series are new to old
			apDisplay.printMsg("Process series old to new")
			self.seriestree.sort(self._reverseSortSeriesTree)

		### LIMIT NUMBER
		if self.params['limit'] is not None:
			lim = self.params['limit']
			if len(self.seriestree) > lim:
				apDisplay.printMsg("Limiting number of series to "+str(lim))
				self.seriestree = self.seriestree[:lim]
		self.stats['seriescount'] = len(self.seriestree)

	#=====================
	def _reverseSortSeriesTree(self, a, b):
		if a.dbid > b.dbid:
			return 1
		return -1

	#=====================
	def _alreadyProcessed(self, tiltseriesdata):
		"""
		checks to see if image (seriesname) has been done already
		"""
		seriesname = "series%3d" % (tiltseriesdata['number'])
		self._reloadDoneDict()
		if seriesname in self.donedict:
			if not self.stats['lastseries_skipped']:
				sys.stderr.write("skipping series\n")
			elif self.stats['skipcount'] % 80 == 0:
				sys.stderr.write(".\n")
			else:
				sys.stderr.write(".")
			self.stats['lastseries_skipped'] = True
			self.stats['skipcount'] += 1
			self.stats['count'] += 1
			return True
		else:
			self.stats['waittime'] = 0
			if self.stats['lastseries_skipped']:
				apDisplay.printMsg("\nskipped"+str(self.stats['skipcount'])+" series so far")
			self.stats['lastseries_skipped']=False
			return False
		return False

	#=====================
	def _startLoop(self, tiltseriesdata):
		"""
		initilizes several parameters for a new series
		and checks if it is okay to start processing series
		"""
		#calc series left
		self.stats['seriesleft'] = self.stats['seriescount'] - self.stats['count']

		if self.params['background'] is False:
			apDisplay.printColor( "\nStarting series %d ( skip:%d, remain:%d ) id:%d"
				%(tiltseriesdata['number'], self.stats['skipcount'], self.stats['seriesleft'], 
				tiltseriesdata.dbid,),
				"green")
		#only if a series was processed last
		if(self.stats['lastcount'] != self.stats['count']):
			sys.stderr.write("\n")
			self.stats['lastcount'] = self.stats['count']
			self._checkMemLeak()
		# skip if last image belong to the series doesn't exist:
		imgtree = apDatabase.getImagesFromTiltSeries(tiltseriesdata,False)
		imgpath = os.path.join(tiltseriesdata['session']['image path'], imgtree[0]['filename']+'.mrc')
		if not os.path.isfile(imgpath):
			apDisplay.printWarning(imgpath+" not found, skipping")
			return False

		# skip if there are some problem with the series
		if self.__isShortTiltSeries(tiltseriesdata) or self.isBadTiltSeries(tiltseriesdata):
			apDisplay.printWarning("Series %d is not good enough for processing, skipping" % (tiltseriesdata['number']))
			seriesname = "series%3d" % (tiltseriesdata['number'])
			self._writeDoneDict(seriesname)
			self.stats['count'] += 1
			return False

		# check to see if series has already been processed
		if self._alreadyProcessed(tiltseriesdata):
			
			return False

		self.stats['waittime'] = 0

		if self.reprocessSeries(tiltseriesdata) is True:
			if self.params['background'] is True:
				sys.stderr.write(",")
			else:
				"""apDisplay.printMsg("reprocessing series %d" % (tiltseriesdata['number']))"""
		else:
			if self.params['background'] is True:
				sys.stderr.write(".")
			else:
				"""apDisplay.printMsg("processing series %d" % (tiltseriesdata['number']))"""

		return True

	#=====================
	def _printSummary(self):
		"""
		print summary statistics on last image
		"""
		### COP OUT
		if self.params['background'] is True:
			self.stats['count'] += 1
			return

		### THIS NEEDS TO BECOME MUCH MORE GENERAL, e.g. Peaks
		tdiff = time.time()-self.stats['startseries']
		if not self.params['continue'] or tdiff > 0.1:
			count = self.stats['count']
			#if(count != self.stats['lastcount']):
			sys.stderr.write("\n\tSUMMARY: "+self.functionname+"\n")
			self._printLine()
			sys.stderr.write("\tTIME:     \t"+apDisplay.timeString(tdiff)+"\n")
			self.stats['timesum'] = self.stats['timesum'] + tdiff
			self.stats['timesumsq'] = self.stats['timesumsq'] + (tdiff**2)
			timesum = self.stats['timesum']
			timesumsq = self.stats['timesumsq']
			if(count > 1):
				timeavg = float(timesum)/float(count)
				timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
				timeremain = (float(timeavg)+float(timestdev))*self.stats['seriesleft']
				sys.stderr.write("\tAVG TIME: \t"+apDisplay.timeString(timeavg,timestdev)+"\n")
				#print "\t(- TOTAL:",apDisplay.timeString(timesum)," -)"
				if(self.stats['seriesleft'] > 0):
					sys.stderr.write("\t(- REMAINING TIME: "+apDisplay.timeString(timeremain)+" for "
						+str(self.stats['seriesleft'])+" series -)\n")
			#print "\tMEM: ",(mem.active()-startmem)/1024,"M (",(mem.active()-startmem)/(1024*count),"M)"
			self.stats['count'] += 1
			self._printLine()

	#=====================
	def _checkMemLeak(self):
		"""
		unnecessary code for determining if the program is eating memory over time
		"""
		### Memory leak code:
		#self.stats['memlist'].append(mem.mySize()/1024)
		self.stats['memlist'].append(mem.active())
		memfree = mem.free()
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
			if(self.stats['memleak'] > 3 and slope > 20 and memleak > 512 and gain > 2048):
				apDisplay.printError("Memory leak of "+str(round(memleak,2))+"MB")
			elif(memleak > 32):
				self.stats['memleak'] += 1
				apDisplay.printWarning("substantial memory leak "+str(round(memleak,2))+"MB")
				print "(",str(n),round(slope,5),round(rho,5),round(gain,2),")"

	#=====================
	def _removeProcessedSeries(self):
		startlen = len(self.seriestree)
		donecount = 0
		reproccount = 0
		rejectcount = 0
		tiltcount = 0
		self.stats['skipcount'] = 0
		newseriestree = []
		for tiltseriesdata in self.seriestree:
			seriesname = "series%3d" % (tiltseriesdata['number'])
			skip = False

			if seriesname in self.donedict:
				donecount += 1
				skip = True

			elif self.reprocessSeries(tiltseriesdata) is False:
				self._writeDoneDict(seriesname)
				reproccount += 1
				skip = True

			# image not done or reprocessing allowed
			if skip is False:
				# will need to implement some way to reject tilt seriese manually
				# similar to images in ViewerImageStatus table
				status=None

				if self.params['norejects'] is True and status is False:
					self._writeDoneDict(seriesname)
					rejectcount += 1
					skip = True
			
				elif self.params['bestseries'] is True and status is not True:
					self._writeDoneDict(seriesname)
					rejectcount += 1
					skip = True

			if skip is True:
				if self.stats['skipcount'] == 0:
					sys.stderr.write("skipping series\n")
				elif self.stats['skipcount'] % 80 == 0:
					sys.stderr.write(".\n")
				else:
					sys.stderr.write(".")
				self.stats['skipcount'] += 1
			else:
				newseriestree.append(tiltseriesdata)
		if self.stats['skipcount'] > 0:
			self.seriestree = newseriestree
			sys.stderr.write("\n")
			apDisplay.printWarning("skipped "+str(self.stats['skipcount'])+" of "+str(startlen)+" series")
			apDisplay.printMsg("[[ "+str(reproccount)+" no reprocess "
				+" | "+str(rejectcount)+" rejected "
				+" | "+str(tiltcount)+" wrong tilt "
				+" | "+str(donecount)+" in donedict ]]")

	#=====================
	def _printLine(self):
		sys.stderr.write("\t------------------------------------------\n")

	#=====================
	def _waitForMoreSeries(self,timeout_min=180):
		"""
		pauses wait_time mins and then checks for more series to process
		"""
		### SKIP MESSAGE
		if(self.stats['skipcount'] > 0):
			apDisplay.printWarning("Series already processed and were therefore skipped (total "+str(self.stats['skipcount'])+" skipped).")
			apDisplay.printMsg("to process them again, remove \'continue\' option and run "+self.functionname+" again.")
			self.stats['skipcount'] = 0

		### SHOULD IT WAIT?
		if self.params['wait'] is False:
			return False
		if self.params["mrcnames"] is not None:
			return False
		if self.params["limit"] is not None:
			return False

		### CHECK FOR IMAGES, IF MORE THAN 10 JUST GO AHEAD
		apDisplay.printMsg("Finished all series, checking for more\n")
		self._getAllSeries()
		### reset counts
		self.stats['seriescount'] = len(self.seriestree)
		self.stats['seriesleft'] = self.stats['seriescount'] - self.stats['count']
		if self.stats['seriesleft'] > 0:
			return True

		### WAIT
		timeout_sec = timeout_min * 60
		# self.stats['waittime'] is in minutes
		if(self.stats['waittime'] > timeout_min):
			timeout_hr = timeout_min / 60.0
			apDisplay.printWarning("waited longer than %.1f hours for new series with no results, so I am quitting" % timeout_hr)
			return False
		apParam.closeFunctionLog(functionname=self.functionname, logfile=self.logfile, msg=False, stats=self.stats)
		twait0 = time.time()
		# Wait at least 30 sec and at most 5 % of timeout before checking for new tilt series
		dot_wait = 30
		timecheck_sec = max(timeout_sec/20,dot_wait*2)
		wait_step = max(1,int(round(timecheck_sec * 1.0 / dot_wait)))
		sys.stderr.write("\nAll Series processed. Waiting %.1f minutes for new Series (waited %.1f min so far" % (timecheck_sec / 60.0, self.stats['waittime']))
		for i in range(wait_step):
			time.sleep(dot_wait)
			#print a dot every 30 seconds
			sys.stderr.write(".")
		self.stats['waittime'] += round((time.time()-twait0)/60.0,2)
		sys.stderr.write("\n")

		### GET NEW IMAGES
		self._getAllSeries()
		### reset counts
		self.stats['seriescount'] = len(self.seriestree)
		self.stats['seriesleft'] = self.stats['seriescount'] - self.stats['count']
		return True

	#=====================
	def close(self):
		"""
		program has finished print final stats
		"""
		ttotal = time.time() - self.stats['startloop'] - self.stats['waittime']
		apDisplay.printColor("COMPLETE LOOP:\t"+apDisplay.timeString(ttotal)+
			" for "+str(self.stats["count"]-1)+" series","green")
		appionScript.AppionScript.close(self)


#=====================
#===Example Script====
#=====================
class PrintLoop(AppionTiltSeriesLoop):
	def setupParserOptions(self):
		"""
		See appion/bin/appionScript.py.template for what you may add in this function
		"""
		return

	def checkConflicts(self):
		"""
		See appion/bin/appionScript.py.template for what you may add in this function
		"""
		return
	def commitToDatabase(self, tiltseriesdata):
		"""
		See appion/bin/appionScript.py.template for what you may add in this function
		"""
		return
	def isBadTiltSeries(self, tiltseriesdata):
		"""
		You must define how you would like to reject bad tilt series.
		a simple return will let everything pass.
		"""
		return False

	def processTiltSeries(self, tiltseriesdata):
		"""
		Call your processing command from here per tilt series
		Here we just print out the filenames of the images in the tilt series
		"""
		print "Tiltseries %d -------------------" % tiltseriesdata['number']
		imgtree = apDatabase.getImagesFromTiltSeries(tiltseriesdata,True)
		for imagedata in imgtree:
			print imagedata['filename']
		
#=====================
if __name__ == '__main__':
	print "__init__"
	imageiter = PrintLoop()
	print "run"
	imageiter.run()
