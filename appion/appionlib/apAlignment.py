import os
import sys
import subprocess
import math
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase

####
# This is a database connections file with no file functions
# Please keep it this way
####

#=====================
def getAlignParticle(stackpdata,alignstackdata):
	oldstack = stackpdata['stack']['oldstack']
	particledata = stackpdata['particle']
	oldstackpdata = appiondata.ApStackParticleData(stack=oldstack,particle=particledata)
	q = appiondata.ApAlignParticleData(alignstack=alignstackdata,stackpart=oldstackpdata)
	results = q.query(readimages=False)
	if results:
		return results[0]

#=====================
def getAlignShift(alignpdata,package):
	shift = None
	if package == 'Spider':
		angle = alignpdata['rotation']*math.pi/180.0
		shift = {'x':alignpdata['xshift']*math.cos(-angle)-alignpdata['yshift']*math.sin(-angle),
				'y':alignpdata['xshift']*math.sin(-angle)+alignpdata['yshift']*math.cos(-angle)}
	elif package == 'Xmipp':
		shift = {'x':alignpdata['xshift'],'y':alignpdata['yshift']}
	return shift

#=====================
def getAlignPackage(alignrundata):
	aligntypedict = {
		'norefrun':'Spider',
		'refbasedrun':'Spider',
		'maxlikerun':'Xmipp',
		'imagicMRA':'Imagic'
	}
	for type in aligntypedict.keys():
		if alignrundata[type]:
			alignpackage = aligntypedict[type]
			break
	return alignpackage

#=====================
def getNumAlignRunsFromSession(sessionname):
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)

	stackrunq = appiondata.ApStackRunData()
	stackrunq['session'] = sessiondata

	runsinstackq = appiondata.ApRunsInStackData()
	runsinstackq['stackRun'] = stackrunq
	runsindatas = runsinstackq.query()

	if not runsindatas:
		return 0
	alignidlist = []
	for runsindata in runsindatas:
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['stack'] = runsindata['stack']
		alignstackdatas = alignstackq.query()
		if not alignstackdatas:
			continue
		for alignstackdata in alignstackdatas:
			alignrunid = alignstackdata['alignrun'].dbid

			if not alignrunid in alignidlist:
				alignidlist.append(alignrunid)

	return len(alignidlist)

#=====================
def _isMaxLikeJobUploaded(maxjobdata):
	maxrunq = appiondata.ApMaxLikeRunData()
	maxrunq['job'] = maxjobdata
	maxrundatas = maxrunq.query(results=1)
	if maxrundatas:
		return True
	return False

#=====================
def getMaxlikeJobDataForUpload(alignrunname):
	maxjobq = appiondata.ApMaxLikeJobData()
	maxjobq['runname'] = alignrunname
	maxjobq['finished'] = True
	maxjobq['hidden'] = False
	maxjobdatas = maxjobq.query()

	freejobs = []
	for maxjobdata in maxjobdatas:
		if not _isMaxLikeJobUploaded(maxjobdata):
			freejobs.append(maxjobdata)
	
	if len(freejobs) == 0:
		return None
	elif len(freejobs) > 1:
		apDisplay.printError("Found too many align runs for specified criteria")

	return freejobs[0]

#=====================
def getAlignRunIdFromName(alignrunname):
	alignrunq = appiondata.ApAlignRunData()
	alignrunq['runname'] = alignrunname
	alignrundatas = alignrunq.query()

	if not alignrundatas:
		return None
	if len(alignrundatas) == 1:
		### simpe case
		alignrunid = alignrundatas[0].dbid
	else:
		for alignrundata in alignrundatas:
			print alignrundata
		apDisplay.printError("Found too many align runs for specified criteria")

	apDisplay.printMsg("Found align run id %d"%(alignrunid))
	return alignrunid

####
# This is a database connections file with no file functions
# Please keep it this way
####
