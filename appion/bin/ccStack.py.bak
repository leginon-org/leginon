#!/usr/bin/env python

import pyami.quietscipy
from scipy import stats
from optparse import OptionParser
#appion
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apImagicFile

#=====================
#=====================
#=====================
def getCCValue(imgarray1, imgarray2):
	### faster cc, thanks Jim
	ccs = stats.pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
	return ccs[0]

	### old methods follow
	npix = imgarray1.shape[0] * imgarray1.shape[1]

	avg1=imgarray1.mean()
	avg2=imgarray2.mean()

	std1=imgarray1.std()
	var1=std1*std1
	std2=imgarray2.std()
	var2=std2*std2

	### convert 2d -> 1d array and compute dot product
	cc = numpy.dot(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
	cc /= npix
	cc -= (avg1*avg2)
	cc /= math.sqrt(var1*var2)
	return cc

#=====================
#=====================
#=====================
def fillSimilarityMatrix(stackfile, partnum, outfile):
	### Get initial correlation values
	### this is really, really slow

	numpart = apFile.numImagesInStack(stackfile)

	### read data and estimate time
	imagicdict = apImagicFile.readImagic(stackfile, first=partnum)
	partarray = imagicdict['images']
	numpart = partarray.shape[0]
	boxsize = partarray.shape[1]
	#timeper = 27.0e-9
	timeper = 17.0e-9
	apDisplay.printMsg("Computing CC values in about %s"
		%(apDisplay.timeString(timeper*numpart**2*boxsize**2)))

	### Computing CC values
	simf = open(outfile, 'w')
	cctime = time.time()
	for i in range(partnum, numpart):
		if i % 100 == 99:
			sys.stderr.write(".")
		for j in range(i+1, numpart):
			ccval = self.getCCValue(partarray[i],partarray[j])
			str1 = "%05d %05d %.10f\n" % (i+1, j+1, ccval)
			simf.write(str1)
			str2 = "%05d %05d %.10f\n" % (j+1, i+1, ccval)
			simf.write(str2)
	sys.stderr.write("\n")
	simf.close()
	del partarray
	del imagicdict['images']
	apDisplay.printMsg("CC calc time: %s :: %s per part :: %s per part per pixel"
		%(apDisplay.timeString(time.time()-cctime),
		apDisplay.timeString((time.time()-cctime)/numpart**2),
		apDisplay.timeString((time.time()-cctime)/numpart**2/boxsize**2)))

	return

if __name__ == '__main__':
	### setup
	parser = OptionParser()
	parser.add_option("-i", "--stackfile", dest="stackfile",
		help="Path to stack file", metavar="FILE")
	parser.add_option("-p", "--partnum", dest="partnum", type="int",
		help="Particle number to process, starting at 0, e.g. --partnum=159", metavar="#")
	parser.add_option("-o", "--outfile", dest="outfile",
		help="Output file to write CC values", metavar="FILE")
	params = apParam.convertParserToParams(parser)
	if params['stackfile'] is None:
		apDisplay.printError("Please provide a stackfile")
	if params['partnum'] is None:
		apDisplay.printError("Please provide a particle number")
	if params['outfile'] is None:
		apDisplay.printError("Please provide a output file")

	fillSimilarityMatrix(params['stackfile'], params['partnum'], params['outfile'])







