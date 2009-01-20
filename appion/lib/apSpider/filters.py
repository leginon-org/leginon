
## python
import time
import os
## PIL
import numpy
#import Image
## spider
import spyder
## appion
#from apSpider import operations ### fails
import apParam
import apDisplay
try:
	from pyami import spider
except:
	print "could not import spider from pyami"

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
def fermiLowPassFilter(imgarray, pixrad=2.0, dataext="spi"):
	### save array to spider file
	arrayToSpiderSingle(imgarray, "temp001."+dataext)
	### run the filter
	import spyder
	spider_exe = os.popen("which spider").read().strip()
	mySpider = spyder.SpiderSession(spiderexec=spider_exe, dataext=dataext, logo=False)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpiderQuiet("FQ NP", "temp001", "filt001", "5", str(1.0/pixrad), "0.02")
	mySpider.close()
	### this function does not wait for a results
	while(not os.path.isfile("filt001."+dataext)):
		time.sleep(0.2)
	time.sleep(0.5)
	### read array from spider file
	filtarray = spiderSingleToArray("filt001."+dataext)
	### clean up
	os.popen("rm -f temp001."+dataext+" filt001."+dataext)
	return filtarray

#===============================
def fermiHighPassFilter(imgarray, pixrad=200.0, dataext="spi"):
	### save array to spider file
	arrayToSpiderSingle(imgarray, "temp001."+dataext)
	### run the filter
	import spyder
	spider_exe = os.popen("which spider").read().strip()
	mySpider = spyder.SpiderSession(spiderexec=spider_exe, dataext=dataext, logo=False)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpiderQuiet("FQ NP", "temp001", "filt001", "6", str(1.0/pixrad), "0.02")
	mySpider.close()
	### this function does not wait for a results
	while(not os.path.isfile("filt001."+dataext)):
		time.sleep(0.2)
	time.sleep(0.5)
	### read array from spider file
	filtarray = spiderSingleToArray("filt001."+dataext)
	### clean up
	os.popen("rm -f temp001."+dataext+" filt001."+dataext)
	return filtarray

#===============================
def arrayToSpiderSingle(imgarray, imgfile, msg=False):
	spider.write(imgarray, imgfile)
	return

#===============================
def spiderSingleToArray(imgfile, msg=False):
	imgarray = spider.read(imgfile)
	return imgarray



