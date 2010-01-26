
## python
import os
import time
import numpy
import subprocess
## appion
import spyder
import apParam
import apDisplay
import apFile
from pyami import spider

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
def fermiLowPassFilter(imgarray, pixrad=2.0, dataext="spi", nproc=None):
	if dataext[0] == '.': dataext = dataext[1:]
	if nproc is None:
		nproc = apParam.getNumProcessors(msg=False)
	### save array to spider file
	spider.write(imgarray, "rawimg."+dataext)
	### run the filter
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, nproc=nproc)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpiderQuiet("FQ", "rawimg", "filtimg", "5", str(1.0/pixrad), "0.04")
	mySpider.close()
	### read array from spider file
	filtarray = spider.read("filtimg."+dataext)
	### clean up
	apFile.removeFile("rawimg."+dataext)
	apFile.removeFile("filtimg."+dataext)
	return filtarray

#===============================
def fermiHighPassFilter(imgarray, pixrad=200.0, dataext="spi", nproc=None):
	if dataext[0] == '.': dataext = dataext[1:]
	if nproc is None:
		nproc = apParam.getNumProcessors(msg=False)
	### save array to spider file
	spider.write(imgarray, "rawimg."+dataext)
	### run the filter
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, nproc=nproc)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpiderQuiet("FQ", "rawimg", "filtimg", "6", str(1.0/pixrad), "0.04")
	mySpider.close()
	### read array from spider file
	filtarray = spider.read("filtimg."+dataext)
	### clean up
	apFile.removeFile("temp001."+dataext)
	apFile.removeFile("filtimg."+dataext)
	return filtarray



