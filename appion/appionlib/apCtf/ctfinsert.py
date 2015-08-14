#Part of the new pyappion

#pythonlib
import os
import re
import sys
import math
import shutil
#appion
from appionlib import apFile
from appionlib import apDisplay
from appionlib import appiondata
from appionlib.apCtf import ctfdisplay
from appionlib.apCtf import ctfdb

debug = False
confirm_degrees = False
radian_suspects = 0

#====================
#====================
def validateAndInsertCTFData(imgdata, ctfvalues, rundata, rundir, fftpath=None, fftfreq=None):
	"""
	function to insert CTF values in database
	"""
	apDisplay.printMsg("Committing ctf parameters for "
		+apDisplay.short(imgdata['filename'])+" to database")

	if ctfvalues is None or not 'defocus2' in ctfvalues:
		apDisplay.printWarning("No ctf values")
		return False

	### convert to common convention
	ctfvalues = convertDefociToConvention(ctfvalues)

	### check to make sure parameters are valid
	isvalid = checkParams(ctfvalues)
	if isvalid is False:
		apDisplay.printWarning("Bad CTF values, insert but not create images")

	### run the main CTF display program
	opimagedir = os.path.join(rundir, "opimages")
	if isvalid is True:
		oldctfvalues = ctfvalues.copy()
		ctfvalues = runCTFdisplayTools(imgdata, ctfvalues, opimagedir, fftpath, fftfreq)
		# check if image creation failed
		if ctfvalues is None:
			ctfvalues = oldctfvalues

	### clean rundir from all entries:
	if not rundir.endswith("/"):
		rundir += "/"
	for key in ctfvalues.keys():
		if isinstance(ctfvalues[key], str) and ctfvalues[key].startswith(rundir):
			ctfvalues[key] = ctfvalues[key].replace(rundir, "")

	### time to insert
	ctfq = appiondata.ApCtfData()
	ctfq['acerun'] = rundata
	ctfq['image'] = imgdata
	if debug is True:
		apDisplay.printMsg("CTF data values")
		print ctfvalues
	for key in ctfq.keys():
		if key in ctfvalues:
			ctfq[key] = ctfvalues[key]
			if debug is True:
				apDisplay.printMsg("%s :: %s"%(key, ctfvalues[key]))
		elif debug is True:
			try:
				apDisplay.printMsg("SKIPPING %s :: %s"%(key, ctfvalues[key]))
			except KeyError:
				apDisplay.printMsg("SKIPPING %s "%(key))
	ctfdb.printCtfData(ctfq)
	ctfq.insert()

	return

#====================
#====================
def runCTFdisplayTools(imgdata, ctfvalues, opimagedir, fftpath=None, fftfreq=None):
	### RUN CTF DISPLAY TOOLS
	ctfdisplaydict = ctfdisplay.makeCtfImages(imgdata, ctfvalues, fftpath, fftfreq)
	if ctfdisplaydict is None:
		return ctfvalues
	### save the classic images as well
	if 'graph1' in ctfvalues:
		ctfvalues['graph3'] = os.path.basename(ctfvalues['graph1'])
	if 'graph2' in ctfvalues:
		ctfvalues['graph4'] = os.path.basename(ctfvalues['graph2'])
	### new powerspec file
	psfile = os.path.join(opimagedir, ctfdisplaydict['powerspecfile'])
	if not os.path.isfile(ctfdisplaydict['powerspecfile']):
		apDisplay.printWarning("Powerspec file not created")
	else:
		print ctfdisplaydict['powerspecfile']
		shutil.move(ctfdisplaydict['powerspecfile'], psfile)
		ctfvalues['graph1'] = os.path.basename(psfile)
	### new 1d plot file
	plotfile = os.path.join(opimagedir, ctfdisplaydict['plotsfile'])
	shutil.move(ctfdisplaydict['plotsfile'], plotfile)
	ctfvalues['graph2'] = os.path.basename(plotfile)
	ctfvalues['confidence_30_10'] = ctfdisplaydict['conf3010']
	ctfvalues['confidence_5_peak'] = ctfdisplaydict['conf5peak']
	ctfvalues['overfocus_conf_30_10'] = ctfdisplaydict['overconf3010']
	ctfvalues['overfocus_conf_5_peak'] = ctfdisplaydict['overconf5peak']
	ctfvalues['resolution_80_percent'] = ctfdisplaydict['res80']
	ctfvalues['resolution_50_percent'] = ctfdisplaydict['res50']
	if not 'confidence_d' in ctfvalues or ctfvalues['confidence_d'] is None:
		ctfvalues['confidence_d'] = ctfdisplaydict['conf5peak']
	if not 'confidence' in ctfvalues or ctfvalues['confidence'] is None:
		ctfvalues['confidence'] = ctfdisplaydict['conf3010']

	### override the confidence
	ctfvalues['confidence'] = max(ctfvalues['confidence'], ctfvalues['confidence_d'], ctfdisplaydict['conf5peak'], ctfdisplaydict['conf3010'])

	return ctfvalues

