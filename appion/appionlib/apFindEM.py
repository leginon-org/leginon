#FindEM specific options that will be depricated in the future

#pythonlib
import os
import threading
import sys
import time
import subprocess
#appion
from appionlib import apDisplay
from appionlib import apImage
from appionlib import apParam
from appionlib import apFile

#===========
def runSpectralFindEM(imgdict, params, thread=False):
	"""
	runs a separate thread of findem.exe for each template
	to get cross-correlation maps
	"""
	imgname = imgdict['filename']
	dwnimgname = os.path.splitext(imgname)[0]+".dwn.mrc"
	os.chdir(params['rundir'])
	joblist = []
	ccmaplist = []

	processAndSaveImage(imgdict, params)

	if len(params['templatelist']) < 1:
		apDisplay.printError("templatelist == 0; there are no templates")

	for i,templatename in enumerate(params['templatelist']):
		classavg = i + 1

		#First round: normal findem: template x image
		numstr = "%03d" % (100+classavg)
		ccmapfile1 = "cccmaxmap"+numstr+".mrc"
		apFile.removeFile(ccmapfile1)
		params["startang"+str(100+classavg)] = params["startang"+str(classavg)]
		params["endang"+str(100+classavg)] = params["endang"+str(classavg)]
		params["incrang"+str(100+classavg)] = params["incrang"+str(classavg)]
		feed = findEMString(100+classavg, templatename, dwnimgname, ccmapfile1, params)
		execFindEM(feed)

		#Second round: template x template
		numstr = "%03d" % (200+classavg)
		ccmapfile2 = "cccmaxmap"+numstr+".mrc"
		apFile.removeFile(ccmapfile2)
		params["startang"+str(200+classavg)] = params["startang"+str(classavg)]
		params["endang"+str(200+classavg)] = params["endang"+str(classavg)]
		params["incrang"+str(200+classavg)] = params["incrang"+str(classavg)]
		feed = findEMString(200+classavg, templatename, templatename, ccmapfile2, params)
		execFindEM(feed)

		#Final round: (template x template) x (template x image) = spectral
		numstr = "%03d" % (300+classavg)
		ccmapfile3 = "cccmaxmap"+numstr+".mrc"
		apFile.removeFile(ccmapfile3)
		params["startang"+str(300+classavg)] = 0
		params["endang"+str(300+classavg)] = 10
		params["incrang"+str(300+classavg)] = 20
		feed = findEMString(300+classavg, ccmapfile2, ccmapfile1, ccmapfile3, params)
		execFindEM(feed)

		#READ OUTPUT FILE
		if not os.path.isfile(ccmapfile3):
			apDisplay.printError("findem.exe did not run or crashed.\n"+
				"Did you source useappion.sh?")
		else:
			ccmaxmap = apImage.mrcToArray(ccmapfile3)
			ccmaplist.append(ccmaxmap)

	return ccmaplist

#===========
def runFindEM(imgdict, params, thread=False):
	"""
	runs a separate thread of findem.exe for each template
	to get cross-correlation maps
	"""
	### check image
	processAndSaveImage(imgdict, params)
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

	### READ OUTPUT FILES
	ccmaplist = []
	for ccmapfile in ccmapfilelist:
		if not os.path.isfile(ccmapfile):
			apDisplay.printError("findem.exe did not run or crashed.\n")
		ccmaxmap = apImage.mrcToArray(ccmapfile)
		ccmaplist.append(ccmaxmap)

	return ccmaplist

#===========
class findemjob(threading.Thread):
	def __init__ (self, feed):
		threading.Thread.__init__(self)
		self.feed = feed
	def run(self):
		findemexe = getFindEMPath()
		#apDisplay.printMsg("threading "+os.path.basename(findemexe))
		logf = open("findem.log", "a")
		proc = subprocess.Popen( findemexe, shell=True, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
		fin = proc.stdin
		fin.write(self.feed)
		fin.flush()
		fin.close()
		proc.wait()

#===========
def execFindEM(feed):
	t0 = time.time()
	findemexe = getFindEMPath()
	apDisplay.printMsg("running "+os.path.basename(findemexe))
	logf = open("findem.log", "a")
	proc = subprocess.Popen( findemexe, shell=True, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
	fin = proc.stdin
	fin.write(feed)
	fin.flush()
	waittime = 2.0
	while proc.poll() is None:
		sys.stderr.write(".")
		time.sleep(waittime)
		logf.flush()
	proc.wait()
	apDisplay.printMsg("\nfinished in "+apDisplay.timeString(time.time()-t0))

#===========
def findEMString(classavg, templatename, dwnimgname, ccmapfile, params):

	#IMAGE INFO
	if not os.path.isfile(dwnimgname):
		apDisplay.printError("image file, "+dwnimgname+" was not found")
	apDisplay.printMsg("image file, "+apDisplay.short(dwnimgname))
	feed = dwnimgname+"\n"

	#TEMPLATE INFO
	if not os.path.isfile(templatename):
		apDisplay.printError("template file, "+templatename+" was not found")

	apDisplay.printMsg("template file, "+templatename)
	feed += templatename + "\n"

	#DUMMY VARIABLE; DOES NOTHING
	feed += "-200.0\n"

	#BINNED APIX
	feed += str(params["apix"]*params["bin"])+"\n"

	#PARTICLE DIAMETER
	feed += str(params["diam"])+"\n"

	#RUN ID FOR OUTPUT FILENAME
	numstr = ("%03d" % classavg)+"\n"
	#numstr = str(classavg%10)+"00\n"
	feed += numstr

	#ROTATION PARAMETERS
	strt = str(params["startang"+str(classavg)])
	end  = str(params["endang"+str(classavg)])
	incr = str(params["incrang"+str(classavg)])

	feed += strt+','+end+','+incr+"\n"

	#BORDER WIDTH
	borderwidth = str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)
	feed += borderwidth+"\n"

	return feed

#===========
def processAndSaveImage(imgdata, params):
	imgpath = os.path.join(params['rundir'], imgdata['filename']+".dwn.mrc")
	if os.path.isfile(imgpath):
		return False

	#downsize and filter leginon image
	if params['uncorrected']:
		imgarray = apImage.correctImage(imgdata, params)
	else:
		imgarray = imgdata['image']
	imgarray = apImage.preProcessImage(imgarray, params=params, msg=False)
	apImage.arrayToMrc(imgarray, imgpath, msg=False)

	return True

#===========
def getFindEMPath():
	unames = os.uname()
	if unames[-1].find('64') >= 0:
		exename = 'findem64.exe'
	else:
		exename = 'findem32.exe'
	findempath = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(findempath):
		findempath = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(findempath):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return findempath

