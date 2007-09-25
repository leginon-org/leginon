#!/usr/bin/python -O

#pythonlib
import os
#appion
import appionLoop
import apImage
#leginon
import NumericImage

class MrcToJpgLoop(appionLoop.AppionLoop):
	def processImage(self, imgdata):
		quality = 80
		image = imgdata['image']
		shape = image.shape
		self.params['bin'] = shape[0]/512
		binnedimage = apImage.binImg(image, bin=self.params['bin'])
		outfile = os.path.join(self.params['rundir'],imgdata['filename']+".jpg")
		num_img = NumericImage.NumericImage(binnedimage)

		num_img.jpeg(outfile,quality)

if __name__ == '__main__':
	imgLoop = MrcToJpgLoop()
	imgLoop.run()

