#!/usr/bin/env python

#pythonlib
import os
import re
import math
import time
import shutil
import subprocess
#appion
from appionlib import apFile
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import appionLoop2

class TopazDenoiser(appionLoop2.AppionLoop):

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--patchsize", dest="patchsize", type="int", default=-1, metavar="#")
		self.parser.add_option("--patchpadding", dest="patchpadding", type="int", default=128, metavar="#")		
		self.parser.add_option('--denoiselabel', dest='denoiselabel', default='a', metavar='CHAR')
		self.parser.add_option('--bin', dest='bin', type="int", default=2, metavar="#")

	def setProcessingDirName(self):
		self.processdirname = "topaz_denois"

	def preLoopFunctions(self):
		self.image_list = []
		return

	def processImage(self, imgdata):
		self.image_list.append(imgdata)
		
	def postLoopFunctions(self):
		if not self.image_list: return
		command = "topaz denoise "
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		image_path = sessiondata['image path']
		out_path = self.params['rundir']
		input_images = ''
		for item in self.image_list:
			input_images += os.path.join(image_path, item.filename()) +' '
		command += input_images
		command += " --format mrc"
		command += " --bin "+str(self.params['bin'])
		command += " --patch-size "+str(self.params['patchsize'])
		command += " --patch-padding "+str(self.params['patchpadding'])
		command += " --output "+out_path
		process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		apDisplay.printMsg(out)
		apDisplay.printMsg(err)
		
		preset = self.image_list[0]['preset'].copy()
		pr_postfix = "_"+self.params['denoiselabel']+"_td"
		preset['name'] += pr_postfix
		preset.insert()
		for item in self.image_list:
			filename = item.filename()
			out_file = os.path.join(out_path, filename)
			if os.path.exists(out_file):
				parts = os.path.splitext(filename)
				dest_file = parts[0]+pr_postfix+parts[1]
				dst = os.path.join(image_path, dest_file)
				shutil.move(out_file, dst)
				imdata = item.copy()
				imdata['preset'] = preset
				image = imdata.items()[1][1]
				image.filename = dest_file
				imdata['image'] = image
				imdata['filename'] = parts[0]+pr_postfix
				imdata.insert()  

	def commitToDatabase(self, imgdata):
		pass


	def checkConflicts(self):
		pass

if __name__ == '__main__':
	imgLoop = TopazDenoiser()
	imgLoop.run()


