#!/usr/bin/env python
# 
# This script provides the user access TomoCTF defocus estimation from Protomo-aligned tilt-series.


import os
import sys
import glob
import math
import time
import subprocess
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apProTomo2Prep
from appionlib import apProTomo2Aligner

#=====================
class ProTomo2TomoCTFEstimate(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")

		self.parser.add_option("-s", "--sessionname", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")

		self.parser.add_option("--tiltseries", dest="tiltseries", type="int",
			help="tilt series number in the session", metavar="int")
		
		self.parser.add_option("--runname", dest="runname", help="Name of protmorun directory as made by Appion")
		
		self.parser.add_option("--jobtype", dest="jobtype", help="Appion jobtype")
		
		self.parser.add_option("--projectid", dest="projectid", help="Appion project ID")
		
		self.parser.add_option("--expid", dest="expid", help="Appion experiment ID")
		
		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")

		self.parser.add_option("--pixelsize", dest="pixelsize", type="float",
			help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
		
		self.parser.add_option("--frame_aligned", dest="frame_aligned",  default="True",
			help="Use frame-aligned images instead of naively summed images, if present.")
		
		self.parser.add_option('--defocus_min', dest='defocus_min', type="float", default=0,
			help='Initial defocus for search, in micrometers, e.g. --defocus_min=2.1')
		
		self.parser.add_option('--defocus_max', dest='defocus_max', type="float", default=0,
			help='Maximum defocus for search, in micrometers, e.g. --defocus_max=4.2')
		
		self.parser.add_option('--defocus_difference', dest='defocus_difference', type="float",  default=0.2,
			help='Defocus difference for strip extraction, in micrometers, e.g. --defocus_difference=0.5')
		
		self.parser.add_option('--defocus_ang_negative', dest='defocus_ang_negative', type="float", default=-90,
			help='Negative angle, in degrees, beyond which images will be excluded before defocus estimation by TomoCTF, e.g. --defocus_ang_negative=-44')

		self.parser.add_option('--defocus_ang_positive', dest='defocus_ang_positive', type="float", default=90,
			help='Positive angle, in degrees, beyond which images will be excluded before defocus estimation by TomoCTF, e.g. --defocus_ang_positive=62')

		self.parser.add_option('--amp_contrast_defocus', dest='amp_contrast_defocus', type="float", default=0.07,
			help='Amplitude contrast used with defocus estimation, e.g. --amp_contrast_defocus=0.07')
		
		self.parser.add_option('--res_min', dest='res_min', type="float", default=10000,
			help='Lowest resolution information, in angstroms, to use to fit the signal falloff before defocus estimation, e.g. --res_min=200')
		
		self.parser.add_option('--res_max', dest='res_max', type="float", default=10,
			help='Highest resolution information, in angstroms, to use to fit the signal falloff before defocus estimation, e.g. --res_max=5')
		
		self.parser.add_option('--defocus_tlt', dest='defocus_tlt', default='best_bin1or2',
			help='How should the tilt-azimuth be determined for defocus estimation? Options: original, best, best_bin1or2, or iteration, e.g. --defocus_tlt=best')
		
		self.parser.add_option('--defocus_tlt_iteration', dest='defocus_tlt_iteration', type="int",  default=0,
			help='Refinement iteration from which the tilt-azimuth will be extracted from for use in defocus estimation, e.g. --defocus_tlt_iteration=16')
		
	
	#=====================
	def checkConflicts(self):
		pass

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
		rundir=self.params['rundir']
		os.chdir(rundir)
		tiltseriesnumber = int(self.params['tiltseries'])
		seriesnumber = "%04d" % tiltseriesnumber
		seriesname='series'+seriesnumber
		
		if self.params['defocus_tlt'] == 'original':
			apDisplay.printMsg("Using the tilt-azimuth found in the original tlt file (as recorded in the database) for Tilt-Series #%s." % tiltseriesnumber)
			tiltfilename = 'original.tlt'
		elif self.params['defocus_tlt'] == 'best_bin1or2':
			try:
				best_bin1or2=glob.glob('best_bin1or2*')
				best_bin1or2=int(os.path.splitext(best_bin1or2[0])[1][1:])-1
				best_bin1or2_iteration="%03d" % best_bin1or2
				tiltfilename=seriesname.split()[0]+best_bin1or2_iteration+'.tlt'
				apDisplay.printMsg("Using the tilt-azimuth found in the tlt file from the best binned by 1 or 2 iteration (#%d) for Tilt-Series #%s." % ((best_bin1or2+1), tiltseriesnumber))
			except IndexError:
				apDisplay.printWarning("Best w/ bin 1 or 2 iteration not found. Reverting to best tlt file...")
				try:
					best=glob.glob('best*')
					best=int(os.path.splitext(best[0])[1][1:])-1
					best_iteration="%03d" % best
					tiltfilename=seriesname.split()[0]+best_iteration+'.tlt'
					apDisplay.printMsg("Using the tilt-azimuth found in the tlt file from the best iteration (#%d) for Tilt-Series #%s." % ((best+1), tiltseriesnumber))
				except IndexError:
					apDisplay.printWarning("Best iteration not found. Reverting to original tlt file...")
					apDisplay.printMsg("Using the tilt-azimuth found in the original tlt file (as recorded in the database) for Tilt-Series #%s." % tiltseriesnumber)
					self.params['defocus_tlt'] = 'original'
					tiltfilename = 'original.tlt'
		elif self.params['defocus_tlt'] == 'best':
			try:
				best=glob.glob('best*')
				best=int(os.path.splitext(best[0])[1][1:])-1
				best_iteration="%03d" % best
				tiltfilename=seriesname.split()[0]+best_iteration+'.tlt'
				apDisplay.printMsg("Using the tilt-azimuth found in the tlt file from the best iteration (#%d) for Tilt-Series #%s." % ((best+1), tiltseriesnumber))
			except IndexError:
				apDisplay.printWarning("Best iteration not found. Reverting to original tlt file...")
				apDisplay.printMsg("Using the tilt-azimuth found in the original tlt file (as recorded in the database) for Tilt-Series #%s." % tiltseriesnumber)
				self.params['defocus_tlt'] = 'original'
				tiltfilename = 'original.tlt'
		elif (self.params['defocus_tlt'] == 'iteration' and isinstance(self.params['defocus_tlt_iteration'],int)):
			try:
				iteration=self.params['defocus_tlt_iteration']-1
				iteration="%03d" % iteration
				tiltfilename=seriesname.split()[0]+iteration+'.tlt'
				apDisplay.printMsg("Using the tilt-azimuth found in the tlt file from iteration #%d for Tilt-Series #%s." % (self.params['defocus_tlt_iteration'], tiltseriesnumber))
			except IndexError:
				apDisplay.printWarning("Requested iteration %d not found. Reverting to original tlt file..." % self.params['defocus_tlt_iteration'])
				apDisplay.printMsg("Using the tilt-azimuth found in the original tlt file (as recorded in the database) for Tilt-Series #%s." % tiltseriesnumber)
				self.params['defocus_tlt'] = 'original'
				tiltfilename = 'original.tlt'
		
		defocus = (self.params['defocus_min'] + self.params['defocus_max'])/2
		apProTomo2Prep.defocusEstimate(seriesname, rundir, self.params['projectid'], self.params['sessionname'], "all", int(self.params['tiltseries']), tiltfilename, self.params['frame_aligned'], self.params['pixelsize'], self.params['defocus_ang_negative'], self.params['defocus_ang_positive'], self.params['amp_contrast_defocus'], self.params['res_min'], self.params['res_max'], defocus, self.params['defocus_difference'], self.params['defocus_min'], self.params['defocus_max'], 0)
		
		apProTomo2Aligner.printTips("Defocus")
		
		apDisplay.printMsg('Did everything blow up and now you\'re yelling at your computer screen?')
		apDisplay.printMsg('If so, kindly email Alex at anoble@nysbc.org explaining the issue and include this log file.')
		apDisplay.printMsg('If everything worked beautifully and you publish, please use the appropriate citations listed on the Appion webpage! You can also print out all citations by typing: protomo2aligner.py --citations')
		print("\n")
		

#=====================
if __name__ == '__main__':
	protomo2tomoctfestimate = ProTomo2TomoCTFEstimate()
	protomo2tomoctfestimate.start()
	protomo2tomoctfestimate.close()
