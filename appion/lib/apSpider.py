
## python
import time
import os
## PIL
#import Image
## spider
import spyder
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
	### save array to spider file
	arrayToSpiderSingle(imgarray, "temp001."+dataext)
	### run the filter
	import spyder
	spider_exe = os.popen("which spider").read().strip()
	mySpider = spyder.SpiderSession(spiderexec=spider_exe, dataext=dataext)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpider("FQ NP", "temp001", "filt001", "5", str(1.0/pixrad), "0.02")
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

def fermiHighPassFilter(imgarray, pixrad=200.0, dataext="spi"):
	### save array to spider file
	arrayToSpiderSingle(imgarray, "temp001."+dataext)
	### run the filter
	import spyder
	spider_exe = os.popen("which spider").read().strip()
	mySpider = spyder.SpiderSession(spiderexec=spider_exe, dataext=dataext)
	### filter request: infile, outfile, filter-type, inv-radius, temperature
	mySpider.toSpider("FQ NP", "temp001", "filt001", "6", str(1.0/pixrad), "0.02")
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

def refFreeAlignParticles(stackfile, template, numpart, pixrad,
		firstring=2, lastring=100, dataext=".spi"):
	"""
	inputs:
		stack
		template
		search params
	outputs:
		aligned stack
		rotation/shift params
	"""
	### setup
	t0 = time.time()
	apParam.createDirectory("alignment")

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext)
	mySpider.toSpider("CP", template+"@1", "_9") #copy template to memory
	mySpider.toSpider("AP SR", 
		stackfile+"@*****", "1-"+str(numpart), 
		str(pixrad), str(firstring)+","+str(firstring), 
		"_9", "alignment/avgimg***", "alignment/paramdoc***")
	mySpider.close()

	### find number of iterations
	numiter = 0
	while os.path.isfile("alignment/avgimg%03d%s" % (numiter+1, dataext)):
		numiter += 1
	if numiter == 0:
		apDisplay.printError("alignment failed")
	apDisplay.printMsg(str(numiter)+" alignment iterations were run by spider")

	### write aligned stack -- with python loop
	### I tried this loop in both spider and python: python was faster?!? -neil
	t0 = time.time()
	mySpider = spyder.SpiderSession(dataext=dataext)
	for p in range(1,numpart+1):
		mySpider.toSpider(
			"UD IC,"+str(p)+",x21,x22,x23",
			("alignment/paramdoc%03d" % (numiter)),
			"RT SQ",
			stackfile+"@"+("%05d" % (p)),
			"alignedstack@"+("%05d" % (p)),
			"x21", "x22,x23")
	mySpider.close()
	td1 = time.time()-t0

	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return "alignedstack.spi"


def correspondenceAnalysis(alignedstack, boxsize, maskrad, numpart, numfactors=20, dataext=".spi"):
	"""
	inputs:
		aligned stack
		search params
	outputs:
		eigen images
		eigen vectors
		coran parameters
	"""
	### setup
	t0 = time.time()
	apParam.createDirectory("coran")

	### make template in memory
	mySpider = spyder.SpiderSession(dataext=dataext)
	mySpider.toSpider("MO", "_9", "%d,%d" % (boxsize, boxsize), "C", str(maskrad))

	### performing correspondence analysis
	apDisplay.printMsg("Performing correspondence analysis (long wait)")
	mySpider.toSpider(
		"CA S",
		alignedstack+"@*****", "1-"+str(numpart),
		"_9", str(numfactors), "C", "10",
		"coran/corandata")

	### generate eigen images
	for fact in range(1,numfactors+1):
		mySpider.toSpider(
			"CA SRE", "coran/corandata", str(fact), 
			"coran/eigenimg@"+("%03d" % (fact)), )
		### make a nice png for webpage
		emancmd = ("proc2d coran/eigenimg.spi "
			+"coran/eigenimg"+("%03d" % (fact))+".png "
			+" first="+str(fact-1)+" last="+str(fact-1))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	### convert SPIDER image to IMAGIC for webpage
	emancmd = "proc2d coran/eigenimg.spi coran/eigenimg.hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	td1 = time.time()-t0
	apDisplay.printMsg("completed correspondence analysis of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return




