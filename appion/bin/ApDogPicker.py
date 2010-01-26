#!/usr/bin/env python

from optparse import OptionParser
import sys
#PIL
import Image
import ImageDraw
#appion
from appionlib import appionScript
from appionlib import apImage
from appionlib import apDog
from appionlib import apPeaks
from appionlib import apDisplay
from appionlib import apParam
import math

class DogPicker(appionScript.AppionScript):
	def setupParserOptions(self):
		"""
		set the input parameters
		"""
		self.parser.set_usage("Usage: %prog --image=FILE --thresh=FLOAT [options]")
		self.parser.add_option("-i", "--image", dest="image",
			help="Image to run dog picker on", metavar="FILE")
		self.parser.add_option("-t", "--thresh", dest="thresh", type="float",
			help="Threshold in standard deviations above the mean, e.g. --thresh=0.7", metavar="FLOAT")
		self.parser.add_option("-o", "--outfile", dest="outfile", default="picks.txt",
			help="Text file to write particle picks to", metavar="FILE")
		self.parser.add_option("-d", "--pixdiam", dest="pixdiam", type="float",
			help="Diameter of particle in pixels", metavar="FLOAT")

	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['image'] is None:
			apDisplay.printError("enter a image file ID, e.g. --image=bestimage.mrc")
		if self.params['thresh'] is None:
			apDisplay.printError("enter a threshold, e.g. --thresh=0.7")
		if self.params['outfile'] is None:
			apDisplay.printError("enter a output txt file, e.g. --outfile=picks.txt")
		if self.params['pixdiam'] is None:
			apDisplay.printError("enter the diameter of particle in pixels, e.g. --pixdiam=140")
		self.params["overlapmult"] = 1.5
		self.params["maxpeaks"] = 500
		self.params["maxsizemult"] = 1.0
		self.params["maxthresh"] = 2.0

	def _peakCompare(self, a, b):
		if float(a['xcoord']+a['ycoord']) > float(b['xcoord']+b['ycoord']):
			return 1
		else:
			return -1

	def writeTextFile(self, peaktree):
		peaktree.sort(self._peakCompare)
		f = open(self.params['outfile'], "w")
		for peak in peaktree:
			#print peak
			f.write(str(round(peak['xcoord'],2))+"\t"+str(round(peak['ycoord'],2))+"\n")
		f.close()

	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		imgarray = apImage.mrcToArray(self.params['image'])
		pixrad = self.params['pixdiam']/2.0
		dogmap = apDog.diffOfGauss(imgarray, pixrad, k=1.2)
		dogmap = apImage.normStdev(dogmap)/4.0
		pixrad=self.params['pixdiam']/2.0
		peaktree = apPeaks.findPeaksInMap(dogmap, thresh=self.params['thresh'],
			pixdiam=self.params['pixdiam'], count=1, olapmult=self.params["overlapmult"],
			maxpeaks=self.params["maxpeaks"], maxsizemult=self.params["maxsizemult"],
			maxthresh=self.params["maxthresh"], msg=True, bin=1)
		#remove peaks from areas near the border of the image
		peaktree = apPeaks.removeBorderPeaks(peaktree, self.params['pixdiam'], 
			dogmap.shape[0], dogmap.shape[1])
		mapfile = self.params['image'][:-4]+"-map.jpg"
		apPeaks.createPeakMapImage(peaktree, dogmap, imgname=mapfile, pixrad=pixrad)
		imgfile = self.params['image'][:-4]+"-picks.jpg"
		apPeaks.subCreatePeakJpeg(imgarray, peaktree, pixrad, imgfile, bin=1)

		self.writeTextFile(peaktree)

if __name__ == '__main__':
	dogpicker = DogPicker(False)
	dogpicker.start()
	dogpicker.close()


