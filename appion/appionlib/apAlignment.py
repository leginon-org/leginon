import os
import sys
import subprocess
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apEMAN

#=====================
def spiderline(var, value, comment=None):
	"""
	do not use this function, use appionlib.apSpider.operations
	"""
	# check if var is a numeric type
	if type(var) == type(1):
		line = "x"+str(var)+"="+str(value)+" "
		while len(line) < 11:
			line += " "
		line += "; "+comment+"\n"
	else:
		line = "["+var+"]"+value+"\n"
	sys.stderr.write(line)
	return line

#=====================
def executeSpiderCmd(spidercmd, verbose=True):
	"""
	do not use this function, use appionlib.spyder
	"""
	sys.stderr.write("SPIDER: "+spidercmd+"\n")
	try:
		if verbose is False:
			proc = subprocess.Popen(spidercmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		else:
			proc = subprocess.Popen(spidercmd, shell=True)
		proc.wait()
	except:
		apDisplay.printError("could not run spider command: "+spidercmd)

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

