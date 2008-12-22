#!/usr/bin/env python

#python
import os
import re
import time
import sys
import math
from optparse import OptionParser
import numpy
from numpy import linalg
import subprocess
import threading
#appion
from pyami import mrc, spider
import apParam
import apDisplay
import apFile
import apImage

##========================
##========================
class AceTilt(object):
	##========================
	def __init__(self):
		self.setupParseOpts()
		self.timestamp = apParam.makeTimestamp()
		self.params = apParam.convertParserToParams(self.parser)
		self.ace2exe = self.getACE2Path()

	##========================
	def setupParseOpts(self):
		self.parser = OptionParser()
		self.parser.set_usage("Usage: %prog -f <filename> [ -t <tiltangle> ]")
		self.parser.add_option("-f", "--filename", dest="filename",
			help="Name of imput mrc of spider format image", metavar="FILE")
		self.parser.add_option("-t", "--tiltangle", dest="tiltangle", type="float",
			help="Approximate tilt angle", metavar="#")
		self.parser.add_option("-s", "--splits", dest="splits", type="int", default=2,
			help="Number of divisions to divide image; -s 4 ==> 4x4 or 16 pieces", metavar="#")
		self.parser.add_option("-k", "--kv", dest="kv", type="int",
			help="Voltage of microscope (in kV)", metavar="#")
		self.parser.add_option("-c", "--cs", dest="cs", type="float", default=2.0,
			help="Spherical abberation of the microscope (in mm)", metavar="#")
		self.parser.add_option("-a", "--apix", dest="apix", type="float",
			help="Pixel size of the image (in Angstroms per pixel)", metavar="#")

	#======================
	def getACE2Path(self):
		unames = os.uname()
		if unames[-1].find('64') >= 0:
			exename = 'ace2_64.exe'
		else:
			exename = 'ace2_32.exe'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ace2exe):
			ace2exe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(ace2exe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return ace2exe

	##========================
	def openFile(self):
		if not os.path.isfile(self.params['filename']):
			apDisplay.printError("Cound not find file "+self.params['filename'])

		if self.params['filename'][-4:].lower() == ".mrc":
			imgarray = mrc.read(self.params['filename'])
		else:
			try:
				### assume file is of type spider
				imgarray = spider.read(self.params['filename'])
			except:
				apDisplay.printError("Cound not read file "+self.params['filename'])
		return imgarray

	##========================
	def splitImage(self, imgarray):
		shape = numpy.asarray(imgarray.shape)
		small = shape/self.params['splits']

		imgdict = {}
		for i in range(self.params['splits']):
			for j in range(self.params['splits']):
				key = "%02dx%02d"%(j,i)
				#print key, "==>", small[0]*j, ":", small[0]*(j+1)+1, ",", small[1]*i, ":", small[1]*(i+1)+1
				imgdict[key] = imgarray[small[0]*j:small[0]*(j+1)+1, small[1]*i:small[1]*(i+1)+1]
		return imgdict

	##========================
	def processImage(self, imgfile, msg=False):

		### make command line
		acecmd = ("%s -i %s -c %.2f -k %d -a %.6f"
			%(self.ace2exe, imgfile, self.params['cs'], self.params['kv'], self.params['apix']))

		### run ace2
		aceoutf = open("ace2.stdout", "a")
		ace2proc = subprocess.Popen(acecmd, shell=True, stdout=aceoutf, stderr=aceoutf)
		ace2proc.wait()

		### check if ace2 worked
		imagelog = imgfile+".ctf.txt"
		if not os.path.isfile(imagelog) and self.count <= 1:
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(1)
			ace2proc = subprocess.Popen(acecmd, shell=True, stdout=aceoutf, stderr=aceoutf)
			ace2proc.wait()
		aceoutf.close()

		### die
		if not os.path.isfile(imagelog):
			apDisplay.printError("ace2 did not run")

		### parse log file
		ctfvalues = {}
		logf = open(imagelog, "r")
		for line in logf:
			sline = line.strip()
			if re.search("^Final Defocus:", sline):
				parts = sline.split()
				ctfvalues['defocus1'] = float(parts[2])
				ctfvalues['defocus2'] = float(parts[3])
				### convert to degrees
				ctfvalues['angle_astigmatism'] = math.degrees(float(parts[4]))
			elif re.search("^Amplitude Contrast:",sline):
				parts = sline.split()
				ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("^Confidence:",sline):
				parts = sline.split()
				ctfvalues['confidence'] = float(parts[1])
				ctfvalues['confidence_d'] = float(parts[1])
		logf.close()

		### summary stats
		avgdf = (ctfvalues['defocus1']+ctfvalues['defocus2'])/2.0
		ampconst = 100.0*ctfvalues['amplitude_contrast']
		pererror = 100.0 * (ctfvalues['defocus1']-ctfvalues['defocus2']) / avgdf
		if msg is True:
			apDisplay.printMsg("============")
			apDisplay.printMsg("Defocus: %.3f x %.3f um (%.2f percent error)"%
				(ctfvalues['defocus1']*1.0e6, ctfvalues['defocus2']*1.0e6, pererror ))
			apDisplay.printMsg("Angle astigmatism: %.2f degrees"%(ctfvalues['angle_astigmatism']))
			apDisplay.printMsg("Amplitude contrast: %.2f percent"%(ampconst))
			apDisplay.printMsg("Final confidence: %.3f"%(ctfvalues['confidence']))

		### double check that the values are reasonable 
		if avgdf < -1.0e-3 or avgdf > -1.0e-9:
			apDisplay.printWarning("bad defocus estimate, not committing values to database")
			return None
		if ampconst < 1.0 or ampconst > 80.0:
			apDisplay.printWarning("bad amplitude contrast, not committing values to database")
			return None

		## create power spectra jpeg
		edgefile = imgfile+".edge.mrc"
		if os.path.isfile(edgefile):
			jpegfile = imgfile+".edge.jpg"
			ps = mrc.read(edgefile)
			ps = (ps-ps.mean())/ps.std()
			cutoff = -2.0*ps.min()
			ps = numpy.where(ps < cutoff, ps, cutoff)
			apImage.arrayToJpeg(ps, jpegfile, msg=False)
			apFile.removeFile(edgefile)

		#print ctfvalues

		return ctfvalues

	##========================
	def fitPlaneToCtf(self, imgarray):
		"""
		performs a two-dimensional linear regression and subtracts it from an image
		essentially a fast high pass filter
		"""
		def retx(y,x):
			return x
		def rety(y,x):
			return y
		count = float((imgarray.shape)[0]*(imgarray.shape)[1])
		xarray = numpy.fromfunction(retx, imgarray.shape)
		yarray = numpy.fromfunction(rety, imgarray.shape)
		xsum = float(xarray.sum())
		xsumsq = float((xarray*xarray).sum())
		ysum = xsum
		ysumsq = xsumsq
		xysum = float((xarray*yarray).sum())
		xzsum = float((xarray*imgarray).sum())
		yzsum = float((yarray*imgarray).sum())
		zsum = imgarray.sum()
		zsumsq = (imgarray*imgarray).sum()
		xarray = xarray.astype(numpy.float32)
		yarray = yarray.astype(numpy.float32)
		leftmat = numpy.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]] )
		rightmat = numpy.array( [xzsum, yzsum, zsum] )
		resvec = linalg.solve(leftmat,rightmat)
		xslope = resvec[0]
		yslope = resvec[1]
		print "plane_regress: "
		print " x-slope =  %.2e m"%(xslope)
		print " y-slope =  %.2e m"%(yslope)
		print " xy-intercept =  %.2e m"%(resvec[2])

		tiltaxis = math.degrees(math.atan2(-yslope,xslope))
		print " tilt axis angle = %.2f degrees"%(tiltaxis)

		newarray = xarray*xslope + yarray*yslope + resvec[2]
		#print newarray
		diffarray = imgarray - newarray
		#print diffarray
		rmserror = math.sqrt( (diffarray*diffarray).mean() )
		print " rms error = %.2e m"%(rmserror)

		#print " max1-slope =  %.2e m"%(xslope*math.cos(math.radians(tiltaxis)))
		#print " max2-slope =  %.2e m"%(yslope*math.sin(math.radians(tiltaxis)))

		maxslope = abs(xslope*math.cos(math.radians(tiltaxis))) + abs(yslope*math.sin(math.radians(tiltaxis)))
		print " max-slope =  %.2e m"%(maxslope)
		if abs(maxslope) < max(abs(xslope),abs(yslope)):
			print "ERROR in max slope calculation"

		#print " num1-pix =  %.1f pixels"%(self.imgshape[1]*math.cos(math.radians(tiltaxis)))
		#print " num2-pix =  %.1f pixels"%(self.imgshape[0]*math.sin(math.radians(tiltaxis)))
		numpix = abs(self.imgshape[1]*math.cos(math.radians(tiltaxis))) + abs(self.imgshape[0]*math.sin(math.radians(tiltaxis)))
		#print " num-pix =  %.1f pixels"%(numpix)
		splitpix = numpix/float(self.params['splits'])
		#print " split-pix =  %.1f pixels"%(splitpix)

		splitsize = self.params['apix']*1.0e-10*splitpix
		#print " split-size =  %.2e m"%(splitsize)
		
		#if abs(maxslope) > abs(splitsize):
		#	print "invalid tilt:", maxslope, splitsize
		#	return

		print " angle ratio =  %.2e / %.2e => %.4f "%(maxslope,splitsize,maxslope/splitsize)
		tiltangle = math.degrees(math.atan2(maxslope, splitsize))
		print " tilt-angle =  %.2f degrees"%(tiltangle)


	##========================
	def run(self):
		imgarray = self.openFile()
		self.imgshape = imgarray.shape
		imgdict = self.splitImage(imgarray)
		ctfdict = {}
		self.count = 0
		ctfgrid = numpy.zeros((self.params['splits'], self.params['splits']))
		for key in imgdict.keys():
			self.count += 1
			imgarray = imgdict[key]
			imgfile = "splitimage-"+key+".dwn.mrc"
			mrc.write(imgarray, imgfile)
			ctfvalues = None
			while ctfvalues is None:
				ctfvalues = self.processImage(imgfile)
			ctfdict[key] = ctfvalues
			apFile.removeFilePattern(imgfile+"*", False)
		for j in range(self.params['splits']):
			for i in range(self.params['splits']):
				key = "%02dx%02d"%(j,i)
				ctf = ctfdict[key]
				if ctf is not None:
					avgdf = (ctf['defocus1']+ctf['defocus2'])/2.0
					sys.stdout.write("%.3e\t"%(avgdf))
					ctfgrid[j,i] = avgdf
				else:
					sys.stdout.write("%.3e\t"%(0.0))
			sys.stdout.write("\n")
		self.fitPlaneToCtf(ctfgrid)

##========================
##========================
if __name__ == "__main__":
	acetilt = AceTilt()
	acetilt.run()
