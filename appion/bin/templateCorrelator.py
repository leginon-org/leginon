#!/usr/bin/python -O

#pythonlib
import os, sys
#appion
import appionLoop
import apFindEM
import apImage
import apDisplay

class TemplateCorrelationLoop(appionLoop.AppionLoop):
	def processImage(self, imgdict):
		import pprint
		pprint.pprint(imgdict)
		print imgdict['image']
		imgname = imgdict['filename']
		### RUN FindEM
		if self.params['method'] == "experimental":
			numpeaks = sf2.runCrossCorr(params,imgname)
			sf2.createJPG2(params,imgname)
		else:
			smimgname = self.processAndSaveImage(imgdict)
			if(os.getloadavg() > 3.1):
				ccmaxmaps = apFindEM.runFindEM(self.params, smimgname)
			else:
				ccmaxmaps = apFindEM.threadFindEM(self.params, smimgname)
			numpeaks = sf2.findPeaks2(params,imgname)
			sf2.createJPG2(params,imgname)

	def specialDefaultParams(self):
		self.params['template']=''
		self.params['templatelist']=[]
		self.params['startang']=0
		self.params['endang']=10
		self.params['incrang']=20
		self.params['thresh']=0.5
		self.params['autopik']=0
		self.params['lp']=30
		self.params['hp']=600
		self.params['box']=0
		self.params['method']="updated"
		self.params['overlapmult']=1.5
		self.params['maxpeaks']=1500
		self.params['defocpair']=False
		self.params['templateIds']=''

	def specialParseParams(self,args):
		return

	def specialParamConflicts(self):
		if not params['templateIds'] and not params['apix']:
			apDisplay.printError("if not using templateIds, you must enter a template pixel size")
		if params['templateIds'] and params['template']:
			apDisplay.printError("Both template database IDs and mrc file templates are specified,\nChoose only one")
		if (params['thresh']==0 and params['autopik']==0):
			apDisplay.printError("neither manual threshold or autopik parameters are set, please set one.")
		if not 'diam' in params or params['diam']==0:
			apDisplay.printError("please input the diameter of your particle")

	def _processAndSaveImage(self, imgdict):
		imgdata = apImage.preProcessImage(imgdict['image'],self.params)
		smimgname = os.path.join(self.params['rundir'],imgdict['filename']+".dwn.mrc")
		Mrc.numeric_to_mrc(imgdata, smimgname)
		return os.path.basename(smimgname)


if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

