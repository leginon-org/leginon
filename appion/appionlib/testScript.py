#!/usr/bin/python -O

#python
import re
import os
import sys
import time
import random
import subprocess
#appion
import leginon.leginondata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParticle
from appionlib import apStack
from appionlib import apParam
from appionlib import apFile
from appionlib.apCtf import ctfdb
from appionlib import apAlignment
from appionlib import apDatabase
from appionlib import appiondata

# This is a base class for test scripts. To create a new test script: 

class TestScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ --commit --show-cmd --verbose --limit ]")
		### showcmd
		self.parser.add_option("-S", "--show-cmd", dest="showcmd", default=True,
			action="store_true", help="Show each command before running")
		self.parser.add_option("--no-show-cmd", dest="showcmd", default=True,
			action="store_false", help="Do not show each command before running")
		### verbose
		self.parser.add_option("-v", "--verbose", dest="verbose", default=True,
			action="store_true", help="Show command output while running")
		self.parser.add_option("-q", "--quiet", dest="verbose", default=True,
			action="store_false", help="Do not show command output while running")

		self.parser.add_option("-u", "--uploadimages", dest="uploadimages", default=False,
			action="store_true", help="Download and upload images to new session to process")
		self.parser.add_option("--session", dest="sessionname",
			help="Session name containing GroEL images to process", metavar="XX")
		
		# Options to pass to AppionLoop programs
		self.parser.add_option("--preset", dest="preset",
			help="Image preset associated with processing run, e.g. --preset=en", metavar="PRESET")
		self.parser.add_option("--reprocess", dest="reprocess", type="float",
			help="Only process images that pass this reprocess criteria")
		self.parser.add_option("--limit", dest="limit", type="int",
			help="Only process <limit> number of images")
		self.parser.add_option("--continue", dest="continue", default=True,
			action="store_true", help="Continue processing run from last image")
		self.parser.add_option("--no-continue", dest="continue", default=True,
			action="store_false", help="Do not continue processing run from last image")
		self.parser.add_option("--no-wait", dest="wait", default=True,
			action="store_false", help="Do not wait for more images after completing loop")
		self.parser.add_option("--no-rejects", dest="norejects", default=False,
			action="store_true", help="Do not process hidden or rejected images")
		self.parser.add_option("--sib-assess", dest="sibassess", default=False,
			action="store_true", help="Use image assessment from sibling image")		
		self.parser.add_option("--best-images", dest="bestimages", default=False,
			action="store_true", help="Only process exemplar or keep images")
		self.parser.add_option("--shuffle", dest="shuffle", default=False,
			action="store_true", help="Shuffle the images before processing, i.e. process images out of order")
		self.parser.add_option("--reverse", dest="reverse", default=False,
			action="store_true", help="Process the images from newest to oldest")

		return

	#=====================
	def checkConflicts(self):
		if self.params['uploadimages'] is False and self.params['sessionname'] is None:
			apDisplay.printError("Please set uploadimages to true or provide a GroEL session name")
		if self.params['uploadimages'] is True and self.params['sessionname'] is not None:
			apDisplay.printError("Please set uploadimages to false or remove session name")
		if self.params['description'] is None:
			self.params['description'] = 'running test suite application'
		return

	#=====================
	def setRunDir(self):
		if self.params['uploadimages'] is True:
			self.sessionname = self.timestamp
			try:
				basedir = leginon.leginonconfig.mapPath(leginon.leginonconfig.IMAGE_PATH)
				basedir.replace("leginon", "appion")
			except:
				basedir = os.getcwd()
		else:
			self.sessionname = self.params['sessionname']
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			basedir = os.path.abspath(sessiondata['image path'])
			basedir.replace("leginon", "appion")
			basedir = re.sub("appion.*","appion",basedir)
		self.params['rundir'] = os.path.join(basedir, self.sessionname, "testsuite", self.timestamp)
		return

	#=====================
	def runCommand(self, cmd):
		t0 = time.time()
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "magenta")
			sys.stderr.write(
				apDisplay.colorString("COMMAND: \n","magenta")
				+apDisplay.colorString(cmd, "cyan")+"\n")
			apDisplay.printColor("###################################", "cyan")
		try:
			if self.params['verbose'] is False:
				logf = open('testsuite-programs.log' ,'a')
				proc = subprocess.Popen(cmd, shell=True, 
					stdout=logf, stderr=logf)
			else:
				proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
		except:
			apDisplay.printError("could not run command: "+cmd)
		runtime = time.time() - t0
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "cyan")
			apDisplay.printColor("command ran in "+apDisplay.timeString(runtime), "cyan")
		if runtime < 1:
			apDisplay.printError("command runtime was too short: "
				+apDisplay.timeString(runtime))
		elif runtime < 10:
			apDisplay.printWarning("command runtime was very short: "
				+apDisplay.timeString(runtime))
			return False

		if self.params['verbose'] is False:
			logf.close()

		return True
	
	#=====================
	def insertTestRunData(self):
		#sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		sessiondata = self.getSessionData()

		q = appiondata.ApTestRunData()
		q['session'] = sessiondata
		q['name'] = self.params['runname']
		q['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		q['append_timestamp'] = self.timestamp
		results = q.query()
		if not results:
			q.insert()
			return q
		return results[0]
	
	#=====================
	def downloadImagesFromAMI(self):
		imglist = []
		from urllib import urlretrieve
		imgdict = {
			110: '06jul12a_00022gr_00037sq_00025hl_00005en.mrc',
			111: '06jul12a_00035gr_00063sq_00012hl_00004en.mrc',
			112: '06jul12a_00015gr_00028sq_00004hl_00002en.mrc',
			113: '06jul12a_00015gr_00028sq_00023hl_00002en.mrc',
			114: '06jul12a_00015gr_00028sq_00023hl_00004en.mrc',
			115: '06jul12a_00022gr_00013sq_00002hl_00004en.mrc',
			116: '06jul12a_00022gr_00013sq_00003hl_00005en.mrc',
		}
		for key in imgdict.keys():
			imgfile = os.path.join(self.params['rundir'], imgdict[key])
			url = ("http://ami.scripps.edu/redmine/attachments/download/%d/%s"
				%(key, imgdict[key]))
			apDisplay.printMsg("Downloading image '%s'"%(imgdict[key]))
			urlretrieve(url, imgfile)
			if not os.path.isfile(imgfile):
				apDisplay.printError("could not download file: %s"%(url))
			if apFile.fileSize(imgfile) < 30e6:
				apDisplay.printError("error in downloaded file: %s"%(url))
			imglist.append(imgfile)
		return imglist

	#=====================
	def createImageBatchFile(self, imglist):
		imgstats = {
			'pixelsize': 0.815e-10,
			'binx': 1,
			'biny': 1,
			'mag': 100000,
			'defocus': -2.0e-6,
			'voltage': 120000,
		}

		imagedatfile = os.path.join(self.params['rundir'], "image%s.dat"%(self.sessionname))
		f = open(imagedatfile, "w")
		for imgfile in imglist:
			outstr = ("%s\t%.3e\t%d\t%d\t%d\t%.3e\t%d\n"
				%(imgfile, imgstats['pixelsize'], imgstats['binx'], imgstats['biny'], 
				imgstats['mag'], imgstats['defocus'], imgstats['voltage']))
			f.write(outstr)
		f.close()
		return imagedatfile

	#=====================
	def getInstrumentIds(self):
		### get scope
		scopeq = leginon.leginondata.InstrumentData()
		print scopeq
		scopeq['name'] = 'SimTEM'
		scopedatas = scopeq.query(results=1)
		if not scopedatas or len(scopedatas) < 1:
			apDisplay.printError("Could not find simulated scope")
		random.shuffle(scopedatas)
		scopeid = scopedatas[0].dbid
		apDisplay.printMsg("Selected scope %d from host %s"	
			%(scopeid, scopedatas[0]['hostname']))

		### get camera
		cameraq = leginon.leginondata.InstrumentData()
		cameraq['name'] = 'SimCCDCamera'
		cameradatas = cameraq.query(results=1)
		if not cameradatas or len(cameradatas) < 1:
			apDisplay.printError("Could not find simulated CCD camera")
		random.shuffle(scopedatas)
		carmeraid = cameradatas[0].dbid
		apDisplay.printMsg("Selected camera %d from host %s"	
			%(carmeraid, cameradatas[0]['hostname']))
		return scopeid, carmeraid

	#=====================
	def uploadImages(self):
		### get simulated instrument ids
		scopeid, cameraid = self.getInstrumentIds()
		### Download images
		imglist = self.downloadImagesFromAMI()
		### create batch file
		imagedatfile = self.createImageBatchFile(imglist)
		### run command
		script = os.path.join(self.appiondir, "bin", "imageloader.py ")
		params = (" --runname=%s --projectid=%d --session=%s --batch=%s --scopeid=%d --cameraid=%d --description='%s' "
			%(self.sessionname, self.params['projectid'], self.sessionname, 
			imagedatfile, scopeid, cameraid, self.params['description']))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)
		for imgname in imglist:
			apFile.removeFile(imgname)

	#=====================
	def setAppionFlags(self):
		
		params = " "
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		if self.params['preset']:
			params += " --preset=" + self.params['preset'] + " "
		if self.params['limit']:
			params += " --limit=%d " %(self.params['limit'],)
		if self.params['continue'] is True:
			params += " --continue "
		else:
			params += " --no-continue "
		if self.params['norejects'] is True:
			params += " --no-rejects "
		if self.params['sibassess'] is True:
			params += " --sib-assess "
		if self.params['bestimages'] is True:
			params += " --best-images "
		if self.params['shuffle'] is True:
			params += " --shuffle "
		if self.params['reverse'] is True:
			params += " --reverse "
			
		self.appionFlags = params

	
	#=====================
	#  Sample Command:
	#
	#  dogPicker.py --projectid=303 --preset=en --session=zz07jul25b --runname=dogrun2 --rundir=/ami/data17/appion/zz07jul25b/extract/dogrun2 
	#  --no-rejects --no-wait --commit --limit=4 --continue --peaktype=centerofmass --maxthresh=0.8 --thresh=0.42 --invert 
	#  --median=2 --lowpass=15 --highpass=0 --planereg --bin=4 --diam=150 --pixlimit=4.0 --numslices=3 --sizerange=50 --expId=8556 --jobtype=dogpicker
	#
	def dogPicker(self, diam=150, thresh=0.42, maxthresh=0.8, peaktype='centerofmass', median=2, lowpass=15, highpass=0, maxsize=0.5, numslices=3, pixlimit=4.0, sizerange=50, bin=4 ):
		runnum = apParticle.getNumSelectionRunsFromSession(self.sessionname)
		dogname = "dogrun%d-%s"%(runnum+1, self.timestamp)

		# Build the command
		script = os.path.join(self.appiondir, "bin", "dogPicker.py ")
		params = (" --runname=%s --projectid=%d --session=%s --diam=%d --thresh=%.2f --maxthresh=%.2f --invert --no-wait --peaktype=%s --median=%d --lowpass=%d --highpass=%d --planereg --maxsize=%.2f --numslices=%d --pixlimit=%.2f --sizerange=%d  --bin=%d"
			%(dogname, self.params['projectid'], self.sessionname, diam, thresh, maxthresh, peaktype, median, lowpass, highpass, maxsize, numslices, pixlimit, sizerange, bin ))
		
		# Add appion flags 
		params += self.appionFlags
		
		# Run the command
		self.runCommand(script+" "+params)
		return dogname

	#=====================
	def aceTwo(self, bin, blur=10):
		runnum = ctfdb.getNumCtfRunsFromSession(self.sessionname)
		acetwoname = "acetwo%d-%s"%(runnum+1, self.timestamp)

		script = os.path.join(self.appiondir, "bin", "pyace2.py ")
		params = (" --runname=%s --projectid=%d --session=%s --no-wait --bin=%d --edge1=%.1f"
			%(acetwoname, self.params['projectid'], self.sessionname, bin, blur))

		# Add appion flags 
		params += self.appionFlags
		
		self.runCommand(script+" "+params)

	#=====================
	def makeStack(self, boxsize=512, bin=2, ctfcutoff=0.7):
		runnum = apStack.getNumStacksFromSession(self.sessionname)
		stackname = "stack%d-%s"%(runnum+1, self.timestamp)

		selectid = apParticle.getRecentSelectionIdFromSession(self.sessionname)

		script = os.path.join(self.appiondir, "bin", "makestack2.py ")
		params = ((" --runname=%s --projectid=%d --session=%s --no-wait --boxsize=%d --bin=%d --ctfcutoff=%.2f --invert --phaseflip --flip-type=ace2image --selectionid=%d --description='%s'")
			%(stackname, self.params['projectid'], self.sessionname, boxsize, bin, ctfcutoff, selectid, 'running test suite application'))
		
		# Add appion flags 
		params += self.appionFlags
			
		self.runCommand(script+" "+params)
		return stackname

	#=====================
	def filterStack(self, stackname, minx=600, maxx=1600, miny=82, maxy=150):
		runnum = apStack.getNumStacksFromSession(self.sessionname)
		filtstackname = "meanfilt%d-%s"%(runnum+1, self.timestamp)

		stackid = apStack.getStackIdFromRunName(stackname, self.sessionname)
		if not stackid:
			apDisplay.printError("Failed to find stack %s for session %s"%(stackname, self.sessionname))


		script = os.path.join(self.appiondir, "bin", "stackFilter.py ")
