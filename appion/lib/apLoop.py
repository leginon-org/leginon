#Part of the new pyappion

import os,sys
import cPickle
import time
import math
import types
#import selexonFunctions  as sf1
#import selexonFunctions2 as sf2
import apParam
import apDatabase

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
	images   = apDatabase.getAllImages(params,stats)
### create output directories
	apParam.createOutputDirs(params)
### write log of command line options
	apParam.writeFunctionLog(args,file="."+params['function']+"log")
	apParam.writeFunctionLog(sys.argv,params=params)
### read/create dictionary to keep track of processed images
	donedict = readDoneDict(params)

	return (images,params,stats,donedict)

def waitForMoreImages(stats,params):
	if params["dbimages"]==False:
		return False
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
		return False
	return True


def readDoneDict(params):
	doneDictName = params['doneDictName']
	if os.path.isfile(doneDictName):
		# unpickle previously modified dictionary
		f = open(doneDictName,'r')
		donedict=cPickle.load(f)
		f.close()
		print " ... reading old done dictionary:",doneDictName,
		print " ... found",len(donedict),"entries"
	else:
		#set up dictionary
		donedict={}
		print " ... creating new done dictionary:",doneDictName
	return donedict


def writeDoneDict(donedict,params,imgname=None):
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

def startLoop(img,donedict,stats,params):
	"""
	initilizes several parameter for a new image
	and checks if it is okay to start processing image
	"""
	if(stats['lastcount'] != stats['count']):
		remainImg = stats['imagecount']-stats['count']-stats['skipcount']
		print "\nStarting new image",stats['count'],"( skipped:",stats['skipcount'],\
			", remain:",remainImg,")"
		stats['lastcount'] = stats['count']

	# get the image's pixel size:
	params['apix']=apParam.getPixelSize(img)

	# skip if image doesn't exist:
	imagepath = params['imgdir']+img['filename']+'.mrc'
	if not os.path.isfile(imagepath):
		print " !!!",imagepath,"not found, skipping"
		return False

	# if continue option is true, check to see if image has already been processed
	imgname=img['filename']
	if(_alreadyProcessed(donedict,img['filename'],stats,params)==True):
		return False

	# match the original template pixel size to the img pixel size

			
	stats['beginLoopTime'] = time.time()
	return True

def printSummary(stats,params):
	"""
	print summary statistics
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

		print "\tTIME:     \t",_timeString(tdiff)
		stats['timesum'] = stats['timesum'] + tdiff
		stats['timesumsq'] = stats['timesumsq'] + (tdiff**2)
		timesum = stats['timesum']
		timesumsq = stats['timesumsq']
		if(count > 1):
			timeavg = float(timesum)/float(count)
			timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
			timeremain = (float(timeavg)+float(timestdev))*stats['imagesleft']
			print "\tAVG TIME: \t",_timeString(timeavg,timestdev)
			#print "\t(- TOTAL:",_timeString(timesum)," -)"
			if(stats['imagesleft'] > 0):
				print "\t(- REMAINING TIME:",_timeString(timeremain),"for",stats['imagesleft'],"images -)"
			else:
				print "\t(- LAST IMAGE -)"
		#print "\tMEM: ",(mem.used()-startmem)/1024,"M (",(mem.used()-startmem)/(1024*count),"M)"
		stats['count'] = stats['count'] + 1
		_printLine()

def _printLine():
	print "\t------------------------------------------"

def completeLoop(stats):
	ttotal= time.time()-stats["startTime"]
	print "COMPLETE LOOP:\t",_timeString(ttotal),"for",stats["count"]-1,"images"
	print "end run"
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print "====================================================="
	print ""

def _timeString(avg,stdev=0):
	""" 
	returns a string with the length of time scaled for clarity
	"""
	avg = float(avg)
	stdev = float(stdev)
	#less than 90 seconds
	if avg < 90.0:
		if stdev > 0.0:
			timestr = str(round(avg,2))+" +/- "+str(round(stdev,2))+" sec"
		else:
			timestr = str(round(avg,2))+" sec"
	#less than 90 minutes
	elif avg < 5400.0:
		if stdev > 0.0:
			timestr = str(round(avg/60.0,2))+" +/- "+str(round(stdev/60.0,2))+" min"
		else:
			timestr = str(int(avg/60.0))+" min "+str(int((avg/60.0-int(avg/60.0))*60.0+0.5))+" sec"
	#more than 1.5 hours
	else:
		if stdev > 0.0:
			timestr = str(round(avg/3600.0,2))+" +/- "+str(round(stdev/3600.0,2))+" hrs"
		else:
			timestr = str(int(avg/3600.0))+" hrs "+str(int((avg/3600.0-int(avg/3600.0))*60.0+0.5))+" min"
	return str(timestr)




def color(text, fg, bg=None):
	"""Return colored text.

	Uses terminal color codes; set avk_util.enable_color to 0 to
	return plain un-colored text. If fg is a tuple, it's assumed to
	be (fg, bg). Both colors may be 'None'.

	"""

	colors = {
		"black" :"30",
		"red"   :"31",
		"green" :"32",
		"brown" :"33",
		"blue"  :"34",
		"purple":"35",
		"cyan"  :"36",
		"lgray" :"37",
		"gray"  :"1;30",
		"lred"  :"1;31",
		"lgreen":"1;32",
		"yellow":"1;33",
		"lblue" :"1;34",
		"pink"  :"1;35",
		"lcyan" :"1;36",
		"white" :"1;37"
	}

	if type(fg) in (types.TupleType, types.ListType):
		fg, bg = fg
	if not fg:
		return text
	opencol = "\033["
	closecol = "m"
	clear = opencol + "0" + closecol
	xterm = 0
	if os.environ["TERM"] == "xterm": 
		xterm = 1
	b = ''
	# In xterm, brown comes out as yellow..
	if xterm and fg == "yellow": 
		fg = "brown"
	f = opencol + colors[fg] + closecol
	if bg:
		if bg == "yellow" and xterm: 
			bg = "brown"
		try: 
			b = colors[bg].replace('3', '4', 1)
			b = opencol + b + closecol
		except KeyError: 
			pass
	return "%s%s%s%s" % (b, f, text, clear)

