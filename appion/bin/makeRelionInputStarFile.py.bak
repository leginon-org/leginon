#!/usr/bin/env python

import os
from appionlib import apDisplay
from appionlib import veryBasicScript
from appionlib import appiondata
from appionlib import apStack
from appionlib.apCtf import ctfdb

class RelionMaker(veryBasicScript.VeryBasicScript):

	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --database=ID --input_images=filename --output_starfile=filename --ctfrunid=ID --stackid=ID --voltage=int --cs=float")
		self.parser.add_option("--database", dest="dbnum", type="int",
			help="Appion project database ID", metavar="ID#")	
		self.parser.add_option("--input_images", dest="images", type="str",
			help="full path to the input mrc image filename (must end in .mrcs)", metavar="filename")	
		self.parser.add_option("--output_starfile", dest="starfile", type="str",
			help="output starfile to be written with all variables", metavar="filename")	
		self.parser.add_option("--ctfrunid", dest="ctfrunid", type="int",
			help="CTF run ID number from Appion database", metavar="ID#")	
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="stack ID number from Appion database", metavar="ID#")	
		self.parser.add_option("--voltage", dest="voltage", type="int", 
			help="microscope operating voltage (in kV), e.g. 300", metavar="INT")	
		self.parser.add_option("--cs", dest="cs", type="float",
			help="microscope spherical aberration value (in mm), e.g. 2.7", metavar="FLOAT")	
		self.parser.add_option("--amplitude_contrast", dest="wgh", type="float", default=0.07,
			help="amplitude contrast value, e.g. 0.07", metavar="INT")	


	def checkConflicts(self):
		if self.params['dbnum'] is None:
			print apDisplay.printError("please specify a database ID")	
		if self.params['images'] is None:
			print apDisplay.printError("please specify an image stack filename")	
		if self.params['starfile'] is None:
			print apDisplay.printError("please specify an output starfile")	
		if self.params['ctfrunid'] is None:
			print apDisplay.printWarning("using best CTF run ID from Appion db")	
		if self.params['stackid'] is None:
			print apDisplay.printError("please specify a stack ID from Appion db")	
		if self.params['voltage'] is None:
			print apDisplay.printError("please specify the microscope operating voltage (in kV)")	
		if self.params['cs'] is None:
			print apDisplay.printError("please specify the microscope spherical aberation constant (in mm)")	

	def start(self):
		### default parameters
		starfile = self.params['starfile']
		images = self.params['images']
		dbnum = self.params['dbnum']
		ctfrunid = self.params['ctfrunid']
		stackid = self.params['stackid']
		voltage = self.params['voltage']
		cs = self.params['cs']
		wgh = self.params['wgh']
	
		### particles, angles
		appiondata.sinedon.setConfig('appiondata', db="ap%d" % dbnum)
		particledata = apStack.getStackParticlesFromId(stackid)

		### write Relion starfile header
		sf = open(starfile, "w")
		sf.write("data_images\n")
		sf.write("loop_\n")
		sf.write("_rlnImageName\n")
		sf.write("_rlnMicrographName\n")
		sf.write("_rlnDefocusU\n")
		sf.write("_rlnDefocusV\n")
		sf.write("_rlnDefocusAngle\n")
		sf.write("_rlnVoltage\n")
		sf.write("_rlnSphericalAberration\n")
		sf.write("_rlnAmplitudeContrast\n")
	
		### write info to starfile
		olddx = 0
		micn = 0
		oldimgid = None
		for i in range(len(particledata)):
			if i % 1000 == 0:
				print "done with %d particles" % i
	
			### CTF info
			image = particledata[i]['particle']['image']
			imgid = image.dbid
			try:
				ctf = ctfdb.getCtfValueForCtfRunId(image, ctfrunid, msg=False)
				dx = ctf['defocus1'] * 10e9 
				dy = ctf['defocus2'] * 10e9 
				astig = ctf['angle_astigmatism']
			except: 
				ctf = None
#				print "didn't find CTF values for image ", image.dbid
	
			if ctf is None:
				if oldimgid != imgid:
					print "particle %d: " % i, "getting best value for image: %d" % imgid
					ctf = ctfdb.getBestCtfValueForImage(image, msg=False, method='ctffind')
					dx = ctf[0]['defocus1'] * 10e9 
					dy = ctf[0]['defocus2'] * 10e9 
					astig = ctf[0]['angle_astigmatism']		
					oldctf = ctf
					oldimgid = imgid
				else:
					try:
						ctf = oldctf
						dx = oldctf[0]['defocus1'] * 10e9
						dy = oldctf[0]['defocus2'] * 10e9
						astig = oldctf[0]['angle_astigmatism']
					except:
						apDisplay.printError("no CTF information for image")
	
			if dx != olddx:
				micn += 1
				olddx = dx
	
			### write input Relion parameters 
			sf.write("%06d@%s%10d%12.3f%12.3f%12.3f%8.3f%8.3f%8.3f\n" 
				% (i+1, images, micn, dx, dy, astig, voltage, cs, wgh)
			)
		sf.close()

if __name__ == "__main__":
	starmaker = RelionMaker()
	starmaker.start()
	starmaker.close()
