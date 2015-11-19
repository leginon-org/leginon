#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for the initial coarse alignment and subsequent iterative alignments
# to be performed serially.

from __future__ import division
import os
import sys
import glob
import time
import shutil
import subprocess
import numpy as np
import multiprocessing as mp
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apProTomo2Aligner
from appionlib import apProTomo2Prep

try:
	import protomo
except:
	apDisplay.printWarning("Protomo did not get imported. Alignment functionality won't work.")

try:
	from appionlib import appiondata
except:
	apDisplay.printWarning("MySQLdb not found...commit function disabled")

# Required for cleanup at end
cwd=os.getcwd()
rundir=''
time_start = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")

#=====================
class ProTomo2Aligner(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --sessionname=<sessionname> [options]"
			+"\nFor initial coarse alignment: %prog --tiltseriesnumber=<#> --sessionname=<sessionname> --coarse=True [options]")
		
		self.parser.add_option("--seriesname", dest="seriesname", help="Series name (for database)")
		
		self.parser.add_option("--sessionname", dest="sessionname", help="Session date, e.g. --sessionname=14aug02a")
		
		self.parser.add_option("--tiltseries", dest="tiltseries", help="Name of Protomo series, e.g. --tiltseries=31")
		
		self.parser.add_option("--runname", dest="runname", help="Name of protomorun directory as made by Appion")
		
		self.parser.add_option("--description", dest="description", default="", help="Run description")
		
		self.parser.add_option("--jobtype", dest="jobtype", help="Appion jobtype")
		
		self.parser.add_option("--projectid", dest="projectid", help="Appion project ID")
		
		self.parser.add_option("--expid", dest="expid", help="Appion experiment ID")
		
		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")
		
		self.parser.add_option('--dimx', dest='dimx', type='int', metavar='int', help='Dimension (x) of micrographs, e.g. --dimx=4096')
		
		self.parser.add_option('--dimy', dest='dimy', type='int', metavar='int', help='Dimension (y) of micrographs, e.g. --dimy=4096')
		
		self.parser.add_option('--maxtilt', dest='maxtilt', type='int', metavar='int', help='Highest image tilt in degrees, e.g. --maxtilt=65') 
		
		self.parser.add_option('--shift_limit', dest='shift_limit', type='float', metavar='float', help='Percentage of image size, above which shifts with higher shifts will be discarded for all images, e.g. --shift_limit=50') 
		
		self.parser.add_option('--angle_limit', dest='angle_limit', type='float', metavar='float', help='Only remove images from the tilt file greater than abs(angle_limit), e.g. --angle_limit=35') 
		
		self.parser.add_option('--translimit', dest='translimit', default=999999, type='float', metavar='float', help='Discard alignment and keep original geometric parameters if translational shift, in pixels, exceeds specified value, e.g. --translimit=50') 
		
		self.parser.add_option("--region_x", dest="region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --region=1024", metavar="int")
		
		self.parser.add_option("--r1_region_x", dest="r1_region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --r1_region=1024", metavar="int")
		
		self.parser.add_option("--r2_region_x", dest="r2_region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --r2_region=1024", metavar="int")
		
		self.parser.add_option("--r3_region_x", dest="r3_region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --r3_region=1024", metavar="int")
		
		self.parser.add_option("--r4_region_x", dest="r4_region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --r4_region=1024", metavar="int")
		
		self.parser.add_option("--r5_region_x", dest="r5_region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --r5_region=1024", metavar="int")
		
		self.parser.add_option("--region_y", dest="region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --region=1024", metavar="int")
		
		self.parser.add_option("--r1_region_y", dest="r1_region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --r1_region=1024", metavar="int")
		
		self.parser.add_option("--r2_region_y", dest="r2_region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --r2_region=1024", metavar="int")
		
		self.parser.add_option("--r3_region_y", dest="r3_region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --r3_region=1024", metavar="int")
		
		self.parser.add_option("--r4_region_y", dest="r4_region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --r4_region=1024", metavar="int")
		
		self.parser.add_option("--r5_region_y", dest="r5_region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --r5_region=1024", metavar="int")
		
		self.parser.add_option("--lowpass_diameter_x", dest="lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_diameter_x", dest="r1_lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_diameter_x", dest="r2_lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_diameter_x", dest="r3_lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_diameter_x", dest="r4_lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r5_lowpass_diameter_x", dest="r5_lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_diameter_y", dest="lowpass_diameter_y",  default=0.5, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_diameter_y", dest="r1_lowpass_diameter_y",  default=0.5, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_diameter_y", dest="r2_lowpass_diameter_y",  default=0.5, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_diameter_y", dest="r3_lowpass_diameter_y",  default=0.5, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_diameter_y", dest="r4_lowpass_diameter_y",  default=0.5, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r5_lowpass_diameter_y", dest="r5_lowpass_diameter_y",  default=0.5, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_apod_x", dest="lowpass_apod_x", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_apod_x", dest="r1_lowpass_apod_x", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_apod_x", dest="r2_lowpass_apod_x", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_apod_x", dest="r3_lowpass_apod_x", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_apod_x", dest="r4_lowpass_apod_x", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r5_lowpass_apod_x", dest="r5_lowpass_apod_x", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_apod_y", dest="lowpass_apod_y", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_apod_y", dest="r1_lowpass_apod_y", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_apod_y", dest="r2_lowpass_apod_y", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_apod_y", dest="r3_lowpass_apod_y", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_apod_y", dest="r4_lowpass_apod_y", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r5_lowpass_apod_y", dest="r5_lowpass_apod_y", default=0.05, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--highpass_diameter_x", dest="highpass_diameter_x", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r1_highpass_diameter_x", dest="r1_highpass_diameter_x", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r2_highpass_diameter_x", dest="r2_highpass_diameter_x", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r3_highpass_diameter_x", dest="r3_highpass_diameter_x", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r4_highpass_diameter_x", dest="r4_highpass_diameter_x", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r5_highpass_diameter_x", dest="r5_highpass_diameter_x", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_diameter_y", dest="highpass_diameter_y", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r1_highpass_diameter_y", dest="r1_highpass_diameter_y", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r2_highpass_diameter_y", dest="r2_highpass_diameter_y", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r3_highpass_diameter_y", dest="r3_highpass_diameter_y", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r4_highpass_diameter_y", dest="r4_highpass_diameter_y", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r5_highpass_diameter_y", dest="r5_highpass_diameter_y", default=0.001, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--highpass_apod_x", dest="highpass_apod_x", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r1_highpass_apod_x", dest="r1_highpass_apod_x", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r2_highpass_apod_x", dest="r2_highpass_apod_x", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r3_highpass_apod_x", dest="r3_highpass_apod_x", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r4_highpass_apod_x", dest="r4_highpass_apod_x", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r5_highpass_apod_x", dest="r5_highpass_apod_x", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_apod_y", dest="highpass_apod_y", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r1_highpass_apod_y", dest="r1_highpass_apod_y", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r2_highpass_apod_y", dest="r2_highpass_apod_y", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r3_highpass_apod_y", dest="r3_highpass_apod_y", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r4_highpass_apod_y", dest="r4_highpass_apod_y", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r5_highpass_apod_y", dest="r5_highpass_apod_y", default=0.002, type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--thickness", dest="thickness",  default=1000, type="float",
			help="Estimated thickness of unbinned specimen (in pixels), e.g. --thickness=100.0", metavar="float")
		
		self.parser.add_option("--pixelsize", dest="pixelsize", type="float",
			help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
		
		self.parser.add_option("--param", dest="param",
			help="Override other parameters and use an external paramfile. e.g. --param=/path/to/max.param", metavar="FILE")

		self.parser.add_option("--iters", dest="iters", default=1, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --iters=4", metavar="int")

		self.parser.add_option("--r1_iters", dest="r1_iters", default=1, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r1_iters=4", metavar="int")

		self.parser.add_option("--r2_iters", dest="r2_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r2_iters=4", metavar="int")

		self.parser.add_option("--r3_iters", dest="r3_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r3_iters=4", metavar="int")

		self.parser.add_option("--r4_iters", dest="r4_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r4_iters=4", metavar="int")

		self.parser.add_option("--r5_iters", dest="r5_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r5_iters=4", metavar="int")

		self.parser.add_option("--sampling", dest="sampling",  default=8, type="int",
			help="Sampling rate of raw data, e.g. --sampling=4")
		
		self.parser.add_option("--r1_sampling", dest="r1_sampling",  default=8, type="int",
			help="Sampling rate of raw data, e.g. --r1_sampling=4")
		
		self.parser.add_option("--r2_sampling", dest="r2_sampling",  default=6, type="int",
			help="Sampling rate of raw data, e.g. --r2_sampling=4")
		
		self.parser.add_option("--r3_sampling", dest="r3_sampling",  default=4, type="int",
			help="Sampling rate of raw data, e.g. --r3_sampling=4")
		
		self.parser.add_option("--r4_sampling", dest="r4_sampling",  default=2, type="int",
			help="Sampling rate of raw data, e.g. --r4_sampling=4")
		
		self.parser.add_option("--r5_sampling", dest="r5_sampling",  default=2, type="int",
			help="Sampling rate of raw data, e.g. --r5_sampling=4")
		
		self.parser.add_option("--map_sampling", dest="map_sampling",  default=8, type="int",
			help="Sampling rate of raw data for use in reconstruction, e.g. --map_sampling=4")
		
		self.parser.add_option("--r1_body", dest="r1_body",  default=0, type="float",
			help="Body size (see Protomo docs). For internal use only.")
		
		self.parser.add_option("--r2_body", dest="r2_body",  default=0, type="float",
			help="Body size (see Protomo docs). For internal use only.")
		
		self.parser.add_option("--r3_body", dest="r3_body",  default=0, type="float",
			help="Body size (see Protomo docs). For internal use only.")
		
		self.parser.add_option("--r4_body", dest="r4_body",  default=0, type="float",
			help="Body size (see Protomo docs). For internal use only.")
		
		self.parser.add_option("--r5_body", dest="r5_body",  default=0, type="float",
			help="Body size (see Protomo docs). For internal use only.")
		
		self.parser.add_option("--border", dest="border", default=100,  type="int",
			help="Width of area at the image edge to exclude from image statistics, e.g. --border=100", metavar="int")
		
		self.parser.add_option("--clip_low", dest="clip_low", default=999999,  type="float",
			help="Lower threshold specified as a multiple of the standard deviation, e.g. --clip_low=3.5", metavar="float")

		self.parser.add_option("--clip_high", dest="clip_high", default=999999,  type="float",
			help="Upper threshold specified as a multiple of the standard deviation, e.g. --clip_high=3.5", metavar="float")
		
		self.parser.add_option("--thr_low", dest="thr_low", default=0,  type="float",
			help="Lower threshold specified as density values, e.g. --thr_low=1.5", metavar="float")

		self.parser.add_option("--thr_high", dest="thr_high", default=999999,  type="float",
			help="Upper threshold specified as density values, e.g. --thr_high=2.5", metavar="float")
		
		self.parser.add_option("--gradient", dest="gradient",  default="true",
			help="Enable linear gradient subtraction for preprocessing masks, e.g. --gradient=false")
		
		self.parser.add_option("--gradient_switch", dest="gradient_switch",  type="int",
			help="Enable linear gradient subtraction for preprocessing masks, e.g. --gradient_switch=3")
		
		self.parser.add_option("--iter_gradient", dest="iter_gradient",  default="true",
			help="Iterate gradient subtraction once, e.g. --iter_gradient=false")
		
		self.parser.add_option("--iter_gradient_switch", dest="iter_gradient_switch",  type="int",
			help="Iterate gradient subtraction once, e.g. --iter_gradient_switch=3")
		
		self.filters = ( "median", "gauss" )
		self.parser.add_option("--filter", dest="filter", type="choice", choices=self.filters, default="median",
			help="Preprocessing filter. Options are 'median' or 'gauss', e.g. --filter=median")
		
		self.parser.add_option("--kernel_x", dest="kernel_x", default=3,  type="int",
			help="Filter window size, e.g. --kernel_x=5", metavar="int")

		self.parser.add_option("--r1_kernel_x", dest="r1_kernel_x", default=3,  type="int",
			help="Filter window size, e.g. --r1_kernel_x=5", metavar="int")

		self.parser.add_option("--r2_kernel_x", dest="r2_kernel_x", default=3,  type="int",
			help="Filter window size, e.g. --r2_kernel_x=5", metavar="int")

		self.parser.add_option("--r3_kernel_x", dest="r3_kernel_x", default=3,  type="int",
			help="Filter window size, e.g. --r3_kernel_x=5", metavar="int")

		self.parser.add_option("--r4_kernel_x", dest="r4_kernel_x", default=3,  type="int",
			help="Filter window size, e.g. --r4_kernel_x=5", metavar="int")

		self.parser.add_option("--r5_kernel_x", dest="r5_kernel_x", default=3,  type="int",
			help="Filter window size, e.g. --r5_kernel_x=5", metavar="int")

		self.parser.add_option("--kernel_y", dest="kernel_y", default=3,  type="int",
			help="Filter window size, e.g. --kernel_y=5", metavar="int")
		
		self.parser.add_option("--r1_kernel_y", dest="r1_kernel_y", default=3,  type="int",
			help="Filter window size, e.g. --r1_kernel_y=5", metavar="int")
		
		self.parser.add_option("--r2_kernel_y", dest="r2_kernel_y", default=3,  type="int",
			help="Filter window size, e.g. --r2_kernel_y=5", metavar="int")
		
		self.parser.add_option("--r3_kernel_y", dest="r3_kernel_y", default=3,  type="int",
			help="Filter window size, e.g. --r3_kernel_y=5", metavar="int")
		
		self.parser.add_option("--r4_kernel_y", dest="r4_kernel_y", default=3,  type="int",
			help="Filter window size, e.g. --r4_kernel_y=5", metavar="int")
		
		self.parser.add_option("--r5_kernel_y", dest="r5_kernel_y", default=3,  type="int",
			help="Filter window size, e.g. --r5_kernel_y=5", metavar="int")
		
		self.parser.add_option("--radius_x", dest="radius_x",  type="float",
			help="Widths of the Gaussian function, e.g. --radius_x=5", metavar="float")

		self.parser.add_option("--radius_y", dest="radius_y",  type="float",
			help="Widths of the Gaussian function, e.g. --radius_y=5", metavar="float")
		
		self.parser.add_option("--grow", dest="grow",  type="int",
			help="Grow the selected regions in the binary mask by the specified number of pixels. int > 0, e.g. --grow=3", metavar="int")

		self.parser.add_option("--do_estimation", dest="do_estimation",  default="false",
			help="Estimate geometric parameters instead of using stored values from previous cycle, e.g. --do_estimation=false")

		self.parser.add_option("--max_correction", dest="max_correction",  type="float",  default=999999,
			help="Terminate alignment if correction exceeds specified value e.g. --max_correction=0.04", metavar="float")

		self.parser.add_option("--max_shift", dest="max_shift",  type="float",  default=999999,
			help="Terminate alignment if translational shift exceeds specified value e.g. --max_shift=100", metavar="float")

		self.parser.add_option("--image_apodization_x", dest="image_apodization_x",  type="float",  default=None,
			help="TODO, e.g. --image_apodization_x=10.0", metavar="float")

		self.parser.add_option("--image_apodization_y", dest="image_apodization_y",  type="float",  default=None,
			help="TODO, e.g. --image_apodization_y=10.0", metavar="float")

		self.parser.add_option("--reference_apodization_x", dest="reference_apodization_x",  type="float",  default=None,
			help="TODO, e.g. --reference_apodization_x=10.0", metavar="float")

		self.parser.add_option("--reference_apodization_y", dest="reference_apodization_y",  type="float",  default=None,
			help="TODO, e.g. --reference_apodization_y=10.0", metavar="float")

		self.correlation_modes = ( "xcf", "mcf", "pcf", "dbl" )
		self.parser.add_option("--corr_mode", dest="corr_mode",
			help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
	
		self.parser.add_option("--r1_corr_mode", dest="r1_corr_mode",
			help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--r2_corr_mode", dest="r2_corr_mode",
			help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--r3_corr_mode", dest="r3_corr_mode",
			help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--r4_corr_mode", dest="r4_corr_mode",
			help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--r5_corr_mode", dest="r5_corr_mode",
			help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--correlation_size_x", dest="correlation_size_x",  type="int",  default="128",
			help="X size of cross correlation peak image, e.g. --correlation_size_x=128", metavar="int")

		self.parser.add_option("--correlation_size_y", dest="correlation_size_y",  type="int",  default="128",
			help="Y size of cross correlation peak image, e.g. --correlation_size_y=128", metavar="int")
		
		self.parser.add_option("--peak_search_radius_x", dest="peak_search_radius_x",  type="float",  default="100",
			help="Defines peak search region, e.g. --peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--r1_peak_search_radius_x", dest="r1_peak_search_radius_x",  type="float",  default="100",
			help="Defines peak search region, e.g. --r1_peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--r2_peak_search_radius_x", dest="r2_peak_search_radius_x",  type="float",  default="100",
			help="Defines peak search region, e.g. --r2_peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--r3_peak_search_radius_x", dest="r3_peak_search_radius_x",  type="float",  default="100",
			help="Defines peak search region, e.g. --r3_peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--r4_peak_search_radius_x", dest="r4_peak_search_radius_x",  type="float",  default="100",
			help="Defines peak search region, e.g. --r4_peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--r5_peak_search_radius_x", dest="r5_peak_search_radius_x",  type="float",  default="100",
			help="Defines peak search region, e.g. --r5_peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--peak_search_radius_y", dest="peak_search_radius_y",  type="float",  default="100",
			help="Defines peak search region, e.g. --peak_search_radius_y=19.0", metavar="float")
		
		self.parser.add_option("--r1_peak_search_radius_y", dest="r1_peak_search_radius_y",  type="float",  default="100",
			help="Defines peak search region, e.g. --r1_peak_search_radius_y=19.0", metavar="float")
		
		self.parser.add_option("--r2_peak_search_radius_y", dest="r2_peak_search_radius_y",  type="float",  default="100",
			help="Defines peak search region, e.g. --r2_peak_search_radius_y=19.0", metavar="float")
		
		self.parser.add_option("--r3_peak_search_radius_y", dest="r3_peak_search_radius_y",  type="float",  default="100",
			help="Defines peak search region, e.g. --r3_peak_search_radius_y=19.0", metavar="float")
		
		self.parser.add_option("--r4_peak_search_radius_y", dest="r4_peak_search_radius_y",  type="float",  default="100",
			help="Defines peak search region, e.g. --r4_peak_search_radius_y=19.0", metavar="float")
		
		self.parser.add_option("--r5_peak_search_radius_y", dest="r5_peak_search_radius_y",  type="float",  default="100",
			help="Defines peak search region, e.g. --r5_peak_search_radius_y=19.0", metavar="float")
		
		#self.parser.add_option("--cmdiameter_x", dest="cmdiameter_x",  type="float",
		#	help="Size of region for center of mass calculation, e.g. --cmdiameter_x=19.0", metavar="float")

		#self.parser.add_option("--cmdiameter_y", dest="cmdiameter_y",  type="float",,
		#	help="Size of region for center of mass calculation, e.g. --cmdiameter_y=19.0", metavar="float")

		self.parser.add_option("--slab", dest="slab", default="true",
			help="Adjust back-projection body size for a slab-like specimen, e.g. --slab=false")

		self.parser.add_option("--map_size_x", dest="map_size_x",  type="int",  default="1024",
			help="Size of the reconstructed tomogram in the X direction, e.g. --map_size_x=256", metavar="int")

		self.parser.add_option("--map_size_y", dest="map_size_y",  type="int",  default="1024",
			help="Size of the reconstructed tomogram in the Y direction, e.g. --map_size_y=256", metavar="int")

		self.parser.add_option("--map_size_z", dest="map_size_z",  type="int",  default="200",
			help="Size of the reconstructed tomogram in the Z direction, e.g. --map_size_z=128", metavar="int")
		
		self.parser.add_option("--map_lowpass_diameter_x", dest="map_lowpass_diameter_x",  type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --map_lowpass_diameter_x=0.5", metavar="float")
		
		self.parser.add_option("--map_lowpass_diameter_y", dest="map_lowpass_diameter_y",  type="float",
			help="Provide in angstroms. This will be converted to Protomo units, e.g. --map_lowpass_diameter_y=0.5", metavar="float")
		
		self.parser.add_option("--image_file_type", dest="image_file_type",
			help="Filetype extension for images. Protomo supports CCP4, EM, FFF, IMAGIC, MRC, SPIDER, SUPRIM,and TIFF, e.g. --image_file_type=mrc")
		
		self.parser.add_option("--filename_prefix", dest="filename_prefix",  default="",
			help="Prefix for input and output files, with the exception of raw image files, which are specified in the geometry file, e.g. --filename_prefix=run1")
		
		self.parser.add_option('--cachedir', dest='cachedir', default="cache", help="Directory where cache files are stored")
		
		self.parser.add_option('--protomo_outdir', dest='protomo_outdir', default="out", help="Directory where other output files are stored")
		
		self.parser.add_option("--preprocessing", dest="preprocessing",  default="true",
			help="Enable/disable preprocessing of raw image files, e.g. --preprocessing=false")
		
		self.parser.add_option("--binning", dest="binning",  default="true",
			help="Enable/disable binning of raw image files, e.g. --binning=false")
		
		# self.parser.add_option("--select_images", dest="select_images",  default="0-999999",
		# 	help='Select specific images in the tilt-series, e.g. --select_images="1,2,5-7"')
		
		self.parser.add_option("--exclude_images", dest="exclude_images",  default="999999",
			help='Select specific images in the tilt-series, e.g. --exclude_images="1,2,5-7"')
		
		self.parser.add_option("--logging", dest="logging",  default="true",
			help="Enable diagnostic terminal output, e.g. --logging=false")
		
		self.parser.add_option("--loglevel", dest="loglevel",  type="int",  default=2,
			help="Increase verbosity of diagnostic output where int > 0, e.g. --loglevel=2")
		
		self.parser.add_option("--window_area", dest="window_area",  type="float",  default=0.95,
			help="Fraction of extracted area that must lie within the source image. Real value between 0 and 1, e.g. --window_area=0.95")
			
		self.parser.add_option("--orientation", dest="orientation",  default="true",
			help="Include orientation angles in refinement, e.g. --orientation=false")
			
		self.parser.add_option("--orientation_switch", dest="orientation_switch",  type="int",
			help="Include orientation angles in refinement, e.g. --orientation_switch=3")
		
		self.parser.add_option("--azimuth", dest="azimuth",  default="true",
			help="Include tilt azimuth in refinement, e.g. --azimuth=false")
		
		self.parser.add_option("--azimuth_switch", dest="azimuth_switch",  type="int",
			help="Include tilt azimuth in refinement, e.g. --azimuth_switch=3")
		
		self.parser.add_option("--elevation", dest="elevation",  default="false",
			help="Include tilt axis elevation in refinement, e.g. --elevation=true")
		
		self.parser.add_option("--elevation_switch", dest="elevation_switch",  type="int",
			help="Include tilt axis elevation in refinement, e.g. --elevation_switch=3")
		
		self.parser.add_option("--rotation", dest="rotation",  default="true",
			help="Include in-plane rotations in refinement, e.g. --rotation=false")
		
		self.parser.add_option("--rotation_switch", dest="rotation_switch",  type="int",
			help="Include in-plane rotations in refinement, e.g. --rotation_switch=3")
		
		self.parser.add_option("--scale", dest="scale",  default="false",
			help="Include scale factors (magnification) in refinement, e.g. --scale=true")
		
		self.parser.add_option("--scale_switch", dest="scale_switch",  type="int",
			help="Include scale factors (magnification) in refinement, e.g. --scale_switch=3")
		
		self.parser.add_option("--norotations", dest="norotations",  default="false",
			help="Set in-plane rotations to zero instead of using stored values, e.g. --norotations=true")
		
		self.parser.add_option("--mask_width_x", dest="mask_width_x",  default="1024",
			help="Rectangular mask width (x), e.g. --mask_width_x=2")
		
		self.parser.add_option("--r1_mask_width_x", dest="r1_mask_width_x",  default="1024",
			help="Rectangular mask width (x), e.g. --r1_mask_width_x=2")
		
		self.parser.add_option("--r2_mask_width_x", dest="r2_mask_width_x",  default="1024",
			help="Rectangular mask width (x), e.g. --r2_mask_width_x=2")
		
		self.parser.add_option("--r3_mask_width_x", dest="r3_mask_width_x",  default="1024",
			help="Rectangular mask width (x), e.g. --r3_mask_width_x=2")
		
		self.parser.add_option("--r4_mask_width_x", dest="r4_mask_width_x",  default="1024",
			help="Rectangular mask width (x), e.g. --r4_mask_width_x=2")
		
		self.parser.add_option("--r5_mask_width_x", dest="r5_mask_width_x",  default="1024",
			help="Rectangular mask width (x), e.g. --r5_mask_width_x=2")
		
		self.parser.add_option("--mask_width_y", dest="mask_width_y",  default="1024",
			help="Rectangular mask width (y), e.g. --mask_width_y=2")
		
		self.parser.add_option("--r1_mask_width_y", dest="r1_mask_width_y",  default="1024",
			help="Rectangular mask width (y), e.g. --r1_mask_width_y=2")
		
		self.parser.add_option("--r2_mask_width_y", dest="r2_mask_width_y",  default="1024",
			help="Rectangular mask width (y), e.g. --r2_mask_width_y=2")
		
		self.parser.add_option("--r3_mask_width_y", dest="r3_mask_width_y",  default="1024",
			help="Rectangular mask width (y), e.g. --r3_mask_width_y=2")
		
		self.parser.add_option("--r4_mask_width_y", dest="r4_mask_width_y",  default="1024",
			help="Rectangular mask width (y), e.g. --r4_mask_width_y=2")
		
		self.parser.add_option("--r5_mask_width_y", dest="r5_mask_width_y",  default="1024",
			help="Rectangular mask width (y), e.g. --r5_mask_width_y=2")
		
		self.parser.add_option("--mask_apod_x", dest="mask_apod_x",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --mask_apod_x=10")
		
		self.parser.add_option("--r1_mask_apod_x", dest="r1_mask_apod_x",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r1_mask_apod_x=10")
		
		self.parser.add_option("--r2_mask_apod_x", dest="r2_mask_apod_x",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r2_mask_apod_x=10")
		
		self.parser.add_option("--r3_mask_apod_x", dest="r3_mask_apod_x",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r3_mask_apod_x=10")
		
		self.parser.add_option("--r4_mask_apod_x", dest="r4_mask_apod_x",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r4_mask_apod_x=10")
		
		self.parser.add_option("--r5_mask_apod_x", dest="r5_mask_apod_x",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r5_mask_apod_x=10")
		
		self.parser.add_option("--mask_apod_y", dest="mask_apod_y",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --mask_apod_y=10")
		
		self.parser.add_option("--r1_mask_apod_y", dest="r1_mask_apod_y",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r1_mask_apod_y=10")
		
		self.parser.add_option("--r2_mask_apod_y", dest="r2_mask_apod_y",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r2_mask_apod_y=10")
		
		self.parser.add_option("--r3_mask_apod_y", dest="r3_mask_apod_y",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r3_mask_apod_y=10")
		
		self.parser.add_option("--r4_mask_apod_y", dest="r4_mask_apod_y",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r4_mask_apod_y=10")
		
		self.parser.add_option("--r5_mask_apod_y", dest="r5_mask_apod_y",  default="10",
			help="Apodization for rectangular and ellipsoidal masks, e.g. --r5_mask_apod_y=10")
		
		self.parser.add_option("--coarse", dest="coarse",  default=False,
			help="To perform an initial coarse alignment, set to 'True'. Requires gridsearch, corr, and mask options, e.g. --coarse=True")
		
		self.parser.add_option("--gridsearch_limit", dest="gridsearch_limit",  type="float",  default=2.0,
			help="Protomo2.4 only: Gridseach +-angle limit for coarse alignment. To do a translational alignment only set to 1 and set gridsearch_limit to 0, e.g. --gridsearch_limit=2.0", metavar="float")
			
		self.parser.add_option("--gridsearch_step", dest="gridsearch_step",  type="float",  default=0.1,
			help="Protomo2.4 only: Gridseach angle step size for coarse alignment, e.g. --gridsearch_step=0.5", metavar="float")
		
		self.parser.add_option("--create_tilt_video", dest="create_tilt_video",
			help="Appion: Create a tilt-series video for depiction, e.g. --create_tilt_video=false")
		
		self.parser.add_option("--create_reconstruction", dest="create_reconstruction",
			help="Appion: Create a reconstruction and video for depiction, e.g. --create_reconstruction=false")
		
		self.parser.add_option("--show_window_size", dest="show_window_size",  default="true",
			help="Appion: Show the window size used for alignment in the reconstruction video, e.g. --show_window_size=false")
		
		self.parser.add_option("--keep_recons", dest="keep_recons",
			help="Appion: Keep intermediate reconstruction files, e.g. --keep_recons=true")

		self.parser.add_option("--tilt_clip", dest="tilt_clip",  default="true",
			help="Appion: Clip pixel values for tilt-series video to +-5 sigma, e.g. --tilt_clip=false")
		
		self.parser.add_option("--video_type", dest="video_type",
			help="Appion: Create either gifs or html5 videos using 'gif' or 'html5vid', respectively, e.g. --video_type=html5vid")
		
		self.parser.add_option("--restart_cycle", dest="restart_cycle",  type="int",  default=0,
			help="Restart a Refinement at this iteration, e.g. --restart_cycle=2", metavar="int")
		
		self.parser.add_option("--link", dest="link",  default="False",
			help="Link raw images if True, copy if False, e.g. --link=False (NOW OBSOLETE)")
		
		self.parser.add_option("--ctf_correct", dest="ctf_correct",  default="False",
			help="CTF correct images before dose compensation and before coarse alignment?, e.g. --ctf_correct=True")
		
		self.parser.add_option('--DefocusTol', dest='DefocusTol', type="int", default=200,
			help='Defocus tolerance in nanometers that limits the width of the strips, e.g. --DefocusTol=200')
		
		self.parser.add_option('--iWidth', dest='iWidth', type="int", default=20,
			help='The distance in pixels between the center lines of two consecutive strips, e.g. --iWidth=20')
		
		self.parser.add_option('--amp_contrast', dest='amp_contrast', type="float", default=0.07,
			help='Amplitude contrast, e.g. --amp_contrast=0.07')
		
		self.parser.add_option("--dose_presets", dest="dose_presets",  default="False",
			help="Dose compensate using equation given by Grant & Grigorieff, 2015, e.g. --dose_presets=Moderate")
		
		self.parser.add_option('--dose_a', dest='dose_a', type="float",  default=0.245,
			help='\'a\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_a=0.2')
		
		self.parser.add_option('--dose_b', dest='dose_b', type="float",  default=-1.665,
			help='\'b\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_b=-1.5')
		
		self.parser.add_option('--dose_c', dest='dose_c', type="float",  default=2.81,
			help='\'c\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_c=2')
		
		self.parser.add_option("--commit", dest="commit",  default="False",
			help="Commit per-iteration information to database.")
		
		self.parser.add_option("--parallel", dest="parallel",  default="True",
			help="Parallelize image and video production.")
		
		self.parser.add_option("--frame_aligned", dest="frame_aligned",  default="True",
			help="Use frame-aligned images instead of naively summed images, if present.")
		
		self.parser.add_option("--my_tlt", dest="my_tlt",  default="False",
			help="Allows for manual tilt-series setup")
		
		self.parser.add_option("--make_searchable", dest="make_searchable",  default="False",
			help="Hidden option. Places a .tiltseries.XXXX file in the rundir so that it will be found by Batch Summary webpages.")
		
		#File path returns and extra information for database
		self.parser.add_option("--corr_peak_gif", dest="corr_peak_gif", default=None)
		self.parser.add_option("--corr_peak_mp4", dest="corr_peak_mp4", default=None)
		self.parser.add_option("--corr_peak_ogv", dest="corr_peak_ogv", default=None)
		self.parser.add_option("--corr_peak_webm", dest="corr_peak_webm", default=None)
		self.parser.add_option("--tiltseries_gif", dest="tiltseries_gif", default=None)
		self.parser.add_option("--tiltseries_mp4", dest="tiltseries_mp4", default=None)
		self.parser.add_option("--tiltseries_ogv", dest="tiltseries_ogv", default=None)
		self.parser.add_option("--tiltseries_webm", dest="tiltseries_webm", default=None)
		self.parser.add_option("--recon_gif", dest="recon_gif", default=None)
		self.parser.add_option("--recon_mp4", dest="recon_mp4", default=None)
		self.parser.add_option("--recon_ogv", dest="recon_ogv", default=None)
		self.parser.add_option("--recon_webm", dest="recon_webm", default=None)
		self.parser.add_option("--qa_gif", dest="qa_gif", default=None)
		self.parser.add_option("--corr_plot_coa_gif", dest="corr_plot_coa_gif", default=None)
		self.parser.add_option("--corr_plot_cofx_gif", dest="corr_plot_cofx_gif", default=None)
		self.parser.add_option("--corr_plot_cofy_gif", dest="corr_plot_cofy_gif", default=None)
		self.parser.add_option("--corr_plot_rot_gif", dest="corr_plot_rot_gif", default=None)
		self.parser.add_option("--corr_plot_scl_gif", dest="corr_plot_scl_gif", default=None)
		self.parser.add_option("--azimuth_gif", dest="azimuth_gif", default=None)
		self.parser.add_option("--model_azimuth", dest="model_azimuth", default=None)
		self.parser.add_option("--model_elevation", dest="model_elevation", default=None)
		self.parser.add_option("--model_psi", dest="model_psi", default=None)
		self.parser.add_option("--model_theta", dest="model_theta", default=None)
		self.parser.add_option("--model_phi", dest="model_phi", default=None)
	
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
	def insertIterationIntoDatabase(self, r):
		"""
		All parameters, geometry model, and output file paths need to be
		written to the database for each iteration.
		"""
		
		#Set round parameters
		if r != 0:
			self.param['region_x'] = self.param['r%s_region_x' % r];self.param['region_y'] = self.param['r%s_region_y' % r];
			self.param['lowpass_diameter_x'] = self.param['r%s_lowpass_diameter_x' % r];self.param['lowpass_diameter_y'] = self.param['r%s_lowpass_diameter_y' % r];
			self.param['highpass_diameter_x'] = self.param['r%s_highpass_diameter_x' % r];self.param['highpass_diameter_y'] = self.param['r%s_highpass_diameter_y' % r];
			self.param['lowpass_apod_x'] = self.param['r%s_lowpass_apod_x' % r];self.param['lowpass_apod_y'] = self.param['r%s_lowpass_apod_y' % r];
			self.param['highpass_apod_x'] = self.param['r%s_highpass_apod_x' % r];self.param['highpass_apod_y'] = self.param['r%s_highpass_apod_y' % r];
			self.param['sampling'] = self.param['r%s_sampling' % r];
			self.param['kernel_x'] = self.param['r%s_kernel_x' % r];self.param['kernel_y'] = self.param['r%s_kernel_y' % r];
			self.param['corr_mode'] = self.param['r%s_corr_mode' % r];
			self.param['peak_search_radius_x'] = self.param['r%s_peak_search_radius_x' % r];self.param['peak_search_radius_y'] = self.param['r%s_peak_search_radius_y' % r];
			self.param['mask_width_x'] = self.param['r%s_mask_width_x' % r];self.param['mask_width_y'] = self.param['r%s_mask_width_y' % r];
			self.param['mask_apod_x'] = self.param['r%s_mask_apod_x' % r];self.param['mask_apod_y'] = self.param['r%s_mask_apod_y' % r];
		
		#Gather iteration parameters model, output files
		protomodata = appiondata.ApProtomoParamsData()
		protomodata['series_name'] = self.params['seriesname']
		protomoparams = appiondata.ApProtomoAlignmentParamsData()
		protomoparams['shift_limit'] = self.params['shift_limit']
		protomoparams['angle_limit'] = self.params['angle_limit']
		protomoparams['translimit'] = self.params['translimit']
		protomoparams['region_x'] = self.params['region_x']
		protomoparams['region_y'] = self.params['region_y']
		protomoparams['lowpass_diameter_x'] = self.params['lowpass_diameter_x']
		protomoparams['lowpass_diameter_y'] = self.params['lowpass_diameter_y']
		protomoparams['lowpass_apod_x'] = self.params['lowpass_apod_x']
		protomoparams['lowpass_apod_y'] = self.params['lowpass_apod_y']
		protomoparams['highpass_diameter_x'] = self.params['highpass_diameter_x']
		protomoparams['highpass_diameter_y'] = self.params['highpass_diameter_y']
		protomoparams['highpass_apod_x'] = self.params['highpass_apod_x']
		protomoparams['highpass_apod_y'] = self.params['highpass_apod_y']
		protomoparams['thickness'] = self.params['thickness']
		protomoparams['param'] = self.params['param']
		protomoparams['sampling'] = self.params['sampling']
		protomoparams['map_sampling'] = self.params['map_sampling']
		protomoparams['border'] = self.params['border']
		protomoparams['clip_low'] = self.params['clip_low']
		protomoparams['clip_high'] = self.params['clip_high']
		protomoparams['thr_low'] = self.params['thr_low']
		protomoparams['thr_high'] = self.params['thr_high']
		protomoparams['gradient'] = self.params['gradient']
		protomoparams['gradient_switch'] = self.params['gradient_switch']
		protomoparams['iter_gradient'] = self.params['iter_gradient']
		protomoparams['iter_gradient_switch'] = self.params['iter_gradient_switch']
		protomoparams['filter'] = self.params['filter']
		protomoparams['kernel_x'] = self.params['kernel_x']
		protomoparams['kernel_y'] = self.params['kernel_y']
		protomoparams['radius_x'] = self.params['radius_x']
		protomoparams['radius_y'] = self.params['radius_y']
		protomoparams['grow'] = self.params['grow']
		protomoparams['do_estimation'] = self.params['do_estimation']
		protomoparams['max_correction'] = self.params['max_correction']
		protomoparams['max_shift'] = self.params['max_shift']
		protomoparams['image_apodization_x'] = self.params['image_apodization_x']
		protomoparams['image_apodization_y'] = self.params['image_apodization_y']
		protomoparams['reference_apodization_x'] = self.params['reference_apodization_x']
		protomoparams['reference_apodization_y'] = self.params['reference_apodization_y']
		protomoparams['corr_mode'] = self.params['corr_mode']
		protomoparams['correlation_size_x'] = self.params['correlation_size_x']
		protomoparams['correlation_size_y'] = self.params['correlation_size_y']
		protomoparams['peak_search_radius_x'] = self.params['peak_search_radius_x']
		protomoparams['peak_search_radius_y'] = self.params['peak_search_radius_y']
		protomoparams['cmdiameter_x'] = self.params['cmdiameter_x']
		protomoparams['cmdiameter_y'] = self.params['cmdiameter_y']
		protomoparams['map_size_x'] = self.params['map_size_x']
		protomoparams['map_size_y'] = self.params['map_size_y']
		protomoparams['map_size_z'] = self.params['map_size_z']
		protomoparams['map_lowpass_diameter_x'] = self.params['map_lowpass_diameter_x']
		protomoparams['map_lowpass_diameter_y'] = self.params['map_lowpass_diameter_y']
		protomoparams['image_file_type'] = self.params['image_file_type']
		protomoparams['filename_prefix'] = self.params['filename_prefix']
		protomoparams['cachedir'] = self.params['cachedir']
		protomoparams['protomo_outdir'] = self.params['protomo_outdir']
		protomoparams['preprocessing'] = self.params['preprocessing']
		protomoparams['binning'] = self.params['binning']
		#protomoparams['select_images'] = self.params['select_images']
		protomoparams['exclude_images'] = self.params['exclude_images']
		protomoparams['logging'] = self.params['logging']
		protomoparams['loglevel'] = self.params['loglevel']
		protomoparams['window_area'] = self.params['window_area']
		protomoparams['orientation'] = self.params['orientation']
		protomoparams['orientation_switch'] = self.params['orientation_switch']
		protomoparams['azimuth'] = self.params['azimuth']
		protomoparams['azimuth_switch'] = self.params['azimuth_switch']
		protomoparams['elevation'] = self.params['elevation']
		protomoparams['elevation_switch'] = self.params['elevation_switch']
		protomoparams['rotation'] = self.params['rotation']
		protomoparams['rotation_switch'] = self.params['rotation_switch']
		protomoparams['scale'] = self.params['scale']
		protomoparams['scale_switch'] = self.params['scale_switch']
		protomoparams['norotations'] = self.params['norotations']
		protomoparams['mask_width_x'] = self.params['mask_width_x']
		protomoparams['mask_width_y'] = self.params['mask_width_y']
		protomoparams['mask_apod_x'] = self.params['mask_apod_x']
		protomoparams['mask_apod_y'] = self.params['mask_apod_y']
		protomoparams['coarse'] = self.params['coarse']
		protomoparams['gridsearch_limit'] = self.params['gridsearch_limit']
		protomoparams['gridsearch_step'] = self.params['gridsearch_step']
		protomoparams['create_tilt_video'] = self.params['create_tilt_video']
		protomoparams['create_reconstruction'] = self.params['create_reconstruction']
		protomoparams['show_window_size'] = self.params['show_window_size']
		protomoparams['keep_recons'] = self.params['keep_recons']
		protomoparams['tilt_clip'] = self.params['tilt_clip']
		protomoparams['video_type'] = self.params['video_type']
		protomoparams['restart_cycle'] = self.params['restart_cycle']
		protomoparams['corr_peak_gif'] = self.params['corr_peak_gif']
		protomoparams['corr_peak_mp4'] = self.params['corr_peak_mp4']
		protomoparams['corr_peak_ogv'] = self.params['corr_peak_ogv']
		protomoparams['corr_peak_webm'] = self.params['corr_peak_webm']
		protomoparams['tiltseries_gif'] = self.params['tiltseries_gif']
		protomoparams['tiltseries_mp4'] = self.params['tiltseries_mp4']
		protomoparams['tiltseries_ogv'] = self.params['tiltseries_ogv']
		protomoparams['tiltseries_webm'] = self.params['tiltseries_webm']
		protomoparams['recon_gif'] = self.params['recon_gif']
		protomoparams['recon_mp4'] = self.params['recon_mp4']
		protomoparams['recon_ogv'] = self.params['recon_ogv']
		protomoparams['recon_webm'] = self.params['recon_webm']
		protomoparams['qa_gif'] = self.params['qa_gif']
		protomoparams['corr_plot_coa_gif'] = self.params['corr_plot_coa_gif']
		protomoparams['corr_plot_cofx_gif'] = self.params['corr_plot_cofx_gif']
		protomoparams['corr_plot_cofy_gif'] = self.params['corr_plot_cofy_gif']
		protomoparams['corr_plot_rot_gif'] = self.params['corr_plot_rot_gif']
		protomoparams['corr_plot_scl_gif'] = self.params['corr_plot_scl_gif']
		protomoparams['azimuth_gif'] = self.params['azimuth_gif']
		protomoparams['theta_gif'] = self.params['theta_gif']
		
		#Get iteration model
		protomomodel = appiondata.ApProtomoModelData()
		protomomodel['model_azimuth'] = self.params['model_azimuth']
		protomomodel['model_elevation'] = self.params['model_elevation']
		protomomodel['model_psi'] = self.params['model_psi']
		protomomodel['model_theta'] = self.params['model_theta']
		protomomodel['model_phi'] = self.params['model_phi']
		
		#Insert run information
		protomorun = appiondata.ApTomoAlignmentRunData()
		protomorun['session'] = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		protomorun['tiltseries'] = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(int(self.params['tiltseries']), protomorun['session'])
		protomorun['refineProtomoParams'] = protomoparams
		protomorun['sessionname'] = self.params['sessionname']
		protomorun['rundir'] = os.path.join(self.params['rundir'],self.params['runname'])
		protomorun['runname'] = self.params['runname']
		protomorun['description'] = self.params['description']
		
		#Insert
		protomorun.insert()
		
		return
		
	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def getPerImageTransforms(self, tiltfile, dimx, dimy):
		"""
		Sets parameters for shifts, rotatons, and scale to be inserted into database.
		"""
		cmd1="awk '/IMAGE /{print $2}' %s | head -n +1" % tiltfile
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(start, err) = proc.communicate()
		start=int(start)
		
		cmd2="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(rawimagecount, err) = proc.communicate()
		rawimagecount=int(rawimagecount)
		
		for i in range(start, rawimagecount+1):
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			cmd5="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ROTATION/) print $(j+1)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(rotation, err) = proc.communicate()
			rotation=float(rotation)
			cmd6="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/SCALE/) print $(j+1)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd6, stdout=subprocess.PIPE, shell=True)
			(scale, err) = proc.communicate()
			scale=float(scale)
			
			transx=int((dimx/2) - originx)
			transy=int((dimy/2) - originy)
			
		return
		
	#=====================
	def getModelAngles(self, tiltfile):
		"""
		Sets parameters for model to be inserted into database.
		"""
		cmd1="awk '/AZIMUTH /{print $3}' %s" % tiltfile
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(azimuth, err) = proc.communicate()
		self.params['model_azimuth']=float(azimuth)
		try:
			cmd2="awk '/ELEVATION /{print $3}' %s" % tiltfile
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(elevation, err) = proc.communicate()
			self.params['model_elevation']=float(elevation)
		except ImportError:
			pass
		
		try:
			cmd3="awk '/PSI /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(psi, err) = proc.communicate()
			self.params['model_psi']=float(psi)
		except ImportError:
			pass
		
		try:
			cmd4="awk '/THETA /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(theta, err) = proc.communicate()
			self.params['model_theta']=float(theta)
		except ImportError:
			pass
		
		try:
			cmd5="awk '/PHI /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(phi, err) = proc.communicate()
			self.params['model_phi']=float(phi)
		except ImportError:
			pass
		
	
	#=====================
	def excludeImages(self, tiltfilename_full, f):
		#Remove images from .tlt file if user requests
		if self.params['exclude_images'] != "999999":
			exclude_images='%s' % self.params['exclude_images']
			imageranges=apProTomo2Aligner.hyphen_range(exclude_images)
			for imagenumber in imageranges:
				apProTomo2Aligner.removeImageFromTiltFile(tiltfilename_full, imagenumber, remove_refimg="False")
			apDisplay.printMsg("Images %s have been removed from the .tlt file by user request" % imageranges)
			f.write("Images %s have been removed from the .tlt file by user request" % imageranges)
		cmd1="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(rawimagecount, err) = proc.communicate()
		rawimagecount=int(rawimagecount)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename_full)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		maxtilt=0
		for i in range(tiltstart-1,tiltstart+rawimagecount-1):
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfilename_full)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			try:
				tilt_angle=float(tilt_angle)
				maxtilt=max(maxtilt,abs(tilt_angle))
			except: #Image is not in the .tlt file
				pass
		return rawimagecount, maxtilt
	
	
	#=====================
	def angstromsToProtomo(self, coarse=False):
		#Backup lp values for depiction purposes
		r1_lp=r2_lp=r3_lp=r4_lp=r5_lp=0
		r1_lp=(self.params['lowpass_diameter_x']+self.params['lowpass_diameter_y'])/2
		self.params['thickness'] = self.params['thickness']/self.params['pixelsize']
		self.params['lowpass_diameter_x'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['lowpass_diameter_x']
		self.params['lowpass_diameter_y'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['lowpass_diameter_y']
		self.params['highpass_diameter_x'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['highpass_diameter_x']
		self.params['highpass_diameter_y'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['highpass_diameter_y']
		self.params['lowpass_apod_x'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['lowpass_apod_x']
		self.params['lowpass_apod_y'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['lowpass_apod_y']
		self.params['highpass_apod_x'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['highpass_apod_x']
		self.params['highpass_apod_y'] = 2*self.params['pixelsize']*self.params['sampling']/self.params['highpass_apod_y']
		
		#Set map_size_z (for reconstruction depictions) to be 2 times the thickness (thickness plus 50% on both sizes)
		self.params['map_size_z']=int(2*self.params['thickness']/self.params['map_sampling'])
		
		if coarse == "False":
			r1_lp=(self.params['r1_lowpass_diameter_x']+self.params['r1_lowpass_diameter_y'])/2
			self.params['r1_lowpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_lowpass_diameter_x']
			self.params['r1_lowpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_lowpass_diameter_y']
			self.params['r1_highpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_highpass_diameter_x']
			self.params['r1_highpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_highpass_diameter_y']
			self.params['r1_lowpass_apod_x'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_lowpass_apod_x']
			self.params['r1_lowpass_apod_y'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_lowpass_apod_y']
			self.params['r1_highpass_apod_x'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_highpass_apod_x']
			self.params['r1_highpass_apod_y'] = 2*self.params['pixelsize']*self.params['r1_sampling']/self.params['r1_highpass_apod_y']
			self.params['r1_body']=(self.params['thickness']/self.params['r1_sampling'])/self.params['cos_alpha']
			self.params['map_size_z']=int(2*self.params['thickness']/self.params['map_sampling'])
			try:
				r2_lp=(self.params['r2_lowpass_diameter_x']+self.params['r2_lowpass_diameter_y'])/2
				self.params['r2_lowpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r2_lowpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r2_highpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r2_highpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r2_lowpass_apod_x'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r2_lowpass_apod_y'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r2_highpass_apod_x'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_highpass_apod_x']
			except:
				pass
			try:
				self.params['r2_highpass_apod_y'] = 2*self.params['pixelsize']*self.params['r2_sampling']/self.params['r2_highpass_apod_y']
				self.params['r2_body']=(self.params['thickness']/self.params['r2_sampling'])/self.params['cos_alpha']
			except:
				pass
			try:
				r3_lp=(self.params['r3_lowpass_diameter_x']+self.params['r3_lowpass_diameter_y'])/2
				self.params['r3_lowpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r3_lowpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r3_highpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r3_highpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r3_lowpass_apod_x'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r3_lowpass_apod_y'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r3_highpass_apod_x'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_highpass_apod_x']
			except:
				pass
			try:
				self.params['r3_highpass_apod_y'] = 2*self.params['pixelsize']*self.params['r3_sampling']/self.params['r3_highpass_apod_y']
				self.params['r3_body']=(self.params['thickness']/self.params['r3_sampling'])/self.params['cos_alpha']
			except:
				pass
			try:
				r4_lp=(self.params['r4_lowpass_diameter_x']+self.params['r4_lowpass_diameter_y'])/2
				self.params['r4_lowpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r4_lowpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r4_highpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r4_highpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r4_lowpass_apod_x'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r4_lowpass_apod_y'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r4_highpass_apod_x'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_highpass_apod_x']
			except:
				pass
			try:
				self.params['r4_highpass_apod_y'] = 2*self.params['pixelsize']*self.params['r4_sampling']/self.params['r4_highpass_apod_y']
				self.params['r4_body']=(self.params['thickness']/self.params['r4_sampling'])/self.params['cos_alpha']
			except:
				pass
			try:
				r5_lp=(self.params['r5_lowpass_diameter_x']+self.params['r5_lowpass_diameter_y'])/2
				self.params['r5_lowpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r5_lowpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r5_highpass_diameter_x'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r5_highpass_diameter_y'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r5_lowpass_apod_x'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r5_lowpass_apod_y'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r5_highpass_apod_x'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_highpass_apod_x']
			except:
				pass
			try:
				self.params['r5_highpass_apod_y'] = 2*self.params['pixelsize']*self.params['r5_sampling']/self.params['r5_highpass_apod_y']
				self.params['r5_body']=(self.params['thickness']/self.params['r5_sampling'])/self.params['cos_alpha']
			except:
				pass
		
		return r1_lp, r2_lp, r3_lp, r4_lp, r5_lp, self.params['r1_body'], self.params['r2_body'], self.params['r3_body'], self.params['r4_body'], self.params['r5_body']
	
	#=====================
	def start(self):
	
		###setup
		global rundir
		rundir=self.params['rundir']
		global cwd
		global time_start
		self.params['raw_path']=os.path.join(rundir,'raw')
		raw_path=self.params['raw_path']
		if os.path.exists(rundir):
			os.chdir(rundir)
		else:
			os.system("mkdir -p %s" % rundir)
			os.chdir(rundir)
		self.params['cachedir']=rundir+'/'+self.params['cachedir']
		self.params['protomo_outdir']=rundir+'/'+self.params['protomo_outdir']
		shutil.copy('%s/protomo2aligner.log' % cwd, "%s/protomo2aligner_%s.log" % (rundir, time_start))
		f = open("%s/protomo2aligner_%s.log" % (rundir, time_start),'a');f.write("\n")
		f.write('Start time: %s\n' % time_start)
		f.write('Description: %s\n' % self.params['description'])
		apDisplay.printMsg("Writing to log %s/protomo2aligner_%s.log" % (rundir, time_start))
		
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		seriesname='series'+seriesnumber
		tiltfilename=seriesname+'.tlt'
		tiltfilename_full=rundir+'/'+tiltfilename
		originaltilt=rundir+'/original.tlt'
		
		if (self.params['make_searchable'] == "True"):
			os.system('touch %s/.tiltseries.%04d' % (rundir, self.params['tiltseries']))  #Internal tracker for what has been batch processed through alignments
		
		###Do queries, make tlt file, CTF correct (optional), dose compensate (optional), remove highly shifted images (optional), and remove high tilt images (optional) if first run from Appion/Leginon database
		if (self.params['coarse'] == 'True' and self.params['my_tlt'] == 'False'):
			apDisplay.printMsg('Preparing raw images and initial tilt file')
			f.write('Preparing raw images and initial tilt file\n')
			tilts, accumulated_dose_list, new_ordered_imagelist, self.params['maxtilt'] = apProTomo2Prep.prepareTiltFile(self.params['sessionname'], seriesname, tiltfilename, int(self.params['tiltseries']), raw_path, self.params['frame_aligned'], link="False", coarse="True")
			
			#CTF Correction
			if (self.params['ctf_correct'] == 'True'):
				apProTomo2Prep.ctfCorrect(seriesname, rundir, self.params['projectid'], self.params['sessionname'], int(self.params['tiltseries']), tiltfilename, self.params['frame_aligned'], self.params['pixelsize'], self.params['DefocusTol'], self.params['iWidth'], self.params['amp_contrast'])
			
			#Dose Compensation
			if (self.params['dose_presets'] != 'False'):
				apProTomo2Prep.doseCompensate(seriesname, rundir, self.params['sessionname'], int(self.params['tiltseries']), self.params['frame_aligned'], raw_path, self.params['pixelsize'], self.params['dose_presets'], self.params['dose_a'], self.params['dose_b'], self.params['dose_c'])
			
			#Backup original tilt file
			shutil.copy(tiltfilename_full,originaltilt)
			#Removing highly shifted images
			bad_images, bad_kept_images=apProTomo2Aligner.removeHighlyShiftedImages(tiltfilename_full, self.params['dimx'], self.params['dimy'], self.params['shift_limit'], self.params['angle_limit'])
			if bad_images:
				apDisplay.printMsg('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.' % (bad_images, self.params['shift_limit']))
				f.write('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.\n' % (bad_images, self.params['shift_limit']))
				if bad_kept_images:
					apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, self.params['angle_limit']))
					f.write('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.\n' % (bad_kept_images, self.params['angle_limit']))
			else:
				if bad_kept_images:
					apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, self.params['angle_limit']))
					f.write('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.\n' % (bad_kept_images, self.params['angle_limit']))
				apDisplay.printMsg('No images were removed from the .tlt file due to high shifts.')
				f.write('No images were removed from the .tlt file due to high shifts.\n')
			rawimagecount, maxtilt=self.excludeImages(tiltfilename_full, f)  #Remove images from .tlt file if user requests
		elif (self.params['coarse'] == 'True' and self.params['my_tlt'] == 'True'): #if user already setup directory, raw_dir, and tlt file
			apDisplay.printMsg('Using provided tilt file instead of creating one')
			f.write('Using provided tilt file instead of creating one\n')
			rawimagecount, maxtilt=self.excludeImages(tiltfilename_full, f)  #Remove images from .tlt file if user requests
			self.params['maxtilt'] = maxtilt
			apDisplay.printMsg("Normalizing and converting raw images to float32 for Protomo...")
			apProTomo2Aligner.fixImages(raw_path)
		else: #Refinement. Just get maxtilt for param file
			rawimagecount, maxtilt=self.excludeImages(tiltfilename_full, f)  #Remove images from .tlt file if user requests
			self.params['maxtilt'] = maxtilt
		
		self.params['cos_alpha']=np.cos(self.params['maxtilt']*np.pi/180)
		
		###convert angstroms to pixels
		r1_lp, r2_lp, r3_lp, r4_lp, r5_lp, self.params['r1_body'], self.params['r2_body'], self.params['r3_body'], self.params['r4_body'], self.params['r5_body'] = self.angstromsToProtomo(coarse=self.params['coarse'])
		
		###create param file
		param_out=seriesname+'.param'
		param_out_full=rundir+'/'+param_out
		iters = self.params['iters']
		
		coarse_param_in, param_in=apProTomo2Prep.getPrototypeParamPath()
		paramdict = apProTomo2Prep.createParamDict(self.params)
		apProTomo2Prep.modifyParamFile(param_in, param_out_full, paramdict)
		seriesparam=protomo.param(param_out_full)
		if self.params['coarse'] == 'True':
			os.system("mkdir %s/coarse_out" % rundir)
			coarse_param_out='coarse_'+seriesname+'.param'
			coarse_param_out_full=rundir+'/'+coarse_param_out
			apProTomo2Prep.modifyParamFile(coarse_param_in, coarse_param_out_full, paramdict)
			coarse_seriesparam=protomo.param(coarse_param_out_full)

		apDisplay.printMsg('Starting Protomo alignment')
		f.write('Starting Protomo alignment\n')
		
		#create series object and use presence of i3t to determine if protomo has been run once already
		
		if self.params['coarse'] == 'True':
			jobs1=[]
			if self.params['create_tilt_video'] == "true":
				apDisplay.printMsg("Creating initial tilt-series video in the background...")
				f.write('Creating initial tilt-series video in the background...\n')
				jobs1.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, 0, tiltfilename_full, rawimagecount, rundir, raw_path, self.params['pixelsize'], self.params['map_sampling'], self.params['image_file_type'], self.params['video_type'], self.params['tilt_clip'], self.params['parallel'], "Initial",)))
				for job in jobs1:
					job.start()
				if self.params['parallel'] != "True":
					[p.join() for p in mp.active_children()]
			else:
				apDisplay.printMsg("Skipping initial tilt-series depiction\n")
				f.write('Skipping initial tilt-series depiction\n')
			
			coarse_i3tfile=rundir+'/'+'coarse_'+seriesname+'.i3t'
			if os.path.exists(coarse_i3tfile):
				series=protomo.series(coarse_seriesparam)
			else:
				coarse_seriesgeom=protomo.geom(tiltfilename_full)
				series=protomo.series(coarse_seriesparam,coarse_seriesgeom)
		else:
			i3tfile=rundir+'/'+seriesname+'.i3t'
			if os.path.exists(i3tfile):
				series=protomo.series(seriesparam)
			else:
				seriesgeom=protomo.geom(tiltfilename_full)
				series=protomo.series(seriesparam,seriesgeom)

		if self.params['coarse'] == 'True':
			name='coarse_'+seriesname
			
			#Align and restart alignment if failed
			retry=0
			brk=None
			end=0
			new_region_x=int(self.params['region_x']/self.params['sampling'])   #Just initializing
			new_region_y=int(self.params['region_y']/self.params['sampling'])   #Just initializing
			while (min(new_region_x,new_region_y) != 20 and end == 0):
				try:
					if (brk != None):
						apDisplay.printMsg("Keyboard Interrupt!")
						break
					if (retry > 0):
						new_region_x = apProTomo2Aligner.nextLargestSize(new_region_x)
						new_region_y = apProTomo2Aligner.nextLargestSize(new_region_y)
						apDisplay.printMsg("Coarse Alignment failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)..." % (retry, new_region_x, new_region_y, self.params['sampling']))
						f.write('Coarse Alignment failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)...\n' % (retry, new_region_x, new_region_y, self.params['sampling']))
						time.sleep(1)  #Allows Ctrl-C to be caught by except
						newsize = "{ %s %s }" % (new_region_x, new_region_y)
						series.setparam("window.size", newsize)
					retry+=1
					series.align()
					final_retry=retry-1
					end=1
				except KeyboardInterrupt:  #Only caught if not in series.align()
					brk=sys.exc_info()
				except:
					if (min(new_region_x,new_region_y) == 20):
						apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed after rescaling the search area %s time(s)." % (self.params['tiltseries'], retry-1))
						apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*self.params['sampling']))
						apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*self.params['sampling']))
						apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n")
						f.write('Coarse Alignment for Tilt-Series #%s failed after rescaling the search area %s time(s).\n' % (self.params['tiltseries'], retry-1))
						f.write('Window Size (x) was windowed down to %s\n' % (new_region_x*self.params['sampling']))
						f.write('Window Size (y) was windowed down to %s\n' % (new_region_y*self.params['sampling']))
						f.write('Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n')
						brk=1
					pass
			
			if (brk != None):   #resampling failed, break out of all refinement iterations
				#Finish background process
				for job in jobs1:
					job.join()
				return None
			
			corrfile=name+'.corr'
			series.corr(corrfile)
			
			#archive results
			tiltfile=name+'.tlt'
			series.geom(1).write(tiltfile)
			if self.params['parallel'] != "True":
				apDisplay.printMsg("Creating Depiction Videos...")
				f.write('Creating Depiction Videos...\n')
			else:
				apDisplay.printMsg("Creating Depiction Videos in Parallel...")
				f.write('Creating Depiction Videos in Parallel...\n')
			
			# For multiprocessing
			jobs2=[]
			
			# Make correlation peak videos for depiction
			self.params['corr_peak_gif']='media/correlations/'+seriesname+'00_cor.gif';self.params['corr_peak_ogv']='media/correlations/'+seriesname+'00_cor.ogv';self.params['corr_peak_mp4']='media/correlations/'+seriesname+'00_cor.mp4';self.params['corr_peak_webm']='media/correlations/'+seriesname+'00_cor.webm'
			jobs2.append(mp.Process(target=apProTomo2Aligner.makeCorrPeakVideos, args=(name, 0, rundir, self.params['protomo_outdir'], self.params['video_type'], "Coarse",)))
			if self.params['parallel'] != "True":
				[p.join() for p in mp.active_children()]
			# Make tiltseries video for depiction
			if self.params['create_tilt_video'] == "true":
				apDisplay.printMsg("Creating Coarse Alignment tilt-series video...")
				f.write('Creating Coarse Alignment tilt-series video...\n')
				self.params['tiltseries_gif']='media/tiltseries/'+'coarse_'+seriesname+'.gif';self.params['tiltseries_ogv']='media/tiltseries/'+'coarse_'+seriesname+'.gif';self.params['tiltseries_mp4']='media/tiltseries/'+'coarse_'+seriesname+'.mp4';self.params['tiltseries_webm']='media/tiltseries/'+'coarse_'+seriesname+'.webm';
				jobs2.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, 0, tiltfile, rawimagecount, rundir, raw_path, self.params['pixelsize'], self.params['map_sampling'], self.params['image_file_type'], self.params['video_type'], self.params['tilt_clip'], self.params['parallel'], "Coarse",)))
				if self.params['parallel'] != "True":
					[p.join() for p in mp.active_children()]
			else:
				apDisplay.printMsg("Skipping tilt-series depiction\n")
				f.write('Skipping tilt-series depiction\n')
				
			# Send off processes in the background
			for job in jobs2:
				job.start()
			
			# Generate intermediate reconstructions and videos for depiction
			if self.params['create_reconstruction'] == "true":			
				# Create intermediate reconstruction
				apDisplay.printMsg("Generating Coarse Alignment reconstruction...")
				f.write('Generating Coarse Alignment reconstruction...\n')
				series.mapfile()
				rx='region_x'
				ry='region_y'
				lp=round(r1_lp, 1)
				thickness=int(round(self.params['pixelsize']*self.params['thickness']))
				self.params['recon_gif']='media/reconstructions/'+seriesname+'.gif';self.params['recon_ogv']='media/reconstructions/'+seriesname+'.ogv';self.params['recon_mp4']='media/reconstructions/'+seriesname+'.mp4';self.params['recon_webm']='media/reconstructions/'+seriesname+'.webm';
				apProTomo2Aligner.makeReconstructionVideos(name, 0, rundir, self.params[rx], self.params[ry], self.params['show_window_size'], self.params['protomo_outdir'], self.params['pixelsize'], self.params['sampling'], self.params['map_sampling'], lp, thickness, self.params['video_type'], self.params['keep_recons'], self.params['parallel'], align_step="Coarse")
			else:
				apDisplay.printMsg("Skipping reconstruction depiction\n")
				f.write('Skipping reconstruction depiction\n')
			
			# Join processes
			for job in jobs1:
				job.join()
			for job in jobs2:
				job.join()
			
			cleanup="cp coarse*.* coarse_out; rm %s.corr; mv %s.tlt coarse_out/initial_%s.tlt; cp %s.tlt %s.tlt" % (name, seriesname, seriesname, name, seriesname)
			os.system(cleanup)
			
			if final_retry > 0:
				if bad_images:
					apDisplay.printMsg('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.' % (bad_images, self.params['shift_limit']))
					f.write('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.\n' % (bad_images, self.params['shift_limit']))
				else:
					apDisplay.printMsg('No images were removed from the .tlt file due to high shifts.')
					f.write('No images were removed from the .tlt file due to high shifts.\n')
				apDisplay.printMsg("Coarse Alignment finished after retrying %s time(s) due to the sampled search area being too small." % (final_retry))
				apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*self.params['sampling']))
				apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*self.params['sampling']))
				apDisplay.printMsg("Put these values into the corresponding parameter boxes on the Protomo Refinement Appion webpage.\n")
				f.write('Coarse Alignment finished after retrying %s time(s) due to the sampled search area being too small.\n' % (final_retry))
				f.write('Window Size (x) was windowed down to %s\n' % (new_region_x*self.params['sampling']))
				f.write('Window Size (y) was windowed down to %s\n' % (new_region_y*self.params['sampling']))
				f.write('Put these values into the corresponding parameter boxes on the Protomo Refinement Appion webpage.\n')
			
			#Insert iteration information into the database
			if self.params['commit'] == "True":
				self.insertIterationIntoDatabase(r=0)
			
			apDisplay.printMsg("Finished Coarse Alignment for Tilt-Series #%s!\n" % self.params['tiltseries'])
			f.write('Finished Coarse Alignment for Tilt-Series #%s!\n' % self.params['tiltseries'])

		else: # Normal refinement with area matching
			name=seriesname
			start=0  #Counter for prevous iterations

			#figure out starting number
			previters=glob.glob(name+'*.corr')
			if len(previters) > 0:
				previters.sort()
				lastiter=previters[-1]
				start=int(lastiter.split(name)[1].split('.')[0])+1
			
			#rewind to previous iteration if requested
			if (self.params['restart_cycle'] > 0):
				apDisplay.printMsg("Rewinding to iteration %s" % (self.params['restart_cycle']))
				f.write('Rewinding to iteration %s\n' % (self.params['restart_cycle']))
				start=self.params['restart_cycle']-1
				series.setcycle(start)
				
				#Remove all files after this iteration
				apProTomo2Aligner.removeForRestart(self.params['restart_cycle'], name, rundir)
			
			
			iters=start+self.params['r1_iters']+self.params['r2_iters']+self.params['r3_iters']+self.params['r4_iters']+self.params['r5_iters']
			round1={"window.size":"{ %s %s }" % (int(self.params['r1_region_x']/self.params['r1_sampling']),int(self.params['r1_region_y']/self.params['r1_sampling'])),"window.lowpass.diameter":"{ %s %s }" % (self.params['r1_lowpass_diameter_x'],self.params['r1_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r1_lowpass_diameter_x'],self.params['r1_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r1_lowpass_apod_x'],self.params['r1_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r1_highpass_apod_x'],self.params['r1_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r1_highpass_diameter_x'],self.params['r1_highpass_diameter_y']),"sampling":"%s" % (self.params['r1_sampling']),"map.sampling":"%s" % (self.params['r1_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r1_kernel_x'],self.params['r1_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r1_peak_search_radius_x'],self.params['r1_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r1_mask_width_x'],self.params['r1_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r1_mask_width_x'],self.params['r1_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r1_mask_apod_x'],self.params['r1_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r1_mask_apod_x'],self.params['r1_mask_apod_y']),"reference.body":"%s" % (self.params['r1_body']),"map.body":"%s" % (self.params['r1_body']),"align.correlation.mode":"%s" % (self.params['r1_corr_mode'])}
			round2={"window.size":"{ %s %s }" % (int(self.params['r2_region_x']/self.params['r2_sampling']),int(self.params['r2_region_y']/self.params['r2_sampling'])),"window.lowpass.diameter":"{ %s %s }" % (self.params['r2_lowpass_diameter_x'],self.params['r2_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r2_lowpass_diameter_x'],self.params['r2_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r2_lowpass_apod_x'],self.params['r2_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r2_highpass_apod_x'],self.params['r2_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r2_highpass_diameter_x'],self.params['r2_highpass_diameter_y']),"sampling":"%s" % (self.params['r2_sampling']),"map.sampling":"%s" % (self.params['r2_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r2_kernel_x'],self.params['r2_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r2_peak_search_radius_x'],self.params['r2_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r2_mask_width_x'],self.params['r2_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r2_mask_width_x'],self.params['r2_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r2_mask_apod_x'],self.params['r2_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r2_mask_apod_x'],self.params['r2_mask_apod_y']),"reference.body":"%s" % (self.params['r2_body']),"map.body":"%s" % (self.params['r2_body']),"align.correlation.mode":"%s" % (self.params['r2_corr_mode'])}
			round3={"window.size":"{ %s %s }" % (int(self.params['r3_region_x']/self.params['r3_sampling']),int(self.params['r3_region_y']/self.params['r3_sampling'])),"window.lowpass.diameter":"{ %s %s }" % (self.params['r3_lowpass_diameter_x'],self.params['r3_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r3_lowpass_diameter_x'],self.params['r3_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r3_lowpass_apod_x'],self.params['r3_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r3_highpass_apod_x'],self.params['r3_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r3_highpass_diameter_x'],self.params['r3_highpass_diameter_y']),"sampling":"%s" % (self.params['r3_sampling']),"map.sampling":"%s" % (self.params['r3_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r3_kernel_x'],self.params['r3_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r3_peak_search_radius_x'],self.params['r3_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r3_mask_width_x'],self.params['r3_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r3_mask_width_x'],self.params['r3_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r3_mask_apod_x'],self.params['r3_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r3_mask_apod_x'],self.params['r3_mask_apod_y']),"reference.body":"%s" % (self.params['r3_body']),"map.body":"%s" % (self.params['r3_body']),"align.correlation.mode":"%s" % (self.params['r3_corr_mode'])}
			round4={"window.size":"{ %s %s }" % (int(self.params['r4_region_x']/self.params['r4_sampling']),int(self.params['r4_region_y']/self.params['r4_sampling'])),"window.lowpass.diameter":"{ %s %s }" % (self.params['r4_lowpass_diameter_x'],self.params['r4_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r4_lowpass_diameter_x'],self.params['r4_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r4_lowpass_apod_x'],self.params['r4_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r4_highpass_apod_x'],self.params['r4_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r4_highpass_diameter_x'],self.params['r4_highpass_diameter_y']),"sampling":"%s" % (self.params['r4_sampling']),"map.sampling":"%s" % (self.params['r4_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r4_kernel_x'],self.params['r4_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r4_peak_search_radius_x'],self.params['r4_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r4_mask_width_x'],self.params['r4_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r4_mask_width_x'],self.params['r4_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r4_mask_apod_x'],self.params['r4_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r4_mask_apod_x'],self.params['r4_mask_apod_y']),"reference.body":"%s" % (self.params['r4_body']),"map.body":"%s" % (self.params['r4_body']),"align.correlation.mode":"%s" % (self.params['r4_corr_mode'])}
			round5={"window.size":"{ %s %s }" % (int(self.params['r5_region_x']/self.params['r5_sampling']),int(self.params['r5_region_y']/self.params['r5_sampling'])),"window.lowpass.diameter":"{ %s %s }" % (self.params['r5_lowpass_diameter_x'],self.params['r5_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r5_lowpass_diameter_x'],self.params['r5_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r5_lowpass_apod_x'],self.params['r5_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r5_highpass_apod_x'],self.params['r5_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r5_highpass_diameter_x'],self.params['r5_highpass_diameter_y']),"sampling":"%s" % (self.params['r5_sampling']),"map.sampling":"%s" % (self.params['r5_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r5_kernel_x'],self.params['r5_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r5_peak_search_radius_x'],self.params['r5_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r5_mask_width_x'],self.params['r5_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r5_mask_width_x'],self.params['r5_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r5_mask_apod_x'],self.params['r5_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r5_mask_apod_x'],self.params['r5_mask_apod_y']),"reference.body":"%s" % (self.params['r5_body']),"map.body":"%s" % (self.params['r5_body']),"align.correlation.mode":"%s" % (self.params['r5_corr_mode'])}
			switches={"preprocess.mask.gradient":{"%s" % (self.params['gradient']):self.params['gradient_switch']},"preprocess.mask.iter":{"%s" % (self.params['iter_gradient']):self.params['iter_gradient_switch']},"fit.orientation":{"%s" % (self.params['orientation']):self.params['orientation_switch']},"fit.azimuth":{"%s" % (self.params['azimuth']):self.params['azimuth_switch']},"fit.elevation":{"%s" % (self.params['elevation']):self.params['elevation_switch']},"fit.rotation":{"%s" % (self.params['rotation']):self.params['rotation_switch']},"fit.scale":{"%s" % (self.params['scale']):self.params['scale_switch']}}
			
			apDisplay.printMsg("Beginning Refinements\n")
			f.write('\nBeginning Refinements\n')
			
			for n in range(start,start+iters):
				#change parameters depending on rounds
				self.params['cycle'] = n+1  #Iterations in Protomo start at 0
				if (n+1 == start+1):
					r=1  #Round number
					apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
					f.write('\nBeginning Refinement Iteration #%s, Round #%s\n' % (n+1,r))
					apDisplay.printMsg("lowpass = %s Angstroms\n" % r1_lp)
					f.write("lowpass = %s Angstroms\n" % r1_lp)
					region_x=self.params['r1_region_x']
					region_y=self.params['r1_region_y']
					sampling=self.params['r1_sampling']
					f.write("\nRound #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					for val in round1:
						f.write("%s = %s\n" % (val,round1[val]))
						apDisplay.printMsg("%s = %s" % (val,round1[val]))
						series.setparam(val,round1[val])
				elif (n+1 == start+self.params['r1_iters']+1):
					r=2
					apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
					f.write('\nBeginning Refinement Iteration #%s, Round #%s\n' % (n+1,r))
					apDisplay.printMsg("lowpass = %s angstroms\n" % r2_lp)
					f.write("lowpass = %s angstroms\n" % r2_lp)
					region_x=self.params['r2_region_x']
					region_y=self.params['r2_region_y']
					sampling=self.params['r2_sampling']
					f.write("\nRound #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					for val in round2:
						f.write("%s = %s\n" % (val,round2[val]))
						apDisplay.printMsg("%s = %s" % (val,round2[val]))
						series.setparam(val,round2[val])
				elif (n+1 == start+self.params['r1_iters']+self.params['r2_iters']+1):
					r=3
					apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
					f.write('\nBeginning Refinement Iteration #%s, Round #%s\n' % (n+1,r))
					apDisplay.printMsg("lowpass = %s angstroms\n" % r3_lp)
					f.write("lowpass = %s angstroms\n" % r3_lp)
					region_x=self.params['r3_region_x']
					region_y=self.params['r3_region_y']
					sampling=self.params['r3_sampling']
					f.write("\nRound #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					for val in round3:
						f.write("%s = %s\n" % (val,round3[val]))
						apDisplay.printMsg("%s = %s" % (val,round3[val]))
						series.setparam(val,round3[val])
				elif (n+1 == start+self.params['r1_iters']+self.params['r2_iters']+self.params['r3_iters']+1):
					r=4
					apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
					f.write('\nBeginning Refinement Iteration #%s, Round #%s\n' % (n+1,r))
					apDisplay.printMsg("lowpass = %s angstroms\n" % r4_lp)
					f.write("lowpass = %s angstroms\n" % r4_lp)
					region_x=self.params['r4_region_x']
					region_y=self.params['r4_region_y']
					sampling=self.params['r4_sampling']
					f.write("\nRound #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					for val in round4:
						f.write("%s = %s\n" % (val,round4[val]))
						apDisplay.printMsg("%s = %s" % (val,round4[val]))
						series.setparam(val,round4[val])
				elif (n+1 == start+self.params['r1_iters']+self.params['r2_iters']+self.params['r3_iters']+self.params['r4_iters']+1):
					r=5
					apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
					f.write('\nBeginning Refinement Iteration #%s, Round #%s\n' % (n+1,r))
					apDisplay.printMsg("lowpass = %s angstroms\n" % r5_lp)
					f.write("lowpass = %s angstroms\n" % r5_lp)
					region_x=self.params['r5_region_x']
					region_y=self.params['r5_region_y']
					sampling=self.params['r5_sampling']
					f.write("\nRound #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*self.params['pixelsize'], 2*sampling*self.params['pixelsize']))
					for val in round5:
						f.write("%s = %s\n" % (val,round5[val]))
						apDisplay.printMsg("%s = %s" % (val,round5[val]))
						series.setparam(val,round5[val])
				else:
					f.write("\nNo Round parameters changed for Iteration #%s\n" % (n+1))
					apDisplay.printMsg("No Round parameters changed for Iteration #%s\n" % (n+1))
					apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
					f.write('\nBeginning Refinement Iteration #%s, Round #%s\n' % (n+1,r))
				
				#change parameters depending on switches
				toggle=0
				for switch in switches:
					for key in switches[switch]:
						if (switches[switch][key] == n+1-start):
							toggle=1
							if (key == "true"):
								newval="false"
								f.write("%s switched from true to false on Iteration #%s" % (switch, n+1))
								apDisplay.printMsg("%s switched from true to false on Iteration #%s" % (switch, n+1))
							else:
								newval="true"
								f.write("%s switched from false to true on Iteration #%s" % (switch, n+1))
								apDisplay.printMsg("%s switched from false to true on Iteration #%s" % (switch, n+1))
							series.setparam(switch,newval)
				if toggle == 0:
					f.write("No parameters were switched for Iteration #%s\n" % (n+1))
					apDisplay.printMsg("No parameters were switched for Iteration #%s\n" % (n+1))
				
				#Align and restart alignment if failed
				retry=0
				brk=None
				end=0
				new_region_x=int(region_x/sampling)   #Just initializing
				new_region_y=int(region_y/sampling)   #Just initializing
				while (min(new_region_x,new_region_y) != 20 and end == 0):
					try:
						if (brk != None):
							apDisplay.printMsg("Keyboard Interrupt!")
							break
						if (retry > 0):
							new_region_x = apProTomo2Aligner.nextLargestSize(new_region_x)
							new_region_y = apProTomo2Aligner.nextLargestSize(new_region_y)
							apDisplay.printMsg("Refinement failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)..." % (retry, new_region_x*sampling, new_region_y*sampling, sampling))
							f.write('Refinement failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)...\n' % (retry, new_region_x*sampling, new_region_y*sampling, sampling))
							time.sleep(1)  #Allows Ctrl-C to be caught by except
							newsize = "{ %s %s }" % (new_region_x, new_region_y)
							series.setparam("window.size", newsize)
						retry+=1
						series.align()
						final_retry=retry-1
						end=1
					except KeyboardInterrupt:  #Only caught if not in series.align()
						brk=sys.exc_info()
					except:
						if (min(new_region_x,new_region_y) == 20):
							apDisplay.printMsg("Refinement Iteration #%s for Tilt-Series #%s failed after resampling the search area %s time(s)." % (n+1, self.params['tiltseries'], retry-1))
							apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
							apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
							apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
							f.write('Refinement Iteration #%s for Tilt-Series #%s failed after resampling the search area %s time(s).\n' % (n+1, self.params['tiltseries'], retry-1))
							f.write('Window Size (x) was windowed down to %s\n' % (new_region_x*sampling))
							f.write('Window Size (y) was windowed down to %s\n' % (new_region_y*sampling))
							f.write('Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n')
							brk=1
						pass

				if (brk != None):   #resampling failed, break out of all refinement iterations
					break
				
				it="%03d" % (n)
				itt="%02d" % (n+1)
				ittt="%02d" % (n)
				#ite="_ite%02d" % (n+start)
				basename='%s%s' % (name,it)
				corrfile=basename+'.corr'
				series.corr(corrfile)
				series.fit()
				series.update()

				#archive results
				tiltfile=basename+'.tlt'
				series.geom(0).write(tiltfile)
				
				#Produce quality assessment statistics and plot image using corrfile information
				apDisplay.printMsg("Creating quality assessment statistics...")
				f.write('Creating quality assessment statistics...\n')
				numcorrfiles=len(glob.glob1(rundir,'*.corr'))
				for i in range(numcorrfiles):
					it="%03d" % (i)
					basename='%s%s' % (name,it)
					corrfile=basename+'.corr'
					try:  #Sometimes Protomo fails to write a corr file correctly...I don't understand this
						CCMS_shift, CCMS_rots, CCMS_scale, CCMS_sum = apProTomo2Aligner.makeQualityAssessment(name, i, rundir, corrfile)
					except NoneType:
						apDisplay.printMsg("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.")
					if i == numcorrfiles-1:
						self.params['qa_gif']='media/quality_assessment/'+seriesname+'_quality_assessment.gif'
						apProTomo2Aligner.makeQualityAssessmentImage(self.params['tiltseries'], self.params['sessionname'], name, rundir, start+self.params['r1_iters'], self.params['r1_sampling'], r1_lp, start+self.params['r2_iters'], self.params['r2_sampling'], r2_lp, start+self.params['r3_iters'], self.params['r3_sampling'], r3_lp, start+self.params['r4_iters'], self.params['r4_sampling'], r4_lp, start+self.params['r5_iters'], self.params['r5_sampling'], r5_lp)
				it="%03d" % (n)
				basename='%s%s' % (name,it)
				corrfile=basename+'.corr'
				
				apDisplay.printMsg("\033[43mCCMS(shift) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_shift,5), n+1, self.params['tiltseries']))
				f.write('CCMS(shift) = %s for Iteration #%s of Tilt-Series #%s.\n' % (round(CCMS_shift,5), n+1, self.params['tiltseries']))
				
				apDisplay.printMsg("\033[46mCCMS(rotations) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_rots,5), n+1, self.params['tiltseries']))
				f.write('CCMS(rotations) = %s for Iteration #%s of Tilt-Series #%s.\n' % (round(CCMS_rots,5), n+1, self.params['tiltseries']))
				
				apDisplay.printMsg("\033[43mCCMS(scale) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_scale,5), n+1, self.params['tiltseries']))
				f.write('CCMS(scale) = %s for Iteration #%s of Tilt-Series #%s.\n' % (round(CCMS_scale,5), n+1, self.params['tiltseries']))
				
				apDisplay.printMsg("\033[1mThe scaled sum of CCMS values is %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_sum,5), n+1, self.params['tiltseries']))
				f.write('The scaled sum of CCMS values is #%s for Tilt-Series #%s.\n' % (round(CCMS_sum,5), self.params['tiltseries']))
				
				if self.params['parallel'] != "True":
					apDisplay.printMsg("Creating Depiction Videos for Iteration #%s..." % (n+1))
					f.write('Creating Depiction Videos for Iteration #%s...\n' % (n+1))
				else:
					apDisplay.printMsg("Creating Depiction Videos for Iteration #%s in Parallel..." % (n+1))
					f.write('Creating Depiction Videos for Iteration #%s in Parallel...\n' % (n+1))
					
				# For multiprocessing
				jobs=[]
				
				# Make correlation peak videos for depiction
				self.params['corr_peak_gif']='media/correlations/'+seriesname+ittt+'_cor.gif';self.params['corr_peak_ogv']='media/correlations/'+seriesname+ittt+'_cor.ogv';self.params['corr_peak_mp4']='media/correlations/'+seriesname+ittt+'_cor.mp4';self.params['corr_peak_webm']='media/correlations/'+seriesname+ittt+'_cor.webm'
				jobs.append(mp.Process(target=apProTomo2Aligner.makeCorrPeakVideos, args=(name, it, rundir, self.params['protomo_outdir'], self.params['video_type'], "Refinement")))
				if self.params['parallel'] != "True":
					[p.start() for job in jobs]
					[p.join() for p in mp.active_children()]
					jobs=[]
				
				# Make correction factor plot pngs for depiction
				self.params['corr_plot_coa_gif']='media/corrplots/'+seriesname+ittt+'_coa.gif';self.params['corr_plot_cofx_gif']='media/corrplots/'+seriesname+ittt+'_cofx.gif';self.params['corr_plot_cofy_gif']='media/corrplots/'+seriesname+ittt+'_cofy.gif';self.params['corr_plot_rot_gif']='media/corrplots/'+seriesname+ittt+'_rot.gif';self.params['corr_plot_scl_gif']='media/corrplots/'+seriesname+ittt+'_scl.gif';
				jobs.append(mp.Process(target=apProTomo2Aligner.makeCorrPlotImages, args=(name, it, rundir, corrfile)))
				if self.params['parallel'] != "True":
					[p.start() for job in jobs]
					[p.join() for p in mp.active_children()]
					jobs=[]
				
				# Make refinement plots of tilt azimuth and theta
				self.params['azimuth_gif']='media/angle_refinement/'+seriesname+'_azimuth.gif';self.params['theta_gif']='media/angle_refinement/'+seriesname+'_theta.gif';
				jobs.append(mp.Process(target=apProTomo2Aligner.makeAngleRefinementPlots, args=(rundir, name,)))
				if self.params['parallel'] != "True":
					[p.start() for job in jobs]
					[p.join() for p in mp.active_children()]
					jobs=[]
				
				# Make tiltseries video for depiction
				if self.params['create_tilt_video'] == "true":
					apDisplay.printMsg("Creating Refinement tilt-series video for iteration #%s..." % (n+1))
					f.write('Creating Refinement tilt-series video for iteration #%s...\n' % (n+1))
					self.params['tiltseries_gif']='media/tiltseries/'+seriesname+ittt+'.gif';self.params['tiltseries_ogv']='media/tiltseries/'+seriesname+ittt+'.gif';self.params['tiltseries_mp4']='media/tiltseries/'+seriesname+ittt+'.mp4';self.params['tiltseries_webm']='media/tiltseries/'+seriesname+ittt+'.webm';
					jobs.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, it, tiltfile, rawimagecount, rundir, raw_path, self.params['pixelsize'], self.params['map_sampling'], self.params['image_file_type'], self.params['video_type'], self.params['tilt_clip'], self.params['parallel'], "Refinement",)))
					if self.params['parallel'] != "True":
						[p.start() for job in jobs]
						[p.join() for p in mp.active_children()]
						jobs=[]
				else:
					apDisplay.printMsg("Skipping tilt-series depiction\n")
					f.write('Skipping tilt-series depiction\n')
				
				# Send off processes in the background
				if self.params['parallel'] == "True":
					for job in jobs:
						job.start()
				
				# Generate intermediate reconstructions and videos for depiction
				if self.params['create_reconstruction'] == "true":
					# Create intermediate reconstruction
					apDisplay.printMsg("Generating Refinement reconstruction for iteration #%s..." % (n+1))
					f.write('Generating Refinement reconstruction for iteration #%s...\n' % (n+1))
					#Rescale if necessary
					s='r%s_sampling' % r
					lpx='r%s_lowpass_diameter_x' % r
					lpy='r%s_lowpass_diameter_y' % r
					if self.params['map_sampling'] != self.params[s]:
						new_map_sampling='%s' % self.params['map_sampling']
						series.setparam("sampling",new_map_sampling)
						series.setparam("map.sampling",new_map_sampling)
						
						#Rescale the lowpass and body for depiction
						b='r%s_body' % r
						new_lp_x = self.params[lpx]*self.params['map_sampling']/self.params[s]
						new_lp_y = self.params[lpy]*self.params['map_sampling']/self.params[s]
						new_body = self.params[b]*self.params[s]/self.params['map_sampling']
						series.setparam("map.lowpass.diameter", "{ %s %s }" % (new_lp_x, new_lp_y))
						series.setparam("map.body", "%s" % (new_body))
						
						series.mapfile()
						
						#Reset sampling values for next iteration
						series.setparam("sampling",'%s' % self.params[s])
						series.setparam("map.sampling",'%s' % self.params[s])
					else:
						series.mapfile()
					
					rx='r%s_region_x' % r
					ry='r%s_region_y' % r
					lp=round(2*self.params['pixelsize']*self.params[s]/((self.params[lpx]+self.params[lpy])/2), 1)
					thickness=int(round(self.params['pixelsize']*self.params['thickness']))
					self.params['recon_gif']='media/reconstructions/'+seriesname+itt+'.gif';self.params['recon_ogv']='media/reconstructions/'+seriesname+itt+'.ogv';self.params['recon_mp4']='media/reconstructions/'+seriesname+itt+'.mp4';self.params['recon_webm']='media/reconstructions/'+seriesname+itt+'.webm';
					apProTomo2Aligner.makeReconstructionVideos(name, itt, rundir, self.params[rx], self.params[ry], self.params['show_window_size'], self.params['protomo_outdir'], self.params['pixelsize'], sampling, self.params['map_sampling'], lp, thickness, self.params['video_type'], self.params['keep_recons'], self.params['parallel'], align_step="Refinement")
					
				else:
					apDisplay.printMsg("Skipping reconstruction depiction\n")
					f.write('Skipping reconstruction depiction\n')
				
				# Join processes
				for job in jobs:
					job.join()
				
				if final_retry > 0:
					apDisplay.printMsg("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small." % (n+1, final_retry))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					f.write('Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small.\n' % (n+1, final_retry))
					f.write('Window Size (x) was windowed down to %s\n' % (new_region_x*sampling))
					f.write('Window Size (y) was windowed down to %s\n' % (new_region_y*sampling))
				
				if n == range(iters)[-1]:
					apDisplay.printMsg("Finished Refinement for Tilt-Series #%s!\n" % self.params['tiltseries'])
					f.write('Finished Refinement for Tilt-Series #%s!\n' % self.params['tiltseries'])
			
			#Insert iteration information into the database
			#if self.params['commit']=="True":
			#	self.getModelAngles(tiltfile)
			#	self.param['seriesname'] = name
			#	self.insertIterationIntoDatabase(r)
		
		time_end = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")
		apDisplay.printMsg('Did everything blow up and now you\'re yelling at your computer screen?')
		apDisplay.printMsg('If so, kindly email Alex at ajn10d@fsu.edu and include this log file.')
		apDisplay.printMsg('If everything worked beautifully and you publish it, please use the appropriate citations listed on the Appion webpage!')
		f.write('Did everything blow up and now you\'re yelling at your computer screen?\n')
		f.write('If so, kindly email Alex at ajn10d@fsu.edu and include this log file\n.')
		f.write('If everything worked beautifully and you publish it, please use the appropriate citations listed on the Appion webpage!\n')
		print "\n"
		apDisplay.printMsg("Closing log file %s/protomo2aligner_%s.log\n" % (rundir, time_start))
		f.write("\nEnd time: %s" % time_end)
		f.close()
		
#=====================
#=====================
if __name__ == '__main__':
	protomo2aligner = ProTomo2Aligner()
	protomo2aligner.start()
	protomo2aligner.close()
