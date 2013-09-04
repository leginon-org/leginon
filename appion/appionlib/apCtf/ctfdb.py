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
	return None

#=====================
def printCtfData(ctfvalue):
	if ctfvalue is None:
		return
	defocusratio = ctfvalue['defocus2']/ctfvalue['defocus1']
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
def printResults(params, nominal, ctfvalue):
	nom1 = float(-nominal*1e6)
	defoc1 = float(ctfvalue[0]*1e6)
	if (params['stig']==1):
		defoc2 = float(ctfvalue[1]*1e6)
	else:
		defoc2=None
	conf1 = float(ctfvalue[16])
	conf2 = float(ctfvalue[17])

	if(conf1 > 0 and conf2 > 0):
		totconf = math.sqrt(conf1*conf2)
	else:
		totconf = 0.0
	if (params['stig']==0):
		if nom1 != 0: pererror = (nom1-defoc1)/nom1
		else: pererror = 1.0
		labellist = ["Nominal","Defocus","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	else:
		avgdefoc = (defoc1+defoc2)/2.0
		if nom1 != 0: pererror = (nom1-avgdefoc)/nom1
		else: pererror = 1.0
		labellist = ["Nominal","Defocus1","Defocus2","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,defoc2,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,0,1,1,1,]
		apDisplay.printDataBox(labellist,numlist,typelist)
	return

#=====================
def mkTempDir(temppath):
	return apParam.createDirectory(temppath)

#=====================
def getBestDefocusForImage(imgdata, msg=False):
	"""
	takes an image and get the best defocus (in negative meters) for that image
	indepedent of method (ACE1 or ACE2)
	"""
	#print "ERROR getBestDefocusForImage(), use getBestCtfByResolution() instead"
	#sys.exit(1)

	ctfvalue, conf = getBestCtfValueForImage(imgdata)
	if ctfvalue is None:
		bestdf = imgdata['scope']['defocus']
		apDisplay.printWarning("no acceptable ctf values found, using nominal defocus")
		return bestdf
	elif abs(ctfvalue['defocus1'] - ctfvalue['defocus2'])*1e6 > 0.01:
		bestdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		if msg is True:
			apDisplay.printWarning("astigmatism was estimated; averaging defocus values (%.3f, %.3f => %.3f) "
				%(ctfvalue['defocus1']*1e6, ctfvalue['defocus2']*1e6, bestdf*1e6) )
	else:
		bestdf = ctfvalue['defocus1']

	### make sure value is negative
	bestdf = -1.0*abs(bestdf)

	return bestdf

#=====================
def getDefocusAndampcontrastForImage(imgdata, ctf_estimation_runid=None, msg=False, method=None):
	"""
	takes an image and get the defocus (in negative meters) and amplitude contrast for that image
	"""
	#print "ERROR getDefocusAndampcontrastForImage(), use getBestCtfByResolution() instead"
	#sys.exit(1)
	
	if ctf_estimation_runid is not None:
		ctfvalue, conf = getCtfValueForImage(imgdata, ctf_estimation_runid, msg=False, method=method)
	else:
		ctfvalue, conf = getBestCtfValueForImage(imgdata, msg=False, method=method)

	if ctfvalue is None:
		bestdf = imgdata['scope']['defocus']
		bestamp = 0.1
		apDisplay.printWarning("no acceptable ctf values found, using nominal defocus")
	elif abs(ctfvalue['defocus1'] - ctfvalue['defocus2'])*1e6 > 0.01:
		bestdf = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		bestamp = ctfvalue['amplitude_contrast']
		if msg is True:
			apDisplay.printWarning("astigmatism was estimated; averaging defocus values (%.3f, %.3f => %.3f) "
				%(ctfvalue['defocus1']*1e6, ctfvalue['defocus2']*1e6, bestdf*1e6) )
	else:
		bestdf = ctfvalue['defocus1']
		bestamp = ctfvalue['amplitude_contrast']

	### make sure value is negative
	bestdf = -1.0*abs(bestdf)

	return bestdf, bestamp

#=====================
def getBestDefocusAndampcontrastForImage(imgdata, msg=False, method=None):
	''' takes an image and get the best defocus (in negative meters) for that image '''
	#print "ERROR getBestDefocusAndampcontrastForImage(), use getBestCtfByResolution() instead"
	#sys.exit(1)

	return getDefocusAndampcontrastForImage(imgdata, msg=msg, method=method)

#=====================
def getCtfValueForImage(imgdata, ctf_estimation_runid=None, ctfavg=True, msg=True, method=None):
	"""
	takes an image and get the ctf value for that image for the specified ctf estimation run
	specified methods can be: ace2 or ctffind
	"""
	#print "ERROR getCtfValueForImage(), use getBestCtfByResolution() instead"
	#sys.exit(1)

	if ctf_estimation_runid is None:
		apDisplay.printError("This function requires a ctf_estimation_runid")

	### get all ctf values
	ctfq = appiondata.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = ctfq.query()

	### check if it has values
	if ctfvalues is None:
		return None, None
	### find the value
	ctfdata = None
	for ctfvalue in ctfvalues:
		### limit to specific method if requested:
		if method is not None and getCtfMethod(ctfvalue) != method:
			continue

		### specify ID for CTF run
		if ctfvalue['acerun'].dbid == ctf_estimation_runid:
			### make sure that CTF values were estimated		
			if ctfvalue['defocus1'] is None and ctfvalue['defocus2'] is None:
				apDisplay.printWarning("CTF estimation using the specified parameters did not work")
				return None, None
			else:
				ctfdata = ctfvalue
			break
	# no data found with the criteria
	if ctfdata is None:
		return None, None

	conf = calculateConfidenceScore(ctfvalue,ctfavg)

	if msg is True:
		printCtfData(ctfvalue)

	return ctfvalue, conf

#=====================
def calculateConfidenceScore(ctfdata, ctfavg=True):
	# get ctf confidence values
	conf1 = ctfdata['confidence']
	conf2 = ctfdata['confidence_d']
	conf3 = ctfdata['confidence_30_10']
	conf4 = ctfdata['confidence_5_peak']
	conf = max(conf1, conf2, conf3, conf4)
	if conf < 0:
		conf = 0
	return conf

#=====================
def getBestCtfValueForImage(imgdata, ctfavg=True, msg=True, method=None):
	"""
	takes an image and get the best ctfvalues for that image
	specified methods can be: ace2 or ctffind
	"""
	#print "ERROR getBestCtfValueForImage(), use getBestCtfByResolution() instead"
	#sys.exit(1)

	### get all ctf values
	ctfq = appiondata.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = ctfq.query()

	### check if it has values
	if ctfvalues is None:
		return None, None

	### find the best values
	bestconf = 0.0
	bestctfvalue = None
	count = 0
	for ctfvalue in ctfvalues:
		count += 1
		### limit to specific method if requested:
		if method is not None and getCtfMethod(ctfvalue) != method:
			continue

		conf = calculateConfidenceScore(ctfvalue, ctfavg)
		if msg is True:
			if ctfvalue['resolution_50_percent']:
				print "%d conf %.4f (res %.1f) (?? %.4f)"%(count, conf, ctfvalue['resolution_50_percent'], bestconf)
			else:
				print "%d conf %.4f (?? %.4f)"%(count, conf, bestconf)
				
		
		if conf > bestconf:
			bestconf = conf
			bestctfvalue = ctfvalue

	if bestctfvalue == None:
		return None, None

	if msg is True:
		print "selected conf %.2f"%(bestconf)
		printCtfData(bestctfvalue)

	return bestctfvalue, bestconf


#=====================
def getBestCtfByResolution(imgdata, msg=True, method=None):
	"""
	takes an image and get the best ctfvalues for that image
	specified methods can be: ace2 or ctffind
	"""
	### get all ctf values
	ctfq = appiondata.ApCtfData()
	ctfq['image'] = imgdata
	ctfvalues = ctfq.query()

	if msg is True:
		print "Found %d ctf values"%(len(ctfvalues))

	### check if it has values
	if ctfvalues is None:
		print "no CTF values found in database"
		return None

	### find the best values
	bestres50 = 1000.0
	bestctfvalue = None
	for ctfvalue in ctfvalues:
		conf = calculateConfidenceScore(ctfvalue)
		if conf < 0.3:
			continue
		if method is not None:
			imgmethod = getCtfMethod(ctfvalue)
			if method != imgmethod:
				continue
		res50 = ctfvalue['resolution_50_percent']
		if res50 is None:
			continue
		if msg is True:
			print "%.3f -- %s"%(res50, ctfvalue['acerun']['name'])
		if res50 is None:
			continue
		if res50 < bestres50:
			bestres50 = res50
			bestctfvalue = ctfvalue

	if bestctfvalue is None:
		print "no best value"
		return None

	if msg is True:
		print "*** %.3f"%(bestres50)
		printCtfData(bestctfvalue)

	return bestctfvalue

#=====================
def getBestTiltCtfValueForImage(imgdata):
	"""
	takes an image and get the tilted ctf parameters for that image
	"""
	#print "ERROR getBestTiltCtfValueForImage(), use getBestCtfByResolution() instead"
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

