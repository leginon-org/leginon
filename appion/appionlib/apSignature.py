#Signature specific options that will be depricated in the future

#pythonlib
import os
import sys
import time
import subprocess
#appion
from appionlib import apDisplay
from appionlib import apImage
from appionlib import apParam
from appionlib import apFile

#===========
def runSignature(imgdict, params):
	"""
	runs Signature
	"""
	### check image
	processAndSaveImage(imgdict, params)
	dwnimgname = imgdict['filename']+".dwn.mrc"
	if not os.path.isfile(dwnimgname):
		apDisplay.printError("cound not find image to process: "+dwnimgname)

	t0 = time.time()
	
	#get Signature run commands
	feed = signatureString(params['templatename'], dwnimgname, params)
	execSignature(feed)

	apDisplay.printMsg("Signature finished in "+apDisplay.timeString(time.time()-t0))

	### READ OUTPUT FILES
	outf = "picks.ems/particles/img.spd"
	if not os.path.isfile(outf):
		apDisplay.printError("signature.exe did not run or crashed.\n")

	return outf

#===========
class signaturejob():
	def __init__ (self, feed):
		self.feed = feed
	def run(self):
		signatureexe = getSignaturePath()
		logf = open("signature.log", "a")
		proc = subprocess.Popen( signatureexe, shell=True, stdout=logf, stderr=logf)
		proc.wait()

#===========
def execSignature(feed):
	t0 = time.time()
	signatureexe = getSignaturePath()
	apDisplay.printMsg("running "+os.path.basename(signatureexe))
	logf = open("signature.log", "a")

	sigcmd=signatureexe+feed
	proc = subprocess.Popen(sigcmd, shell=True, stdout=logf, stderr=logf)
	waittime = 2.0
	while proc.poll() is None:
		sys.stderr.write(".")
		time.sleep(waittime)
		logf.flush()
	proc.wait()
	apDisplay.printMsg("\nfinished in "+apDisplay.timeString(time.time()-t0))

#===========
def signatureString(templatename, dwnimgname, params):

	# start batch mode
	feed = " -c -film img -space picks"

	#IMAGE INFO
	if not os.path.isfile(dwnimgname):
		apDisplay.printError("image file, "+dwnimgname+" was not found")
	apDisplay.printMsg("image file, "+apDisplay.short(dwnimgname))
	feed += " -source %s"%dwnimgname

	#TEMPLATE INFO
	if not os.path.isfile(templatename):
		apDisplay.printError("template file, "+templatename+" was not found")
	apDisplay.printMsg("template file, "+templatename)
	feed += " -template %s"%templatename

	#BINNED APIX
	feed += " -pixelsize %.3f"%(params["apix"]*params["bin"])

	#PARTICLE DIAMETER
	feed += " -partsize %i"%int(params['diam'])

	#BORDER WIDTH
	borderwidth = int((params["diam"]/params["apix"]/params["bin"])/2)+1
	feed += " -margin %i"%borderwidth

	#threshold
	feed += " -lcf-thresh %.2f"%params['thresh']

	#particle distance
	feed += " -partdist %i"%(params['overlapmult']*params['diam'])

	#resizing set to 1 always (binning done beforehand)
	feed += " -resize 1"

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
def partToPeakTree(pfile,bin):
	f=open(pfile)
	peaktree=[]
	for line in f:
		d=line.strip().split()
		if len(d)<4:
			continue
		if d[0][0]==';':
			continue
		try:
			float(d[0])
		except:
			continue
		part={}
		part['xcoord']=int(float(d[2]))*bin
		part['ycoord']=int(float(d[3]))*bin
		# placeholder for peakarea
		part['peakarea']=1
		peaktree.append(part)
	f.close()

	return peaktree

#===========
def getSignaturePath():
	unames = os.uname()
	if unames[-1].find('64') >= 0:
		exename = 'signature64.exe'
	else:
		exename = 'signature32.exe'
	signaturepath = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(signaturepath):
		signaturepath = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(signaturepath):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return signaturepath

