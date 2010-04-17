#!/usr/bin/env python

import os
#appion
from appionlib import appionScript
from appionlib import apDog
from appionlib import apPeaks
from appionlib import apDisplay
from pyami import mrc

class DogPicker(appionScript.AppionScript):
	#=====================
	def uploadScriptData(self):
		return

	#=====================
	def setupRunDirectory(self):
		return

	#=================
	def setupParserOptions(self):
		"""
		set the input parameters
		"""

		self.parser.set_usage("Usage: %prog --image=FILE --thresh=FLOAT [options]")

		self.parser.add_option("-i", "--image", dest="image",
			help="Image to run dog picker on", metavar="FILE")

		self.parser.add_option("-d", "--diam", dest="diam", type="float",
			help="Diameter of particle", metavar="#")
		self.parser.add_option("--num-slices", dest="numslices", type="int", default=2,
			help="Number of different sizes to try", metavar="#")
		self.parser.add_option("--size-range", dest="sizerange", type="float", default=10,
			help="Size range in pixels about diam to search", metavar="#")

		self.parser.add_option("-a", "--apix", dest="apix", type="float", default=1.0,
			help="Pixel size of images in Angstroms", metavar="#")
		self.parser.add_option("-t", "--thresh", dest="thresh", type="float", default=0.6,
			help="Threshold in standard deviations above the mean, e.g. --thresh=0.7", metavar="#")
		self.parser.add_option("--max-thresh", dest="maxthresh", type="float", default=1.5,
			help="Threshold in standard deviations above the mean, e.g. --thresh=0.7", metavar="#")

		self.parser.add_option("--max-area", dest="maxsizemult", type="float", default=0.3,
			help="When thresholded the peak must be less than maxarea*pi*r^2", metavar="#")
		self.parser.add_option("--max-peaks", dest="maxpeaks", type="int", default=500,
			help="Maximum number of allowed peaks", metavar="#")

		self.parser.add_option("-o", "--outfile", dest="outfile", default="picks.txt",
			help="Text file to write particle picks to", metavar="FILE")


	#=================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['image'] is None:
			apDisplay.printError("enter a image MRC file, e.g. --image=bestimage.mrc")
		if self.params['outfile'] is None:
			apDisplay.printError("enter a output txt file, e.g. --outfile=picks.txt")
		if self.params['diam'] is None:
			apDisplay.printError("enter the diameter of particle, e.g., --diam=140")

		### extra parameters
		self.params["overlapmult"] = 1.5
		self.params["kfactor"] = 1.1
		self.params["bin"] = 1

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#=================
	def _peakCompare(self, a, b):
		if float(a['xcoord']+a['ycoord']) > float(b['xcoord']+b['ycoord']):
			return 1
		else:
			return -1

	#=================
	def writeTextFile(self, peaktree):
		peaktree.sort(self._peakCompare)
		f = open(self.params['outfile'], "w")
		for peak in peaktree:
			#print peak
			f.write(str(round(peak['xcoord'],2))+"\t"+str(round(peak['ycoord'],2))+"\n")
		f.close()

	#=================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""

		imgarray = mrc.read(self.params['image'])
		dogmaps = apDog.diffOfGaussParam(imgarray, self.params)
		rootname = os.path.splitext(self.params['image'])[0]
		pixdiam = self.params['diam']/self.params['apix']
		pixrad = pixdiam/2.0

		peaktreelist = []
		count = 0
		for dogmap in dogmaps:
			count += 1

			### threshold maps and extract peaks
			peaktree = apPeaks.findPeaksInMap(dogmap, thresh=self.params['thresh'],
				pixdiam=pixdiam, count=count, olapmult=self.params["overlapmult"],
				maxpeaks=self.params["maxpeaks"], maxsizemult=self.params["maxsizemult"],
				maxthresh=self.params["maxthresh"], msg=True, bin=1)

			### remove peaks from areas near the border of the image
			peaktree = apPeaks.removeBorderPeaks(peaktree, pixdiam, 
				dogmap.shape[0], dogmap.shape[1])

			### create a nice image of pick locations
			mapfile = "%s-map%02d.jpg"%(rootname, count)
			apPeaks.createPeakMapImage(peaktree, dogmap, imgname=mapfile, pixrad=pixrad)
			imgfile = "%s-picks%02d.jpg"%(rootname, count)
			apPeaks.subCreatePeakJpeg(imgarray, peaktree, pixrad, imgfile, bin=1)

			peaktreelist.append(peaktree)

		### merge list in a single set of particle picks
		imgdata = { 'filename': self.params['image'], }
		peaktree = apPeaks.mergePeakTrees(imgdata, peaktreelist, self.params)

		### throw away particles above maxthresh
		precount = len(peaktree)
		peaktree = maxThreshPeaks(peaktree, maxthresh)
		postcount = len(peaktree)
		apDisplay.printMsg("Filtered %d particles above max threshold %.2f"
			%(precount-postcount,maxthresh))

		### create final images with pick locations
		mapfile = "%s-finalmap.jpg"%(rootname, count)
		apPeaks.createPeakMapImage(peaktree, dogmap, imgname=mapfile, pixrad=pixrad)
		imgfile = "%s-finalpicks.jpg"%(rootname, count)
		apPeaks.subCreatePeakJpeg(imgarray, peaktree, pixrad, imgfile, bin=1)

		### write output file
		self.writeTextFile(peaktree)

#=================
#=================
#=================
if __name__ == '__main__':
	dogpicker = DogPicker(False)
	dogpicker.start()
	dogpicker.close()


