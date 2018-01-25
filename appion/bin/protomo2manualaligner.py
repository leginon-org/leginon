#!/usr/bin/env python
# coding: utf8
# 
# This script provides the user access to the protomo command line interface,
# allowing for the manual alignment

from __future__ import division
import os
import re
import sys
import glob
import subprocess
import numpy as np
import multiprocessing as mp
from pyami import mrc
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apProTomo2Aligner

try:
	import protomo
	print "\033[92m(Ignore the error: 'protomo: could not load libi3tiffio.so, TiffioModule disabled')\033[0m"
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

		self.parser.add_option("--max_image_fraction", dest="max_image_fraction", type="float",  default="0.75",
			help="Central fraction of the tilt images that will be samples for manual alignment, e.g. --max_image_fraction=0.5", metavar="float")
		
		self.parser.add_option("--sampling", dest="sampling", type="int",  default="4",
			help="Tilt image sampling factor for manual alignment, e.g. --sampling=8", metavar="int")
		
		self.parser.add_option("--center_all_images", dest="center_all_images",  default="False",
			help="Re-center all images. Used when there is significant overshifting either by Leginon or Protomo, e.g. --center_all_images=True")
		
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
		os.system('rm *i3t')
		
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		base_seriesname='series'+seriesnumber
		if (self.params['iteration'] == 'Original') or (self.params['iteration'] == 'original') or (self.params['iteration'] == 'Initial') or (self.params['iteration'] == 'initial'):
			seriesname='coarse_'+base_seriesname
			tiltfilename='original.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		elif (self.params['iteration'] == 'Coarse') or (self.params['iteration'] == 'coarse'):
			seriesname='coarse_'+base_seriesname
			tiltfilename=seriesname+'.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		elif (self.params['iteration'] == 'Coarse2') or (self.params['iteration'] == 'coarse2'):
			seriesname='coarse_'+base_seriesname+'_iter2'
			tiltfilename=seriesname+'.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		elif (self.params['iteration'] == 'Imod') or (self.params['iteration'] == 'imod') or (self.params['iteration'] == 'IMOD'):
			seriesname='imod_coarse_'+base_seriesname
			tiltfilename=seriesname+'.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		elif float(self.params['iteration']).is_integer():
			seriesname=base_seriesname
			it="%03d" % (int(self.params['iteration'])-1)
			basename='%s%s' % (seriesname,it)
			tiltfilename=basename+'.tlt'
			tiltfilename_full=self.params['rundir']+'/'+tiltfilename
		else:
			apDisplay.printError("--integer should be either an integer > 0, 'Coarse', 'Coarse2', 'Imod', or 'Original'. Aborting.")
			sys.exit()
		
		paramfilename=seriesname+'.param'
		paramfilename_full=self.params['rundir']+'/'+paramfilename
		if (self.params['iteration'] == 'Imod') or (self.params['iteration'] == 'imod') or (self.params['iteration'] == 'IMOD'):
			paramfilename='coarse_'+base_seriesname+'.param'
			paramfilename_full=self.params['rundir']+'/'+paramfilename
		
		#Print out Protomo IMAGE == TILT ANGLE pairs
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfilename_full)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename_full)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		for i in range(tiltstart-1,tiltstart+numimages+100):
			try: #If the image isn't in the .tlt file, skip it
				cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfilename_full)
				proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				if tilt_angle:
					print "Protomo Image #%d is %s degrees" % (i+1, tilt_angle.rstrip('\r\n'))
			except:
				pass
		
		print ""
		apDisplay.printMsg("\033[1mAlign images manually (to within ~5% accuracy), Save, & Quit.\033[0m")
		apDisplay.printMsg("\033[1mQuick Manual Alignment instructions:\033[0m")
		apDisplay.printMsg("\033[1m    1) View > image, Actions > Show movie. Identify an image in the center of the overall shift range.\033[0m")
		apDisplay.printMsg("\033[1m    2) View > overlay. Set the image in 1) to the reference.\033[0m")
		apDisplay.printMsg("\033[1m    3) First try Actions > Align all. Then 'show movie' again. If it aligned, then File > Save, File > Quit.\033[0m")
		apDisplay.printMsg("\033[1m    4) If 3) failed, then manually align each nearest-neighbor images by dragging and pressing 'A' to align.\033[0m")
		apDisplay.printMsg("\033[1mNote: If you get a popup error, then use the Reset button to reset the current image, or Actions > revert to reset all images.\033[0m")
		apDisplay.printMsg("\033[1mTip: Hold the 'A' button to continually align.\033[0m")
		print ""
		
		manualparam = '%s/manual_%s.param' % (self.params['rundir'], base_seriesname)
		manuali3t = '%s/manual_%s.i3t' % (self.params['rundir'], base_seriesname)
		os.system('rm %s 2>/dev/null' % manuali3t)
		raw_dir_mrcs = self.params['rundir']+'/raw/*mrc'
		image_list=glob.glob(raw_dir_mrcs)
		random_mrc=mrc.read(image_list[1])
		dimy, dimx = random_mrc.shape
		
		maxsearch_file=glob.glob(tiltfilename+'.maxsearch.*')
		if not maxsearch_file == 0:
			apProTomo2Aligner.findMaxSearchArea(os.path.basename(tiltfilename_full), dimx, dimy)
			maxsearch_file=glob.glob(tiltfilename+'.maxsearch.*')
		maxsearch_x = int(maxsearch_file[0].split('.')[-2])
		maxsearch_y = int(maxsearch_file[0].split('.')[-1])
		
		manual_x_size = apProTomo2Aligner.nextLargestSize(int(self.params['max_image_fraction']*maxsearch_x)+1)
		manual_y_size = apProTomo2Aligner.nextLargestSize(int(self.params['max_image_fraction']*maxsearch_y)+1)
		
		if self.params['center_all_images'] == "True":
			temp_tlt_file = os.path.join(os.path.dirname(tiltfilename_full),'manual_centered.tlt')
			os.system('cp %s %s' % (tiltfilename_full, temp_tlt_file))
			tiltfilename_full = temp_tlt_file
			apProTomo2Aligner.centerAllImages(tiltfilename_full, dimx, dimy)
			manual_x_size = apProTomo2Aligner.nextLargestSize(int(self.params['max_image_fraction']*dimx)+1)
			manual_y_size = apProTomo2Aligner.nextLargestSize(int(self.params['max_image_fraction']*dimy)+1)
		
		os.system('cp %s %s' % (paramfilename_full, manualparam))
		os.system("sed -i '/AP sampling/c\ S = %d' %s" % (self.params['sampling'], manualparam))
		os.system("sed -i '/AP orig window/c\ W = { %d, %d }' %s" % (manual_x_size, manual_y_size, manualparam))
		os.system("sed -i '/preprocessing/c\ preprocessing: false' %s" % manualparam)
		os.system("sed -i '/width/c\     width: { %d, %d }' %s" % (manual_x_size, manual_y_size, manualparam))
		#os.system("sed -i '/consider using N/c\     width: { %d, %d }' %s" % (manual_x_size, manual_y_size, manualparam))
		#os.system("sed -i '/AP width2/c\     width: { %d, %d }' %s" % (int(manual_x_size*0.5), int(manual_y_size*0.5), manualparam))
		print "\033[92m(Don't worry about the following potential error: 'tomoalign-gui: could not load libi3tiffio.so, TiffioModuleDisabled')\033[0m"
		process = subprocess.Popen(["tomoalign-gui", "-tlt", "%s" % tiltfilename_full, "%s" % manualparam], stdout=subprocess.PIPE)
		stdout, stderr = process.communicate()
		
		manualparam=protomo.param(manualparam)
		manualseries=protomo.series(manualparam)
		manualtilt=self.params['rundir']+'manual_'+base_seriesname+'.tlt'
		manualseries.geom(0).write(manualtilt)
		
		#cleanup
		os.system('rm -rf %s' % self.params['rundir']+'/cache/')
		if self.params['center_all_images'] == "True":
			os.system('rm -rf %s' % tiltfilename_full)
		
		apProTomo2Aligner.findMaxSearchArea(os.path.basename(manualtilt), dimx, dimy)
		
		apProTomo2Aligner.printTips("Alignment")
		
		apDisplay.printMsg('Did everything blow up and now you\'re yelling at your computer screen?')
		apDisplay.printMsg('If so, kindly email Alex at anoble@nysbc.org explaining the issue and include this log file.')
		apDisplay.printMsg('If everything worked beautifully and you publish, please use the appropriate citations listed on the Appion webpage! You can also print out all citations by typing: protomo2manualaligner.py --citations')
		
		
#=====================
#=====================
if __name__ == '__main__':
	protomo2manualaligner = ProTomo2ManualAligner()
	protomo2manualaligner.start()
	protomo2manualaligner.close()
