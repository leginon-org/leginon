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
import apParam
#leginon
import appionScript
from pyami import mem
import leginondata

class AppionLoop(appionScript.AppionScript):
	#=====================
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		overrides appionScript
		"""
		appionScript.AppionScript.__init__(self, True)
		### extra appionLoop functions:
		self._addDefaultParams()
		self.setFunctionResultKeys()
		self._setRunAndParameters()
		#self.specialCreateOutputDirs()
		self._readDoneDict()
		self.result_dirs={}


	#=====================
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
				results = self.loopProcessImage(imgdata)

				### WRITE db data
				if self.params['badprocess'] is False:
					if self.params['commit'] is True:
						apDisplay.printColor(" ==== Committing data to database ==== ", "blue")
						self.loopCommitToDatabase(imgdata)
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
		appionScript.AppionScript.close(self)

	#=====================
	def loopProcessImage(self, imgdata):
		"""
		setup like this to override things
		"""
		return self.processImage(imgdata)

	#=====================
	def loopCommitToDatabase(self, imgdata):
		"""
		setup like this to override things
		"""
		return self.commitToDatabase(imgdata)

	#######################################################
	#### ITEMS BELOW SHOULD BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def setRunDir(self):
		if self.params['sessionname'] is not None:
			#auto set the output directory
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			path = os.path.abspath(sessiondata['image path'])
			path = re.sub("leginon","appion",path)
			path = re.sub("/rawdata","",path)
			path = os.path.join(path, self.processdirname, self.params['runname'])
			self.params['rundir'] = path

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
	def reprocessImage(self, imgdata):
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
	def processImage(self, imgdata):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		apDisplay.printError("you did not create a 'processImage' function in your script")
		raise NotImplementedError()

	#=====================
	def commitToDatabase(self, imgdata):
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
		put in run and param insertion to db here
		"""
		self.rundata = {}
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
	def commitResultsToDatabase(self, imgdata, results):
		if results is not None and len(results) > 0:
			resulttypes = results.keys()
			for resulttype in resulttypes:
				result = results[resulttype]
				self._writeDataToDB(result)

	#=====================
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
		if self.params['mrcnames'] and self.params['preset']:
			apDisplay.printError("preset can not be specified if particular images have been specified")
		if self.params['sessionname'] is None and self.params['mrcnames'] is None:
			apDisplay.printError("please specify an mrc name or session")

	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		appionScript.AppionScript.setupGlobalParserOptions(self)

		self.tiltoptions = ["notilt", "hightilt", "lowtilt", "minustilt", "plustilt", "all"]

		### Set usage
		self.parser.set_usage("Usage: %prog --projectid=## --runname=<runname> --session=<session> "
			+"--preset=<preset> --description='<text>' --commit [options]")
		### Input value options
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("--preset", dest="preset",
			help="Image preset associated with processing run, e.g. --preset=en", metavar="PRESET")
		self.parser.add_option("-m", "--mrclist", dest="mrcnames",
			help="List of mrc files to process, e.g. --mrclist=..003en,..002en,..006en", metavar="MRCNAME")
		self.parser.add_option("--reprocess", dest="reprocess", type="float",
			help="Only process images that pass this reprocess criteria")
		self.parser.add_option("--limit", dest="limit", type="int",
			help="Only process <limit> number of images")
		self.parser.add_option("--tiltangle", dest="tiltangle", default="all",
			help="Only process images with specific tilt angles, options: "+str(self.tiltoptions))
		### True / False options
		self.parser.add_option("--continue", dest="continue", default=True,
			action="store_true", help="Continue processing run from last image")
		self.parser.add_option("--no-continue", dest="continue", default=True,
			action="store_false", help="Do not continue processing run from last image")
		self.parser.add_option("--background", dest="background", default=False,
			action="store_true", help="Run in background mode, i.e. reduce the number of messages printed")
		self.parser.add_option("--uncorrected", dest="uncorrected", default=False,
			action="store_true", help="Assume images are not bright/dark field corrected and correct them")
		self.parser.add_option("--no-wait", dest="wait", default=True,
			action="store_false", help="Do not wait for more images after completing loop")
		self.parser.add_option("--no-rejects", dest="norejects", default=False,
			action="store_true", help="Do not process hidden or rejected images")
		self.parser.add_option("--best-images", dest="bestimages", default=False,
			action="store_true", help="Only process exemplar or keep images")
		self.parser.add_option("--shuffle", dest="shuffle", default=False,
			action="store_true", help="Shuffle the images before processing, i.e. process images out of order")
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
	def _parseCommandLineInput(self, args):
		if self.params['rundir']:
			pass
		else:
			#go down one directory from img path i.e. remove 'rawdata'
			rundir = os.path.split(self.params['imgdir'])[0]
			#change leginon to appion
			rundir = re.sub('leginon','appion',rundir)
			#add the function name
			if self.processdirname is not None:
				self.params['rundir'] = os.path.join(rundir, self.processdirname)
			else:
				self.params['rundir'] = os.path.join(rundir, self.functionname)

		if self.params['runname'] is None:
			apDisplay.printError("please enter a runname, example: 'runname=run1'")
		self.params['rundir'] = os.path.join(self.params['rundir'], self.params['runname'])
		apDisplay.printMsg("RUNDIR:\t "+self.params['rundir'])


	#=====================
	def _shuffleTree(self, tree):
		oldtree = tree
		newtree = []
		while len(oldtree) > 0:
			j = int(len(oldtree)*random.random())
			newtree.append(oldtree[j])
			del oldtree[j]
		return newtree

	#=====================
	def _writeFunctionLog(self, args):
		self.params['functionLog'] = os.path.join(self.params['rundir'], self.functionname+".log")
		apParam.writeFunctionLog(args, logfile=self.params['functionLog'])

	#=====================
	def _setRunAndParameters(self):
		rundata = self.insertFunctionRun()
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
	def _readDoneDict(self):
		"""
		reads or creates a done dictionary
		"""
		self.params['doneDictName'] = os.path.join(self.params['rundir'] , self.functionname+".donedict")
		doneDictName = self.params['doneDictName']
		if os.path.isfile(doneDictName) and self.params['continue'] == True:
			apDisplay.printMsg("reading old done dictionary:\n"+doneDictName)
			# unpickle previously modified dictionary
			f = open(doneDictName,'r')
			self.donedict = cPickle.load(f)
			f.close()
			if 'commit' in self.donedict:
				if self.donedict['commit'] is True and self.params['commit'] is not True:
					apDisplay.printError("Commit flag was enabled and is now disabled, create a new runname")
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

	#=====================
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

	#=====================
	def _getAllImages(self):
		startt = time.time()
		if self.params['mrcnames'] is not None:
			mrcfileroot = self.params['mrcnames'].split(",")
			self.imgtree = apDatabase.getSpecificImagesFromDB(mrcfileroot)
		elif self.params['sessionname'] is not None:
			if self.params['preset'] is not None:
				self.imgtree = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
			else:
				self.imgtree = apDatabase.getAllImagesFromDB(self.params['sessionname'])
		else:
			if self.params['mrcnames'] is not None:
				apDisplay.printMsg("MRC List: "+str(len(self.params['mrcnames']))+" : "+str(self.params['mrcnames']))
			apDisplay.printMsg("Session: "+str(self.params['sessionname'])+" : "+str(self.params['preset']))
			apDisplay.printError("no files specified")
		precount = len(self.imgtree)
		apDisplay.printMsg("found "+str(precount)+" in "+apDisplay.timeString(time.time()-startt))

		### REMOVE PROCESSED IMAGES
		apDisplay.printMsg("remove processed images")
		self._removeProcessedImages()

		### SET IMAGE ORDER
		if self.params['shuffle'] is True:
			self.imgtree = self._shuffleTree(self.imgtree)
			apDisplay.printMsg("process images shuffled")
		elif self.params['reverse'] is True:
			apDisplay.printMsg("process images new to old")
		else:
			# by default images are new to old
			apDisplay.printMsg("process images old to new")
			self.imgtree.sort(self._reverseSortImgTree)

		### LIMIT NUMBER
		if self.params['limit'] is not None:
			lim = self.params['limit']
			if len(self.imgtree) > lim:
				apDisplay.printMsg("limiting number of images to "+str(lim))
				self.imgtree = self.imgtree[:lim]

		self.stats['imagecount'] = len(self.imgtree)

	#=====================
	def _reverseSortImgTree(self, a, b):
		if a.dbid > b.dbid:
			return 1
		return -1

	#=====================
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

	#=====================
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

		# skip if image doesn't exist:
		imgpath = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')
		if not os.path.isfile(imgpath):
			apDisplay.printWarning(imgpath+" not found, skipping")
			return False

		# check to see if image has already been processed
		if self._alreadyProcessed(imgdata):
			return False
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
		tdiff = time.time()-self.stats['startloop']
		if not self.params['continue'] or tdiff > 0.1:
			count = self.stats['count']
			#if(count != self.stats['lastcount']):
			print "\n\tSUMMARY: "+self.functionname
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

	#=====================
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

	#=====================
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

			elif self.params['norejects'] is True and apDatabase.getImgCompleteStatus(imgdata) is False:
				self._writeDoneDict(imgname)
				rejectcount += 1
				skip = True

			elif self.params['bestimages'] is True and apDatabase.getImgCompleteStatus(imgdata) is not True:
				self._writeDoneDict(imgname)
				rejectcount += 1
				skip = True

			elif ( self.params['tiltangle'] is not None or self.params['tiltangle'] != 'all' ):
				tiltangle = abs(apDatabase.getTiltAngleDeg(imgdata))
				tiltskip = False
				if (self.params['tiltangle'] == 'notilt' and abs(tiltangle) < 3.0 ):
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

	#=====================
	def _printLine(self):
		print "\t------------------------------------------"

	#=====================
	def _waitForMoreImages(self):
		"""
		pauses 10 mins and then checks for more images to process
		"""
		### SKIP MESSAGE
		if(self.stats['skipcount'] > 0):
			apDisplay.printWarning("Images already processed and were therefore skipped (total "+\
				str(self.stats['skipcount'])+" skipped).")
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
		apDisplay.printMsg("\nfinished all images, checking for more")
		self._getAllImages()
		### reset counts
		self.stats['imagecount'] = len(self.imgtree)
		self.stats['imagesleft'] = self.stats['imagecount'] - self.stats['count']
		if self.stats['imagesleft'] > 10:
			return True

		### WAIT
		if(self.stats['waittime'] > 180):
			apDisplay.printWarning("waited longer than three hours for new images with no results, so I am quitting")
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

		### GET NEW IMAGES
		self._getAllImages()
		### reset counts
		self.stats['imagecount'] = len(self.imgtree)
		self.stats['imagesleft'] = self.stats['imagecount'] - self.stats['count']
		return True

	#=====================
	def close(self):
		"""
		program has finished print final stats
		"""
		apDisplay.printColor("COMPLETE LOOP:\t"+apDisplay.timeString(ttotal)+
			" for "+str(self.stats["count"]-1)+" images","green")
		appionScript.AppionScript.close(self)


#=====================
#=====================
#=====================
class BinLoop(AppionLoop):
	def setupParserOptions(self):
		return
	def checkConflicts(self):
		return
	def commitToDatabase(self):
		return
	def processImage(self, imgdict):
		from pyami import mrc
		outimg = apImage.binImg(imgdict['image'], 2)
		mrc.write(outimg, imgdict['filename']+"_sm.mrc")

#=====================
if __name__ == '__main__':
	print "__init__"
	imageiter = BinLoop()
	print "run"
	imageiter.run()
