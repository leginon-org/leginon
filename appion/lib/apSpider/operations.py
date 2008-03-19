
## python
import time
import os
## PIL
#import Image
## spider
import spyder
## pyami
from pyami import spider
## appion
import apImage
import apEMAN
import apParam
import apDisplay

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def spiderOutputLine(int1, int2, float1, float2, float3, float4, float5, float6=1.0):
	line = "%04d" % int1
	line += " %1d" % int2
	line += apDisplay.leftPadString("%4.6f" % float1, n=12)
	line += apDisplay.leftPadString("%4.6f" % float2, n=12)
	line += apDisplay.leftPadString("%4.6f" % float3, n=12)
	line += apDisplay.leftPadString("%4.6f" % float4, n=12)
	line += apDisplay.leftPadString("%4.6f" % float5, n=12)
	line += apDisplay.leftPadString("%4.6f" % float6, n=12)
	line += "\n"
	return line

#===============================
def arrayToSpiderSingle(imgarray, imgfile, msg=False):
	### temp hack
	apImage.arrayToMrc(imgarray, "temp001.mrc", msg=msg)
	apEMAN.executeEmanCmd("proc2d temp001.mrc "+imgfile+" spiderswap-single", verbose=False, showcmd=False)
	while(not os.path.isfile(imgfile)):
		time.sleep(0.2)
	os.popen("rm -f temp001.mrc")
	### better way to do it
	#img = apImage.arrayToImage(imgarray)
	#img.save(imgfile, format='SPIDER')

#===============================
def spiderSingleToArray(imgfile, msg=False):
	### temp hack
	if not os.path.isfile(imgfile):
		apDisplay.printError("File: "+imgfile+" does not exist")
	apEMAN.executeEmanCmd("proc2d "+imgfile+" temp001.mrc", verbose=False, showcmd=False)
	while(not os.path.isfile("temp001.mrc")):
		time.sleep(0.2)
	imgarray = apImage.mrcToArray("temp001.mrc", msg=msg)
	os.popen("rm -f temp001.mrc")
	### better way to do it
	#img = Image.open(imgfile)
	#imgarray = apImage.imageToArray(img)
	return imgarray



