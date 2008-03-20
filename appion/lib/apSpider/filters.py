
## python
import time
import os
## PIL
#import Image
## spider
import spyder
## appion
#from apSpider import operations ### fails
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



