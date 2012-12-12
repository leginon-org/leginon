#FindEM specific options that will be depricated in the future

#pythonlib
import os
import threading
import sys
import time
import subprocess
import numpy

#appion
from appionlib import apDisplay
from appionlib import apImage
from appionlib import apDBImage
from appionlib import apParam
from appionlib import apFile
from appionlib import apPeaks
from appionlib import apFindEM

#===========
def runFindEM(imgdict, params, thread=False):
	"""
	runs a separate thread of findem.exe for each template
	to get cross-correlation maps
	"""
	### check image
	apFindEM.processAndSaveImage(imgdict, params)
	dwnimgname = imgdict['filename']+".dwn.mrc"
	if not os.path.isfile(dwnimgname):
		apDisplay.printError("cound not find image to process: "+dwnimgname)

	### check template
	if len(params['templatelist']) < 1:
		apDisplay.printError("templatelist == 0; there are no templates")

	joblist = []
	ccmapfilelist = []

	t0 = time.time()
	for i,templatename in enumerate(params['templatelist']):
		classavg = i + 1

		#DETERMINE OUTPUT FILE NAME
		#CHANGE THIS TO BE 00%i in future
		numstr = "%03d" % classavg
		#numstr = str(classavg%10)+"00"
		ccmapfile="cccmaxmap"+numstr+".mrc"
		apFile.removeFile(ccmapfile)

		#GET FINDEM RUN COMMANDS
		feed = findEMString(classavg, templatename, dwnimgname, ccmapfile, params)

		#RUN THE PROGRAM
		if thread is True:
			job = findemjob(feed)
			joblist.append(job)
			job.start()
		else:
			execFindEM(feed)

		#TO REMOVE LATER: Fake output
		fakeOutput(dwnimgname,ccmapfile,params)

		#STORE OUTPUT FILE
		ccmapfilelist.append(ccmapfile)

	### WAIT FOR THREADS TO COMPLETE
	if thread is True:
		apDisplay.printMsg("waiting for "+str(len(joblist))+" findem threads to complete")
		for i,job in enumerate(joblist):
			while job.isAlive():
				sys.stderr.write(".")
				time.sleep(1.5)
		sys.stderr.write("\n")
	apDisplay.printMsg("FindEM finished in "+apDisplay.timeString(time.time()-t0))

	for ccmapfile in ccmapfilelist:
		if not os.path.isfile(ccmapfile):
			apDisplay.printError("findem.exe did not run or crashed.\n")

	return ccmapfilelist

