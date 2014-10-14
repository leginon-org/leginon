#Part of the new pyappion

#pythonlib
import os
import re
import sys
import math
import shutil
#appion
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata

####
# This is a database connections file with no file functions
# Please keep it this way
####

#=====================
def getNumCtfRunsFromSession(sessionname):
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	ctfrunq = appiondata.ApAceRunData()
	ctfrunq['session'] = sessiondata
	ctfrundatas = ctfrunq.query()
	if not ctfrundatas:
		return 0
	return len(ctfrundatas)

#=====================
def getCtfMethod(ctfvalue):
	if not 'acerun' in ctfvalue:
		return None
	if ctfvalue['acerun']['aceparams'] is not None:
		return "ace1"
	elif ctfvalue['acerun']['ace2_params'] is not None:
		return "ace2"
	elif ctfvalue['acerun']['ctftilt_params'] is not None:
		return "ctffind"
	elif ctfvalue['acerun']['xmipp_ctf_params'] is not None:
		return "xmipp_ctf"
	return "unknown"

#=====================
def printCtfData(ctfvalue):
	if ctfvalue is None:
		return
	try:
		defocusratio = ctfvalue['defocus2']/ctfvalue['defocus1']
	except ZeroDivisionError:
		print ctfvalue
		print "invalid CTF"
		return
	method = getCtfMethod(ctfvalue)
	if 'acerun' in ctfvalue:
		method = getCtfMethod(ctfvalue)
		runname = ctfvalue['acerun']['name']
		sys.stderr.write("[%s]   method: %s | runname %s\n"%
		(apDisplay.colorString("CTF run", "blue"), method, runname))
	sys.stderr.write("[%s] def1: %.2e | def2: %.2e | angle: %.1f | ampcontr %.2f | defratio %.3f\n"%
		(apDisplay.colorString("CTF param", "blue"), ctfvalue['defocus1'], 
		ctfvalue['defocus2'], ctfvalue['angle_astigmatism'], 
		ctfvalue['amplitude_contrast'], defocusratio))
	if 'resolution_80_percent' in ctfvalue.keys() and ctfvalue['resolution_80_percent'] is not None:
		sys.stderr.write("[%s] conf_30-10: %s | conf_5peak: %s | res_0.8: %.1fA | res_0.5 %.1fA\n"%
			(apDisplay.colorString("CTF stats", "blue"), 
			apDisplay.colorProb(ctfvalue['confidence_30_10']), 
			apDisplay.colorProb(ctfvalue['confidence_5_peak']),
			ctfvalue['resolution_80_percent'], ctfvalue['resolution_50_percent']))
	#sys.stderr.write("[%s] conf: %s | conf_d: %s\n"%
	#	(apDisplay.colorString("CTF stats", "blue"), apDisplay.colorProb(ctfvalue['confidence']), 
	#	apDisplay.colorProb(ctfvalue['confidence_d'])))
	#apDisplay.colorProb(numlist[i])
	#time.sleep(3)
	return

#=====================
def mkTempDir(temppath):
	return apParam.createDirectory(temppath)

#=====================
def getCtfValueForCtfRunId(imgdata, ctfrunid=None, msg=False):
	"""
	takes an image and get the ctf value for that image for the specified ctf estimation run
	specified methods can be: ace2 or ctffind
	"""

	if ctfrunid is None:
		apDisplay.printError("This function requires a ctf_estimation_runid")

	ctfrundata = appiondata.ApAceRunData.direct_query(ctfrunid)

	if ctfrundata is None:
		apDisplay.printError("ctf_estimation_runid not found")

	### get all ctf values
	ctfq = appiondata.ApCtfData()
	ctfq['image'] = imgdata
	ctfq['acerun'] = ctfrundata
	ctfvalues = ctfq.query()

	### check if it has values
	if ctfvalues is None:
		return None
	### find the value
	ctfdata = None

	if len(ctfvalues) == 1:
		if msg is True:
			printCtfData(ctfvalues[0])
		return ctfvalues[0]
	elif len(ctfvalues) > 1:
		apDisplay.printWarning("more than one run found for ctfrunid %d and image %s"
			%(ctfrunid, apDisplay.short(imgdata['filename'])))
		return ctfvalues[-1]
	return None

#=====================
def calculateConfidenceScore(ctfdata, ctfavg=True):
	# get ctf confidence values
	if ctfdata is None:
		return None

	conf1 = ctfdata['confidence']
	conf2 = ctfdata['confidence_d']
	try:
		conf3 = ctfdata['confidence_30_10']
		conf4 = ctfdata['confidence_5_peak']
		conf = max(conf1, conf2, conf3, conf4)
	except KeyError:
		conf = max(conf1, conf2)
	if conf < 0:
		conf = 0
	return conf

