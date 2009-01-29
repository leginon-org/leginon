
## python
import time
import os
## appion
import apDisplay
import spyder

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
	line += " "+apDisplay.leftPadString("%3.6f" % float1, n=11)
	line += " "+apDisplay.leftPadString("%3.6f" % float2, n=11)
	line += " "+apDisplay.leftPadString("%3.6f" % float3, n=11)
	line += " "+apDisplay.leftPadString("%3.6f" % float4, n=11)
	line += " "+apDisplay.leftPadString("%3.6f" % float5, n=11)
	line += " "+apDisplay.leftPadString("%3.6f" % float6, n=11)
	line += "\n"
	return line


#===============================
def spiderOutLine(num, floatlist):
	line = "%04d" % num
	line += " %1d" % len(floatlist)
	for fnum in floatlist:
		line += " "+apDisplay.leftPadString("%3.6f" % fnum, n=11)
	line += "\n"
	return line


#===============================
def spiderInLine(line):
	sline = line.strip()
	if sline[0] == ";":
		return None
	bits = sline.split()
	rownum = int(bits[0])
	numfloats = int(bits[1])
	floatlist = []
	for i in range(numfloats):
		floatlist.append(float(bits[i+2]))
	spidict = {
		'row': rownum,
		'count': numfloats,
		'floatlist': floatlist,
	}
	return spidict

#===============================
def addParticleToStack(partnum, partfile, stackfile, dataext=".spi"):
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet("CP", 
		spyder.fileFilter(partfile), #particle file
		spyder.fileFilter(stackfile)+"@%06d"%(partnum), #stack file
	)
	mySpider.close()
	return

#===============================
def averageStack(stackfile, numpart, avgfile, varfile, dataext=".spi"):
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("AS R", 
		spyder.fileFilter(stackfile)+"@******", #stack file
		"1-%6d"%(numpart), #num of particles
		"A", #use all particles
		spyder.fileFilter(avgfile), #average file
		spyder.fileFilter(varfile), #variance file
	)
	mySpider.close()
	return

#===============================
def createMask(maskfile, maskdiam, boxsize, dataext=".spi"):
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet("MO", 
		spyder.fileFilter(maskfile), 
		"%d,%d" % (boxsize, boxsize), 
		"C", 
		str(maskdiam),
	)
	mySpider.close()
	if not os.path.isfile(maskfile):
		apDisplay.printError("Failed to create mask file")
	return




