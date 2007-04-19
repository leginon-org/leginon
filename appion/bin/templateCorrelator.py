#!/usr/bin/python -O

#pythonlib
import os, sys
#appion
import appionLoop
import apFindEM

class TemplateCorrelationLoop(appionLoop.AppionLoop):
	def processImage(self, img):
		### RUN FindEM
		if self.params['method'] == "experimental":
			numpeaks = sf2.runCrossCorr(params,imgname)
			sf2.createJPG2(params,imgname)
		else:
			smimgname = processAndSaveImage(img)
			if(os.getloadavg() > 3.1):
				ccmaxmaps = apFindEM.runFindEM(self.params, smimgname)
			else:
				ccmaxmaps = apFindEM.threadFindEM(self.params, smimgname)
			numpeaks = sf2.findPeaks2(params,imgname)
			sf2.createJPG2(params,imgname)

	def processAndSaveImage(img):
		imgdata = apImage.preProcessImage(img['image'],self.params)
		smimgname = os.path.join(self.params['rundir'],img['filename']+".dwn.mrc")
		Mrc.numeric_to_mrc(imgdata, smimgname)
		return os.path.basename(smimgname)


if __name__ == '__main__':
	imageiter = TemplateCorrelationLoop()
	imageiter.loop()

