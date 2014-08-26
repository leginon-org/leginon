#FindEM specific options that will be depricated in the future

#pythonlib
import os
import threading
import sys
import time
import subprocess
import string
import random
import multiprocessing
#appion
from appionlib import apDisplay
from appionlib import apImage
from appionlib import apDBImage
from appionlib import apParam
from appionlib import apFile
# for FindEM2
#from pyami import imagefun 

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
	### FindEM crashes when an input image is longer than 76 characters
	if len(dwnimgname) > 76:
		randlink = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
		randlink+= '.mrc'
		os.symlink(dwnimgname, randlink)

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
		if len(dwnimgname) > 76:
			feed = findEMString(100+classavg, templatename, randlink, ccmapfile1, params)
		else:
			feed = findEMString(100+classavg, templatename, dwnimgname, ccmapfile1, params)
		sys.exit()
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
	
	### FindEM crashes when an input image is longer than 76 characters
	if len(dwnimgname) > 76:
		randlink = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
		randlink+= '.mrc'
		os.symlink(dwnimgname, randlink)

	### check template
	if len(params['templatelist']) < 1:
		apDisplay.printError("templatelist == 0; there are no templates")

	joblist = []
	ccmapfilelist = []

#	For FindEM2
#	### generate circular mask for FindEM2
#	apDisplay.printMsg("creating mask file for template matching")
#	img = apImage.mrcToArray(params['templatelist'][0])
#	circlemask = 1 - imagefun.filled_circle(img.shape,img.shape[0]/2*0.95)
#	apImage.arrayToMrc(circlemask,"tmpmask.mrc")
#	del img,circlemask
	
	workimg = randlink if len(dwnimgname) > 76 else dwnimgname

	### create list of inputs for findem threads
	feeds = []
	for i,templatename in enumerate(params['templatelist']):
		classavg = i + 1

		# OUTPUT FILE NAME
		numstr = "%03d" % classavg
		ccmapfile="cccmaxmap"+numstr+".mrc"
		apFile.removeFile(ccmapfile)

		feeds.append(findEMString(classavg, templatename, workimg, ccmapfile, params))

		#STORE OUTPUT FILE
		ccmapfilelist.append(ccmapfile)

	### launch findem threads
	t0 = time.time()
	findemexe = getFindEMPath()
	pool = multiprocessing.Pool(processes=params['nproc'])
	runner = findemrunner(findemexe,len(params['templatelist']))
	for i,feed in enumerate(feeds):
		pool.apply_async(runner, (i,feed))
	pool.close()
	pool.join()

	apDisplay.printMsg("\nFindEM finished in "+apDisplay.timeString(time.time()-t0)+"\n")
#	For FindEM2
#	os.remove("tmpmask.mrc")

	### READ OUTPUT FILES
	ccmaplist = []
	for ccmapfile in ccmapfilelist:
		if not os.path.isfile(ccmapfile):
			apDisplay.printError("findem.exe did not run or crashed.\n")
		ccmaxmap = apImage.mrcToArray(ccmapfile)
		ccmaplist.append(ccmaxmap)

	return ccmaplist

#===========
class findemrunner(object):
	def __init__(self,exe,numtmplts):
		self.findemexe = exe
		self.totnum=numtmplts
	def __call__(self,num,feed):
		apDisplay.printMsg("threading %s (%i of %i)" % (os.path.basename(self.findemexe),num+1,self.totnum))
		logf = open("findem.log", "a")
		p = subprocess.Popen( self.findemexe, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
		fin = p.stdin
		fin.write(feed)
		output,error = p.communicate()

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

#	For FindEM2
#	#MASK
#	feed +="tmpmask.mrc\n"

#	For FindEM2, comment out border
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
		imgarray = apDBImage.correctImage(imgdata)
	else:
		imgarray = imgdata['image']
	imgarray = apImage.preProcessImage(imgarray, params=params, msg=False)
	apImage.arrayToMrc(imgarray, imgpath, msg=False)

	return True

#===========
def getFindEMPath():
	unames = os.uname()
	if unames[-1].find('64') >= 0:
#		For FindEM2
#		exename = '/ami/sw/packages/FindEM2/FindEM2_V1.00.exe'
		exename = 'findem64.exe'
	else:
		exename = 'findem32.exe'
	findempath = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(findempath):
		findempath = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(findempath):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return findempath