#====================
#====================
def convertDefociToConvention(ctfvalues):
	if debug is True:
		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f"%
			(ctfvalues['defocus1'], ctfvalues['defocus2'], ctfvalues['angle_astigmatism']), "cyan")

	# amplitude contrast must be btw 0.0 and 0.5
	# sometimes we get a slightly negative number from ACE1, see bug #2003
	if abs(ctfvalues['amplitude_contrast']) < 0.005:
		ctfvalues['amplitude_contrast'] = 0.0

	# program specific corrections?
	angle = ctfvalues['angle_astigmatism']

	#by convention: abs(ctfvalues['defocus1']) < abs(ctfvalues['defocus2'])
	if abs(ctfvalues['defocus1']) > abs(ctfvalues['defocus2']):
		# incorrect, need to shift angle by 90 degrees
		apDisplay.printWarning("|def1| > |def2|, flipping defocus axes")
		defocus1 = ctfvalues['defocus2']
		defocus2 = ctfvalues['defocus1']
		angle += 90
	else:
		# correct, ratio > 1
		defocus1 = ctfvalues['defocus1']
		defocus2 = ctfvalues['defocus2']
	if defocus1 < 0 and defocus2 < 0:
		apDisplay.printWarning("Negative defocus values, taking absolute value")
		defocus1 = abs(defocus1)
		defocus2 = abs(defocus2)

	# get angle within range -90 < angle <= 90
	while angle > 90:
		angle -= 180
	while angle < -90:
		angle += 180

	if debug is True:
		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f"%
			(defocus1, defocus2, angle), "cyan")

		perdiff = abs(defocus1-defocus2)/abs(defocus1+defocus2)
		print ("Defocus Astig Percent Diff %.2f -- %.3e, %.3e"
				%(perdiff*100,defocus1,defocus2))

	ctfvalues['defocus1'] = defocus1
	ctfvalues['defocus2'] = defocus2
	ctfvalues['angle_astigmatism'] = angle

	return ctfvalues

#====================
#====================
def checkParams(ctfvalues):
	"""
	check to see if CTF values exist and are in an appropriate range
	"""
	### set values as local variables
	focus1 = ctfvalues['defocus1']
	focus2 = ctfvalues['defocus2']
	cs = ctfvalues['cs']
	volts = ctfvalues['volts']
	ampcontrast = ctfvalues['amplitude_contrast']
	absangle = abs(ctfvalues['angle_astigmatism'])
	### print debug
	if debug is True:
		print "  Defocus1 %.2f microns (underfocus is positive)"%(focus1*1e6)
		if focus1 != focus2:
			print "  Defocus2 %.2f microns (underfocus is positive)"%(focus2*1e6)
		print "  C_s %.1f mm"%(cs)
		print "  High tension %.1f kV"%(volts*1e-3)
		print ("  Amp Contrast %.3f (shift %.1f degrees)"
			%(ampcontrast, math.degrees(-math.asin(ampcontrast))))

	### check angle to make sure we reach values in range above 2*Pi and below 90
	global confirm_degrees
	global radian_suspects
	if absangle > 6.3:
		confirm_degrees = True
		radian_suspects = 0
	elif not confirm_degrees and absangle > 0 and absangle < 1.571:
		msg = "suspicious angle astigmatism, may be in radians (%.4f)"%(absangle)
		radian_suspects += 1
		apDisplay.printWarning(msg)
		return False
	if not confirm_degrees and radian_suspects > 5:
		print "confirm_degrees", confirm_degrees
		msg = "too many (%d) suspicious angle astigmatisms, likely in radians"%(radian_suspects)
		apDisplay.printWarning(msg)

	### various test of data
	if focus1*1e6 > 25.0 or focus1*1e6 < 0.01:
		msg = "atypical defocus #1 value %.4f microns (underfocus is positve)"%(focus1*1e6)
		apDisplay.printWarning(msg)
		return False
	if focus2*1e6 > 25.0 or focus2*1e6 < 0.01:
		msg = "atypical defocus #2 value %.4f microns (underfocus is positve)"%(focus2*1e6)
		apDisplay.printWarning(msg)
		return False
	if cs > 9.0 or cs < 0.0:
		msg = "atypical C_s value %.4f mm"%(cs)
		apDisplay.printWarning(msg)
		return False
	if volts*1e-3 > 400.0 or volts*1e-3 < 60:
		msg = "atypical high tension value %.4f kiloVolts"%(volts*1e-3)
		apDisplay.printWarning(msg)
		return False
	if ampcontrast < 0.0 or ampcontrast > 0.5:
		msg = "atypical amplitude contrast value %.4f"%(ampcontrast)
		apDisplay.printWarning(msg)
		return False
	### passed all test, return True
	return True
