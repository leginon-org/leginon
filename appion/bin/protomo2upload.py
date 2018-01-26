#!/usr/bin/env python
# 
# This script allows users to upload Leginon and SerialEM tilt-series to
# Appion for use in Appion-Protomo.

import os
import sys
import glob
import time
import subprocess
import numpy as np
import multiprocessing as mp
from pyami import mrc
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apProTomo2Aligner
from appionlib import apProTomo2Prep

# Required for cleanup at end
cwd=os.getcwd()
wd=''
timestr = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")

#=====================
class Protomo2Upload(basicScript.BasicScript):
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
		
		self.parser.add_option('--protomo_outdir', dest='protomo_outdir', default="out", help="Directory where other output files are stored")
		
		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")

		self.parser.add_option("--pixelsize", dest="pixelsize", type="float",
			help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
		
		self.parser.add_option("--exclude_images", dest="exclude_images",  default="999999",
			help='Select specific images in the tilt-series, e.g. --exclude_images="1,2,5-7"')
		
		self.parser.add_option("--exclude_images_by_angle", dest="exclude_images_by_angle",  default="",
			help='Select specific tilt angles in the tilt-series to remove. Accuracy must be within +-0.5 degrees, e.g. --exclude_images_by_angle="-37.5, 4.2, 27"')
		
		self.parser.add_option("--negative_recon", dest="negative_recon", type="float",  default="-90",
			help="Tilt angle, in degrees, below which all images will be removed, e.g. --negative_recon=-45", metavar="float")
		
		self.parser.add_option("--positive_recon", dest="positive_recon", type="float",  default="90",
			help="Tilt angle, in degrees, above which all images will be removed, e.g. --positive_recon=45", metavar="float")
		
		self.parser.add_option("--stack_procs", dest="stack_procs", default=1,
			help="Number of cores to use in stack creation, e.g. --stack_procs=24")

		self.parser.add_option("--tomo3d_procs", dest="tomo3d_procs", default=1,
			help="Number of cores to use in Tomo3D, e.g. --tomo3d_procs=24")

		self.parser.add_option("--tomo3d_options", dest="tomo3d_options", default='',
			help="Number of Tomo3D SIRT iterations, e.g. --tomo3d_options=-m 0.35 -A 7 -w off")

		self.parser.add_option("--tomo3d_sirt_iters", dest="tomo3d_sirt_iters",  type="int",
			help="Number of Tomo3D SIRT iterations, e.g. --tomo3d_sirt_iters=20", metavar="int")

		self.parser.add_option("--reconstruction_actions", dest="reconstruction_actions",  type="int",
			help="Actions and order of actions to perform. 1: Reconstruct, 2: CTF correct then reconstruct, 3: Dose compensate then reconstruct, 4: CTF correct then dose compensate then reconstruct, e.g. --reconstruction_actions=2", metavar="int")

		self.parser.add_option("--reconstruction_method", dest="reconstruction_method",  type="int",
			help="Software to use for reconstructon. 1: Protomo WBP, 2: Tomo3D WBP, 3: Tomo3D SIRT, 4: Stack only e.g. --reconstruction_method=2", metavar="int")

		self.parser.add_option("--recon_map_size_x", dest="recon_map_size_x",  type="int",  default="2048",
			help="Size of the reconstructed tomogram in the X direction, e.g. --recon_map_size_x=256", metavar="int")

		self.parser.add_option("--recon_map_size_y", dest="recon_map_size_y",  type="int",  default="2048",
			help="Size of the reconstructed tomogram in the Y direction, e.g. --recon_map_size_y=256", metavar="int")

		self.parser.add_option("--recon_thickness", dest="recon_thickness",  type="float",  default="2000",
			help="Thickness of the reconstructed tomogram in the Z direction, in angstroms, e.g. --recon_thickness=1000", metavar="float")
		
		self.parser.add_option("--recon_map_sampling", dest="recon_map_sampling",  default="1", type="int",
			help="Sampling rate of raw data for use in reconstruction, e.g. --recon_map_sampling=4")
		
		self.parser.add_option("--recon_lowpass", dest="recon_lowpass",  default=False, 
			help="Lowpass filter the reconstruction?, e.g. --recon_lowpass=True")
		
		self.parser.add_option("--recon_lp_diam_x", dest="recon_lp_diam_x",  default=15, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --recon_lp_diam_x=10", metavar="float")
		
		self.parser.add_option("--recon_lp_diam_y", dest="recon_lp_diam_y",  default=15, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --recon_lp_diam_y=10", metavar="float")
		
		self.parser.add_option("--recon_iter", dest="recon_iter", type="int",
			help="Refinement iteration used to make final reconstruction, e.g. --recon_iter=10", metavar="int")
			
		self.parser.add_option("--link_recon", dest="link_recon",  default="",
			help="Path to link reconstruction, e.g. --link_recon=/full/path/")
		
		self.parser.add_option("--ctf_correct", dest="ctf_correct", type="int", default=3,
			help="CTF correct images before dose compensation and before coarse alignment? 1: TomoCTF, 2: IMOD's ctfphaseflip, 3: None, e.g. --ctf_correct=2")
		
		self.parser.add_option('--DefocusTol', dest='DefocusTol', type="int", default=200,
			help='Defocus tolerance in nanometers that limits the width of the strips, e.g. --DefocusTol=200')
		
		self.parser.add_option('--iWidth', dest='iWidth', type="int", default=20,
			help='The distance in pixels between the center lines of two consecutive strips, e.g. --iWidth=20')
		
		self.parser.add_option('--amp_contrast_ctf', dest='amp_contrast_ctf', type="float", default=0.07,
			help='Amplitude contrast, e.g. --amp_contrast_ctf=0.07')
		
		self.parser.add_option('--defocus_save_recon', dest='defocus_save_recon', type="float", default=0,
			help='Save and use this defocus for TomoCTF correction, e.g. --defocus_save_recon=3000')
		
		self.parser.add_option("--dose_presets", dest="dose_presets",  default="False",
			help="Dose compensate using equation given by Grant & Grigorieff, 2015, e.g. --dose_presets=Moderate")
		
		self.parser.add_option('--dose_a', dest='dose_a', type="float",  default=0.245,
			help='\'a\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_a=0.2')
		
		self.parser.add_option('--dose_b', dest='dose_b', type="float",  default=-1.665,
			help='\'b\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_b=-1.5')
		
		self.parser.add_option('--dose_c', dest='dose_c', type="float",  default=2.81,
			help='\'c\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_c=2')
		
		self.parser.add_option("--frame_aligned", dest="frame_aligned",  default="True",
			help="Use frame-aligned images instead of naively summed images, if present.")
		
		self.parser.add_option("--bin_type", dest="bin_type",  default="",
			help="Bin by fourier, sum, or by interpolation.")
		
		self.parser.add_option("--amp_correct", dest="amp_correct",  default="off",
			help="Amplitude correct? e.g. --amp_correct=on")
		
		self.parser.add_option("--amp_correct_w1", dest="amp_correct_w1", type="float",  default=0.66,
			help="Wiener filter paramater e.g. --amp_correct_w1=0.5")
		
		self.parser.add_option("--amp_correct_w2", dest="amp_correct_w2", type="float",  default=0.33,
			help="Wiener filter paramater e.g. --amp_correct_w2=0.25")
		
		self.parser.add_option("--defocus_difference", dest="defocus_difference", type="float",  default=250,
			help="Defocus difference used for strip extraction e.g. --defocus_difference=0.5")
		
		self.parser.add_option("--pick_tomogram", dest="pick_tomogram", type="int", default=False,
			help="Pick the resulting tomogram? Options are: 1 = dogpicker, e.g. --pick_tomogram=1")
		
		self.parser.add_option("--dog_particle_diam", dest="dog_particle_diam", type="float",
			help="Particle diameter to use for DoG lowpassing, in angstroms, +-dog_diam_variance% e.g. --dog_particle_diam=100")
		
		self.parser.add_option("--dog_diam_variance", dest="dog_diam_variance", type="float",
			help="How much the expected particle varies in diameter, in angstroms. Used when making two lowpass filtered tomograms for DoG picking e.g. --dog_diam_variance=20")
		
		self.parser.add_option("--dog_max_picks", dest="dog_max_picks", type="int",  default=500,
			help="Defocus difference used for strip extraction e.g. --dog_max_picks=0.5")
		
		self.parser.add_option("--dog_junk_tolerance", dest="dog_junk_tolerance", type="float",
			help="Defocus difference used for strip extraction e.g. --dog_junk_tolerance=0.5")
		
		self.parser.add_option("--dog_lowpass_type", dest="dog_lowpass_type", default='proc3d',
			help="Defocus difference used for strip extraction e.g. --dog_lowpass_type=0.5")
		
	
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
		global wd
		wd=self.params['rundir']
		
		apDisplay.printMsg('Did everything blow up and now you\'re yelling at your computer screen?')
		apDisplay.printMsg('If so, kindly email Alex at anoble@nysbc.org explaining the issue and include this log file.')
		apDisplay.printMsg('If everything worked beautifully and you publish, please use the appropriate citations listed on the Appion webpage! You can also print out all citations by typing: protomo2aligner.py --citations')
		print "\n"
		
		apProTomo2Aligner.printTips("Reconstruction")
		

#=====================
if __name__ == '__main__':
	protomo2upload = Protomo2Upload()
	protomo2upload.start()
	protomo2upload.close()
	protomo2upload_log=cwd+'/'+'protomo2upload.log'
	cleanup="mv %s %s/protomo2upload_%s.log" % (protomo2upload_log, wd, timestr)
	os.system(cleanup)
