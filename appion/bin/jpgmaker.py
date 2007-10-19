#!/usr/bin/python -O

#pythonlib
import os
#appion
import appionLoop
import apImage
#leginon
import pyami.jpg as jpg

class MrcToJpgLoop(appionLoop.AppionLoop):
	'''
	Writes a maximal 512x512 jpg image
	default is 
		min = mean - 3 * stdev
		max = mean + 3 * stdev
	if params['min'] > params['max'], use the image min and max to scale.
	Otherwise min and max are specified by params['min'],params['max']
	'''

	def specialDefaultParams(self):
		self.params['min']= None
		self.params['max']= None
		self.params['quality']= 80
		self.params['imgsize']= 512
	
	def specialParseParams(self, args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='min'):
				self.params['min']=int(elements[1])
			elif (elements[0]=='max'):
				self.params['max']=int(elements[1])
			elif (elements[0]=='quality'):
				self.params['quality']=int(elements[1])
			elif (elements[0]=='imgsize'):
				self.params['imgsize']=int(elements[1])


	def processImage(self, imgdata):			
		imgmax = self.params['max']
		imgmin = self.params['min']
		quality = self.params['quality']
		sizelimit = self.params['imgsize']
		image = imgdata['image']

		# determine binning for the final image to be no larger than 512x512
		shape = image.shape
		maxlength =max(shape)
		bin = maxlength // sizelimit
		if bin < 1:
			bin = 1
		if maxlength/bin > sizelimit:
			bin += 1
		self.params['bin'] = bin
		
		# binning first makes standard deviation scaling better
		binnedimage = apImage.binImg(image, bin=self.params['bin'])

		if imgmin > imgmax:
			imgmax = binnedimage.max()
			imgmin = binnedimage.min()

		outfile = os.path.join(self.params['rundir'],imgdata['filename']+".jpg")

		jpg.write(binnedimage,outfile, min=imgmin,max=imgmax,quality=quality)

if __name__ == '__main__':
	imgLoop = MrcToJpgLoop()
	imgLoop.run()

