#!/usr/bin/env python

import os, re, sys, time
import tempfile
import cPickle
import math
import numpy
import string
import shutil
import subprocess
#appion
from appionlib import appiondata
#from appionlib import apDatabase
from appionlib import apParam
from appionlib import apDisplay
#from appionlib import apEMAN
#from appionlib import apEulerDraw
#from appionlib import apChimera
from appionlib import apStack
from appionlib import apFile
from appionlib import apFourier 
#from appionlib import apSymmetry

#==================
#==================
def getResolutionFromFSCFile(fscfile, boxsize, apix, criteria=0.5, msg=False):
	"""
	should use more general apFourier.getResolution()
	"""
	if not os.path.isfile(fscfile):
		apDisplay.printError("fsc file does not exist")
	if msg is True:
		apDisplay.printMsg("box: %d, apix: %.3f, file: %s"%(boxsize, apix, fscfile))
	f = open(fscfile, 'r')
	lastx=0
	lasty=0
	for line in f:
		xy = line.strip().split()
		if xy[0].startswith('#'):
			continue
		x = float(xy[0])
		y = float(xy[1])
		if x != 0.0 and x < 0.9:
			apDisplay.printWarning("FSC is wrong data format")
		if y > criteria:
			#store values for later
			lastx = x
			lasty = y
		else:
			# get difference of fsc
			diffy = lasty-y
			# get distance from criteria 0.5 or 0.143
			distfsc = (criteria-y) / diffy
			# get interpolated spatial freq
			intfsc = x - distfsc * (x-lastx)
			# convert to Angstroms
			if intfsc > 0.0:
				res = boxsize * apix / intfsc
			else:
				res = boxsize * apix
			f.close()
			return res
	# fsc did not fall below criteria 0.5 or 0.143
	apDisplay.printWarning("Failed to determine resolution")
	res = boxsize * apix / (lastx + 1)
	return res

def getResolutionFromGenericFSCFile(fscfile, boxsize, apix, filtradius=3, criterion=0.5, msg=False):
	"""
	parses standard 2-column FSC file with 1) spatial frequency and 2) FRC, returns resolution
	"""
	if not os.path.isfile(fscfile):
		apDisplay.printError("fsc file does not exist")
	if msg is True:
		apDisplay.printMsg("box: %d, apix: %.3f, file: %s"%(boxsize, apix, fscfile))

	f = open(fscfile, 'r')
	fscfileinfo = f.readlines()
	f.close()
	fscdata = numpy.zeros((int(boxsize)/2), dtype=numpy.float32)
	for i, info in enumerate(fscfileinfo):		# skip commented out lines
		if info[0] == "#":
			pass
		else: 
			fscfileinfo = fscfileinfo[i:]
			break
	for j, info in enumerate(fscfileinfo):      
		frc = float(info.split()[1])
		fscdata[j] = frc
	res = apFourier.getResolution(fscdata, apix, boxsize, filtradius=filtradius, crit=criterion)

	return res


#==================
#==================
def getReconRunIdFromNamePath(runname, path):
	reconrunq = appiondata.ApRefineRunData()
	reconrunq['runname'] = runname
	reconrunq['path'] = appiondata.ApPathData(path=os.path.abspath(path))
	reconrundatas = reconrunq.query(results=1)
	if not reconrundatas:
		return None
	return reconrundatas[0].dbid

#==================
#==================
def calcRes(fscfile, boxsize, apix):
	return getResolutionFromFSCFile(fscfile, boxsize, apix, False)

#==================
#==================
def getRMeasurePath():
	unames = os.uname()
	if unames[-1].find('64') >= 0:
		exename = 'rmeasure64.exe'
	else:
		exename = 'rmeasure32.exe'
	rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		rmeasexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(rmeasexe):
		exename = "rmeasure.exe"
		rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		exename = "rmeasure"
		rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		apDisplay.printWarning(exename+" was not found at: "+apParam.getAppionDirectory())
		return None
	return rmeasexe

