#!/usr/bin/env python

import os
import sys
import glob
import subprocess
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import appionScript

#topazPicker.py -p 1 -S 2 -n testing

#=====================
#=====================
class TopazPicker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):

		### Session Info
		### session id and preset id can be obtained from the selection id
		#self.parser.add_option("--sessionid", dest="sessionid", type="int",
		#	help="the session code, e.g., '21sep21a' ", metavar="#")
		#self.parser.add_option("--presetid", dest="presetid", type="int",
		#	help="the preset id, e.g., 'enn' ", metavar="#")
		self.parser.add_option("-S", "--selection-id", dest="selectionid", type="int",
			help="the particle selection id", metavar="#")

		### Topaz Parameters
		self.parser.add_option("--num-images", dest="numimages", type="int", default=6,
			help="Number of micrographs to use for training purposes", metavar="#")
		self.parser.add_option("--threshold", dest="threshold", type="float", default=0.01,
			help="Threshold for particle cutoff, higher number -> less particles", metavar="#")
		self.parser.add_option("--test-set", dest="testset", type="int", default=33,
			help="Integer percentage of micrographs to put into the test set, default=33%", metavar="#")

		### Image Filters (copied from filterLoop.y)
		self.parser.add_option("--lowpass", "--lp", "--lpval", dest="lowpass", type="float",
			help="Low pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--highpass", "--hp", "--hpval", dest="highpass", type="float",
			help="High pass filter radius in Angstroms", metavar="FLOAT")
		self.parser.add_option("--median", "--medianval", dest="median", type="int",
			help="Median filter radius in Pixels", metavar="INT")
		self.parser.add_option("--pixlimit", dest="pixlimit", type="float",
			help="Limit pixel values to within <pixlimit> standard deviations", metavar="FLOAT")
		self.parser.add_option("--bin","--binval", "--shrink", "--binby", dest="bin", type="int", default=4,
			help="Bin the image", metavar="INT")
		### True/False Image Filter options
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert image density before processing")
		self.parser.add_option("--planereg", dest="planereg", default=False,
			action="store_true", help="Fit a 2d plane regression to the data and subtract")

	#=====================
	def checkConflicts(self):
		if self.params['selectionid'] is None:
			apDisplay.printError("Please provide a particle selection id, e.g. --selection-id=15")
		self.particledata = apParticle.getOneParticleFromSelectionId(self.params['selectionid'])
		#print(self.particledata.keys())
		#print(self.particledata['image'].keys())
		self.sessiondata = self.particledata['image']['session']
		self.params['expid'] = self.particledata['image']['session'].dbid
		self.params['sessionname'] = self.sessiondata['name']
		print("Session Name: %s"%(self.params['sessionname']))
		self.presetdata = self.particledata['image']['preset']
		self.params['preset'] = self.presetdata['name']
		print("Preset Name:  %s"%(self.params['preset']))

	#=====================
	def setRunDir(self):
		if self.params['rundir'] is None:
			if self.sessiondata is not None:
				self.params['rundir'] = self.getDefaultBaseAppionDir(self.sessiondata, [self.processdirname, self.params['runname']])

		self.params['outdir'] = self.params['rundir']

	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		self.processdirname = "topazpicker"
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def preProcessImages(self, limit=True):
		cmd = "topazPreProcessImages.py "
		print self.params.keys()
		cmd += " --projectid=%d "%(self.params['projectid'])
		cmd += " --expid=%d "%(self.params['expid'])
		cmd += " --session='%s' "%(self.params['sessionname'])
		cmd += " --preset='%s' "%(self.params['preset'])
		cmd += " --runname='preprocess' "
		self.preprocessdir = os.path.join(self.params['rundir'], "preprocess")
		cmd += " --rundir='%s' "%(self.preprocessdir)

		### KEY FLAG: usually run this twice once with limit
		###   and after training run again to process the rest
		if limit is True:
			#only process an few images for training
			cmd += " --limit=%d "%(self.params['numimages'])

		### filter parameters
		cmd += " --bin=%d "%(self.params['bin'])
		if self.params['lowpass'] is not None:
			cmd += " --lowpass=%f "%(self.params['lowpass'])
		if self.params['highpass'] is not None:
			cmd += " --highpass=%f "%(self.params['highpass'])
		if self.params['median'] is not None:
			cmd += " --median=%d "%(self.params['median'])
		if self.params['pixlimit'] is not None:
			cmd += " --pixlimit=%f "%(self.params['pixlimit'])

		if self.params['invert'] is True:
			cmd += " --invert "
		if self.params['planereg'] is True:
			cmd += " --planereg "
		### this has to be True
		cmd += " --keepall "
		cmd += " --no-wait "
		print("")
		apDisplay.printColor(cmd, "cyan")
		proc = subprocess.Popen(cmd, shell=True)
		proc.communicate()
		for i in range(3):
			print("")

#=====================
	def writeCoordinatesFile(self):
		self.particle_coordinates_file = "particle_coordinates.csv"
		self.training_images = glob.glob(os.path.join(self.preprocessdir, "*.mrc"))
		imglist = []
		for imagefilename in self.training_images:
			basename = os.path.basename(imagefilename)
			imgname = basename.split(".")[0]
			imglist.append(imgname)
		imgtree = apDatabase.getSpecificImagesFromDB(imglist, self.sessiondata)

		f = open(self.particle_coordinates_file, "w")
		f.write("image_name\tx_coord\ty_coord\n")
		for i in range(len(imgtree)):
			imgdata = imgtree[i]
			imagefilename = self.training_images[i]
			basename = os.path.basename(imagefilename)
			print basename, imgdata['filename']
			particles = apParticle.getParticles(imgdata, self.params['selectionid'])
			print("Found %d particles"%(len(particles)))
			#print(particles[0].keys())
			for partdata in particles:
				f.write("%s\t%d\t%d\n"
					%(basename,
						partdata['xcoord']/self.params['bin'],
						partdata['ycoord']/self.params['bin'],
					))
		f.close()
		sys.exit(1)

	#=====================
	def trainTopaz(self):
		cmd = ("topaz/scripts/train_test_split.py "
		+" --images all_filtered_images.txt "
		+" --targets all_scaled_coord.txt -n 10")
		
		cmd = ("topaz train "
		+" --train-images all_filtered_images_train.txt "
		+" --test-images all_filtered_images_test.txt "
		+" --train-targets all_scaled_coord_train.txt "
		+" --test-targets all_scaled_coord_test.txt")
		
		cmd = ("topaz train"
		+" --train-images all_filtered_images_train.txt "
		+" --test-images all_filtered_images_test.txt "
		+" --train-targets all_scaled_coord_train.txt "
		+" --test-targets all_scaled_coord_test.txt "
		+" --pi 0.035 ")

	#=====================
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
		apDisplay.printMsg("\n\n")
		### get info about the stack
		apDisplay.printMsg("Information about particle selection id %d"%(self.params['selectionid']))
		self.preProcessImages(limit=True)
		self.writeCoordinatesFile()

#=====================
#=====================
if __name__ == '__main__':
	topazpicker = TopazPicker()
	topazpicker.start()
	topazpicker.close()

