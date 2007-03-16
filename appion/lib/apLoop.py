#Part of the new pyappion

import os
import cPickle
import time
import math
import sys
import selexonFunctions  as sf1
import selexonFunctions2 as sf2


def waitForMoreImages(stats,params):
	if params["dbimages"]==False:
		return False
	if(stats['skipcount'] > 0):
		print ""
		print " !!! Images already processed and were therefore skipped (total",skipcount,"skipped)."
		print " !!! to them process again, remove \'continue\' option and run selexon again."
		stats['skipcount'] = 0
	print "\nAll images processed. Waiting ten minutes for new images (waited",\
		stats['waittime'],"min so far)."
	time.sleep(600)
	stats['waittime'] = stats['waittime'] + 10
	newimages = sf1.getImagesFromDB(params['session']['name'],params['preset'])
	if(params["crud"]==True or params['method'] == "classic"):
		sf1.createImageLinks(images)
	if(stats['waittime'] > 120):
		print "Waited longer than two hours, so I am quitting"
		return False
	return True


def readDoneDict(params):
	doneDictName = params['doneDictName']
	if os.path.exists(doneDictName):
		# unpickle previously modified dictionary
		f=open(doneDictName,'r')
		donedict=cPickle.load(f)
		f.close()
	else:
		#set up dictionary
		donedict={}
	return (donedict)


def writeDoneDict(donedict,params,imgname=None):
	if imgname != None:
	 	donedict[imgname]=True
	doneDictName = params['doneDictName']
	f=open(doneDictName,'w')
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
				print " skipped",stats['skipcount'],"images so far"
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
	params['apix']=sf1.getPixelSize(img)

	# skip if image doesn't exist:
	if not os.path.isfile(params['imgdir']+img['filename']+'.mrc'):
		print " !!! "+img['filename']+".mrc not found, skipping"
		return False

	# if continue option is true, check to see if image has already been processed
	imgname=img['filename']
	if(_alreadyProcessed(donedict,img['filename'],stats,params)==True):
		return False

	# insert selexon params into dbparticledata.selectionParams table
	expid=int(img['session'].dbid)
	if params['commit']==True:
		sf1.insertSelexonParams(params,expid)

	# match the original template pixel size to the img pixel size
	if params['templateIds']:
		sf1.rescaleTemplates(img,params)
			
	stats['beginLoopTime'] = time.time()
	return True

def printSummary(stats,params):
	"""
	print summary statistics
	"""
	tdiff = time.time()-stats['beginLoopTime']
	count = stats['count']
	#if(count != stats['lastcount']):
	if(params['method'] != None):
		print "\n\tSUMMARY: using",params['method'],"method"
	else:
		print "\n\tSUMMARY:"
	_printLine()
	if(stats['lastpeaks'] != None):
		print "\tPEAKS:    \t",numpeaks,"peaks"
		if(count > 1):
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
