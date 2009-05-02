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

'''
def findSubStackConditionData(stackdata):
	substackname = stackdata['substackname']
	if not substackname:
		return None,None
	typedict = {
		'alignsub':appionData.ApAlignStackData(),
		'clustersub':appionData.ApClusteringStackData(),
	}
	substacktype = None
	for type in typedict.keys():
		if substackname.find(type) >= 0:
			substacktype = type
			break
	if substacktype is None:
		return None,None
	conditionids = re.findall('[0-9]+',substackname)
	q = typedict[substacktype]
	return substacktype,q.direct_query(conditionids[-1])

def getAlignStack(substacktype,conditionstackdata):
	if substacktype == 'clustersub':
		conditionstackdata = conditionstackdata['alignstack']
	return conditionstackdata

def getAlignParticle(stackpdata,alignstackdata):
	oldstack = stackpdata['stack']['oldstack']
	particledata = stackpdata['particle']
	oldstackpdata = appionData.ApStackParticlesData(stack=oldstack,particle=particledata)
	q = appionData.ApAlignParticlesData(alignstack=alignstackdata,stackpart=oldstackpdata)
	results = q.query(readimages=False)
	if results:
		return results[0]

def getAlignShift(alignpdata,package):
	shift = None
	if package == 'Spider':
		angle = alignpdata['rotation']*math.pi/180.0
		shift = (alignpdata['xshift']*math.cos(-angle)-alignpdata['yshift']*math.sin(-angle),
				alignpdata['xshift']*math.sin(-angle)+alignpdata['yshift']*math.cos(-angle))
	elif package == 'Xmipp':
		shift = {'x':alignpdata['xshift'],'y':alignpdata['yshift']}
	return shift

def getAlignPackage(alignrundata):
	aligntypedict = {
		'norefrun':'Spider',
		'refbasedrun':'Spider',
		'maxlikerun':'Xmipp',
		'imagicMRA':'Imagic'
	}
	for type in aligntypedict.keys():
		if alignrundata[type]:
			alignpackage = aligntypedict[type]
			break
	return alignpackage

def getSubvolumeShape(subtomorundata):
	tomoq = appionData.ApTomogramData(subtomorun=subtomorundata)
	results = tomoq.query(results=1)
	if results:
		tomo = results[0]
		shape = (tomo['dimension']['z'],tomo['dimension']['y'],tomo['dimension']['x'])
		return shape

def getFullZSubvolume(subtomorundata,stackpdata):
	pdata = stackpdata['particle']
	tomoq = appionData.ApTomogramData(subtomorun=subtomorundata,center=pdata)
	results = tomoq.query()
	if results:
		tomo = results[0]
		print tomo['center']['xcoord']
		if tomo['center']['xcoord'] < 800 or tomo['center']['xcoord'] > 1150:
			return None
		if tomo['center']['ycoord'] < 800 or tomo['center']['ycoord'] > 1250:
			return None
		path = tomo['path']['path']
		name = tomo['name']+'.rec'
		print name
		volume = mrc.read(os.path.join(path,name))
		return volume

def getParticleCenterZProfile(subvolume,shift,halfwidth):
	shape = subvolume.shape
	ystart = max(0,int(shape[1]/2.0 - shift['y'] - halfwidth))
	xstart = max(0,int(shape[1]/2.0 - shift['x'] - halfwidth))
	yend = min(shape[1],ystart + 2 * halfwidth + 1)
	xend = min(shape[2],xstart + 2 * halfwidth + 1)
	array = subvolume[:,ystart:yend,xstart:xend]
	xavg = numpy.sum(array,axis=2)/(2*halfwidth+1)
	xyavg = numpy.sum(xavg,axis=1)/(2*halfwidth+1)
	bgwidth = 35
	background = numpy.sum(xyavg[:bgwidth])/bgwidth
	background += numpy.sum(xyavg[-bgwidth:])/bgwidth
	background = background / 2
	vmax = xyavg.max()
	return (xyavg - background) / (vmax-background)

def transformTomo(a,package,alignpdata,zshift=0.0):
	shift = (alignpdata['xshift'],alignpdata['yshift'],zshift)
	angle = alignpdata['rotation']
	mirror = alignpdata['mirror']
	print shift,angle,mirror
	if package == 'Xmipp':
		return xmippTransformTomo(a,angle,shift,mirror,2)

def xmippTransformTomo(a,rot=0,shift=(0,0,0), mirror=False, order=2):
	"""
		similar to apImage.xmippTransform but on 3D volume and rotate on the
		xy plane
	"""
	b = a
	shiftxyz = (shift[2],shift[1],shift[0])
	b = ndimage.shift(b, shift=shiftxyz, mode='reflect', order=order)
	if mirror is True:
		b = numpy.fliplr(b)
	b = ndimage.shift(b, shift=(0,-0.5,-0.5), mode='wrap',order=order)
	b = ndimage.rotate(b, angle=-1*rot, axes=(2,1), reshape=False, order=order)
	b = ndimage.shift(b, shift=(0, 0.5, 0.5), mode='wrap',order=order)
	return b
	

def gaussianCenter(array):
	X = numpy.arange(array.size)
	#ignore negative shadow
	array = numpy.where(array < 0, 0,array)
	return numpy.sum(X*array)/numpy.sum(array)
'''
class Test(appionScript.AppionScript):
	def setupParserOptions(self):
		self.parser.set_usage('')
		self.parser.add_option("--subtomoId", dest="subtomoId", type="int",
			help="subtomogram id for subvolume averaging, e.g. --subtomoId=2", metavar="int")
		self.parser.add_option("--stackId", dest="stackId", type="int",
			help="Stack selected for averaging, e.g. --stackId=2", metavar="int")

	def checkConflicts(self):
		pass

	def start(self):
		subtomorunq = appionData.ApSubTomogramRunData()
		subtomorundata = subtomorunq.direct_query(self.params['subtomoId'])
		stackq = appionData.ApStackData()
		stackdata = stackq.direct_query(self.params['stackId'])
		halfwidth = 20
		ztolerance = 10
		zbackgroundrange = 15
		profiles = []
		volshape = apTomo.getSubvolumeShape(subtomorundata)
		sumvol = numpy.zeros(volshape)
		substacktype,conditionstackdata = apStack.findSubStackConditionData(stackdata)
		if substacktype in ['clustersub','alignsub']:
			alignstack = apStack.getAlignStack(substacktype,conditionstackdata)
			alignpackage = apAlignment.getAlignPackage(alignstack['alignrun'])
			stackprtls = apStack.getStackParticlesFromId(stackdata.dbid)
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
						shiftz = zcenter - center
						transformedvolume = apTomo.transformTomo(subvolume,alignpackage,alignp,shiftz)
						sumvol += transformedvolume
		mrc.write(sumvol,'test.mrc')
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

