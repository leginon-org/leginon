import os
import sys
import subprocess
from appionlib import apDisplay
from appionlib import appiondata

#=====================
def getAlignParticle(stackpdata,alignstackdata):
	oldstack = stackpdata['stack']['oldstack']
	particledata = stackpdata['particle']
	oldstackpdata = appiondata.ApStackParticlesData(stack=oldstack,particle=particledata)
	q = appiondata.ApAlignParticlesData(alignstack=alignstackdata,stackpart=oldstackpdata)
	results = q.query(readimages=False)
	if results:
		return results[0]

#=====================
def getAlignShift(alignpdata,package):
	shift = None
	if package == 'Spider':
		angle = alignpdata['rotation']*math.pi/180.0
		shift = {'x':alignpdata['xshift']*math.cos(-angle)-alignpdata['yshift']*math.sin(-angle),
				'y':alignpdata['xshift']*math.sin(-angle)+alignpdata['yshift']*math.cos(-angle)}
	elif package == 'Xmipp':
		shift = {'x':alignpdata['xshift'],'y':alignpdata['yshift']}
	return shift

#=====================
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

