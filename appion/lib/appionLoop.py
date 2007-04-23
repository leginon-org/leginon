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
import apXml
#leginon
try:
	import mem
except:
	apDisplay.printError("Please load 'usepythoncvs' for CVS leginon code,"
		+" which includes 'mem.py'")
			
class AppionLoop(object):
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		"""
		#set the name of the function; needed for param setup
		self.setFunctionName()

		### setup default params: output directory, etc.
		self.createDefaultParams()

		### setup default stats: timing variables, etc.
		self.createDefaultStats()

		### parse command line options: diam, apix, etc.
		self.parseCommandLineInput(sys.argv)

		### create output directories
		#self.createOutputDirs()

		### write log of command line options
		self.writeFunctionLog(sys.argv)

		### read/create dictionary to keep track of processed images
		#self.readDoneDict()

	def run(self):
		"""
		processes all images
		"""
		### get images from database
		self.getAllImages()
		#self.removeProcessedImages()
		### start the loop
		notdone=True
		while notdone:
			for imgdict in self.imgtree:
				#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
				if self.alreadyProcessed(imgdict):
					continue
 
				### START any custom functions HERE:
				self.processImage(imgdict)
				### FINISH with custom functions
 
	 			self.writeDoneDict(imgdict['filename'])
				self.printSummary()
				#END LOOP OVER IMAGES
			notdone = self.waitForMoreImages()
			#END NOTDONE LOOP
		self.finishLoop()

	def setFunctionName(self, arg=None):
		"""
		Sets the name of the function
		by default takes the first variable in the argument
		"""
		if arg == None:
			arg = sys.argv[0]
		self.functionname = os.path.basename(arg.strip())
		#remove all letters after a dot, e.g. "func.py" -> "func"
		self.functionname = re.sub("\.[a-zA-Z]+$","",self.functionname)

	def reprocessImage(self, imgdict):
		"""
		Returns True if an image should be reprocess
		e.g. a confidence less than 80%
		"""
		return False

	def processImage(self, imgdict):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		raise NotImplementedError()

	def specialParamConflicts():
		"""
		put in any additional conflicting parameters
		"""
		return

	#################################################
	#### ITEMS BELOW ARE NOT USUALLY OVERWRITTEN ####
	#################################################

	def checkParamConflicts():
		"""
		put in any conflicting parameters
		"""
		return

	def _createDefaultParams(self):
		self.params = {}
		self.params['functionname'] = self.functionname

		self.params['rundir'] = "."
		self.params['appionhome'] = os.environ.get('APPIONHOME')
		print "APPION home defined as:",self.params['appionhome']
		self.params['method'] = "updated"
		self.params['xmlglobfile'] = os.path.join(self.params['appionhome'],"xml","allAppion.xml")
		print "XML global parameter file:",self.params['xmlglobfile']
		self.params['xmlfuncfile'] = os.path.join(self.params['appionhome'],"xml",self.functionname+".xml")
		print "XML function parameter file:",self.params['xmlfuncfile']
		self.params = apXml.readTwoXmlFiles(self.params['xmlglobfile'], self.params['xmlfuncfile'])

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
		self.params['functionname'] = self.functionname
		#self.checkParamConflicts()

	def _writeFunctionLog(self, args):
		file = os.path.join(self.params['rundir'],self.functionname+".log")
		out=""
		for arg in args:
			out += arg+" "
		f=open(file,'aw')
		f.write(out)
		f.write("\n")
		f.close()

	def _readDoneDict():
		"""
		reads or creates a done dictionary
		"""
		doneDictName = self.params['doneDictName']
		if os.path.isfile(doneDictName):
			print " ... reading old done dictionary:\n\t",doneDictName
			# unpickle previously modified dictionary
			f = open(doneDictName,'r')
			self.donedict = cPickle.load(f)
			f.close()
			print " ... found",len(donedict),"dictionary entries"
		else:
			#set up dictionary
			self.donedict = {}
			print " ... creating new done dictionary:\n\t",doneDictName

	def _writeDoneDict(self, imgname=None):
		"""
		write finished image (imgname) to done dictionary
		"""
		if imgname != None:
			self.donedict[imgname]=True
		doneDictName = self.params['doneDictName']
		f = open(doneDictName, 'w', 0666)
		cPickle.dump(self.donedict, f)
		f.close()

	def _createDirectory(path, mode=0777):
		if os.path.exists(path):
			apDisplay.printWarning("directory \'"+path+"\' already exists.")
			return False
		os.makedirs(path,mode)
		return True

	def _getAllImages(self):
		#import apDatabase
		#self.imgtree = getAllImages(self.stats, self.params)
		#import operator
		#self.imgtree.sort(key=operator.itemgetter('imgname'))
		import data
		import dbdatakeeper
		p = data.PresetData(name='en')
		q = data.AcquisitionImageData(preset = p)
		legdb = dbdatakeeper.DBDataKeeper()
		self.imgtree = legdb.query(q, readimages=False, results=50)
		#print 'LEN', len(self.imgtree)

	def _alreadyProcessed(self, imgname):
		""" 
		checks to see if image (imgname) has been done already
		"""
		
		if self.params["continue"]:
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

	def _printSummary(self):
		"""
		print summary statistics on last image
		"""
		### THIS NEEDS TO BECOME MUCH MORE GENERAL, e.g. Peaks
		tdiff = time.time()-self.stats['beginLoopTime']
		if not self.params["continue"] or tdiff > 0.3:
			count = self.stats['count']
			#if(count != self.stats['lastcount']):
			if(self.params['method'] != None):
				print "\n\tSUMMARY: using", self.params['method'], "method for",\
					self.params['function']
			else:
				print "\n\tSUMMARY:"
			_printLine()
			if(self.stats['lastpeaks'] != None):
				print "\tPEAKS:    \t",self.stats['lastpeaks'],"peaks"
				if(count > 1):
					peaksum   = self.stats['peaksum']
					peaksumsq = self.stats['peaksumsq']
					peakstdev = math.sqrt(float(count*peaksumsq - peaksum**2) / float(count*(count-1)))
					print "\tAVG PEAKS:\t",round(float(peaksum)/float(count),1),"+/-",\
						round(peakstdev,1),"peaks"
					print "\t(- TOTAL:",peaksum,"peaks for",count,"images -)"
				_printLine()
	
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
			_printLine()

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
		newimgtree = []
		for imgdict in self.imgtree:
			imgname = imgdict['filename']
			if not _alreadyProcessed(imgname) or _reprocessImage(imgdict):
				#add imgdict to new imgtree
				newimgtree.append(imgdict)
		self.imgtree = newimgtree

	def _printLine():
		print "\t------------------------------------------"

	def _waitForMoreImages(self):
		"""
		pauses 10 mins and then checks for more images to process
		"""
		if params['nowait']:
			return False,None
		if not self.params["dbimages"]:
			return False,None
		if(self.stats['skipcount'] > 0):
			print ""
			print " !!! Images already processed and were therefore skipped (total",\
				self.stats['skipcount'],"skipped)."
			print " !!! to them process again, remove \'continue\' option and run selexon again."
			self.stats['skipcount'] = 0
		print "\nAll images processed. Waiting ten minutes for new images (waited",\
			self.stats['waittime'],"min so far)."
		for i in range(20):
			time.sleep(30)
			#print a dot every 30 seconds
			sys.stderr.write(".")
		print ""
		self.stats['waittime'] = self.stats['waittime'] + 10
		if(self.stats['waittime'] > 120):
			print "Waited longer than two hours, so I am quitting"
			return False,None
		images = apDatabase.getAllImages(self.stats, self.params)
		return True,images

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
	print "start"
	imageiter.start()
	print "loop"
	imageiter.loop()
