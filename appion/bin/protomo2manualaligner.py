#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for the manual alignment

from __future__ import division
import os
import re
import sys
import glob
import time
import shutil
import socket
import subprocess
import numpy as np
import multiprocessing as mp
from pyami import mrc
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apProTomo2Aligner
from appionlib import apProTomo2Prep

try:
	import protomo
except:
	apDisplay.printError("Protomo did not get imported. Aborting.")
	sys.exit()


#=====================
class ProTomo2ManualAligner(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseries=<#> --rundir=<rundir> --iteration=<iteration> [options]")
		
		self.parser.add_option("--tiltseries", dest="tiltseries", help="Name of Protomo series, e.g. --tiltseries=31")
		
		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")
		
		self.parser.add_option('--iteration', dest='iteration', help="Iteration to run manual alignment on. Either an integer > 0, 'Coarse', or 'Original'.")
		
		self.parser.add_option("--citations", dest="citations", action='store_true', help="Print citations list and exit.")
		
	
	#=====================
	def checkConflicts(self):
		pass
		
		#check if files exist
		#check if necessary options exist
		
		return True


	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def start(self):
		###setup
		if self.params['citations']:
			apProTomo2Aligner.printCitations()
			sys.exit()
		os.chdir(self.params['rundir'])
		
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		base_seriesname='series'+seriesnumber
		if self.params['iteration'] == 'Original':
			seriesname='coarse_'+base_seriesname
			tiltfilename='original.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		elif self.params['iteration'] == 'Coarse':
			seriesname='coarse_'+base_seriesname
			tiltfilename=seriesname+'.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		elif float(self.params['iteration']).is_integer():
			seriesname=base_seriesname
			it="%03d" % (int(self.params['iteration'])-1)
			basename='%s%s' % (seriesname,it)
			tiltfilename=basename+'.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		else:
			apDisplay.printError("--integer should be either an integer > 0, 'Coarse', or 'Original'. Aborting.")
			sys.exit()
		
		paramfilename=seriesname+'.param'
		paramfilename_full=self.params['rundir']+'/'+paramfilename
		
		print ""
		apDisplay.printMsg("\033[1mAlign images manually (to within ~5% accuracy), Save, & Quit.\033[0m")
		apDisplay.printMsg("\033[1mQuick Manual Alignment instructions:\033[0m")
		apDisplay.printMsg("\033[1m    1) View > image, Actions > Show movie. Identify an image in the center of the overall shift range.\033[0m")
		apDisplay.printMsg("\033[1m    2) View > overlay. Set the image in 1) to the reference.\033[0m")
		apDisplay.printMsg("\033[1m    3) First try Actions > Align all. Then 'show movie' again. If it aligned, then File > Save, File > Quit.\033[0m")
		apDisplay.printMsg("\033[1m    4) If 3) failed, then manually align each nearest-neighbor images by dragging and pressing 'A' to align.\033[0m")
		apDisplay.printMsg("\033[1mNote: If you get a popup error, then use the Reset button to reset the current image, or Actions > revert to reset all images.\033[0m")
		print ""
		
		manualparam = '%s/more_manual_%s.param' % (self.params['rundir'], base_seriesname)
		manuali3t = '%s/more_manual_%s.i3t' % (self.params['rundir'], base_seriesname)
		os.system('rm %s 2>/dev/null' % manuali3t)
		raw_dir_mrcs = self.params['rundir']+'/raw/*mrc'
		image_list=glob.glob(raw_dir_mrcs)
		random_mrc=mrc.read(image_list[1])
		dimx=len(random_mrc[0])
		dimy=len(random_mrc[1])
		manual_x_size = apProTomo2Aligner.nextLargestSize(int(0.65*dimx)+1)
		manual_y_size = apProTomo2Aligner.nextLargestSize(int(0.65*dimy)+1)
		os.system('cp %s %s' % (paramfilename_full, manualparam))
		os.system("sed -i '/AP sampling/c\ S = 4' %s" % manualparam)
		os.system("sed -i '/AP orig window/c\ W = { %d, %d }' %s" % (manual_x_size, manual_y_size, manualparam))
		os.system("sed -i '/preprocessing/c\ preprocessing: false' %s" % manualparam)
		os.system("sed -i '/width/c\     width: { %d, %d }' %s" % (manual_x_size, manual_y_size, manualparam))
		#os.system("sed -i '/consider using N/c\     width: { %d, %d }' %s" % (manual_x_size, manual_y_size, manualparam))
		#os.system("sed -i '/AP width2/c\     width: { %d, %d }' %s" % (int(manual_x_size*0.5), int(manual_y_size*0.5), manualparam))
		process = subprocess.Popen(["tomoalign-gui", "-tlt", "%s" % tiltfilename_full, "%s" % manualparam], stdout=subprocess.PIPE)
		stdout, stderr = process.communicate()
		
		manualparam=protomo.param(manualparam)
		manualseries=protomo.series(manualparam)
		manualtilt=self.params['rundir']+'more_manual_'+seriesname+'.tlt'
		manualseries.geom(0).write(manualtilt)
		
		#cleanup
		os.system('rm -rf %s' % self.params['rundir']+'/cache/')
		
		apProTomo2Aligner.printTips("Alignment")
		
		apDisplay.printMsg('Did everything blow up and now you\'re yelling at your computer screen?')
<<<<<<< HEAD
		apDisplay.printMsg('If so, kindly email Alex at anoble@nysbc.org and include this log file.')
=======
		apDisplay.printMsg('If so, kindly email Alex at anoble@nysbc.org explaining the issue and include this log file.')
>>>>>>> c72a4fabafee24e37ab291805391ed2edf26ee21
		apDisplay.printMsg('If everything worked beautifully and you publish, please use the appropriate citations listed on the Appion webpage! You can also print out all citations by typing: protomo2manualaligner.py --citations')
		
		
#=====================
#=====================
if __name__ == '__main__':
	protomo2manualaligner = ProTomo2ManualAligner()
	protomo2manualaligner.start()
	protomo2manualaligner.close()
