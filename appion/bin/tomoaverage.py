#!/usr/bin/env python
import re
import math
import os
import numpy
from scipy import ndimage
import appionData
import appionScript
import apStack
import apTomo
import apImod
import apAlignment
import apDisplay
from pyami import mrc

class Test(appionScript.AppionScript):
	def setupParserOptions(self):
		self.parser.set_usage('')
		self.parser.add_option("--subtomorunId", dest="subtomoId", type="int",
			help="subtomogram id for subvolume averaging, e.g. --subtomoId=2", metavar="int")
		self.parser.add_option("--stackId", dest="stackId", type="int",
			help="Stack selected for averaging, e.g. --stackId=2", metavar="int")
		self.parser.add_option("--maxsize", dest="maxsize", type="int",
			help="Maximum movie pixel numbers in x or y, whichever is larger. Will respect proportion in scaling, e.g. --maxsize=500", default = 512, metavar="int")

	def checkConflicts(self):
		pass

	def setRunDir(self):
		"""
		this function only runs if no rundir is defined at the command line
		"""
		subtomorunq = appionData.ApSubTomogramRunData()
		subtomorundata = subtomorunq.direct_query(self.params['subtomoId'])
		subtomoq = appionData.ApTomogramData(subtomorun=subtomorundata)
		results = subtomoq.query(results=1)
		if results:
			subtomodir = results[0]['path']['path']
			tiltdirs = subtomodir.split('/tiltseries')
			self.params['rundir'] = os.path.join(tiltdirs[0],"average",self.params['runname'])

	def start(self):
		subtomorunq = appionData.ApSubTomogramRunData()
		subtomorundata = subtomorunq.direct_query(self.params['subtomoId'])
		volshape,totalbin,pixelsize = apTomo.getSubvolumeInfo(subtomorundata)
		if volshape is None:
			apDisplay.printError('No subvolume exists for the subtomoId')
		sessionname = subtomorundata['session']['name']
		stackq = appionData.ApStackData()
		stackdata = stackq.direct_query(self.params['stackId'])
		diameter = apStack.getStackParticleDiameter(stackdata)
		diameterpixel = diameter * 1e-10 / pixelsize
		halfwidth = diameterpixel / 4
		ztolerance = halfwidth
		zbackgroundrange = max(((volshape[0] - diameterpixel*3)/2,10))
		if self.params['commit']:
			avgrundata = apTomo.insertTomoAverageRun(self.params['runname'],
					self.params['rundir'],
					subtomorundata,
					stackdata,
					halfwidth,
					self.params['description'],
			)
		profiles = {}
		sumvol = numpy.zeros(volshape)
		substacktype,conditionstackdata = apStack.findSubStackConditionData(stackdata)
		if substacktype in ['clustersub','alignsub']:
			alignstack = apStack.getAlignStack(substacktype,conditionstackdata)
			alignpackage = apAlignment.getAlignPackage(alignstack['alignrun'])
			stackprtls = apStack.getStackParticlesFromId(stackdata.dbid)
			i = 0
			for stackp in stackprtls:
				alignp = apAlignment.getAlignParticle(stackp,alignstack)
				shift = apAlignment.getAlignShift(alignp,alignpackage)
				subtomodata = apTomo.getSubTomogramData(subtomorundata,stackp)
				subvolume = apTomo.getTomoVolume(subtomodata)
				if subvolume is not None:
					zcenter = volshape[0] / 2
					profile = apTomo.getParticleCenterZProfile(subvolume,shift,halfwidth,zbackgroundrange)
					subtomoid = subtomodata.dbid
					profiles[subtomoid] = profile
					center = apTomo.gaussianCenter(profile)
					if center > zcenter - ztolerance and center < zcenter + ztolerance:
						i += 1
						shiftz = zcenter - center
						transformedvolume = apTomo.transformTomo(subvolume,alignpackage,alignp,shiftz,totalbin)
						## write transformed mrc file to check the result
						filename = os.path.join(self.params['rundir'],'./transformed%05d.mrc' %subtomoid)
						mrc.write(transformedvolume,filename)
						sumvol += transformedvolume
						t = numpy.sum(transformedvolume,axis=0)
						filename = os.path.join(self.params['rundir'],'./p%05d.mrc' %subtomoid)
						mrc.write(transformedvolume,filename)
						if self.params['commit']:
							apTomo.insertTomoAvgParticle(avgrundata,subtomodata,alignp,shiftz)
			if i < 1:
				apDisplay.printError('no subtomogram qualifies for averaging')
			else:
				avgvol = sumvol / i
			avgvolfilename = sessionname+"_"+self.params['runname']+".mrc"
			avgvolpath = os.path.join(self.params['rundir'],avgvolfilename)
			mrc.write(avgvol,avgvolpath)
			if not os.path.isfile(avgvolpath):
					apDisplay.printError("tomogram not exist")
			apTomo.makeMovie(avgvolpath,self.params['maxsize'])
			apTomo.makeProjection(avgvolpath,self.params['maxsize'])
		
		proshape = profile.shape
		for id in profiles.keys():
			out = open('profile_%05d.txt'%id,'w')
			for z in range(0,proshape[0]):
				str = "%5d\t" % z
				str += "%6.3f\t" % profiles[id][z]
				str += "\n"
				out.write(str)
			out.close()
	
if __name__ == '__main__':
	test = Test()
	test.start()
	test.close()

