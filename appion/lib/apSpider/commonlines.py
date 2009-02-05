
## python
import time
import os
import subprocess
import cPickle
import sys
import math
import numpy
import random
## PIL
#import Image
## spider
import spyder
## appion
import apImage
import apEMAN
import apParam
import apDisplay
import apFile
from apSpider import operations

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
image stack file: 
	*****stack.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def commonLines(stackfile, maskdiam=None, minfreq=0, maxfreq=0.25, 
	ang=5.0, numiter=200, outdocfile=None, numpart=None, dataext=".spi"):
	"""
	performs common lines on a input spider stack
	"""
	if numpart is None or numpart < 3:
		apDisplay.printError("undefined number of particles")
	if maskdiam is None:
		apDisplay.printError("undefined mask diameter")
	starttime = time.time()
	if dataext in stackfile:
		stackfile = stackfile[:-4]

	randdocfile = generateRandomAngles(numpart)

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("OP",
		stackfile+"@*****", #stack file
		"1-%d"%(numpart), #number of particles
		str(maskdiam), #mark diameter
		"%.3f,%.3f"%(minfreq,maxfreq), #frequency range for line projections
		str(ang), #angular increment or accuracy
		str(numiter), #number of iterations
		randdocfile, #random angles doc file
		outdocfile, #output angles doc file
	)
	mySpider.close()
	apDisplay.printColor("finished common lines in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return

#===============================
def generateRandomAngles(numpart, dataext=".spi"):
	i = 0
	randdocfile = "randomeulerdoc"+dataext
	f.open(randdocfile)
	while(i < numpart):
		eulerlist = randomEuler()
		spiline = operations.spiderOutLine(i+1, eulerlist)
		f.write(spiline)
		i+=1
	f.close()
	return randdocfile

#===============================
def randomEuler():
	"""
	alt = int(round(random.random()*180.0,0))
	az = int(round(random.random()*360.0,0))
	phi = int(round(random.random()*360.0,0))
	"""
	#alt = int(round(random.random()*90.0,0))
	alt = int(round(random.random()*180.0,0))
	#alt = 0
	#az = int(round(random.random()*51.43,0))
	az = int(round(random.random()*360.0,0))
	#az = 0
	phi = int(round(random.random()*360.0,0))
	#phi = int(round(random.random()*6.0,0))*60
	return (alt, az, phi)



	




