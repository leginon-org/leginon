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
from pyami import mrc

class Test(appionScript.AppionScript):
	def setupParserOptions(self):
		self.parser.set_usage('')
		self.parser.add_option("--subtomoId", dest="subtomoId", type="int",
			help="subtomogram id for subvolume averaging, e.g. --subtomoId=2", metavar="int")
		self.parser.add_option("--stackId", dest="stackId", type="int",
			help="Stack selected for averaging, e.g. --stackId=2", metavar="int")

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
		profiles = []
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
				subvolume = apTomo.getFullZSubvolume(subtomorundata,stackp)
				if subvolume is not None:
					zcenter = volshape[0] / 2
					profile = apTomo.getParticleCenterZProfile(subvolume,shift,halfwidth,zbackgroundrange)
					#profiles.append(profile)
					center = apTomo.gaussianCenter(profile)
					if center > zcenter - ztolerance and center < zcenter + ztolerance:
						i += 1
						shiftz = zcenter - center
						transformedvolume = apTomo.transformTomo(subvolume,alignpackage,alignp,shiftz,totalbin)
						sumvol += transformedvolume
			if i < 1:
				apDisplay,printError('no subtomogram qualifies for averaging')
			else:
				avgvol = sumvol / i
			if self.params['commit']:
				avgvolfilename = sessionname+"_"+self.params['runname']+".mrc"
				avgvolpath = os.path.join(self.params['rundir'],avgvolfilename)
				mrc.write(sumvol,avgvolpath)
				apTomo.insertTomoAverageRun(self.params['runname'],
						self.params['rundir'],
						subtomorundata,
						stackdata,
						halfwidth,
						self.params['description'],
				)
		'''
		proshape = profile.shape
		out = open('profiles.txt','w')
		for z in range(0,proshape[0]):
			str = "%5d\t" % z
			for i in range(0,len(profiles)):
				str += "%6.3f\t" % profiles[i][z]
			str += "\n"
			out.write(str)
		out.close()
		'''
if __name__ == '__main__':
	test = Test()
	test.start()
	test.close()

