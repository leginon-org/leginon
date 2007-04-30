#Part of the new pyappion

import os,sys
import cPickle
import time
import math
#import selexonFunctions  as sf1
#import selexonFunctions2 as sf2
import apParam
import apDatabase
import apDisplay
try:
	import mem
except:
	apDisplay.printError("Please load 'usepythoncvs' for CVS leginon code, which includes 'mem.py'")


def startNewAppionFunction(args):
	"""
	Starts a new function and gets all the parameters
	"""
### setup default params: output directory, etc.
	params   = apParam.createDefaultParams(function=sys.argv[0])
### setup default stats: timing variables, etc.
	stats    = apParam.createDefaultStats()
### parse command line options: diam, apix, etc.
	apParam.parseCommandLineInput(sys.argv,params)
### check for conflicts in params
	apParam.checkParamConflicts(params)
### get images from database
	images   = apDatabase.getAllImages(stats,params)
### create output directories
	apParam.createOutputDirs(params)
### write log of command line options
	apParam.writeFunctionLog(args,file="."+params['function']+"log")
	apParam.writeFunctionLog(sys.argv,params=params)
### read/create dictionary to keep track of processed images
	donedict = readDoneDict(params)

	return (images,stats,params,donedict)

def waitForMoreImages(stats,params):
	"""
	pauses 10 mins and then checks for more images to process
	"""
	if params["dbimages"]==False:
		return False,None
	if(stats['skipcount'] > 0):
		print ""
		print " !!! Images already processed and were therefore skipped (total",stats['skipcount'],"skipped)."
		print " !!! to them process again, remove \'continue\' option and run selexon again."
		stats['skipcount'] = 0
	print "\nAll images processed. Waiting ten minutes for new images (waited",\
		stats['waittime'],"min so far)."
	for i in range(20):
		time.sleep(30)
		#print a dot every 30 seconds
		sys.stderr.write(".")
	print ""
	stats['waittime'] = stats['waittime'] + 10
	#newimages = apDatabase.getImagesFromDB(params['session']['name'],params['preset'])
	#if(params["crud"]==True or params['method'] == "classic"):
		#sf1.createImageLinks(images)
	if(stats['waittime'] > 120):
		print "Waited longer than two hours, so I am quitting"
		return False,None
	images = apDatabase.getAllImages(stats,params)
	return True,images

def getAllImages(stats,params):
	"""
	depricated: get images from database
	"""
	return apDatabase.getAllImages(stats,params)

def readDoneDict(params):
	"""
	reads or creates a done dictionary
	"""
	doneDictName = params['doneDictName']
	if os.path.isfile(doneDictName):
		# unpickle previously modified dictionary
		f = open(doneDictName,'r')
		donedict=cPickle.load(f)
		f.close()
		print " ... reading old done dictionary:\n\t",doneDictName
		print " ... found",len(donedict),"dictionary entries"
	else:
		#set up dictionary
		donedict={}
		print " ... creating new done dictionary:\n\t",doneDictName
	return donedict


def writeDoneDict(donedict,params,imgname=None):
	"""
	write finished image (imgname) to done dictionary
	"""
	if imgname != None:
	 	donedict[imgname]=True
	doneDictName = params['doneDictName']
	f = open(doneDictName,'w',0666)
	cPickle.dump(donedict,f)
	f.close()


def _alreadyProcessed(donedict, imgname, stats, params):
	""" 
	checks to see if image (imgname) has been done already
	"""
	if (params["continue"]==True):
		if donedict.has_key(imgname):
			if(stats['lastimageskipped']==False):
				sys.stderr.write("skipping images")
			else:
				sys.stderr.write(".")
			stats['lastimageskipped']=True
			stats['skipcount'] = stats['skipcount'] + 1
			return True
		else:
			donedict[imgname]=None
			stats['waittime'] = 0
			if(stats['lastimageskipped']==True):
				print "\nskipped",stats['skipcount'],"images so far"
			stats['lastimageskipped']=False
			return False
	return False


