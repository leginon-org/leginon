#!/usr/bin/python
# beam tilt correction functions

import os, sys, re
import time
import math
import numpy
from scipy import ndimage,fftpack
from pyami import mem,mrc,imagefun,fftfun
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apFile
from appionlib import apImagicFile
from leginon import leginondata

class correctStackBeamTiltPhaseShift(apImagicFile.processStack):
	def __init__(self, oldstackid, newstack, msg=True):
		apImagicFile.processStack.__init__(self,msg)
		self.imgnum = 0
		self.stacklist = []
		self.stackarray = []
		self.partperiter = 0
		self.stackid = oldstackid
		self.newstack = newstack
		self.ht = None
		self.cam = None
		self.tem = None

	def processParticle(self, partarray):
		path = './'
		self.outstackfile = self.newstack
		fft = fftpack.fft2(partarray)
		if self.imgnum == 0:
			self.getInstrumentParams()
		beamtiltdict = self.getBeamTiltFromStackParticleNumber()
		beamtilt = (beamtiltdict['y'],beamtiltdict['x'])
		correction = fftfun.getBeamTiltPhaseShiftCorrection(fft.shape,beamtilt,self.Cs,self.wavelength,self.stackpix)
		cfft = fft * correction
		b = fftpack.ifft2(cfft)
		# need to flip upside down in order to get the same input EMAN stack orientation.
		b = numpy.flipud(b)
		self.writeToStack(b)
		#mrc.write(partarray,os.path.join(path,'in.mrc'))
		#mrc.write(partarray,os.path.join(path,'out.mrc'))

	def getInstrumentParams(self):
		self.stackpix = apStack.getStackPixelSizeFromStackId(self.stackid, True) * 1e-10
		stackparticledata = apStack.getOneParticleFromStackId(self.stackid, self.imgnum+1, msg=True)
		pdata = stackparticledata['particle']
		self.imgpix = apDatabase.getPixelSize(pdata['image'])*1e-10
		scopedata = pdata['image']['scope']
		self.tem = scopedata['tem']
		self.cam = pdata['image']['camera']['ccdcamera']
		self.ht = scopedata['high tension']
		self.Cs = 2e-3
		self.mag = scopedata['magnification']
		self.beamdiameter = 1e-6
		self.c2diameter = 1e-4
		self.wavelength = fftfun.getElectronWavelength(self.ht)

	def getCombinedOffAxisBeamTilt(self,D_C2, D, coord):
		# distances are in meters
		# d: distance of the virtual image of the C2 aperture from the specimen plane
		# M_C2: demagnification factor
		# D: diameter of the illuminated area
		# D_C2: diameter of the C2 aperture
		# These numbers are for Tecnai TWIN
		d = 3.4e-3
		M_C2 = 5.2
		Ki_residual = 0.06
		Ka = 0.65
		betamax = (D_C2/M_C2 - D) / (2*d)
		radius = math.hypot(coord['x'],coord['y'])
		betascaler = betamax * 2 * radius / D
		angle = math.atan2(Ka,Ki_residual) + math.atan2(1,0)
		transform = numpy.matrix([[math.cos(angle),math.sin(angle)],[-math.sin(angle),math.cos(angle)]])
		mcoord = numpy.matrix([coord['x'],coord['y']])
		mbeta = betascaler * mcoord * transform
		return {'x':mbeta[(0,0)], 'y':mbeta[(0,1)]}

	def retrieveImageShiftComaMatrix(self, tem, ccdcamera, ht, mag):
		queryinstance = leginondata.MatrixCalibrationData()
		queryinstance['tem'] = tem
		queryinstance['ccdcamera'] = ccdcamera
		queryinstance['type'] = 'image-shift coma'
		queryinstance['magnification'] = mag
		queryinstance['high tension'] = ht
		caldatalist = queryinstance.query(results=1)
		if caldatalist:
			caldata = caldatalist[0]
			return caldata['matrix'].copy()
		else:
			excstr = 'no matrix for %s, %s, %s, %seV, %sx' % (tem['name'], ccdcamera['name'], caltype, ht, mag)
			apDisplay.printError(excstr)

	def transformImageShiftToBeamTilt(self, imageshift, tem, cam, ht, zerobeamtilt, mag):
		newbeamtilt = {}
		par = 'image-shift coma'
		# not to query specific mag for now
		matrix = self.retrieveImageShiftComaMatrix(tem, cam, ht, None)
		apDisplay.printMsg( "Image Shift ( %5.2f, %5.2f)" % (imageshift['x']*1e6,imageshift['y']*1e6))
		shiftvect = numpy.array((imageshift['x'], imageshift['y']))
		change = numpy.dot(matrix, shiftvect)
		newbeamtilt['x'] = zerobeamtilt['x'] + change[0]
		newbeamtilt['y'] = zerobeamtilt['y'] + change[1]
		apDisplay.printMsg( "Beam Tilt Correction ( %5.2f, %5.2f)" % (change[0]*1e3,change[1]*1e3))
		apDisplay.printMsg( "Beam Tilt ( %5.2f, %5.2f)" % (newbeamtilt['x']*1e3,newbeamtilt['y']*1e3))
		return newbeamtilt

	def getBeamTiltFromStackParticleNumber(self):
		stackparticledata = apStack.getOneParticleFromStackId(self.stackid, self.imgnum+1, msg=True)
		pdata = stackparticledata['particle']
		imageshift = pdata['image']['scope']['image shift']
		zerobeamtilt = {'x':0.0, 'y':0.0}
		axialbeamtilt = self.transformImageShiftToBeamTilt(imageshift, self.tem, self.cam, self.ht, zerobeamtilt, self.mag)
		pcoord = {'x':pdata['xcoord']*self.imgpix,'y':pdata['ycoord']*self.imgpix}
		offaxisbeamtilt = self.getCombinedOffAxisBeamTilt(self.c2diameter,self.beamdiameter,pcoord)
		return {'x':axialbeamtilt['x']+offaxisbeamtilt['x'],
							'y':axialbeamtilt['y']+offaxisbeamtilt['y'] }

	def writeToStack(self,partarray):
		if self.partperiter == 0:
			arrayshape = partarray.shape
			partperiter = int(1e9/(arrayshape[0]*arrayshape[1])/16.)
			if partperiter > 4096:
				partperiter = 4096
			partperiter = 4
			self.partperiter = partperiter
			apDisplay.printMsg("Using %d particle per iteration"%(partperiter))
		stackroot = self.outstackfile[:-4]
		imgnum = self.imgnum
		index = imgnum % self.partperiter
		### Process images
		startmem = mem.active()
		index = imgnum % self.partperiter
		if imgnum % 100 == 0:
			sys.stderr.write(".")
			#sys.stderr.write("%03.1fM %d\n"%((mem.active()-startmem)/1024., index))
			if mem.active()-startmem > 2e6:
				apDisplay.printWarning("Out of memory")
		if index < 1:
			### deal with large stacks, reset loop
			if imgnum > 0:
				sys.stderr.write("\n")
				stackname = "%s-%d.hed"%(stackroot, imgnum)
				apDisplay.printMsg("writing single particles to file "+stackname)
				self.stacklist.append(stackname)
				apFile.removeStack(stackname, warn=False)
				apImagicFile.writeImagic(self.stackarray, stackname, msg=False)
				perpart = (time.time()-self.starttime)/imgnum
				apDisplay.printColor("%d  :: %.1fM mem :: %s/part "%
					(imgnum+1, (mem.active()-startmem)/1024. , apDisplay.timeString(perpart)), 
					"blue")
				self.stackarray = []
			### merge particles
		self.stackarray.append(partarray)
		self.imgnum += 1

	def postLoop(self):
		if len(self.stackarray) > 0:
			stackroot = self.outstackfile[:-4]
			stackname = "%s-%d.hed"%(stackroot, self.imgnum)
			apDisplay.printMsg("writing single particles to file "+stackname)
			self.stacklist.append(stackname)
			apFile.removeStack(stackname, warn=False)
			apImagicFile.writeImagic(self.stackarray, stackname, msg=False)
		### merge stacks
		apFile.removeStack(self.outstackfile, warn=False)
		apImagicFile.mergeStacks(self.stacklist, self.outstackfile)
		filepart = apFile.numImagesInStack(self.outstackfile)
		if filepart != self.imgnum:
			apDisplay.printError("number merged particles (%d) not equal number expected particles (%d)"%
				(filepart, numpart))
		for stackname in self.stacklist:
			apFile.removeStack(stackname, warn=False)

		### summarize
		apDisplay.printColor("merged %d particles in %s"%(self.imgnum, apDisplay.timeString(time.time()-self.starttime)), "cyan")

#===============
def makeCorrectionStack(oldstackid, oldstack, newstack, listfile=None, remove=False, bad=False):
	if not os.path.isfile(oldstack):
		apDisplay.printWarning("could not find old stack: "+oldstack)
	if os.path.isfile(newstack):
		if remove is True:
			apDisplay.printWarning("removing old stack: "+newstack)
			time.sleep(2)
			apFile.removeStack(newstack)
		else:
			apDisplay.printError("new stack already exists: "+newstack)
	apDisplay.printMsg("creating a beam tilt phase correction stack\n\t"+newstack+
		"\nfrom the oldstack\n\t"+oldstack+"\nusing list file\n\t"+str(listfile))
	correcter = correctStackBeamTiltPhaseShift(oldstackid,newstack)
	correcter.start(oldstack)
