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
		#self.parser.add_option("-t", "--tiltangle", dest="tiltangle", type="float",
		#	help="Approximate tilt angle", metavar="#")
		self.parser.add_option("-k", "--kv", dest="kv", type="int",
			help="Voltage of microscope (in kV)", metavar="#")
		self.parser.add_option("-c", "--cs", dest="cs", type="float", default=2.0,
			help="Spherical abberation of the microscope (in mm)", metavar="#")
		self.parser.add_option("-a", "--apix", dest="apix", type="float",
			help="Pixel size of the image (in Angstroms per pixel)", metavar="#")
		self.parser.add_option("-s", "--split-size", dest="splitsize", type="int", default=768,
			help="Size in pixels of areas to image", metavar="#")
		self.parser.add_option("-n", "--num-splits", dest="numsplits", type="int", default=6,
			help="Number of divisions to divide image; -s 4 ==> 4x4 for 16 pieces", metavar="#")

	#======================
	def getACE2Path(self):
		unames = os.uname()
		if unames[-1].find('64') >= 0:
			exename = 'ace2.exe'
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

		"""
		2
		1024 3072
		3
		1638	2457	3276
		4
		1364	2046	2728	3410
		"""

	##========================
	def setupCoordList(self):
		splitsize = self.params['splitsize']
		numsplits = self.params['numsplits']
		coordlist = {}
		xsize = self.imgshape[0]-splitsize
		ysize = self.imgshape[1]-splitsize
		for i in range(numsplits):
			for j in range(numsplits):
				xcenter = int(xsize/float(numsplits-1)*i)+splitsize/2
				ycenter = int(ysize/float(numsplits-1)*j)+splitsize/2
				xstart = xcenter - splitsize/2
				ystart = ycenter - splitsize/2
				xend = xstart + splitsize
				yend = ystart + splitsize
				if (xend <= self.imgshape[0] and yend <= self.imgshape[1]
				 and xstart >= 0 and ystart >= 0):
					key = "%05dx%05d"%(xcenter,ycenter)
					#print key, "==>", xstart, ":", xend, ",", ystart, ":", yend
					#imgdict[key] = imgarray[xstart:xend, ystart:yend]
					coordlist[key] = (xstart, xend, ystart, yend)
		return coordlist


	##========================
	def setupCoordListOld(self):
		splitsize = self.params['splitsize']
		numsplits = self.params['numsplits']
		coordlist = {}
		for i in range(numsplits):
			for j in range(numsplits):
				xcenter = int(self.imgshape[0]/float(2*numsplits)*(2*i+1))
				ycenter = int(self.imgshape[1]/float(2*numsplits)*(2*j+1))
				xstart = xcenter - splitsize/2
				ystart = ycenter - splitsize/2
				xend = xstart + splitsize
				yend = ystart + splitsize
				if (xend <= self.imgshape[0] and yend <= self.imgshape[1]
				 and xstart >= 0 and ystart >= 0):
					key = "%05dx%05d"%(xcenter,ycenter)
					#print key, "==>", xstart, ":", xend, ",", ystart, ":", yend
					#imgdict[key] = imgarray[xstart:xend, ystart:yend]
					coordlist[key] = (xstart, xend, ystart, yend)
		return coordlist

	##========================
	def getSubImage(self, imgarray, x, y):
		splitsize = self.params['splitsize']
		xstart = x - splitsize/2
		xend = xstart + splitsize
		ystart = y - splitsize/2
		yend = ystart + splitsize
		#print (x,y), "-->", (xstart, xend, ystart, yend)
		if (xend <= self.imgshape[0] and yend <= self.imgshape[1]
		 and xstart >= 0 and ystart >= 0):
			key = "%04dx%04d"%(xstart+splitsize/2,ystart+splitsize/2)
			#print key, "==>", xstart, ":", xend, ",", ystart, ":", yend
			subarray = imgarray[xstart:xend, ystart:yend]
			return subarray
		else:
			return None

	##========================
	def getCtfInfo(self, imgarray):
		imgfile = "temp.mrc"
		mrc.write(imgarray, imgfile)
		return processImage(imgfile)

	##========================
	def processImage(self, imgfile, edgeblur=8, msg=False):

		### make command line
		acecmd = ("%s -i %s -c %.2f -k %d -a %.3f -e %d,0.001 -b 1"
			%(self.ace2exe, imgfile, self.params['cs'], self.params['kv'], self.params['apix'], edgeblur))

		### run ace2
		aceoutf = open("ace2.stdout", "w")
		#print acecmd
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
		if ampconst < -0.01 or ampconst > 80.0:
			apDisplay.printWarning("bad amplitude contrast, not committing values to database")
			return None
		if ctfvalues['confidence'] < 0.6:
			sys.stderr.write("c")
			#apDisplay.printWarning("bad confidence")
			return None

		return ctfvalues

	##========================
	def fitPlaneToCtf(self, ctfdict):
		"""
		performs a two-dimensional linear regression and subtracts it from an image
		essentially a fast high pass filter
		"""
		### convert dict to 3 numpy arrays
		xarray = []
		yarray = []
		zarray = []
		confarray = []
		count = 0
		for key in ctfdict.keys():
			(xstr,ystr) = key.split('x')
			x = int(xstr)
			y = int(ystr)
			ctf = ctfdict[key]
			if ctf is None:
				continue
			z = (ctf['defocus1']+ctf['defocus2'])/2.0
			xarray.append(x)
			yarray.append(y)
			zarray.append(z)
			confarray.append(ctf['confidence'])
			count += 1
		xarray = numpy.array(xarray, dtype=numpy.float32)
		yarray = numpy.array(yarray, dtype=numpy.float32)
		zarray = numpy.array(zarray, dtype=numpy.float32)
		meanconf = numpy.array(confarray, dtype=numpy.float32).mean()
		print " mean conf = %.4f"%(meanconf)

		### running sums
		xsum = float(xarray.sum())
		xsumsq = float((xarray*xarray).sum())
		ysum = float(yarray.sum())
		ysumsq = float((yarray*yarray).sum())
		xysum = float((xarray*yarray).sum())
		xzsum = float((xarray*zarray).sum())
		yzsum = float((yarray*zarray).sum())
		zsum = zarray.sum()
		zsumsq = (zarray*zarray).sum()

		### linear solve for plane parameters
		leftmat = numpy.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]] )
		rightmat = numpy.array( [xzsum, yzsum, zsum] )
		resvec = linalg.solve(leftmat,rightmat)
		xslope = resvec[0]
		yslope = resvec[1]
		print "plane_regress: "
		print " x-slope =  %.2e m/pixel"%(xslope)
		print " y-slope =  %.2e m/pixel"%(yslope)
		print " xy-intercept =  %.2e m"%(resvec[2])

		### calculate residual
		newarray = xarray*xslope + yarray*yslope + resvec[2]
		#print "Measured=", zarray
		#print "Calculated=", newarray
		diffarray = zarray - newarray
		#print "Difference=", diffarray
		rmserror = math.sqrt( (diffarray*diffarray).mean() )
		print " rms error = %.2e m"%(rmserror)
		meanz = newarray.mean()
		print " confidence = %.4f"%(1.0-10.0*rmserror/abs(meanz))

		### angle calculations
		tiltaxis = math.degrees(math.atan2(-yslope,xslope))
		print " tilt axis angle = %.2f degrees"%(90-tiltaxis)
		#print " max1-slope =  %.2e m"%(xslope*math.cos(math.radians(tiltaxis)))
		#print " max2-slope =  %.2e m"%(yslope*math.sin(math.radians(tiltaxis)))
		maxslope = abs(xslope*math.cos(math.radians(tiltaxis))) + abs(yslope*math.sin(math.radians(tiltaxis)))
		print " max-slope =  %.2e m/pixel"%(maxslope)
		if abs(maxslope) < max(abs(xslope),abs(yslope)):
			print "ERROR in max slope calculation"
		mpix = self.params['apix']*1.0e-10
		print " angle ratio =  %.2e / %.2e => %.4f "%(maxslope,mpix,maxslope/mpix)
		tiltangle = math.degrees(math.atan2(maxslope, mpix))
		print " tilt-angle =  %.2f degrees"%(tiltangle)

	#=========================
	def printImageInfo(self, im):
		"""
		prints out image information good for debugging
		"""
		avg1 = im.mean()
		stdev1 = im.std()
		min1 = im.min()
		max1 = im.max()
		print " ... shape: "+str(im.shape)
		print " ... avg:  %.1f +- %.1f"%(avg1, stdev1)
		print " ... range: %.1f <> %.1f"%(min1,max1)

		return

	##========================
	def run(self):
		t0 = time.time()
		imgarray = self.openFile()
		self.imgshape = imgarray.shape
		self.printImageInfo(imgarray) 
		coordlist = self.setupCoordList()

		ctfdict = {}
		self.count = 0
		### process image pieces
		print "processing %d image pieces"%(len(coordlist))
		keys = coordlist.keys()
		keys.sort()
		for key in keys:
			(xstr,ystr) = key.split('x')
			x = int(xstr)
			y = int(ystr)
			self.count += 1
			subarray = self.getSubImage(imgarray, x, y)
			#self.printImageInfo(subarray) 
			imgfile = "splitimage-"+key+".dwn.mrc"
			mrc.write(subarray, imgfile)
			ctfvalues = None
			reproc = 0
			edgeblur = 8
			while ctfvalues is None and reproc < 3:
				ctfvalues = self.processImage(imgfile, edgeblur)
				reproc += 1
				edgeblur += 2
			if ctfvalues is not None:
				sys.stderr.write("#")
			else:
				sys.stderr.write("!")
			ctfdict[key] = ctfvalues
			apFile.removeFilePattern(imgfile+"*", False)
		sys.stderr.write("\n")

		### calculate ctf parameters
		self.fitPlaneToCtf(ctfdict)
		apDisplay.printMsg("Time: %s"%(apDisplay.timeString(time.time()-t0)))


##========================
##========================
if __name__ == "__main__":
	acetilt = AceTilt()
	acetilt.run()