#=====================
def getBestCtfValueForImage(imgdata, ctfavg=True, msg=True, method=None):
	"""
	takes an image and get the best ctfvalues for that image
	specified methods can be: ace2 or ctffind
	"""
	ctfvalue = getBestCtfValue(imgdata, sortType='res80', method=method, msg=msg)
	if ctfvalue is None:
		ctfvalue = getBestCtfValue(imgdata, sortType='maxconf', method=method, msg=msg)
	conf = calculateConfidenceScore(ctfvalue)
	return ctfvalue, conf

#=====================
def getSortValueFromCtfQuery(ctfvalue, sortType):
	#self.sortoptions = ('res80', 'res50', 'resplus', 'maxconf', 'conf3010', 'conf5peak')
	# in order to make the highest value the best value, we will take the inverse of the resolution
	try:
		if sortType == 'res80':
			return 1.0/ctfvalue['resolution_80_percent']
		elif sortType == 'res50':
			return 1.0/ctfvalue['resolution_50_percent']
		elif sortType == 'resplus':
			return 1.0/(ctfvalue['resolution_80_percent']+ctfvalue['resolution_50_percent'])
		elif sortType == 'maxconf':
			return calculateConfidenceScore(ctfvalue)
		elif sortType == 'conf3010':
			return ctfvalue['confidence_30_10']
		elif sortType == 'conf5peak':
			return ctfvalue['confidence_5_peak']
		elif sortType == 'crosscorr':
			return ctfvalue['cross_correlation']
	except KeyError:
		pass
	except TypeError:
		pass
	return None

#=====================
def getBestCtfValue(imgdata, sortType='res80', method=None, msg=True):
	"""
	takes an image and get the best ctfvalues for that image
	"""
	### get all ctf values
	ctfq = appiondata.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = ctfq.query()
	imgname = apDisplay.short(imgdata['filename'])

	if msg is True:
		print "Found %d ctf values"%(len(ctfvalues))

	### check if it has values
	if ctfvalues is None:
		apDisplay.printWarning("no CTF values found in database for img %s"%(imgname))
		return None

	### find the best values
	bestsortvalue = -1
	bestctfvalue = None
	for ctfvalue in ctfvalues:
		if method is not None:
			imgmethod = getCtfMethod(ctfvalue)
			if method != imgmethod:
				continue
		sortvalue = getSortValueFromCtfQuery(ctfvalue, sortType)
		if sortvalue is None:
			continue
		if msg is True:
			print "%.3f -- %s"%(sortvalue, ctfvalue['acerun']['name'])
		if sortvalue > bestsortvalue:
			bestsortvalue = sortvalue
			bestctfvalue = ctfvalue

	if bestctfvalue is None:
		apDisplay.printWarning("no best CTF value for image %s"%(imgname))
		return None

	if msg is True:
		print "*** %.3f"%(bestsortvalue)
		printCtfData(bestctfvalue)

	return bestctfvalue

#=====================
def getBestCtfByResolution(imgdata, msg=True, method=None):
	"""
	takes an image and get the best ctfvalues for that image
	specified methods can be: ace2 or ctffind
	"""
	return getBestCtfValue(imgdata, sortType='res80', method=method, msg=msg)

#=====================
def getBestTiltCtfValueForImage(imgdata):
	"""
	takes an image and get the tilted ctf parameters for that image
	"""
	print "ERROR getBestTiltCtfValueForImage(), use getBestCtfByResolution() instead"
	#sys.exit(1)

	### get all ctf values
	ctfq = appiondata.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = ctfq.query()

	bestctftiltvalue = None
	cross_correlation = 0.0
	for ctfvalue in ctfvalues:
		if ctfvalue['acerun'] is not None:
			if bestctftiltvalue is None:
				cross_correlation = ctfvalue['cross_correlation']
				bestctftiltvalue = ctfvalue
			else:
				if cross_correlation < ctfvalue['cross_correlation']:
					cross_correlation = ctfvalue['cross_correlation']
					bestctftiltvalue = ctfvalue

	return bestctftiltvalue

