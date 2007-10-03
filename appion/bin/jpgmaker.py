#!/usr/bin/python -O

#pythonlib
import os
#appion
import appionLoop
import apImage
#leginon
import NumericImage

class MrcToJpgLoop(appionLoop.AppionLoop):
	def specialDefaultParams(self):
		self.params['min']= 0
		self.params['max']= 65000
	
	def specialParseParams(self, args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			if (elements[0]=='min'):
				self.params['min']=int(elements[1])
			elif (elements[0]=='max'):
				self.params['max']=int(elements[1])


	def processImage(self, imgdata):
		quality = 80
		image = imgdata['image']
		shape = image.shape
		self.params['bin'] = shape[0]/512
		binnedimage = apImage.binImg(image, bin=self.params['bin'])
		outfile = os.path.join(self.params['rundir'],imgdata['filename']+".jpg")
		num_img = NumericImage.NumericImage(binnedimage,(self.params['min'],self.params['max']))

		num_img.jpeg(outfile,quality)

if __name__ == '__main__':
	imgLoop = MrcToJpgLoop()
	imgLoop.run()

