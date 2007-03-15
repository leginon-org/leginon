#Part of the new pyappion

import os
import cPickle


def alreadyProcessed(donedict,imgname,params):
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
