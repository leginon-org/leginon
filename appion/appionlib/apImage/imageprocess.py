#Part of the new pyappion

## pythonlib
import time
## numpy
from scipy import ndimage
## appionlib
from appionlib import apDisplay
from appionlib.apImage import imagefilter, imagenorm

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#=====================================
#=====================================
class ImageFilter(object):
	#=====================================
	def __init__(self, msg=True):
		self.median = 0
		self.msg = msg
		self.apix = 1.0
		self.bin = 1
		self.invert = False
		self.highPass = 0.0
		self.highPassType = "tanh"
		self.highPassOptions = ("gauss_subtract", "tanh", "spider_fermi")
		self.planeRegression = False
		self.pixelLimitStDev = 0.0
		self.lowPass = 0.0
		self.lowPassType = "gauss"
		self.lowPassOptions = ("gauss", "tanh")
		self.normalizeType = "256"
		self.normalizeOptions = ("256", "mean0")	
		return

	#=====================================
	def readParamsDict(self, params):
		if 'background' in params and params['background'] is not None:
			self.msg = not params['background']
		if 'apix' in params and params['apix'] is not None:
			self.apix = params['apix']
		if 'bin' in params and params['bin'] is not None:
			self.bin = params['bin']
		if 'planereg' in params and params['planereg'] is not None:
			self.planeRegression = params['planereg']
		if 'median' in params and params['median'] is not None:
			self.median = params['median']
		if 'lowpass' in params and params['lowpass'] is not None:
			self.lowPass = params['lowpass']
		elif 'lp' in params and params['lp'] is not None:
			self.lowPass = params['lp']			
		if 'invert' in params and params['invert'] is not None:
			self.invert = params['invert']		
		if 'highpass' in params and params['highpass'] is not None:
			self.highPass = params['highpass']
		elif 'hp' in params and params['hp'] is not None:
			self.highPass = params['hp']
		if 'pixlimit' in params and params['pixlimit'] is not None:
			self.pixelLimitStDev = params['pixlimit']
		return
	
	#=====================================
	def processImage(self, imgarray):
		"""
		standard processing for an image
		"""
		startt = time.time()
		
		### make a copy to avoid overwriting the original image
		simgarray = imgarray.copy()
		
		if self.median > 0:
			if self.msg is True:
				apDisplay.printMsg("Median filter of size %d pixels"%(self.median))
			simgarray = ndimage.median_filter(simgarray, size=self.median)
		
		if self.bin > 1:
			if self.msg is True:
				apDisplay.printMsg("Binning image by a factor of %d"%(self.bin))
			simgarray = imagefilter.binImg(simgarray, self.bin)
		
		if self.planeRegression is True:
			if self.msg is True:
				apDisplay.printMsg("Applying a 2D plane regression and subtraction")
			simgarray = imagefilter.planeRegression(simgarray, self.msg)
				
		if self.highPass > 0:
			if self.msg is True:
				apDisplay.printMsg("Applying a high pass filter of %s A (apix %.1fA) of type %s"
					%(self.highPass, self.apix, self.highPassType))
			if self.highPassType.startswith("gauss_subtract"):
				simgarray = imagefilter.subtractHighPassFilter(simgarray, self.highPass, apix=self.apix, bin=self.bin)
			else:
				### default: tanh
				simgarray = imagefilter.tanhHighPassFilter(simgarray, self.highPass, apix=self.apix, bin=self.bin)

		if self.pixelLimitStDev > 0:
			if self.msg is True:
				apDisplay.printMsg("Applying pixel limit filter of +/- %.1f standard deviations"%(self.pixelLimitStDev))
			simgarray = imagefilter.pixelLimitFilter(simgarray, self.pixelLimitStDev)

		if self.lowPass > 0:
			if self.msg is True:
				apDisplay.printMsg("Applying a low pass filter of %s A (apix %.1fA) of type %s"
					%(self.lowPass, self.apix, self.lowPassType))
			if self.lowPassType.startswith("tanh"):
				simgarray = imagefilter.tanhLowPassFilter(simgarray, self.lowPass, apix=self.apix, bin=self.bin)
			else:
				### default: gauss
				simgarray = imagefilter.lowPassFilter(simgarray, radius=self.lowPass, apix=self.apix, bin=self.bin)

		if self.invert is True:
			if self.msg is True:
				apDisplay.printMsg("Inverting image")
			simgarray = imagefilter.invertImage(simgarray)

		if self.normalizeType.startswith("256"):
			simgarray = 255.0*(imagenorm.normRange(simgarray)+1.0e-7)
		else:
			### default: mean0
			simgarray = imagenorm.normStdev(simgarray)

		if self.msg is True:
			apDisplay.printMsg("filtered image in "+apDisplay.timeString(time.time()-startt))

		return simgarray		