#===========
class findemjob(threading.Thread):
	def __init__ (self, feed):
		threading.Thread.__init__(self)
		self.feed = feed
	def run(self):
		findemexe = getFindEMPath()
		#apDisplay.printMsg("threading "+os.path.basename(findemexe))
		logf = open("findem.log", "a")
		proc = subprocess.Popen( 'echo "'+findemexe+' '+self.feed+'"', shell=True, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
		proc.wait()

#===========
def execFindEM(feed):
	t0 = time.time()
	findemexe = getFindEMPath()
	apDisplay.printMsg("running "+os.path.basename(findemexe))
	logf = open("findem.log", "a")
	proc = subprocess.Popen( 'echo "'+findemexe+' '+feed+'"', shell=True, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
	fin = proc.stdin
	fin.flush()
	waittime = 2.0
	while proc.poll() is None:
		sys.stderr.write(".")
		time.sleep(waittime)
		logf.flush()
	proc.wait()
	apDisplay.printMsg("\nfinished in "+apDisplay.timeString(time.time()-t0))

def getBoxFileName(ccmapfilename):
	return ccmapfilename[:-4]+'.box'
	
#===========
def findEMString(classavg, templatename, dwnimgname, ccmapfile, params):
	#IMAGE INFO
	if not os.path.isfile(dwnimgname):
		apDisplay.printError("image file, "+dwnimgname+" was not found")
	apDisplay.printMsg("image file, "+apDisplay.short(dwnimgname))
	feed = dwnimgname+" "

	#TEMPLATE INFO
	if not os.path.isfile(templatename):
		apDisplay.printError("template file, "+templatename+" was not found")

	apDisplay.printMsg("template file, "+templatename)
	feed += templatename + " "

	#CCMAPFILE INFO
	apDisplay.printMsg("ccmap file, "+ccmapfile)
	feed += ccmapfile + ' '

	#BOXFILE OUTPUT
	boxfilename = getBoxFileName(ccmapfile)
	feed += boxfilename + ' '

	#FAKE BOX SIZE
	feed += '1 '

	#PEAK_Theshold
	feed += str(params["thresh"])+" "

	#CORRELATION MAP CALCULATION PARTICLE RADIUSa IN PIXELS
	feed += str(int(params["diam"]/(2.0*params["apix"]*params["bin"])))+" "

	#PEAK SEARCH DISTANCE IN PIXELS
	feed += str(int(params["ccsearchmult"]*params["diam"]/(params["apix"]*params["bin"])))+" "

	#ROTATION PARAMETERS
	strt = str(params["startang"+str(classavg)])
	end  = str(params["endang"+str(classavg)])
	incr = str(params["incrang"+str(classavg)])

	feed += strt+' '+end+' '+incr+" "

	#GRAPHICAL CARD DEVICE NUMBER
	borderwidth = str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)
	feed += str(params["gcdev"])+" "

	return feed

#===========
def getFindEMPath():
	unames = os.uname()
	if True:
	#if unames[-1].find('64') >= 0:
		exename = 'automatch'
	else:
		apDisplay.printError(exename+" not implemented for 32 bit computer")
	findempath = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(findempath):
		findempath = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(findempath):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return findempath

def findPeaks(imgdict, maplist, params,pikfile=True):
	#modeified from apPeaks.findPeaks to read peaks from box file per ccmap
	peaktreelist = []
	count = 0

	imgname = imgdict['filename']
	mapdir = os.path.join(params['rundir'], "maps")
	bin =       int(params["bin"])
	diam =      float(params["diam"])
	apix =      float(params["apix"])
	olapmult =  float(params["overlapmult"])
	maxthresh = params["maxthresh"]
	maxsizemult = float(params["maxsize"])
	msg =       not params['background']
	tmpldbid =  None

	for imgmap in maplist:
		count += 1

		if 'templateIds' in params:
			#template correlator
			tmpldbid =  params['templateIds'][count-1]

		peaktree = getPeaksFromBoxFile(imgmap)
		newpeaktree = []
		for peakdict in peaktree:
			peakdict = apPeaks.attachTemplateLabel(peakdict,count,tmpldbid,diam)
			newpeaktree.append(peakdict)
		peaktree = newpeaktree
		#write pikfile
		if pikfile is True:
			apPeaks.peakTreeToPikFile(peaktree, imgname, count, params['rundir'])

		#append to complete list of peaks
		peaktreelist.append(peaktree)

	peaktree = apPeaks.mergePeakTrees(imgdict, peaktreelist, params, msg, pikfile=pikfile)

	#max threshold
	if maxthresh is not None:
		precount = len(peaktree)
		peaktree = apPeaks.maxThreshPeaks(peaktree, maxthresh)
		postcount = len(peaktree)
		#if precount != postcount:
		apDisplay.printMsg("Filtered %d particles above threshold %.2f"%(precount-postcount,maxthresh))

	return peaktree

def initializePeakDict():
	peakdict = {}
	keys = ['ycoord','xcoord','correlation','peakarea','peakstddev','peakmoment']
	for key in keys:
		peakdict[key] = 1
	return peakdict

def getPeaksFromBoxFile(imgmapname):
	peakTree = []
	boxfilename = getBoxFileName(imgmapname)
	f = open(boxfilename,'r')
	lines = f.readlines()
	for line in lines:
		good = []
		bits = line.split(' ')
		for bit in bits:
			if len(bit):
				good.append(bit)
		peakdict = initializePeakDict()
		peakdict['ycoord']    = int(good[1])
		peakdict['xcoord']    = int(good[0])
		peakdict['correlation'] = float(good[4])
		peakTree.append(peakdict)
	return peakTree

def fakeOutput(imgname,ccmapfile,params):
	a = apImage.mrcToArray(imgname)
	a = numpy.zeros(a.shape)
	apImage.arrayToMrc(a,ccmapfile)
	apFile.safeCopy('/home/acheng/Projects/Gfindem/example.box', getBoxFileName(ccmapfile))
	
