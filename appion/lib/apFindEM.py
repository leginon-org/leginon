#FindEM specific options that will be depricated in the future

#pythonlib
import os
import threading
import sys
import time
import subprocess
#appion
import apDisplay
import apImage
import apParam

#===========
def runFindEM(imgdict, params, thread=False):
	"""
	runs a separate thread of findem.exe for each template 
	to get cross-correlation maps
	"""
	imgname = imgdict['filename']
	os.chdir(params['rundir'])
	joblist = []
	ccmaplist = []

	processAndSaveImage(imgdict, params)

	if len(params['templatelist']) < 1:
		apDisplay.printError("templatelist == 0; there are no templates")

	for i,templatename in enumerate(params['templatelist']):
		classavg = i + 1

		#DETERMINE OUTPUT FILE NAME
		#CHANGE THIS TO BE 00%i in future
		numstr = "%03d" % classavg
		#numstr = str(classavg%10)+"00"
		ccmapfile="cccmaxmap"+numstr+".mrc"
		if (os.path.isfile(ccmapfile)):
			os.remove(ccmapfile)

		#GET FINDEM RUN COMMANDS
		feed = findEMString(classavg, templatename, imgname, ccmapfile, params)

		#RUN THE PROGRAM
		if thread is True:
			current = findemjob(feed)
			joblist.append(current)
			current.start()
		else:
			execFindEM(feed)

		#READ OUTPUT FILE
		if not os.path.isfile(ccmapfile):
			apDisplay.printError("findem.exe did not run or crashed.\n"+
				"Did you source useappion.sh?")
		else:
			ccmaxmap = apImage.mrcToArray(ccmapfile)
			ccmaplist.append(ccmaxmap)

	if thread is True:
		for job in joblist:
			job.join()
	return ccmaplist

#===========
class findemjob(threading.Thread):
	def __init__ (self, feed):
		threading.Thread.__init__(self)
		self.feed = feed
   	def run(self):
			findemexe = getFindEMPath()
			apDisplay.printMsg("threading "+os.path.basename(findemexe))
			logf = open("findem.log", "a")
			proc = subprocess.Popen( findemexe, shell=True, 
				stdin=subprocess.PIPE, stdout=logf, stderr=logf)
			fin = proc.stdin
			fin.write(self.feed)
			fin.flush()
			fin.close()

#===========
def execFindEM(feed):
	t0 = time.time()
	findemexe = getFindEMPath()
	apDisplay.printMsg("running "+os.path.basename(findemexe))
	logf = open("findem.log", "a")
	proc = subprocess.Popen( findemexe, shell=True, 
		stdin=subprocess.PIPE, stdout=logf, stderr=logf)
	fin = proc.stdin
	fin.write(feed)
	fin.flush()
	proc.wait()
	apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))

#===========
def findEMString(classavg, templatename, imgname, ccmapfile, params):

	#IMAGE INFO
	dwnimgname = os.path.splitext(imgname)[0]+".dwn.mrc"
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
	if params['multiple_range'] == True:
		strt = str(params["startang"+str(classavg)])
		end  = str(params["endang"+str(classavg)])
		incr = str(params["incrang"+str(classavg)])
	else:
		strt = str(params["startang"])
		end  = str(params["endang"])
		incr = str(params["incrang"])
	feed += strt+','+end+','+incr+"\n"

	#BORDER WIDTH
	borderwidth = str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)
	feed += borderwidth+"\n"

	return feed

#===========
def processAndSaveImage(imgdata, params):
	#downsize and filter leginon image
	if params['uncorrected']:
		imgarray = apImage.correctImage(imgdata, params)
	else:
		imgarray = imgdata['image']
	imgarray = apImage.preProcessImage(imgarray, params=params, msg=False)
	imgpath = os.path.join(params['rundir'], imgdata['filename']+".dwn.mrc")
	apImage.arrayToMrc(imgarray, imgpath, msg=False)
	return

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

