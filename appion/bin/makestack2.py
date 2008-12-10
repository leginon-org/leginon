#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import math
import time
import glob
## never, ever, ever import *
#from numpy import *
import numpy
#appion
import appionLoop
import apImage
import apDisplay
import apDatabase
import apParticle
import apCtf
import apStack
import apDefocalPairs
import appionData
import apPeaks
import apParticle
import apStackMeanPlot
import apDog
import apEMAN
import apProject
import apFile
import apImagicFile
import leginondata
#legacy
#import selexonFunctions  as sf1

class makestack (appionLoop.AppionLoop):

############################################################
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Pre-loop Functions 
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
############################################################

	def preLoopFunctions(self):
		if self.params['selexonId'] is None and self.params['sessionname'] is not None:
			self.params['selexonId'] = apParticle.guessParticlesForSession(sessionname=params['sessionname'])
	
		self.insertStackRun()
	
		self.checkPixelSize()

		# get defocus pair images from database if defocpair option is selected
		if self.params['defocpair']:
			self.imgtree = self.getImgsDefocPairFromSelexonId()

		# remove existing stack
		if self.params['nocontinue']:
			self.removeExistingStack()
			self.totpart = 0
		else:
			self.totpart = self.setExistingStackInfo()
			
		if self.params['partlimit'] is not None and self.params['partlimit'] <= self.totpart:
			apDisplay.printError("Number of particles in existing stack already exceeds limit!")
		
	############################################################
	## Check pixel size
	############################################################
	def checkPixelSize(self):
		# make sure that images all have same pixel size:
		# first get pixel size of first image:
		apDisplay.printMsg("Making sure all images are of the same pixel size...")
		
		if len(self.imgtree) == 0:
			return
		self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		for imgdata in self.imgtree:
			# get pixel size
			if apDatabase.getPixelSize(imgdata) != self.params['apix']:
				apDisplay.printWarning("This particle selection run contains images of varying pixelsizes, a stack cannot be created")
				
	############################################################
	## Remove existing stack
	############################################################
	def removeExistingStack(self):
		# if making a single stack, remove existing stack if exists
		stackfile=os.path.join(self.params['rundir'], os.path.splitext(self.params['single'])[0])
		# if saving to the database, store the stack parameters
		if self.params['spider'] is True and os.path.isfile(stackfile+".spi"):
			os.remove(stackfile+".spi")
		if (os.path.isfile(stackfile+".hed")):
			os.remove(stackfile+".hed")
		if (os.path.isfile(stackfile+".img")):
			os.remove(stackfile+".img")

		self.params['numpart'] = 0
		
	############################################################
	## Retrive existing stack info
	############################################################
	def setExistingStackInfo(self):
		stackfile=os.path.join(self.params['rundir'], os.path.splitext(self.params['single'])[0])
		if (os.path.isfile(stackfile+".hed")):
			self.params['numpart'] = apFile.numImagesInStack(stackfile+".hed")
		else:
			self.params['numpart'] = 0
		
		return int(self.params['numpart'])
		
	############################################################
	## get defocus pair of images
	############################################################	
	def getImgsDefocPairFromSelexonId(self):
		startt = time.time()
		apDisplay.printMsg("Finding defoc pair images that have particles for selection run: id="+str(self.params['selexonId']))

		# get selection run id
		selexonrun = appionData.ApSelectionRunData.direct_query(self.params['selexonId'])
		if not (selexonrun):
			apDisplay.printError("specified runId '"+str(self.params['selexonId'])+"' not in database")
		
		# from id get the session
		self.params['sessionid']=selexonrun['session']

		# get all images from session
		dbimgq=leginondata.AcquisitionImageData(session=self.params['sessionid'])
		dbimginfo=dbimgq.query(readimages=False)

		if not (dbimginfo):
			apDisplay.printError("no images associated with this runId")

		apDisplay.printMsg("Find corresponding image entry in the particle database")
		# for every image, find corresponding image entry in the particle database
		dbimglist=[]
		self.params['sibpairs']={}
		for imgdata in dbimginfo:
			pimgq=appionData.ApParticleData()
			pimgq['image']=imgdata
			pimgq['selectionrun']=selexonrun
			pimg=pimgq.query(results=1)
			if pimg:
				siblingimage = apDefocalPairs.getTransformedDefocPair(imgdata,1)
				if siblingimage:
					#create a dictionary for keeping the dbids of image pairs so we don't have to query later
					self.params['sibpairs'][siblingimage.dbid] = imgdata.dbid
					dbimglist.append(siblingimage)
				else:
					apDisplay.printWarning("no shift data for "+apDisplay.short(imgdata['filename']))
		apDisplay.printMsg("completed in "+apDisplay.timeString(time.time()-startt))
		return (dbimglist)

		
