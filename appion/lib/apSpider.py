import apDisplay
import os
import apImage
import apEMAN
#import Image
import time

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

def fermiLowPassFilter(imgarray, pixrad=2.0, dataext="spi"):
	#save array to spider file
	arrayToSpiderSingle(imgarray, "temp001."+dataext)

	#run the filter
	import spyder
	spider_exe = os.popen("which spider").read().strip()
	mySpider = spyder.SpiderSession(spiderexec=spider_exe, dataext=dataext)
	#filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpider("FQ NP", "temp001", "filt001", "5", str(1.0/pixrad), "0.02")
	mySpider.close()
	#this function does not wait for a results
	time.sleep(2)

	#read array from spider file
	filtarray = spiderSingleToArray("filt001."+dataext)

	#clean up
	os.popen("rm -f temp001."+dataext+" filt001."+dataext)
	
	return filtarray

def arrayToSpiderSingle(imgarray, imgfile):
	## temp hack
	apImage.arrayToMrc(imgarray, "temp001.mrc")
	apEMAN.executeEmanCmd("proc2d temp001.mrc "+imgfile+" spiderswap-single")
	os.popen("rm -f temp001.mrc")
	## better way to do it
	#img = apImage.arrayToImage(imgarray)
	#img.save(imgfile, format='SPIDER')

def spiderSingleToArray(imgfile):
	## temp hack
	apEMAN.executeEmanCmd("proc2d "+imgfile+" temp001.mrc")
	imgarray = apImage.mrcToArray("temp001.mrc")
	os.popen("rm -f temp001.mrc")
	## better way to do it
	#img = Image.open(imgfile)
	#imgarray = apImage.imageToArray(img)
	return imgarray
