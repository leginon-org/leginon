#!/usr/bin/env python

#python
import os
import re
import shutil
import subprocess
import sys
import time
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apStack
from appionlib import apFile
from appionlib import spyder

class boxMaskScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID --align-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-a", "--align-id", dest="alignstackid", type="int",
			help="aligned stack database id", metavar="ID")
		self.parser.add_option("-m", "--mask", dest="mask", type="int",
			help="outer mask radius in Angstroms")
		self.parser.add_option("-i", "--imask", dest="imask", type="int", default=0,
			help="inner mask radius in Angstroms")
		self.parser.add_option("-l", "--len", dest="length", type="int", default=240,
			help="length of mask along filament in Angstroms")
		self.parser.add_option("--falloff", dest="falloff", type="int", default=90,
			help="falloff for edges in Angstroms")
		self.parser.add_option("--vertical", dest="vertical", action="store_true", default=False,
			help="particles are already aligned vertically")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['alignstackid'] is None and self.params['vertical'] is False:
			apDisplay.printError("alignstackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def convertStackToSpider(self, stackfile):
		### convert imagic stack to spider
		emancmd  = "proc2d %s "%stackfile
		spiderstack = os.path.join(self.params['rundir'], "tmpspistack"+self.timestamp+".spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "

		emancmd += "spiderswap edgenorm"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion, this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		time.sleep(1) # wait a sec, for things to finish
		apDisplay.printColor("finished proc2d in "+apDisplay.timeString(time.time()-starttime), "cyan")

		if not os.path.isfile(spiderstack):
			apDisplay.printError("Failed to create a spider stack")

		return spiderstack
	
	#=====================
	def convertStackToImagic(self, stackfile):
		### convert spider stack to imagic
		emancmd  = "proc2d %s "%stackfile
		imagicstack = os.path.join(self.params['rundir'], "start.hed")
		apFile.removeStack(imagicstack, warn=True)
		emancmd += imagicstack+" "

		starttime = time.time()
		apDisplay.printColor("Running stack conversion, this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		time.sleep(1) # wait a sec, for things to finish
		apDisplay.printColor("finished proc2d in "+apDisplay.timeString(time.time()-starttime), "cyan")

		if not os.path.isfile(imagicstack):
			apDisplay.printError("Failed to create an imagic stack")

		return imagicstack

	#=====================
	def findRotation(self,avgimg):
		# use radon transform in SPIDER to find rotation to orient the average image vertical
		if os.path.isfile("angle.spi"):
			os.remove("angle.spi")

		box=self.alignstackdata['boxsize']
		mySpi = spyder.SpiderSession(dataext=".spi", logo=False, log=False)
		# circular mask the average
		mySpi.toSpider("MA",
			spyder.fileFilter(avgimg)+"@1",
			"_1",
			"%i,0"%((box/2)-2),
			"C",
			"E",
			"0",
			"%i,%i"%((box/2)+1,(box/2)+1),
			"3")
		# get power spectrum
		mySpi.toSpider("PW","_1","_2")
		# Radon transform
		mySpi.toSpider("RM 2DN",
			"_2",
			"1",
			"_3",
			"%i"%box,
			"%i"%(box/2),
			"0,0",
			"N")
		# mask in the X direction to only include equator
		mySpi.toSpider("MA X",
			"_3",
			"_4",
			"6,0",
			"D",
			"E",
			"0",
			"%i,%i"%((box/2),(box/2)))
		# find peak
		mySpi.toSpider("PK x20,x21,x22","_4","1,0")
		# save the angles to a file
		mySpi.toSpider("SD 1, x21","angle")
		mySpi.toSpider("SD E","angle")
		mySpi.close()

		f = open("angle.spi")
		for line in f:
			d=line.strip().split()
			if d[0][0]==";" or len(d) < 3:
				continue
			rot = float(d[2])

		os.remove("angle.spi")
		os.remove(avgimg)
		return rot

	#=====================
	def getInplaneRotations(self):
		# get all the particle rotations
		apDisplay.printMsg("reading alignment data from database")
		alignpartq = appiondata.ApAlignParticleData()
		alignpartq['alignstack'] = self.alignstackdata
		alignpartdatas = alignpartq.query()
		rotationlist = [None]*len(alignpartdatas)
		for part in alignpartdatas:
			rotationlist[part['partnum']-1] = -part['rotation']		

		return rotationlist

	#=====================
	def createRotationSpiList(self,rotationlist,rot):
		# create a SPIDER-formatted file for masking
		f = open("spirots.spi",'w')
		f.write(";           angle\n")
		for part in range(len(rotationlist)):	
			spiline = "%5d%2d%10.2f\n" % (part+1,1,rot+rotationlist[part])
			f.write(spiline)
		f.close()
		return "spirots.spi"

	#=====================
	def boxMask(self,infile,outfile,spirots=None):
		from appionlib.apSpider import operations
		# boxmask the particles
		apDisplay.printMsg("masking the particles with a rectangular box")

		nump = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		box = self.stackdata['boxsize']
		apix = self.stackdata['pixelsize']*1e10
		if self.params['mask'] is None:
			mask = box/2-2
		else:
			mask = int(self.params['mask']/apix)
		imask = int(self.params['imask']/apix)
		length = int(self.params['length']/apix)
		falloff = self.params['falloff']/apix

		mask -= falloff/2
		length = (length/2)-(falloff/2)
		
		# create blank image for mask
		maskfile = "boxmask.spi"
		operations.createBoxMask(maskfile,box,mask,length,falloff,imask)
		mySpi = spyder.SpiderSession(dataext=".spi", logo=False, log=False)
		mySpi.toSpiderQuiet("CP",
			spyder.fileFilter(maskfile),"_4")
		mySpi.toSpider("do x10=1,%i"%nump)
		if self.params['vertical'] is not True:
			mySpi.toSpider("UD IC x10,x30",
				spyder.fileFilter(spirots),
				"x30 = -1*x30",
				"RT B",
				"_4",
				"_9",
				"(x30)",
				"(0)",
				"MU",
				spyder.fileFilter(infile)+"@{******x10}",
				"_9")
		else:
			mySpi.toSpider("MU",
				spyder.fileFilter(infile)+"@{******x10}",
				"_4")
	
		mySpi.toSpider(spyder.fileFilter(outfile)+"@{******x10}",
			"*",
			"enddo")
		if self.params['vertical'] is not True:
			mySpi.toSpider("UD ICE",spyder.fileFilter(spirots))
		mySpi.close()

	#=====================
	def start(self):
		self.stackdata = appiondata.ApStackData.direct_query(self.params['stackid'])
		if self.params['vertical'] is not True:
			self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])

		# Path of the stack
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'])
		fn_oldstack = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		rotfile = None
		if self.params['vertical'] is not True:
			# get averaged image:
			self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
			avgimg = os.path.join(self.alignstackdata['path']['path'], self.alignstackdata['avgmrcfile'])

			# Convert averaged aligned mrcfile to spider
			spiavg = os.path.join(self.params['rundir'],"avg.spi")
			emancmd = "proc2d %s %s spiderswap edgenorm"%(avgimg,spiavg)
			apEMAN.executeEmanCmd(emancmd, verbose=True)

			# find rotation for vertical alignment
			rot = self.findRotation(spiavg)
			apDisplay.printMsg("found average rotation: %.2f"%rot)

			rotlist = self.getInplaneRotations()
			rotfile = self.createRotationSpiList(rotlist,rot)

		# Convert the original stack to spider
		spistack = self.convertStackToSpider(fn_oldstack)
		# boxmask the particles
		spimaskfile = "masked"+self.timestamp+".spi"
		self.boxMask(spistack,spimaskfile,rotfile)
		# Convert the spider stack to imagic
		imgstack = self.convertStackToImagic(spimaskfile)

		# Create average MRC
		apStack.averageStack(imgstack)

		# Clean up
		apDisplay.printMsg("deleting temporary processing files")
		os.remove(spistack)
		os.remove(spimaskfile)

		# Upload results
		if self.params['commit'] is True:
			oldstackparts = apStack.getStackParticlesFromId(self.params['stackid'])
			apStack.commitMaskedStack(self.params, oldstackparts, newname='start.hed')

		time.sleep(1)
		return

#=====================
if __name__ == "__main__":
	boxmask = boxMaskScript()
	boxmask.start()
	boxmask.close()