############################################################
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Process Image 
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
############################################################

	def processImage(self, imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgdata['filename'])

		### first remove any existing boxed files
		shortfile = os.path.join(self.params['rundir'], shortname)
		rmfiles = glob.glob(shortfile+"*")
		for rmfile in rmfiles:
			apFile.removeFile(rmfile)

		# check to see if image is rejected by other criteria
		if self.rejectImage(imgdata) is False:
			self.params['badprocess'] = True
			return

		# get CTF parameters for image and skip if criteria is not met
		if self.getCtfParams(imgdata) is False:
			self.params['badprocess'] = True
			return

		# run batchboxer
		if self.params['ctftilt']:
			numpart = self.ctfTiltBatchBox(imgdata)
		else:
			numpart = self.batchBox(imgdata)

		# check to see if a temporary stack of boxed particles was formed
		normstack = os.path.join(self.params['rundir'], shortname+".hed")
		ctfstack = os.path.join(self.params['rundir'], shortname+".ctf.hed")
		if not os.path.isfile(normstack) and not os.path.isfile(ctfstack):
			apDisplay.printWarning("no particles were boxed from "+shortname+"\n")
			self.params['badprocess'] = True
			return
			
		# add boxed particles to a single stack
		if self.params['single']:
			self.singleStack(imgdata)

		self.stats['lastpeaks'] = numpart
		self.totpart = self.totpart + numpart

		# check if particle limit is met
		if self.params['partlimit'] is not None and self.totpart > self.params['partlimit']:
			apDisplay.printWarning("reached particle number limit of "+str(self.params['partlimit'])+"; now stopping")
			self.imgtree = []
			self.notdone = False

		### last remove any existing boxed files
		rmfiles = glob.glob(shortfile+"*")
		for rmfile in rmfiles:
			apFile.removeFile(rmfile)

	############################################################
	##  skip image if additional criteria is not met	
	############################################################
	def rejectImage(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])

		if self.params['mag']:
			if not apDatabase.checkMag(imgdata, self.params['mag']):
				apDisplay.printColor(shortname+".mrc was not at the specific magnification","cyan")
				return False

		if self.params['tiltangle'] is not None:
			tiltangle = apDatabase.getTiltAngleDeg(imgdata)
			apDisplay.printMsg("image tilt angle: "+str(tiltangle))
			# only want negatively tilted images
			if self.params['tiltangle'] == -1.0:
				if tiltangle > -3:
					apDisplay.printColor(shortname+".mrc has been rejected tiltangle: "+str(round(tiltangle,1))+\
						" != "+str(round(self.params['tiltangle'],1))+"\n","cyan")
					return False
			# only want positively tilted images
			elif self.params['tiltangle'] == 1.0:
				if tiltangle < 3:
					apDisplay.printColor(shortname+".mrc has been rejected tiltangle: "+str(round(tiltangle,1))+\
						" != "+str(round(self.params['tiltangle'],1))+"\n","cyan")
					return False
			# only want a specified tiltangle within a two-degree range
			elif abs(abs(self.params['tiltangle']) - abs(tiltangle)) > 2.0:
				apDisplay.printColor(shortname+".mrc has been rejected tiltangle: "+str(round(tiltangle,1))+\
					" != "+str(round(self.params['tiltangle'],1))+"\n","cyan")
				return False
		return True

	############################################################
	## get CTF parameters and skip image if criteria is not met
	############################################################
	def getCtfParams(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])
		self.ctfparams = {}
		
		if self.params['ctftilt']:
			### Get tilted CTF values
			ctfvalue = apCtf.getBestTiltCtfValueForImage(imgdata)

			if ctfvalue is not None:
				apCtf.ctfValuesToParams(ctfvalue, self.ctfparams)
			else:
				apDisplay.printColor(shortname+".mrc was rejected because it has no CTFtilt values\n","cyan")
				return False
		else:
			### Get CTF values
			ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
	
	 		if ctfvalue is None:
				if self.params['acecutoff'] or self.params['mindefocus'] or self.params['maxdefocus'] or self.params['phaseflipped']:
					apDisplay.printColor(shortname+".mrc was rejected because it has no ACE values\n","cyan")
					return False
				else:
					apDisplay.printWarning(shortname+".mrc has no ACE values")

	 		if ctfvalue is not None:
				apCtf.ctfValuesToParams(ctfvalue, self.ctfparams)

				### check that ACE estimation is above confidence threshold
				if self.params['acecutoff'] and conf < self.params['acecutoff']:
					apDisplay.printColor(shortname+".mrc is below ACE threshold (conf="+str(round(conf,3))+")\n","cyan")
					return False

				### skip micrograph that have defocus above or below min & max defocus levels
				if self.params['mindefocus'] and self.ctfparams['df'] > self.params['mindefocus']*1e6:
					apDisplay.printColor(shortname+".mrc defocus ("+str(round(self.ctfparams['df'],3))+\
						" um) is less than mindefocus ("+str(self.params['mindefocus']*1e6)+" um)\n","cyan")
					return False
				if self.params['maxdefocus'] and self.ctfparams['df'] < self.params['maxdefocus']*1e6:
					apDisplay.printColor(shortname+".mrc defocus ("+str(round(self.ctfparams['df'],3))+\
						" um) is greater than maxdefocus ("+str(self.params['maxdefocus']*1e6)+" um)\n","cyan")
					return False
		return True