#		params = ((" --runname=%s --projectid=%d --old-stack-id=%d --minx=%d --maxx=%d --miny=%d --maxy=%d --description='%s'")
#			%(filtstackname, self.params['projectid'], stackid, 
#			600, 1000, 82, 105, 
#			'filtering junk with test suite application'))
		params = ((" --runname=%s --projectid=%d --old-stack-id=%d --minx=%d --maxx=%d --miny=%d --maxy=%d --description='%s'")
			%(filtstackname, self.params['projectid'], stackid, 
			minx, maxx, miny, maxy, 
			'filtering junk with test suite application'))
		
		# Add appion flags 
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "

		self.runCommand(script+" "+params)

		stackid = apStack.getStackIdFromSubStackName(filtstackname, self.sessionname)
		if not stackid:
			apDisplay.printError("Failed to create stack %s for session %s during stackFilter test."%(filtstackname, self.sessionname))

		return filtstackname

	#=====================
	def maxLike(self, substackname, lowpass=10, highpass=2000, numref=3, bin=2, maxiter=12):
		runnum = apAlignment.getNumAlignRunsFromSession(self.sessionname)
		maxlikename = "maxlike%d-%s"%(runnum+1, self.timestamp)

		stackid = apStack.getStackIdFromSubStackName(substackname, self.sessionname)
		if not stackid:
			apDisplay.printError("Failed to find stack %s for session %s during maxLikeAlignment test."%(substackname, self.sessionname))
		

		print (self.params['projectid'], stackid, 10, 2000, 3, 1, 12, 'max like with test suite application')
		

		script = os.path.join(self.appiondir, "bin", "maxlikeAlignment.py")
		params = (" --runname=%s --projectid=%d --stack=%d --lowpass=%d --highpass=%d --num-ref=%d --bin=%d --savemem --converge=slow --mirror --fast --fast-mode=narrow --max-iter=%d --description='%s'"
			%(maxlikename, self.params['projectid'], stackid, lowpass, highpass, numref, bin, maxiter, 
			'max like with test suite application'))
		
		# Add appion flags 
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "

		self.runCommand(script+" "+params)

		return maxlikename

		#uploadMaxlikeAlignment.py --rundir=/ami/data00/appion/10may07o04/align/maxlike1 -t 10may07q59 --commit --projectid=5 

	#=====================
	def uploadMaxLike(self, maxlikename):
		maxjobdata = apAlignment.getMaxlikeJobDataForUpload(maxlikename)
		tstamp = maxjobdata['timestamp']
		rundir = maxjobdata['path']['path']
		script = os.path.join(self.appiondir, "bin", "uploadMaxlikeAlignment.py")
		params = (" --projectid=%d --timestamp=%s --rundir=%s "%(self.params['projectid'], tstamp, rundir))
		
		# Add appion flags 
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "

		self.runCommand(script+" "+params)

	#=====================
	# imgnums is a list formatted as a string of the image numbers to use 
	def createTemplates(self, maxlikename, imgnums="0,1,2", diam=180 ):
		runname = "template-%s"%(self.timestamp)

		alignrunid = apAlignment.getAlignRunIdFromName(maxlikename)
		script = os.path.join(self.appiondir, "bin", "uploadTemplate.py")
		params = (" --projectid=%d --alignid=%d --session=%s --diam=%d --imgnums=%s --runname=%s --description='%s'"
			%(self.params['projectid'], alignrunid, self.sessionname, diam, imgnums, 
			runname, 'templates from max like with test suite application'))
		
		# Add appion flags 
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "

		self.runCommand(script+" "+params)

	#=====================
	def getMostRecentTemplates(self, num=3):
		templateq = appiondata.ApTemplateImageData()
		templatedatas = templateq.query(results=num)
		if not templatedatas:
			apDisplay.printError("No templates found")
		templateids = []
		for templatedata in templatedatas:
			templateids.append(templatedata.dbid)
		return templateids

	#=====================
	def templatePick(self, diam=256, thresh=0.5, maxthresh=0.8, maxsize=0.05, lowpass=25, bin=4, rangelist="0,360,15x"):
		runnum = apParticle.getNumSelectionRunsFromSession(self.sessionname)
		tmplname = "tmplrun%d-%s"%(runnum+1, self.timestamp)

		templateids = self.getMostRecentTemplates(3)
		
		script = os.path.join(self.appiondir, "bin", "templateCorrelator.py ")
		params = (" --runname=%s --projectid=%d --session=%s --diam=%d --thresh=%.2f --maxthresh=%.2f --invert --no-wait --planereg --maxsize=%.2f --lowpass=%d --bin=%d --thread-findem "
			%(tmplname, self.params['projectid'], self.sessionname, diam, thresh, maxthresh, maxsize, lowpass, bin))

		# TODO: what should these lists be set to?
		tmplliststr = " --template-list="
		rangeliststr = " --range-list="
		for templateid in templateids:
			tmplliststr += "%d,"%(templateid)
			#rangeliststr += "%d,%d,%dx"%(0,360,15)
			rangeliststr += rangelist
		params += tmplliststr[:-1]
		params += rangeliststr[:-1]
		
		# Add appion flags 
		params += self.appionFlags

		self.runCommand(script+" "+params)
		return tmplname

	#=====================
	def pdbToModel(self):
		runname = "pdbdensity-%s"%(self.timestamp)

		script = os.path.join(self.appiondir, "bin", "modelFromPDB.py ")
		params = (" --runname=%s --projectid=%d --session=%s --pdbid=%s --apix=%.2f --boxsize=%d --res=%d --symm=%s --biolunit --method=%s "
			%(runname, self.params['projectid'], self.sessionname, '1grl', 1.63, 256, 30, 'd7', 'eman'))

		# Add appion flags 
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		
		self.runCommand(script+" "+params)
		return runname

	#=====================
	def getMostRecentDensities(self, num=3):
		densityq = appiondata.Ap3dDensityData()
		densitydatas = densityq.query(results=num)
		if not densitydatas:
			apDisplay.printError("No densities found")
		densityids = []
		for densitydata in densitydatas:
			densityids.append(densitydata.dbid)
		return densityids

	#=====================
	def uploadModel(self):
		densityids = self.getMostRecentDensities(1)
		if not densityids:
			apDisplay.printError("failed to get 3d density")

		densityid = densityids[0]
		densitydata = appiondata.Ap3dDensityData.direct_query(densityid)

		runname = "pdbmodel-%s"%(self.timestamp)

		script = os.path.join(self.appiondir, "bin", "uploadModel.py ")
		params = (" --runname=%s --projectid=%d --session=%s --densityid=%d --zoom=1.0 --description='%s' "
			%(runname, self.params['projectid'], self.sessionname, densityid, densitydata['description'],))
		
		# Add appion flags 
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "

		self.runCommand(script+" "+params)
		return runname

	#=====================.
	def start(self):
		
		self.setRunDir()
		self.setAppionFlags()
		
		if self.params['commit'] is True:
			self.insertTestRunData()			

		if self.params['uploadimages'] is True:
			self.uploadImages()	

		### Dog Picker
		self.dogPicker()

		### Ace 2
		self.aceTwo(bin=2, blur=10)
		self.aceTwo(bin=2, blur=6)
		self.aceTwo(bin=4)

		### Make stack
		stackname = self.makeStack()

		### Filter stack
		filtstackname = self.filterStack(stackname)
		
		### Maximum likelihood
		maxlikename = self.maxLike(filtstackname)

		### Upload max like
		self.uploadMaxLike(maxlikename)

		### Upload templates
		self.createTemplates(maxlikename)
		return

		### Template pick
		self.templatePick()

		### Make stack
		stackname = self.makeStack()

		### Filter stack
		#filtstackname = self.filterStack(stackname)

		### create PDB model
		self.pdbToModel()

		### Upload model as initial model
		self.uploadModel()

		### Do reconstruction
		### Upload recon
		return

#=====================
if __name__ == "__main__":
	tester = TestScript()
	tester.start()
	tester.close()

