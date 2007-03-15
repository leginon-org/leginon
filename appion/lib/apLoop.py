#Part of the new pyappion

import os
import cPickle
import time
import selexonFunctions  as sf1
import selexonFunctions2 as sf2

def _alreadyProcessed(donedict,imgname,params):
	""" 
	checks to see if image (imgname) has been done already
	"""
	if (params["continue"]==True):
		if donedict[imgname]:
			if(params['lastimageskipped']==False):
				sys.stderr.write("skipping images")
			else:
				sys.stderr.write(".")
			params['lastimageskipped']=True
			params['skipcount'] = params['skipcount'] + 1
			return True
		else:
			params['waittime'] = 0
			if(params['lastimageskipped']==True):
				print " skipped",params['skipcount'],"images so far"
			params['lastimageskipped']=False
	return False


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


def writeDoneDict(donedict,params):
	doneDictName = params['doneDictName']
	f=open(doneDictName,'w')
	cPickle.dump(donedict,f)
	f.close()


def startLoop(img,donedict,params):
	"""
	initilizes several parameter for a new image
	"""
	if(params['lastcount'] != params['count']):
		print "\nStarting new image",params['count'],"( skipped:",params['skipcount'],\
			", remain:",params['imagecount']-params['count']-params['skipcount'],")"
		params['lastcount'] = params['count']

	# get the image's pixel size:
	params['apix']=sf1.getPixelSize(img)

	# skip if image doesn't exist:
	if not os.path.isfile(params['imgdir']+img['filename']+'.mrc'):
		print " !!! "+img['filename']+".mrc not found, skipping"
		return False

	# if continue option is true, check to see if image has already been processed
	imgname=img['filename']
	if(_alreadyProcessed(donedict,imgname,params)==True):
		return False

	# insert selexon params into dbparticledata.selectionParams table
	expid=int(img['session'].dbid)
	if params['commit']==True:
		sf1.insertSelexonParams(params,expid)

	# match the original template pixel size to the img pixel size
	if params['templateIds']:
		sf1.rescaleTemplates(img,params)
			
	params['beginLoopTime'] = time.time()
	return True


def printSummary(params):
	"""
	print summary statistics
	"""
	tdiff = time.time()-params['beginLoopTime']
	count = params['count']
	#if(count != params['lastcount']):
	if(params['method'] != None):
		print "\n\tSUMMARY: using the",params['method'],"method"
	else:
		print "\n\tSUMMARY:"
	_printLine()
	if(params['lastpeaks'] != None):
		print "\tPEAKS:    \t",numpeaks,"peaks"
		if(count > 1):
			peakstdev = math.sqrt(float(count*peaksumsq - peaksum**2) / float(count*(count-1)))
			print "\tAVG PEAKS:\t",round(float(peaksum)/float(count),1),"+/-",\
				round(peakstdev,1),"peaks"
			print "\t(- TOTAL:",peaksum,"peaks for",count,"images -)"
		_printLine()

	print "\tTIME:     \t",_timeString(tdiff)
	params['timesum'] = params['timesum'] + tdiff
	params['timesumsq'] = params['timesumsq'] + (tdiff**2)
	timesum = params['timesum']
	timesumsq = params['timesumsq']
	if(count > 1):
		timeavg = float(timesum)/float(count)
		timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
		timeremain = (float(timeavg)+float(timestdev))*len(images)
		print "\tAVG TIME: \t",_timeString(timeavg,timestdev)
		#print "\t(- TOTAL:",_timeString(timesum)," -)"
		print "\t(- REMAINING TIME:",_timeString(timeremain),"for",len(images),"images -)"
	#print "\tMEM: ",(mem.used()-startmem)/1024,"M (",(mem.used()-startmem)/(1024*count),"M)"
	params['count'] = params['count'] + 1
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
