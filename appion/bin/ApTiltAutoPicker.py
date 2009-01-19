#!/usr/bin/env python

#python
import os
from optparse import OptionParser
import numpy
#appion
import apParam
import apDisplay
from apSpider import operations
from apTilt import autotilt

def readPickFile(pickfile):
	f = open(pickfile, "r")
	picklist = []
	for line in f:
		sline = line.strip()
		if sline[0] == ";":
			continue
		spidict = operations.spiderInLine(line)
		x = spidict['floatlist'][0]
		y = spidict['floatlist'][1]
		picklist.append((x,y))
	picks = numpy.asarray(picklist)
	return picks

def checkConflicts(params):
	if params['imgfile1'] is None:
		apDisplay.printError("image file 1 was not defined")
	if params['imgfile2'] is None:
		apDisplay.printError("image file 2 was not defined")
	if params['pickfile1'] is None:
		apDisplay.printError("pick file 1 was not defined")
	if params['pickfile2'] is None:
		apDisplay.printError("pick file 2 was not defined")
	if params['tiltangle'] is None:
		apDisplay.printError("tilt angle was not defined")
	if params['outfile'] is None:
		apDisplay.printError("outfile was not defined")
	if params['pixdiam'] is None:
		apDisplay.printError("particle diameter was not defined")
	if params['tiltaxis'] is None:
		apDisplay.printError("tilt axis angle was not defined")

if __name__ == '__main__':
	usage = "Usage: %prog -1 image1.mrc -2 image2.mrc -t angle -o output.spi --p1=pick1.spi --p2=pick2.spi"
	parser = OptionParser(usage=usage)
	parser.add_option("-1", "--image1", dest="imgfile1",
		help="First input image", metavar="FILE")
	parser.add_option("-2", "--image2", dest="imgfile2",
		help="Second input image", metavar="FILE")
	parser.add_option("--p1", "--pickfile1", dest="pickfile1",
		help="First particle pick file", metavar="FILE")
	parser.add_option("--p2", "--pickfile2", dest="pickfile2",
		help="Second particle pick file", metavar="FILE")
	parser.add_option("-t", "--tiltangle", dest="tiltangle", type="float",
		help="Absolute tilt angle,"
		+" negative, image 1 is more compressed (tilted), "
		+" positive, image 2 is more compressed (tilted)", metavar="#")
	parser.add_option("-o", "--outfile", dest="outfile",
		help="Particle picks and tilt parameters output file", metavar="FILE")
	parser.add_option("-d", "--diam", "--pixdiam", dest="pixdiam", type="float",
		help="Approximate diameter of particle in pixels", metavar="#")
	parser.add_option("-a", "--tiltaxis", dest="tiltaxis", type="float",
		help="Approximate tilt axis angle", metavar="#")
	params = apParam.convertParserToParams(parser)
	checkConflicts(params)

	curdir = os.getcwd()

	### set important parameters
	imgfile1 = os.path.join(curdir, params['imgfile1'])
	imgfile2 = os.path.join(curdir, params['imgfile2'])
	picks1 = readPickFile(os.path.join(curdir, params['pickfile1']))
	picks2 = readPickFile(os.path.join(curdir, params['pickfile2']))
	theta = params['tiltangle']
	outfile = os.path.join(curdir, params['outfile'])
	pixdiam = params['pixdiam']
	tiltaxis = params['tiltaxis']

	### run tilt automation
	autotilter = autotilt.autoTilt()
	result = autotilter.processTiltPair(imgfile1, imgfile2, picks1, picks2, theta, outfile, pixdiam, tiltaxis)

	if result is None:
		apDisplay.printWarning("Image processing failed")