def checkMemLeak(stats):
	"""
	unnecessary code for determining if the program is eating memory over time
	"""
	### Memory leak code:
	stats['memlist'].append(mem.active())
	memfree = mem.free()
	swapfree = mem.swapfree()
	minavailmem = 64*1024; # 64 MB, size of one image
	if(memfree < minavailmem):
		apDisplay.printError("Memory is low ("+str(int(memfree/1024))+"MB): there is probably a memory leak")

	if(stats['count'] > 5):
		memlist = stats['memlist']
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
		

def startLoop(imgdict,donedict,stats,params):
	"""
	initilizes several parameters for a new image
	and checks if it is okay to start processing image
	"""
	#calc images left
	stats['imagesleft'] = stats['imagecount'] - stats['count'] - stats['skipcount']

	#only if an image was processed
	if(stats['lastcount'] != stats['count']):
		print "\nStarting new image",stats['count'],"( skip:",stats['skipcount'],\
			", left:",stats['imagesleft'],")",apDisplay.shortenImageName(imgdict['filename'])
		stats['lastcount'] = stats['count']
		checkMemLeak(stats)

	# get the next image pixel size:
	params['apix'] = apDatabase.getPixelSize(imgdict)


	# skip if image doesn't exist:
	imagepath = params['imgdir']+imgdict['filename']+'.mrc'
	if not os.path.isfile(imagepath):
		print " !!!",imagepath,"not found, skipping"
		return False

	# if continue option is true, check to see if image has already been processed
	imgname=imgdict['filename']
	if(_alreadyProcessed(donedict,imgdict['filename'],stats,params)==True):
		return False

	# match the original template pixel size to the img pixel size

	stats['beginLoopTime'] = time.time()

	print " ... processing "+apDisplay.shortenImageName(imgname)

	return True

def printSummary(stats,params):
	"""
	print summary statistics on last image
	"""
	tdiff = time.time()-stats['beginLoopTime']
	if(params["continue"]==False or tdiff > 0.3):
		count = stats['count']
		#if(count != stats['lastcount']):
		if(params['method'] != None):
			print "\n\tSUMMARY: using",params['method'],"method for",params['function']
		else:
			print "\n\tSUMMARY:"
		_printLine()
		if(stats['lastpeaks'] != None):
			print "\tPEAKS:    \t",stats['lastpeaks'],"peaks"
			if(count > 1):
				peaksum   = stats['peaksum']
				peaksumsq = stats['peaksumsq']
				peakstdev = math.sqrt(float(count*peaksumsq - peaksum**2) / float(count*(count-1)))
				print "\tAVG PEAKS:\t",round(float(peaksum)/float(count),1),"+/-",\
					round(peakstdev,1),"peaks"
				print "\t(- TOTAL:",peaksum,"peaks for",count,"images -)"
			_printLine()

		print "\tTIME:     \t",apDisplay.timeString(tdiff)
		stats['timesum'] = stats['timesum'] + tdiff
		stats['timesumsq'] = stats['timesumsq'] + (tdiff**2)
		timesum = stats['timesum']
		timesumsq = stats['timesumsq']
		if(count > 1):
			timeavg = float(timesum)/float(count)
			timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
			timeremain = (float(timeavg)+float(timestdev))*stats['imagesleft']
			print "\tAVG TIME: \t",apDisplay.timeString(timeavg,timestdev)
			#print "\t(- TOTAL:",apDisplay.timeString(timesum)," -)"
			if(stats['imagesleft'] > 0):
				print "\t(- REMAINING TIME:",apDisplay.timeString(timeremain),"for",stats['imagesleft'],"images -)"
		#print "\tMEM: ",(mem.active()-startmem)/1024,"M (",(mem.active()-startmem)/(1024*count),"M)"
		stats['count'] = stats['count'] + 1
		_printLine()

def _printLine():
	print "\t------------------------------------------"

def completeLoop(stats):
	"""
	program has finished print final stats
	"""
	ttotal= time.time()-stats["startTime"]
	print apDisplay.color("COMPLETE LOOP:\t"+apDisplay.timeString(ttotal)+\
		" for "+str(stats["count"]-1)+" images","green")
	print "ended ",time.strftime("%a, %d %b %Y %H:%M:%S")
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print ""