############################################################
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Post-loop Functions 
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
############################################################

	def postLoopFunctions(self):
		### Averaging completed stack
		stackpath = os.path.join(self.params['rundir'], "start.hed")
		apStack.averageStack(stack=stackpath)
		if self.params['commit'] is True:
			stackid = apStack.getStackIdFromPath(stackpath)
			apStackMeanPlot.makeStackMeanPlot(stackid)

############################################################
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Functions for tilted CTF correction
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
############################################################

	############################################################
	## Batchbox for CTF tilt correction
	############################################################
	def ctfTiltBatchBox(self, imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
		print "processing:",shortname
		if self.params['uncorrected']:
			tmpname='temporaryCorrectedImage.mrc'
			imgarray = apImage.correctImage(imgdata, self.ctfparams)
			imgpath = os.path.join(self.params['rundir'],tmpname)
			apImage.arrayToMrc(imgarray,imgpath)
			print "processing", imgpath		
		elif self.params['stig']:
			apMatlab.runAceCorrect(imgdata, self.ctfparams)	
			tmpname = imgdata['filename']
			imgpath = os.path.join(self.params['rundir'],tmpname)
		else:
			imgpath = os.path.join(imgdata['session']['image path'], imgname+".mrc")
		output = os.path.join(self.params['rundir'], shortname+".hed")
		outputctf = os.path.join(self.params['rundir'], shortname+".ctf.hed")
		outputtemp = os.path.join(self.params['rundir'], shortname+"-temp.hed")
		outputtempimg = os.path.join(self.params['rundir'], shortname+"-temp.img")
		outputtempctf = os.path.join(self.params['rundir'], shortname+"-temp-ctf.hed")
		outputtempimgctf = os.path.join(self.params['rundir'], shortname+"-temp-ctf.img")

		# if getting particles from database, a temporary
		# box file will be created
		if self.params['selexonId']:
			dbbox=os.path.join(self.params['rundir'], shortname+".eman.box")
			if self.params['defocpair']:
				particles,shift = apParticle.getDefocPairParticles(imgdata,self.params)
			else:
				particles = apParticle.getParticles(imgdata, self.params['selexonId'])
				shift = {'shiftx':0, 'shifty':0,'scale':1}
			if len(particles) > 0:			
				###apply limits
				if self.params['correlationmin'] or self.params['correlationmax']:
					particles = self.eliminateMinMaxCCParticles(particles)
				
				###apply masks
				if self.params['checkmask']:
					particles = self.eliminateMaskedParticles(particles,imgdata)

				###if there is still particles				
				if len(particles) > 0: 
					hasparticles=True
					thrownout = 0
					#for each individual particle
					for i in range(len(particles)):
						part = particles[i]
						dbparts = self.saveIndvParticles(part,shift,dbbox,imgdata)
						f=open(dbbox,'r')
						lines=f.readlines()
						f.close()
						nptcls=len(lines)
						if self.params['selexonId'] and nptcls > 0:
							cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i" %(imgpath, dbbox, outputtemp, self.params['boxsize'])
							apEMAN.executeEmanCmd(cmd)
							
							imagic = apImagicFile.readImagic(output)
							for j in range(len(imagic['images'])):
								part = imagic['images'][i]
								dbparts[j]['mean'] = part.mean()
								dbparts[j]['stdev'] = part.std()
								#inserting stack particles into the database
								if self.params['commit'] is True:
									dbparts[j].insert()
							
							#if ctf correction is selected
							if self.params['phaseflipped'] is True:
								#ctf correct using ctftilt parameters
								self.ctftiltPhaseFlip(part, outputtemp, outputtempctf, imgdata)	

								#move temp particle to growing stack						
								appendcmd="proc2d %s %s" %(outputtempctf, outputctf)
								apEMAN.executeEmanCmd(appendcmd)
								#remove temp particle
								for tmpfile in (outputtemp, outputtempimg, outputtempctf, outputtempimgctf):
									apFile.removeFile(tmpfile)
							else:
								#move temp particle to growing stack						
								appendcmd="proc2d %s %s" %(outputtemp, output)
								apEMAN.executeEmanCmd(appendcmd)
								#remove temp particle
								for tmpfile in (outputtemp, outputtempimg):
									apFile.removeFile(tmpfile)
						else:
							thrownout+=1
					#number of particles for the micrograph
					numpart = i-thrownout+1
				else:
					hasparticles=False
					apDisplay.printColor(shortname+".mrc had no unmasked particles and has been rejected\n","cyan")
			else:
				hasparticles=False
				apDisplay.printColor(shortname+".mrc had no particles and has been rejected\n","cyan")
		else:
			apDisplay.printWarning("CTFtilt correction requires a selexon id!")

		apDisplay.printMsg("number of particles in this micrograph is " + str(numpart))
		return(numpart)

	############################################################
	## Saving Individual Particles
	############################################################
	def saveIndvParticles(self, particle, shift, dbbox, imgdata):
		plist=[]
		box=self.params['boxsize']
		imgxy = imgdata['camera']['dimension']
		eliminated=0
		dbparts=[]
	
		xcoord=int(math.floor(shift['scale']*(particle['xcoord']-shift['shiftx'])-(box/2)+0.5))
		ycoord=int(math.floor(shift['scale']*(particle['ycoord']-shift['shifty'])-(box/2)+0.5))

		if (xcoord>0 and xcoord+box <= imgxy['x'] and ycoord>0 and ycoord+box <= imgxy['y']):
			plist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
			dbparts.append(self.createStackParticle(prtl))
			# save the particles to the database
		else:
			eliminated+=1
		if eliminated > 0:
			apDisplay.printMsg(str(eliminated)+" particle(s) eliminated because out of bounds")
		#write boxfile
		boxfile=open(dbbox,'w')
		boxfile.writelines(plist)
		boxfile.close()
		
		return dbparts

	############################################################
	## Applying CTFtilt correction
	############################################################
	def ctftiltPhaseFlip(self, particle, tempinfile, tempoutfile, imgdata):

		### calculate defocus at given position
		CX = 2048
		CY = 2048
	
		N1 = -math.sin(self.ctfparams['tilt_axis_angle']* math.pi / 180)
		N2 = math.cos(self.ctfparams['tilt_axis_angle']* math.pi / 180)
		PSIZE = self.params['apix']
		DX = CX - particle['xcoord']
		DY = CY - particle['ycoord']
		
 		DF = (N1*DX+N2*DY)*PSIZE*math.tan(self.ctfparams['tilt_angle']* math.pi / 180)
		DFL1 = self.ctfparams['df1']*-1e4 + DF
		DFL2 = self.ctfparams['df2']*-1e4 + DF		
		DF_final = (DFL1+DFL2)/2

		### create input file and output file
		infile  = tempinfile
		outfile = tempoutfile	

		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		defocus = DF_final*-1.0e-4

		self.checkDefocus(defocus, shortname)

		emancmd = "applyctf %s %s parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,2,%f setparm flipphase" % ( infile,\
	  		outfile, defocus, ampconst, voltage, self.params['apix'])

		cmd="applyctf %s %s parm=%f,200,1,0.1,0,17.4,9,1.53,%i,2,%f setparm flipphase" % ( infile,\
		  outfile, defocus, voltage, self.params['apix'])
		apDisplay.printMsg("phaseflipping particles with defocus "+str(round(defocus,3))+" microns")
		apEMAN.executeEmanCmd(cmd)		
		
############################################################		
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Functions for untilted CTF correction
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
############################################################

	############################################################
	## Batchbox for untilted CTF correction
	############################################################
	def batchBox(self,imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
		print "processing:",shortname
		if self.params['uncorrected']:
			tmpname='temporaryCorrectedImage.mrc'
			imgarray = apImage.correctImage(imgdata, self.ctfparams)
			imgpath = os.path.join(self.params['rundir'],tmpname)
			apImage.arrayToMrc(imgarray,imgpath)
			print "processing", imgpath
		elif self.params['stig']:
			apMatlab.runAceCorrect(imgdata,self.ctfparams)	
			tmpname = imgdata['filename']
			imgpath = os.path.join(self.params['rundir'],tmpname)
		else:
			imgpath = os.path.join(imgdata['session']['image path'], imgname+".mrc")
		output = os.path.join(self.params['rundir'], shortname+".hed")
		outputctf = os.path.join(self.params['rundir'], shortname+".ctf.hed")
		outputtemp = os.path.join(self.params['rundir'], shortname+"-temp.hed")
		outputtempimg = os.path.join(self.params['rundir'], shortname+"-temp.img")
		outputtempctf = os.path.join(self.params['rundir'], shortname+"-temp-ctf.hed")
		outputtempimgctf = os.path.join(self.params['rundir'], shortname+"-temp-ctf.img")

		# if getting particles from database, a temporary
		# box file will be created
		if self.params['selexonId']:
			dbbox=os.path.join(self.params['rundir'], shortname+".eman.box")
			if self.params['defocpair']:
				particles,shift = apParticle.getDefocPairParticles(imgdata,self.params)
			else:
				particles = apParticle.getParticles(imgdata, self.params['selexonId'])
				shift = {'shiftx':0, 'shifty':0,'scale':1}
			if len(particles) > 0:			
				###apply limits
				if self.params['correlationmin'] or self.params['correlationmax']:
					particles=self.eliminateMinMaxCCParticles(particles)
				
				###apply masks
				if self.params['checkmask']:
					particles = eliminateMaskedParticles(particles,imgdata)
				
				###save particles
				### for untilted data set
				if len(particles) > 0:
					hasparticles=True
					dbparts = self.saveParticles(particles,shift,dbbox,imgdata)
				else:
					hasparticles=False
					apDisplay.printColor(shortname+".mrc had no unmasked particles and has been rejected\n","cyan")
			else:
				hasparticles=False
				apDisplay.printColor(shortname+".mrc had no particles and has been rejected\n","cyan")
		else:
			dbbox=shortname+".box"
			hasparticles=True
		
		if self.params['boxfiles']:
			return(0)	

		if hasparticles:
			#count number of particles in box file
			f=open(dbbox,'r')
			lines=f.readlines()
			f.close()
			nptcls=len(lines)
			
			if nptcls == 0:
				return(0)
			
			# write batchboxer command
			if self.params['selexonId']:
				cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i" %(imgpath, dbbox, output, self.params['boxsize'])
			elif self.params['boxsize']:
				cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i insideonly" %(imgpath, dbbox, output, self.params['boxsize'])
			else: 
		 		cmd="batchboxer input=%s dbbox=%s output=%s insideonly" %(imgpath, dbbox, output)

			apDisplay.printMsg("boxing "+str(nptcls)+" particles")
			apEMAN.executeEmanCmd(cmd)
			
			imagic = apImagicFile.readImagic(output)
			for i in range(len(imagic['images'])):
				part = imagic['images'][i]
				dbparts[i]['mean'] = part.mean()
				dbparts[i]['stdev'] = part.std()
				#inserting stack particles into the database
				if self.params['commit'] is True:
					dbparts[i].insert()	
			
			if self.params['stig']:
				os.remove(os.path.join(self.params['rundir'],tmpname))
						
			if self.params['phaseflipped'] is True:
				self.phaseFlip(imgdata)

			return(nptcls)		
		else:
			if self.params['stig']:
				os.remove(os.path.join(self.params['rundir'],tmpname))
			return(0)
			
	############################################################
	## Saving Particles on single micrograph
	############################################################			
	def saveParticles(self,particles,shift,dbbox,imgdata):
		plist=[]
		box=self.params['boxsize']
		imgxy=imgdata['camera']['dimension']
		eliminated=0
		dbparts=[]
		for i in range(len(particles)):
			part = particles[i]
			xcoord=int(math.floor(shift['scale']*(part['xcoord']-shift['shiftx'])-(box/2)+0.5))
			ycoord=int(math.floor(shift['scale']*(part['ycoord']-shift['shifty'])-(box/2)+0.5))

			if (xcoord>0 and xcoord+box <= imgxy['x'] and ycoord>0 and ycoord+box <= imgxy['y']):
				plist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
				dbparts.append(self.createStackParticle(part))
				# save the particles to the database
				
			else:
				eliminated+=1
		if eliminated > 0:
			apDisplay.printMsg(str(eliminated)+" particle(s) eliminated because out of bounds")
		#write boxfile
		boxfile=open(dbbox,'w')
		boxfile.writelines(plist)
		boxfile.close()
		return dbparts

	############################################################
	## Applying CTF correction to untilted micrograph
	############################################################		
	def phaseFlip(self, imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
		infile  = os.path.join(self.params['rundir'], shortname+".hed")
		outfile = os.path.join(self.params['rundir'], shortname+".ctf.hed")
		
		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		defocus, ampconst = apCtf.getBestDefocusAndAmpConstForImage(imgdata, display=True)
		defocus *= 1.0e6
		self.checkDefocus(defocus, shortname)

		emancmd = "applyctf %s %s parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,2,%f setparm flipphase" % ( infile,\
	  		outfile, defocus, ampconst, voltage, self.params['apix'])
		apDisplay.printMsg("phaseflipping particles with defocus "+str(round(defocus,3))+" microns")
		apEMAN.executeEmanCmd(emancmd)	

############################################################
## Shared function for tilted and untilted CTF correction
############################################################

	def createStackParticle(self, prtl):
		stackpq=appionData.ApStackParticlesData()
		stackpq['stack'] = self.stackdata
		stackpq['stackRun'] = self.stackrundata
		stackpq['particle']=prtl
		self.params['particleNumber'] += 1
		stackpq['particleNumber']=self.params['particleNumber']
		return stackpq

	def checkDefocus(self, defocus, shortname):
		if defocus > 0:
			apDisplay.printError("defocus is positive "+str(defocus)+" for image "+shortname)
		elif defocus < -1.0e3:
			apDisplay.printError("defocus is very big "+str(defocus)+" for image "+shortname)
		elif defocus > -1.0e-3:
			apDisplay.printError("defocus is very small "+str(defocus)+" for image "+shortname)

	def eliminateMinMaxCCParticles(self, particles):
		newparticles = []
		eliminated = 0
		for prtl in particles:
			if self.params['correlationmin'] and prtl['correlation'] < self.params['correlationmin']:
				eliminated += 1
			elif self.params['correlationmax'] and prtl['correlation'] > self.params['correlationmax']:
				eliminated += 1
			else:
				newparticles.append(prtl)
		if eliminated > 0:
			apDisplay.printMsg(str(eliminated)+" particle(s) eliminated due to min or max correlation cutoff")
		return newparticles
		
	def eliminateMaskedParticles(particles,imgdata):
		newparticles = []
		eliminated = 0
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		if self.params['defocpair']:
			imgdata = apDefocalPairs.getTransformedDefocPair(imgdata,2)
	#		print imgdata.dbid
		maskimg,maskbin = apMask.makeInspectedMask(sessiondata,self.params['checkmask'],imgdata)
		if maskimg is not None:
			for prtl in particles:
				binnedcoord = (int(prtl['ycoord']/maskbin),int(prtl['xcoord']/maskbin))
				if maskimg[binnedcoord] != 0:
					eliminated += 1
				else:
					newparticles.append(prtl)
			print eliminated,"particle(s) eliminated due to masking"
		else:
			print "no masking"
			newparticles = particles
		return newparticles

	############################################################
	## appending temporary stack to growing stack
	############################################################
	def singleStack(self,imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
 		if self.params['phaseflipped'] is True:
			imgpath = os.path.join(self.params['rundir'], shortname+'.ctf.hed')
		else:
			imgpath = os.path.join(self.params['rundir'], shortname+'.hed')
		output = os.path.join(self.params['rundir'], self.params['single'])

		cmd="proc2d %s %s" %(imgpath, output)

		if self.params['normalized'] is True:
			cmd += " norm=0.0,1.0"
			# edge normalization
			cmd += " edgenorm"	

		if self.params['highpass'] or self.params['lowpass']:
			cmd += " apix=%s" % self.params['apix']
			if self.params['highpass']:
				cmd += " hp=%s" % self.params['highpass']
			if self.params['lowpass']:
				cmd += " lp=%s" % self.params['lowpass']
				
		# bin images if specified
		if self.params['bin'] != 1:
			cmd += " shrink="+str(self.params['bin'])
			
		# unless specified, invert the images
		if self.params['inverted'] is True:
			cmd += " invert"	

		# if specified, create spider stack
		if self.params['spider'] is True:
			cmd += " spiderswap"	

	 	apDisplay.printMsg("appending particles to stack: "+output)
		# run proc2d & get number of particles
		f=os.popen(cmd)
		#apEMAN.executeEmanCmd(cmd)
 		lines=f.readlines()
		f.close()
		for n in lines:
			words=n.split()
			if 'images' in words:
				count=int(words[-2])	

		# create particle log file
		partlogfile = os.path.join(self.params['rundir'], "particles.info")
		f = open(partlogfile, 'a')
		for n in range(count-self.params['numpart']):
			particlenum = str(1+n+self.params['numpart'])
			line = str(particlenum)+'\t'+os.path.join(imgdata['session']['image path'], imgname+".mrc")
			f.write(line+"\n")
		f.close()

		self.params['numpart'] = count
		try:
			os.remove(os.path.join(self.params['rundir'], shortname+".hed"))
			os.remove(os.path.join(self.params['rundir'], shortname+".img"))
		except:
			apDisplay.printWarning(os.path.join(self.params['rundir'], shortname+".hed")+" does not exist!")
		if self.params['phaseflipped'] is True:
			apFile.removeStack(os.path.join(self.params['rundir'], shortname+".ctf.hed"))


############################################################
## Insert and Committing 
############################################################

	def insertStackRun(self):
		stparamq=appionData.ApStackParamsData()
		paramlist = ('boxSize','bin','phaseFlipped','aceCutoff','correlationMin','correlationMax',
			'checkMask','minDefocus','maxDefocus','fileType','inverted','normalized', 'defocpair',
			'lowpass','highpass','norejects')

		for p in paramlist:
			if p.lower() in self.params:
				stparamq[p] = self.params[p.lower()]
		paramslist = stparamq.query()	

		if not 'boxSize' in stparamq or stparamq['boxSize'] is None:
			print stparamq
			apDisplay.printError("problem in database insert")

		# make sure that NULL values were not filled in during query
		goodplist=None
		for plist in paramslist:
			notgood=None
			for p in paramlist:
				if plist[p] != self.params[p.lower()]:
					notgood=True
			if notgood is None:
				goodplist=plist
				continue



		# create a stack object
		stackq = appionData.ApStackData()
		stackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		stackq['name'] = self.params['single']	

		# create a stackRun object
		runq = appionData.ApStackRunData()
		runq['stackRunName'] = self.params['runid']
		runq['session'] = self.params['session']	

      # see if stack already exists in the database (just checking path)
		stacks = stackq.query(results=1)

		# recreate stack object
		stackq = appionData.ApStackData()
		stackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		stackq['name'] = self.params['single']
		stackq['description'] = self.params['description']
		stackq['hidden'] = False
		stackq['pixelsize'] = self.params['apix']*self.params['bin']*1e-10
		stackq['project|projects|project'] = apProject.getProjectIdFromSessionName(self.params['session']['name'])

		self.stackdata = stackq

		runids = runq.query(results=1)
		# recreate a stackRun object
		runq = appionData.ApStackRunData()
		runq['stackRunName'] = self.params['runid']
		runq['session'] = self.params['session']
		if goodplist:
			runq['stackParams'] = goodplist
		else:
			runq['stackParams'] = stparamq

		self.stackrundata = runq

		# create runinstack object
		rinstackq = appionData.ApRunsInStackData()

		rinstackq['stackRun'] = runq
		rinstackq['stack'] = stackq
		rinstackq['project|projects|project'] = apProject.getProjectIdFromSessionName(self.params['session']['name'])

		#print stacks[0]['path']

		# if not in the database, make sure run doesn't already exist
		if not stacks:
			if not runids:
				print "Inserting stack parameters into DB"
				if self.params['commit'] is True:
					self.removeExistingStack()
					rinstackq.insert()
			else:
				apDisplay.printError("Run name '"+self.params['runid']+"' already in the database")
		
		# if it's in the database, make sure that all other
		# parameters are the same, since stack will be re-written
		else:
			# make sure description is the same:
			if stacks[0]['description']!=self.params['description']:
				apDisplay.printError("Stack description is not the same!")
				# make sure the the run is the same:
			rinstack = rinstackq.query(results=1)
		
			## if no runinstack found, find out which parameters are wrong:
			if not rinstack:
				rinstackq = appionData.ApRunsInStackData()
				rinstackq['stack'] = stackq.query()[0]
				correct_rinstack=rinstackq.query()
				for i in correct_rinstack[0]['stackRun']['stackParams']:
					if correct_rinstack[0]['stackRun']['stackParams'][i] != stparamq[i]:
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
				apDisplay.printError("All parameters for a particular stack must be identical! \n"+\
							     "please check your parameter settings.")

			if self.params['nocontinue']:
				apDisplay.printWarning("Stack already exist in database! 'nocontinue' option chosen -- existing stack will be overwritten")
			else:
				apDisplay.printWarning("Stack already exist in database! Appending new particles to stack")			
	
			
############################################################
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Additional parameters
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
############################################################
		
	def specialDefaultParams(self):
		self.params['single']=None
		self.params['acecutoff']=None
		self.params['boxsize']=None
#		self.params['inspectfile']=None
		self.params['mag']=None
		self.params['phaseflipped']=False
		self.params['apix']=0.0
		self.params['kv']=0
		self.params['tiltangle']=None
		self.params['inverted']=True
		self.params['spider']=False
		self.params['df']=0.0
		self.params['correlationmin']=None
		self.params['correlationmax']=None
		self.params['mindefocus']=None
		self.params['maxdefocus']=None	
		self.params['selexonId']=None
		self.params['medium']=None
		self.params['normalized']=True
		self.params['checkmask']=None
		self.params['particleNumber']=0
		self.params['bin']=1
		self.params['partlimit']=None
		self.params['defocpair']=False
		self.params['uncorrected']=False
		self.params['stig']=False
		self.params['matlab']=None
		self.params['filetype']='imagic'
		self.params['lowpass']=None
		self.params['ctftilt']=False
		self.params['highpass']=None
		self.params['boxfiles']=False

	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='single'):
				self.params['single']=elements[1]
			elif (elements[0]=='ace'):
				self.params['acecutoff']=float(elements[1])
			elif (elements[0]=='boxsize'):
				self.params['boxsize']=int(elements[1])
			elif (elements[0]=='phaseflip'):
				self.params['phaseflipped']=True
			elif (elements[0]=='apix'):
				self.params['apix']=float(elements[1])
			elif (elements[0]=='tiltangle'):
				self.params['tiltangle']=float(elements[1])
			elif (elements[0]=='noinvert'):
				self.params['inverted']=False
			elif (elements[0]=='spider'):
				self.params['spider']=True
			elif (elements[0]=='prtlrunid'):
				self.params['selexonId']=int(elements[1])
			elif (elements[0]=='selexonmin'):
				self.params['correlationmin']=float(elements[1])
			elif (elements[0]=='selexonmax'):
				self.params['correlationmax']=float(elements[1])
			elif (elements[0]=='mindefocus'):
				self.params['mindefocus']=float(elements[1])
			elif (elements[0]=='maxdefocus'):
				self.params['maxdefocus']=float(elements[1])
			elif (elements[0]=='nonorm'):
				self.params['normalized']=False
			elif (elements[0]=='description'):
				self.params['description']=elements[1]
			elif (elements[0]=='ctftilt'):
				self.params['ctftilt']=True
			elif (elements[0]=='partlimit'):
				self.params['partlimit']=int(elements[1])
			elif (elements[0]=='hp' or elements[0]=='highpass'):
				self.params['highpass']=int(elements[1])
			elif (elements[0]=='lp' or elements[0]=='lowpass'):
				self.params['lowpass']=float(elements[1])
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif (elements[0]=='defocpair'):
				self.params['defocpair']=True
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a parameter")

	def specialParamConflicts(self):
		if self.params['boxsize'] is None:
			apDisplay.printError("A boxsize has to be specified")
		if self.params['description'] is None:
			apDisplay.printError("A description has to be specified")
		if (self.params['mindefocus'] is not None and 
				(self.params['mindefocus'] < -1e-3 or self.params['mindefocus'] > -1e-9)):
			apDisplay.printError("min defocus is not in an acceptable range, e.g. mindefocus=-1.5e-6")
		if (self.params['maxdefocus'] is not None and 
				(self.params['maxdefocus'] < -1e-3 or self.params['maxdefocus'] > -1e-9)):
			apDisplay.printError("max defocus is not in an acceptable range, e.g. maxdefocus=-1.5e-6")


if __name__ == '__main__':
	imgLoop = makestack()
	imgLoop.run()