#==================
#==================
def runRMeasure(apix, volpath, imask=0):
	t0 = time.time()

	apDisplay.printMsg("R Measure at %s, processing volume:\n\t%s"%(time.asctime(), volpath))
	rmeasexe = getRMeasurePath()
	if rmeasexe is None:
		apDisplay.printWarning("R Measure failed: could not find rmeasure program")
		return None
	rmeasproc = subprocess.Popen(rmeasexe, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	fin = rmeasproc.stdin
	fout = rmeasproc.stdout
	fin.write(volpath+"\n"+str(apix)+"\n"+"0,0\n")
	fin.flush()
	fin.close()
	output = fout.readlines()
	fout.close()

	flog = open("rmeasure.log", "a")
	for line in output:
		flog.write(line.rstrip()+"\n")
	flog.close()

	if output is None:
		apDisplay.printWarning("R Measure failed: no output found")
		return None

	resolution = None
	key = "Resolution at FSC = 0.5:"
	for line in output:
		sline = line.strip()
		if sline.startswith(key):
			#print sline
			blocks = sline.split(key)
			resolution = float(blocks[1])
			break

	apDisplay.printColor("R Measure, resolution: "+str(resolution)+" Angstroms", "cyan")
	apDisplay.printMsg("R Measure, completed in: "+apDisplay.timeString(time.time()-t0))

	return resolution

#==================
#==================
def getRefineRunDataFromID(refinerunid):
	return appiondata.ApRefineRunData.direct_query(refinerunid)

#==================
#==================
def getNumIterationsFromRefineRunID(refinerunid):
	refrundata = appiondata.ApRefineRunData.direct_query(refinerunid)
	refq = appiondata.ApRefineIterData()
	refq['refineRun'] = refrundata
	refdatas = refq.query()
	if not refdatas:
		return 0
	maxiter = 0
	for refdata in refdatas:
		iternum = refdata['iteration']
		if iternum > maxiter:
			maxiter = iternum
	return maxiter

#==================
#==================
def getRefinementsFromRun(refinerundata):
	refineitq=appiondata.ApRefineIterData()
	refineitq['refineRun'] = refinerundata
	return refineitq.query()

def getRefineIterDataFromIterationId(iterid):
	return appiondata.ApRefineIterData.direct_query(iterid)
#==================
#==================
def getSessionDataFromReconId(reconid):
	stackid = apStack.getStackIdFromRecon(reconid)
	partdata = apStack.getOneParticleFromStackId(stackid, msg=False)
	sessiondata = partdata['particle']['selectionrun']['session']
	return sessiondata

#==================
#==================
def partnum2defid(stackid):
	"""
	This function must be used because sinedon would take up too much memory?
	"""
	t0 = time.time()
	stackpartnum = apStack.getNumberStackParticlesFromId(stackid)

	apDisplay.printMsg("Mapping %d stack particle IDs"%(stackpartnum))

	import sinedon
	import MySQLdb
	dbconf = sinedon.getConfig('appiondata')
	db     = MySQLdb.connect(**dbconf)
	cursor = db.cursor()

	cursor.execute('SELECT DEF_id, particleNumber FROM ApStackParticleData WHERE `REF|ApStackData|stack` = %s' % (stackid,))
	partdict = {}
	maxnum = 0
	while True:
		row = cursor.fetchone()
		if row is None:
			break
		defid = int(row[0]) #row['DEF_id']
		num = int(row[1]) #row['particleNumber']
		if num > maxnum:
			maxnum = num
		partdict[num] = defid

	if stackpartnum != maxnum:
		apDisplay.printError("Expected to get %d particles, but received %d particles"%(stackpartnum, maxnum))

	apDisplay.printMsg("Mapped %d stack particle IDs in %s"%(stackpartnum, apDisplay.timeString(time.time()-t0)))

	return partdict

#==================
#==================
def setGoodBadParticlesFromReconId(reconid):
	"""
	Goes through existing recons and caches the number of good and bad particles
	"""
	import sinedon
	import MySQLdb
	dbconf = sinedon.getConfig('appiondata')
	db     = MySQLdb.connect(**dbconf)
	db.autocommit(True)
	cursor = db.cursor()

	refinerundata = appiondata.ApRefineRunData.direct_query(reconid)
	refineq = appiondata.ApRefineIterData()
	refineq['refineRun'] = refinerundata
	refineiterdatas = refineq.query()
	r0 = time.time()
	for refineiterdata in refineiterdatas:
		t0 = time.time()
		#print "Iteration %d"%(refineiterdata['iteration'])
		goodbadq = appiondata.ApRefineGoodBadParticleData()
		goodbadq['refine'] = refineiterdata
		goodbaddata = goodbadq.query()
		if goodbaddata:
			continue
		fields = {
			'good_refine': getParticleCount(refineiterdata.dbid, cursor, 'refine_keep', True),
			'bad_refine':  getParticleCount(refineiterdata.dbid, cursor, 'refine_keep', False),
			'good_postRefine':  getParticleCount(refineiterdata.dbid, cursor, 'postRefine_keep', True),
			'bad_postRefine':   getParticleCount(refineiterdata.dbid, cursor, 'postRefine_keep', False),
		}
		#print fields
		goodbadq = appiondata.ApRefineGoodBadParticleData()
		goodbadq['refine'] = refineiterdata
		goodbadq['good_refine'] = fields['good_refine']
		goodbadq['bad_refine'] = fields['bad_refine']
		goodbadq['good_postRefine'] = fields['good_postRefine']
		goodbadq['bad_postRefine'] = fields['bad_postRefine']
		goodbadq.insert()
		if time.time()-t0 > 2.0:
			apDisplay.printMsg("Iter completed in %s"%(apDisplay.timeString(time.time()-t0)))
	if time.time()-r0 > 2.0:
		apDisplay.printMsg("Refine completed in %s"%(apDisplay.timeString(time.time()-r0)))
	return

#=====================
def getParticleCount(refineid, cursor, name="refine_keep", isone=True):
	query = (
		"SELECT \n"
		+"  count(part.`DEF_id`) AS count \n"
		+"FROM `ApRefineParticleData` as part \n"
		+"WHERE \n"
		+"  part.`REF|ApRefineIterData|refineIter` = "+str(refineid)+" \n"
		+"AND \n"
	)
	if isone is True:
		query += "  part.`%s` = 1 \n"%(name)
	else:
		query += " ( part.`%s` != 1 OR part.`%s` IS NULL )\n"%(name, name)
	#print query
	cursor.execute(query)
	results = cursor.fetchall()
	if not results:
		print query
		apDisplay.printError("Failed to get particle counts")
	#print results
	count = results[0][0]
	#print count
	return int(count)

#==================
def getComponentFromVector(vector, iteration, splitter=None):
	''' 
	NOTE: THIS IS MODIFIED FROM XMIPP ARG.PY LIBRARY IN THE XMIPP_PROTOCOLS DIRECTORY 
	'splitter' can be any string, for example, ':' will split on :
	'''

	if splitter is not None:
		listValues = getListFromVector(vector, splitter)
	else:
		listValues = getListFromVector(vector)
	if listValues is None:
		return None
	if iteration<0: iteration=0
	if iteration<len(listValues): 
		return listValues[iteration]
	else:
		return listValues[len(listValues)-1]

#---------------------------------------------------------------------------
# getListFromVector
#---------------------------------------------------------------------------
def getListFromVector(vector, splitter=None):
	''' 
	NOTE: THIS IS MODIFIED FROM XMIPP ARG.PY LIBRARY IN THE XMIPP_PROTOCOLS DIRECTORY 
	'splitter' can be any string, for example, ':' will split on :
	'''	

	if vector is None:
		return None
	if splitter is not None:
		intervals = string.split(str(vector), splitter)
	else:
		intervals = string.split(str(vector))	
	if len(intervals) == 0:
#		raise RuntimeError,"Empty vector"
		return None
	listValues = []
	for i in range(len(intervals)):
		intervalo = intervals[i]
		listaIntervalo = string.split(intervalo,'x')
		if len(listaIntervalo) == 1:
			listValues += listaIntervalo
		elif len(listaIntervalo) == 2:
			listValues += [listaIntervalo[1]] * string.atoi(listaIntervalo[0])
		else:
			raise RuntimeError,"Unknown syntax: "+intervals
	return listValues

#==================
#==================
#==================
#==================
if __name__ == '__main__':
	r = runRMeasure(1.63,"/ami/data15/appion/08may09b/recon/recon1/threed.20a.mrc",'0,0')
	print r


