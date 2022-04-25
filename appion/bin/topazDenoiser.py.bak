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
from appionlib import apDDLoop
from appionlib import apK2process

from pyami import mrc

#this assumes  topaz is available via `module load topaz`
cmd = os.popen("csh -c 'modulecmd python load topaz'")
exec(cmd)

class TopazDenoiser(appionLoop2.AppionLoop):

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--patchsize", dest="patchsize", type="int", default=-1, metavar="#")
		self.parser.add_option("--patchpadding", dest="patchpadding", type="int", default=128, metavar="#")		
		self.parser.add_option('--denoiselabel', dest='denoiselabel', default='a', metavar='CHAR')
		self.parser.add_option('--device', dest='device', type="int", metavar="#")
		self.parser.add_option('--earlyreturn', dest='earlyreturn', action="store_true")
		
	def setProcessingDirName(self):
		self.processdirname = "topaz_denois"

	def preLoopFunctions(self):
		self.image_list = []
		return

	def processImage(self, imgdata):
		command = "topaz denoise "
		
		image_path = imgdata['session']['image path']
		out_path = self.params['rundir']
		correctedImagePath = ""
		if self.params['earlyreturn']:
			if not imgdata['save frames']:
				apDisplay.printMsg(imgdata.filename()+ " does not have frames.")
			else:
				dd = apK2process.GatanK2Processing()
				dd.setImageData(imgdata)
				correctedImage = dd.correctFrameImage(imgdata['use frames'])
				correctedImagePath = os.path.join(os.path.split(out_path)[0],imgdata.filename())
				mrc.write(correctedImage, correctedImagePath)				 
		if not correctedImagePath: 
			command += os.path.join(image_path, imgdata.filename())
		else:
			command += correctedImagePath
		command += " --format mrc"
		command += " --model unet"		
		command += " --patch-size "+str(self.params['patchsize'])
		command += " --patch-padding "+str(self.params['patchpadding'])
		command += " --output "+out_path
		if self.params['device'] is not None :
			command += " --device "+str(self.params['device'])
		apDisplay.printMsg(command)
		process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		apDisplay.printMsg(out)
		apDisplay.printMsg(err)
		
		preset = imgdata['preset'].copy()
		pr_postfix = "-"+self.params['denoiselabel'] # derived preset starts with "-"
		preset['name'] += pr_postfix
		preset.insert()

		filename = imgdata.filename()
		out_file = os.path.join(out_path, filename)
		if os.path.exists(out_file):
			parts = os.path.splitext(filename)
			dest_file = parts[0]+pr_postfix+parts[1]
			dst = os.path.join(image_path, dest_file)
			shutil.move(out_file, dst)
			result = imgdata.copy()
			result['preset'] = preset
			image = imgdata.items()[1][1]
			image.filename = dest_file
			result['image'] = image
			result['filename'] = parts[0]+pr_postfix
			result['denoised'] = True
			result.insert()  
			apDDLoop.transferALSThickness(imgdata, result)
			apDDLoop.transferZLPThickness(imgdata, result)
		if correctedImagePath:
			os.remove(correctedImagePath)
			
	def commitToDatabase(self, imgdata):
		pass

	def checkConflicts(self):
		pass

if __name__ == '__main__':
	imgLoop = TopazDenoiser()
	imgLoop.run()