#=====================
def getParticleTiltDefocus(ctfdata,imgdata,NX,NY):
	### calculate defocus at given position
	dimx = imgdata['camera']['dimension']['x']
	dimy = imgdata['camera']['dimension']['y']
	CX = dimx/2
	CY = dimy/2

	if ctfdata['tilt_axis_angle'] is not None:
		N1 = -1.0 * math.sin( math.radians(ctfdata['tilt_axis_angle']) )
		N2 = math.cos( math.radians(ctfdata['tilt_axis_angle']) )
	else:
		N1 = 0.0
		N2 = 1.0

	PSIZE = apDatabase.getPixelSize(imgdata)	
	### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
	if imgdata['scope']['tem']['name'] == "CM":
		voltage = imgdata['scope']['high tension']
	else:
		voltage = (imgdata['scope']['high tension'])/1000

	# flip Y axis due to reversal of y coordinates
	NY = dimy-NY

	DX = CX - NX
	DY = CY - NY
	DF = (N1*DX + N2*DY) * PSIZE * math.tan( math.radians(ctfdata['tilt_angle']) )
	#print "using tilt axis: %.02f, angle: %.02f"%(ctfdata['tilt_axis_angle'],ctfdata['tilt_angle'])
	#print "df1: %.2f, df2: %.2f, offset is %.2f"%(ctfdata['defocus1']*-1e10,ctfdata['defocus2']*-1e10,DF)
	DFL1 = abs(ctfdata['defocus1'])*1.0e10 + DF
	DFL2 = abs(ctfdata['defocus2'])*1.0e10 + DF

	return DFL1,DFL2
	
#=====================
def ctfValuesToParams(ctfvalue, params, msg=True):
	if ctfvalue['acerun'] is not None:
		if abs(ctfvalue['defocus1'] - ctfvalue['defocus2'])*1e6 > 0.01:
			params['hasace'] = True
			avgdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
			if msg is True:
				apDisplay.printWarning("astigmatism was estimated; averaging defocus values (%.3f, %.3f => %.3f) "
					%(ctfvalue['defocus1']*1e6, ctfvalue['defocus2']*1e6, avgdf*1e6) )
			params['df']     = avgdf*-1.0e6
			params['conf_d'] = ctfvalue['confidence_d']
			params['conf']   = ctfvalue['confidence']
			return -avgdf
		else:
			params['hasace'] = True
			params['df']     = ctfvalue['defocus1']*-1.0e6
			params['conf_d'] = ctfvalue['confidence_d']
			params['conf']   = ctfvalue['confidence']
			return -ctfvalue['defocus1']

	return None

#=====================
def printCtfSummary(params, imgtree):
	"""
	prints a histogram of the best ctfvalues for the session
	"""
	
	# if there are no images in the imgtree, there was no new processing done, so exit this function early.
	if not imgtree:
		apDisplay.printWarning("There are no new results to summarize.")
		return
	
	sys.stderr.write("processing CTF histogram...\n")

	### get best ctf values for each image
	ctfhistconf = []
	ctfhistval = []
	for imgdata in imgtree:
		if params['norejects'] is True and apDatabase.getSiblingImgAssessmentStatus(imgdata) is False:
			continue

		ctfq = appiondata.ApCtfData()
		ctfq['image'] = imgdata
		ctfvalues = ctfq.query()

		### check if it has values
		if ctfvalues is None:
			continue

		### find the best values
		bestconf = 0.0
		bestctfvalue = None
		for ctfvalue in ctfvalues:
			conf = calculateConfidenceScore(ctfvalue,False)
			if conf > bestconf:
				bestconf = conf
				bestctfvalue = ctfvalue
		ctfhistconf.append(bestconf)
		ctfhistval.append(bestctfvalue)

	ctfhistconf.sort()
	confhist = {}
	yspan = 20.0
	minconf = ctfhistconf[0]
	maxconf = ctfhistconf[len(ctfhistconf)-1]
	maxcount = 0
	for conf in ctfhistconf:
		c2 = round(conf*yspan,0)/float(yspan)
		if c2 in confhist:
			confhist[c2] += 1
			if confhist[c2] > maxcount:
				maxcount = confhist[c2]
		else:
			confhist[c2] = 1
	if maxcount > 70:
		scale = 70.0/float(maxcount)
		sys.stderr.write(" * = "+str(round(scale,1))+" images\n")
	else:
		scale = 1.0

	colorstr = {}
	for i in range(int(yspan+1)):
		j = float(i)/yspan
		if j < 0.5:
			colorstr[j] = "red"
		elif j < 0.8:
			colorstr[j] = "yellow"
		else:
			colorstr[j] = "green"

	sys.stderr.write("Confidence histogram:\n")
	for i in range(int(yspan+1)):
		j = float(i)/yspan
		if j < minconf-1.0/yspan:
			continue
		jstr = "%1.2f" % j
		jstr = apDisplay.rightPadString(jstr,5)
		sys.stderr.write(jstr+"> ")
		if j in confhist:
			for k in range(int(confhist[j]*scale)):
				sys.stderr.write(apDisplay.color("*",colorstr[j]))
		sys.stderr.write("\n")

####
# This is a database connections file with no file functions
# Please keep it this way
####

