#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for the initial coarse alignment and subsequent iterative alignments
# to be performed serially.

from __future__ import division
import os
import sys
import math
import glob
import subprocess
import numpy as np
import multiprocessing as mp
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apProTomo2Aligner
from appionlib import apProTomo2Prep
from appionlib import apTomo
from appionlib import apProTomo
from appionlib import apParam

try:
	import protomo
except:
	print "protomo did not get imported"

# Required for cleanup at end
cwd=os.getcwd()
rundir=''

#=====================
class ProTomo2Aligner(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --sessionname=<sessionname> [options]"
			+"\nFor initial coarse alignment: %prog --tiltseriesnumber=<#> --sessionname=<sessionname> --coarse=True [options]")
		
		self.parser.add_option("--sessionname", dest="sessionname", help="Session date, e.g. --sessionname=14aug02a")
		
		self.parser.add_option("--tiltseries", dest="tiltseries", help="Name of Protomo series, e.g. --tiltseries=31")
		
		self.parser.add_option("--runname", dest="runname", help="Name of protmorun directory as made by Appion")
		
		self.parser.add_option("--jobtype", dest="jobtype", help="Appion jobtype")
		
		self.parser.add_option("--projectid", dest="projectid", help="Appion project ID")
		
		self.parser.add_option("--expid", dest="expid", help="Appion experiment ID")
		
		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")
		
		self.parser.add_option('--maxtilt', dest='maxtilt', type='int', metavar='int', help='Highest image tilt in degrees, e.g. --maxtilt=65') 
		
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
		
		self.parser.add_option("--lowpass_diameter_y", dest="lowpass_diameter_y",  default=0.5, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_diameter_y", dest="r1_lowpass_diameter_y",  default=0.5, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_diameter_y", dest="r2_lowpass_diameter_y",  default=0.5, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_diameter_y", dest="r3_lowpass_diameter_y",  default=0.5, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_diameter_y", dest="r4_lowpass_diameter_y",  default=0.5, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_apod_x", dest="lowpass_apod_x", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_apod_x", dest="r1_lowpass_apod_x", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_apod_x", dest="r2_lowpass_apod_x", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_apod_x", dest="r3_lowpass_apod_x", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_apod_x", dest="r4_lowpass_apod_x", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_apod_y", dest="lowpass_apod_y", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r1_lowpass_apod_y", dest="r1_lowpass_apod_y", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r2_lowpass_apod_y", dest="r2_lowpass_apod_y", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r3_lowpass_apod_y", dest="r3_lowpass_apod_y", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r3_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--r4_lowpass_apod_y", dest="r4_lowpass_apod_y", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--highpass_diameter_x", dest="highpass_diameter_x", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r1_highpass_diameter_x", dest="r1_highpass_diameter_x", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r2_highpass_diameter_x", dest="r2_highpass_diameter_x", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r3_highpass_diameter_x", dest="r3_highpass_diameter_x", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r3_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r4_highpass_diameter_x", dest="r4_highpass_diameter_x", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_diameter_y", dest="highpass_diameter_y", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r1_highpass_diameter_y", dest="r1_highpass_diameter_y", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r2_highpass_diameter_y", dest="r2_highpass_diameter_y", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r3_highpass_diameter_y", dest="r3_highpass_diameter_y", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r3_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r4_highpass_diameter_y", dest="r4_highpass_diameter_y", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--highpass_apod_x", dest="highpass_apod_x", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r1_highpass_apod_x", dest="r1_highpass_apod_x", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r2_highpass_apod_x", dest="r2_highpass_apod_x", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r3_highpass_apod_x", dest="r3_highpass_apod_x", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r3_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--r4_highpass_apod_x", dest="r4_highpass_apod_x", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_apod_y", dest="highpass_apod_y", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r1_highpass_apod_y", dest="r1_highpass_apod_y", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r1_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r2_highpass_apod_y", dest="r2_highpass_apod_y", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r2_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r3_highpass_apod_y", dest="r3_highpass_apod_y", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r3_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--r4_highpass_apod_y", dest="r4_highpass_apod_y", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --r4_highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--thickness", dest="thickness",  default=300, type="float",
			help="Estimated thickness of unbinned specimen (in pixels), e.g. --thickness=100.0", metavar="float")
		
		self.parser.add_option("--pixelsize", dest="pixelsize", type="float",
			help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
		
		self.parser.add_option("--param", dest="param",
			help="Override other parameters and use an external paramfile. e.g. --param=/path/to/max.param", metavar="FILE")

		self.parser.add_option("--iters", dest="iters", default=1, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --iters=4", metavar="int")

		self.parser.add_option("--r1_iters", dest="r1_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r1_iters=4", metavar="int")

		self.parser.add_option("--r2_iters", dest="r2_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r2_iters=4", metavar="int")

		self.parser.add_option("--r3_iters", dest="r3_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r3_iters=4", metavar="int")

		self.parser.add_option("--r4_iters", dest="r4_iters", default=0, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --r4_iters=4", metavar="int")

		self.parser.add_option("--sampling", dest="sampling",  default="4", type="int",
			help="Sampling rate of raw data, e.g. --sampling=4")
		
		self.parser.add_option("--r1_sampling", dest="r1_sampling",  default="4", type="int",
			help="Sampling rate of raw data, e.g. --r1_sampling=4")
		
		self.parser.add_option("--r2_sampling", dest="r2_sampling",  default="4", type="int",
			help="Sampling rate of raw data, e.g. --r2_sampling=4")
		
		self.parser.add_option("--r3_sampling", dest="r3_sampling",  default="4", type="int",
			help="Sampling rate of raw data, e.g. --r3_sampling=4")
		
		self.parser.add_option("--r4_sampling", dest="r4_sampling",  default="4", type="int",
			help="Sampling rate of raw data, e.g. --r4_sampling=4")
		
		self.parser.add_option("--map_sampling", dest="map_sampling",  default="8", type="int",
			help="Sampling rate of raw data for use in reconstruction, e.g. --map_sampling=4")
			
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

		self.parser.add_option("--image_apodization_x", dest="image_apodization_x",  type="float",
			help="Protomo2 only: TODO, e.g. --image_apodization_x=10.0", metavar="float")

		self.parser.add_option("--image_apodization_y", dest="image_apodization_y",  type="float",
			help="Protomo2 only: TODO, e.g. --image_apodization_y=10.0", metavar="float")

		self.parser.add_option("--reference_apodization_x", dest="reference_apodization_x",  type="float",
			help="Protomo2 only: TODO, e.g. --reference_apodization_x=10.0", metavar="float")

		self.parser.add_option("--reference_apodization_y", dest="reference_apodization_y",  type="float",
			help="Protomo2 only: TODO, e.g. --reference_apodization_y=10.0", metavar="float")

		self.correlation_modes = ( "xcf", "mcf", "pcf", "dbl" )
		self.parser.add_option("--corr_mode", dest="corr_mode",
			help="Protomo2 only: Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
			type="choice", choices=self.correlation_modes, default="mcf" )
		
		self.parser.add_option("--correlation_size_x", dest="correlation_size_x",  type="int",  default="128",
			help="Protomo2 only: X size of cross correlation peak image, e.g. --correlation_size_x=128", metavar="int")

		self.parser.add_option("--correlation_size_y", dest="correlation_size_y",  type="int",  default="128",
			help="Protomo2 only: Y size of cross correlation peak image, e.g. --correlation_size_y=128", metavar="int")
		
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
		
		#self.parser.add_option("--cmdiameter_x", dest="cmdiameter_x",  type="float",
		#	help="Size of region for center of mass calculation, e.g. --cmdiameter_x=19.0", metavar="float")

		#self.parser.add_option("--cmdiameter_y", dest="cmdiameter_y",  type="float",,
		#	help="Size of region for center of mass calculation, e.g. --cmdiameter_y=19.0", metavar="float")

		self.parser.add_option("--map_size_x", dest="map_size_x",  type="int",  default="1024",
			help="Protomo2 only: Size of the reconstructed tomogram in the X direction, e.g. --map_size_x=256", metavar="int")

		self.parser.add_option("--map_size_y", dest="map_size_y",  type="int",  default="1024",
			help="Protomo2 only: Size of the reconstructed tomogram in the Y direction, e.g. --map_size_y=256", metavar="int")

		self.parser.add_option("--map_size_z", dest="map_size_z",  type="int",  default="200",
			help="Protomo2 only: Size of the reconstructed tomogram in the Z direction, e.g. --map_size_z=128", metavar="int")
		
		self.parser.add_option("--map_lowpass_diameter_x", dest="map_lowpass_diameter_x",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --map_lowpass_diameter_x=0.5", metavar="float")
		
		self.parser.add_option("--map_lowpass_diameter_y", dest="map_lowpass_diameter_y",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --map_lowpass_diameter_y=0.5", metavar="float")
		
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
		
		self.parser.add_option("--select_images", dest="select_images",  default="0-999999",
			help='Select specific images in the tilt series, e.g. --select_images="1,2,5-7"')
		
		self.parser.add_option("--exclude_images", dest="exclude_images",  default="999999",
			help='Select specific images in the tilt series, e.g. --exclude_images="1,2,5-7"')
		
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
		
		self.parser.add_option("--coarse", dest="coarse",  default=False,
			help="To perform an initial coarse alignment, set to 'True'. Requires gridsearch, corr, and mask options, e.g. --coarse=True")
		
		self.parser.add_option("--gridsearch_limit", dest="gridsearch_limit",  type="float",  default=2.0,
			help="Protomo2.4 only: Gridseach +-angle limit for coarse alignment. To do a translational alignment only set to 1 and set gridsearch_limit to 0, e.g. --gridsearch_limit=2.0", metavar="float")
			
		self.parser.add_option("--gridsearch_step", dest="gridsearch_step",  type="float",  default=0.1,
			help="Protomo2.4 only: Gridseach angle step size for coarse alignment, e.g. --gridsearch_step=0.5", metavar="float")
		
		self.parser.add_option("--retry", dest="retry",  type="int",  default="3",
			help="Number of times to retry coarse alignment, which sometimes fails because the search area is too big, e.g. --retry=5", metavar="int")
		
		self.parser.add_option("--retry_shrink", dest="retry_shrink",  type="float",  default="0.9",
			help="How much to shrink the window size from the previous retry, e.g. --retry_shrink=0.75", metavar="float")
	
		self.parser.add_option("--create_reconstruction", dest="create_reconstruction",
			help="Appion: Create a reconstruction and gif for depiction, e.g. --create_reconstruction=false")
		
		self.parser.add_option("--keep_recons", dest="keep_recons",
			help="Appion: Keep intermediate reconstruction files, e.g. --keep_recons=true")

		self.parser.add_option("--gif_optimize", dest="gif_optimize",
			help="Appion: Optimize depiction gif, e.g. --gif_optimize=true")
		
		self.parser.add_option("--restart_cycle", dest="restart_cycle",
			help="Restart a Refinement at this iteration, e.g. --restart_cycle=2")
		
		self.parser.add_option("--link", dest="link",  default=True,
			help="Link raw images if True, copy if False, e.g. --link=False")
		
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
	def pixelsToAngstroms(self, coarse=False):
		self.params['thickness'] = self.params['thickness']/self.params['pixelsize']
		self.params['lowpass_diameter_x'] = 2*self.params['pixelsize']/self.params['lowpass_diameter_x']
		self.params['lowpass_diameter_y'] = 2*self.params['pixelsize']/self.params['lowpass_diameter_y']
		self.params['highpass_diameter_x'] = 2*self.params['pixelsize']/self.params['highpass_diameter_x']
		self.params['highpass_diameter_y'] = 2*self.params['pixelsize']/self.params['highpass_diameter_y']
		self.params['lowpass_apod_x'] = self.params['pixelsize']/self.params['lowpass_apod_x']
		self.params['lowpass_apod_y'] = self.params['pixelsize']/self.params['lowpass_apod_y']
		self.params['highpass_apod_x'] = self.params['pixelsize']/self.params['highpass_apod_x']
		self.params['highpass_apod_y'] = self.params['pixelsize']/self.params['highpass_apod_y']
		
		if coarse == "False":
			self.params['r1_lowpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r1_lowpass_diameter_x']
			self.params['r1_lowpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r1_lowpass_diameter_y']
			self.params['r1_highpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r1_highpass_diameter_x']
			self.params['r1_highpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r1_highpass_diameter_y']
			self.params['r1_lowpass_apod_x'] = self.params['pixelsize']/self.params['r1_lowpass_apod_x']
			self.params['r1_lowpass_apod_y'] = self.params['pixelsize']/self.params['r1_lowpass_apod_y']
			self.params['r1_highpass_apod_x'] = self.params['pixelsize']/self.params['r1_highpass_apod_x']
			self.params['r1_highpass_apod_y'] = self.params['pixelsize']/self.params['r1_highpass_apod_y']
			try:
				self.params['r2_lowpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r2_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r2_lowpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r2_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r2_highpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r2_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r2_highpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r2_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r2_lowpass_apod_x'] = self.params['pixelsize']/self.params['r2_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r2_lowpass_apod_y'] = self.params['pixelsize']/self.params['r2_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r2_highpass_apod_x'] = self.params['pixelsize']/self.params['r2_highpass_apod_x']
			except:
				pass
			try:
				self.params['r2_highpass_apod_y'] = self.params['pixelsize']/self.params['r2_highpass_apod_y']
			except:
				pass
			try:
				self.params['r3_lowpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r3_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r3_lowpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r3_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r3_highpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r3_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r3_highpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r3_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r3_lowpass_apod_x'] = self.params['pixelsize']/self.params['r3_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r3_lowpass_apod_y'] = self.params['pixelsize']/self.params['r3_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r3_highpass_apod_x'] = self.params['pixelsize']/self.params['r3_highpass_apod_x']
			except:
				pass
			try:
				self.params['r3_highpass_apod_y'] = self.params['pixelsize']/self.params['r3_highpass_apod_y']
			except:
				pass
			try:
				self.params['r4_lowpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r4_lowpass_diameter_x']
			except:
				pass
			try:
				self.params['r4_lowpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r4_lowpass_diameter_y']
			except:
				pass
			try:
				self.params['r4_highpass_diameter_x'] = 2*self.params['pixelsize']/self.params['r4_highpass_diameter_x']
			except:
				pass
			try:
				self.params['r4_highpass_diameter_y'] = 2*self.params['pixelsize']/self.params['r4_highpass_diameter_y']
			except:
				pass
			try:
				self.params['r4_lowpass_apod_x'] = self.params['pixelsize']/self.params['r4_lowpass_apod_x']
			except:
				pass
			try:
				self.params['r4_lowpass_apod_y'] = self.params['pixelsize']/self.params['r4_lowpass_apod_y']
			except:
				pass
			try:
				self.params['r4_highpass_apod_x'] = self.params['pixelsize']/self.params['r4_highpass_apod_x']
			except:
				pass
			try:
				self.params['r4_highpass_apod_y'] = self.params['pixelsize']/self.params['r4_highpass_apod_y']
			except:
				pass
	
	#=====================
	def start(self):
	
		###setup
		global rundir
		rundir=self.params['rundir']
		self.params['raw_path']=os.path.join(rundir,'raw')
		raw_path=self.params['raw_path']
		if os.path.exists(rundir):
			os.chdir(rundir)
		else:
			os.mkdir(rundir)
			os.chdir(rundir)
		self.params['cachedir']=rundir+'/'+self.params['cachedir']
		self.params['protomo_outdir']=rundir+'/'+self.params['protomo_outdir']
		
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		seriesname='series'+seriesnumber
		tiltfilename=seriesname+'.tlt'
		tiltfilename_full=rundir+'/'+tiltfilename

		###Do queries and make tlt file if first run
		if self.params['coarse'] == 'True':
			apDisplay.printMsg('Preparing raw images and initial tilt file')
			self.params['maxtilt'] = apProTomo2Prep.prepareTiltFile(self.params['sessionname'], seriesname, tiltfilename, int(self.params['tiltseries']), raw_path, link=self.params['link'], coarse="True")
		else:
			self.params['maxtilt'] = apProTomo2Prep.prepareTiltFile(self.params['sessionname'], seriesname, tiltfilename, int(self.params['tiltseries']), raw_path, link=self.params['link'], coarse="False")
		
		self.params['cos_alpha']=math.cos(self.params['maxtilt']*math.pi/180)
		rawimagecount=len([file for file in os.listdir(raw_path) if os.path.isfile(os.path.join(raw_path,file))])
		
		###convert angstroms to pixels
		self.pixelsToAngstroms(coarse=self.params['coarse'])
		
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
		if self.params['coarse']:
			os.system("mkdir coarse_out")
			coarse_param_out='coarse_'+self.params['seriesname']+'.param'
			apProTomo2Prep.modifyParamFile(coarse_param_in, coarse_param_out, paramdict)
			coarse_seriesparam=protomo.param(coarse_param_out)

		apDisplay.printMsg('Starting protomo alignment')
		
		#create series object and use presence of i3t to determine if protomo has been run once already
		
		if self.params['coarse'] == 'True':
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
			new_region_x=self.params['region_x']/self.params['sampling']   #Just initializing
			new_region_y=self.params['region_y']/self.params['sampling']   #Just initializing
			while (retry <= self.params['retry']):
				try:
					if (retry > 0):
						new_region_x = int(new_region_x*self.params['retry_shrink'])
						new_region_y = int(new_region_y*self.params['retry_shrink'])
						apDisplay.printMsg("Coarse Alignment failed. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (retry, int(100*self.params['retry_shrink']), new_region_x, new_region_y))
						newsize = "{ %s %s }" % (new_region_x, new_region_y)
						series.setparam("window.size", newsize)
					retry+=1
					series.align()
					final_retry=retry-1
					retry = self.params['retry'] + 1 #Alignment worked, don't retry anymore
				except:
					if (retry > self.params['retry']):
						apDisplay.printMsg("Coarse Alignment failed after rescaling the search area %s time(s)." % (retry-1))
						apDisplay.printMsg("Window Size (x) was resampled to %s" % (new_region_x*self.params['sampling']))
						apDisplay.printMsg("Window Size (y) was resampled to %s" % (new_region_y*self.params['sampling']))
						apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n")
					pass
			
			##write all parameters to a file - this is super hacky, but I don't know any other way to output None function return that only prints stdout to the terminal window on run.
			#parameters_coarse = ['sampling','binning','preprocessing','select','exclude','preprocess.logging','preprocess.border','preprocess.clip','preprocess.thr','preprocess.grow','preprocess.mask.gradient','preprocess.mask.iter','preprocess.mask.filter','preprocess.mask.kernel','preprocess.mask.clip','window.size','window.area','window.mask.apodization','window.mask.width','window.lowpass.diameter','window.lowpass.apodization','window.highpass.diameter','window.highpass.apodization','reference.body','reference.select','reference.exclude','align.include','align.exclude','align.gridsearch.limit','align.gridsearch.step','align.mask.apodization','align.mask.width','align.correlation.mode','align.correlation.size','align.peaksearch.radius','fit.orientation','fit.azimuth','fit.elevation','fit.rotation','fit.scale','fit.include','fit.exclude','fit.logging','fit.loglevel','map.size','map.body','map.sampling','map.select','map.exclude','map.lowpass.diameter','map.lowpass.apodization','map.logging','suffix','pathlist','cachedir','outdir','logging']
			#os.system("mkdir tmp; cp %s.* tmp; cd tmp" % (name))   #EVEN A FULL CP DOESN'T WORK! -> protomo.error: file is already in use, coarse_series0003.i3t
			#fname=self.params['runname']+'_coarse_params.py'
			#f = open("%s" % (fname), 'w')
			#f.write("#!/usr/bin/env python\n")
			#f.write("import protomo\n")
			#f.write("p=protomo.param('%s')\n" % (coarse_param_out))
			#f.write("s=protomo.series(p)\n")
			#for parameter in parameters_coarse:
			#	f.write("s.setparam(\"%s\")\n" % (parameter))
			#f.close()
			#os.system("chmod +x %s; ./%s > ../%s.param.log; cd .." % (fname, fname, name))
			
			corrfile=name+'.corr'
			series.corr(corrfile)
			
			#archive results
			tiltfile=name+'.tlt'
			series.geom(1).write(tiltfile)
			
			# For multiprocessing
			jobs=[]
			
			# Make correlation peak gifs for depiction			
			jobs.append(mp.Process(target=apProTomo2Aligner.makeCoarseCorrPeakGifs, args=(name, 0, rundir, self.params['protomo_outdir'], "Coarse",)))
			
			# Make tiltseries gif for depiction
			apDisplay.printMsg("Creating initial tilt series gif...")
			jobs.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesGifs, args=(seriesname, 0, tiltfilename_full, rawimagecount, rundir, raw_path, self.params['pixelsize'], self.params['map_sampling'], self.params['image_file_type'], "Initial",)))

			apDisplay.printMsg("Creating Coarse Alignment tilt series gif...")
			jobs.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesGifs, args=(seriesname, 0, tiltfile, rawimagecount, rundir, raw_path, self.params['pixelsize'], self.params['map_sampling'], self.params['image_file_type'], "Coarse",)))
			
			# Send off processes in the background
			for job in jobs:
				job.start()
			
			# Generate intermediate reconstructions and gifs for depiction
			if self.params['create_reconstruction'] == "true":			
				# Create intermediate reconstruction
				apDisplay.printMsg("Generating Coarse Alignment reconstruction...")
				series.mapfile()
				apProTomo2Aligner.makeReconstructionGifs(name, 0, rundir, self.params['protomo_outdir'], self.params['pixelsize'], self.params['sampling'], self.params['map_sampling'], self.params['gif_optimize'], self.params['keep_recons'], align_step="Coarse")
				
			else:
				apDisplay.printMsg("Skipping reconstruction depiction\n")
			
			# Join processes
			for job in jobs:
				job.join()
			
			cleanup="cp coarse*.* coarse_out; rm %s.corr; ln %s.i3t %s.i3t" % (name, name, seriesname)
			os.system(cleanup)
			
			if final_retry > 0:
				apDisplay.printMsg("Coarse Alignment finished after retrying %s time(s) due to the sampled search area being too small." % (final_retry))
				apDisplay.printMsg("Window Size (x) was resampled to %s" % (new_region_x*self.params['sampling']))
				apDisplay.printMsg("Window Size (y) was resampled to %s" % (new_region_y*self.params['sampling']))
				apDisplay.printMsg("Put these values into the corresponding parameter boxes on the Protomo Refinement Appion webpage.\n")
			
			apDisplay.printMsg("Coarse Alignment finished!\n")

		else: # Normal refinement with area matching
			name=seriesname
			start=0  #Counter for prevous iterations
			r=1  #Round number

			#figure out starting number
			previters=glob.glob(name+'*.corr')
			if len(previters) > 0:
				previters.sort()
				lastiter=previters[-1]
				start=int(lastiter.split(name)[1].split('.')[0])+1
			
			#rewind to previous iteration if requested
			if (type(self.params['restart_cycle']) == int):
				apDisplay.printMsg("Rewinding to iteration %s" % (self.params['restart_cycle']))
				start=self.params['restart_cycle']
				series.setcycle(start-1)
			
			iters=self.params['r1_iters']+self.params['r2_iters']+self.params['r3_iters']+self.params['r4_iters']
			round1={"window.size":"{ %s %s }" % (self.params['r1_region_x'],self.params['r1_region_y']),"window.lowpass.diameter":"{ %s %s }" % (self.params['r1_lowpass_diameter_x'],self.params['r1_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r1_lowpass_diameter_x'],self.params['r1_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r1_lowpass_apod_x'],self.params['r1_lowpass_apod_y']),"map.lowpass.apodization":"{ %s %s }" % (self.params['r1_lowpass_apod_x'],self.params['r1_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r1_highpass_apod_x'],self.params['r1_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r1_highpass_diameter_x'],self.params['r1_highpass_diameter_y']),"sampling":"%s" % (self.params['r1_sampling']),"map.sampling":"%s" % (self.params['r1_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r1_kernel_x'],self.params['r1_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r1_peak_search_radius_x'],self.params['r1_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r1_mask_width_x'],self.params['r1_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r1_mask_width_x'],self.params['r1_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r1_mask_apod_x'],self.params['r1_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r1_mask_apod_x'],self.params['r1_mask_apod_y'])}			
			round2={"window.size":"{ %s %s }" % (self.params['r2_region_x'],self.params['r2_region_y']),"window.lowpass.diameter":"{ %s %s }" % (self.params['r2_lowpass_diameter_x'],self.params['r2_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r2_lowpass_diameter_x'],self.params['r2_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r2_lowpass_apod_x'],self.params['r2_lowpass_apod_y']),"map.lowpass.apodization":"{ %s %s }" % (self.params['r2_lowpass_apod_x'],self.params['r2_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r2_highpass_apod_x'],self.params['r2_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r2_highpass_diameter_x'],self.params['r2_highpass_diameter_y']),"sampling":"%s" % (self.params['r2_sampling']),"map.sampling":"%s" % (self.params['r2_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r2_kernel_x'],self.params['r2_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r2_peak_search_radius_x'],self.params['r2_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r2_mask_width_x'],self.params['r2_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r2_mask_width_x'],self.params['r2_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r2_mask_apod_x'],self.params['r2_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r2_mask_apod_x'],self.params['r2_mask_apod_y'])}
			round3={"window.size":"{ %s %s }" % (self.params['r3_region_x'],self.params['r3_region_y']),"window.lowpass.diameter":"{ %s %s }" % (self.params['r3_lowpass_diameter_x'],self.params['r3_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r3_lowpass_diameter_x'],self.params['r3_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r3_lowpass_apod_x'],self.params['r3_lowpass_apod_y']),"map.lowpass.apodization":"{ %s %s }" % (self.params['r3_lowpass_apod_x'],self.params['r3_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r3_highpass_apod_x'],self.params['r3_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r3_highpass_diameter_x'],self.params['r3_highpass_diameter_y']),"sampling":"%s" % (self.params['r3_sampling']),"map.sampling":"%s" % (self.params['r3_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r3_kernel_x'],self.params['r3_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r3_peak_search_radius_x'],self.params['r3_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r3_mask_width_x'],self.params['r3_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r3_mask_width_x'],self.params['r3_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r3_mask_apod_x'],self.params['r3_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r3_mask_apod_x'],self.params['r3_mask_apod_y'])}
			round4={"window.size":"{ %s %s }" % (self.params['r4_region_x'],self.params['r4_region_y']),"window.lowpass.diameter":"{ %s %s }" % (self.params['r4_lowpass_diameter_x'],self.params['r4_lowpass_diameter_y']),"map.lowpass.diameter":"{ %s %s }" % (self.params['r4_lowpass_diameter_x'],self.params['r4_lowpass_diameter_y']),"window.lowpass.apodization":"{ %s %s }" % (self.params['r4_lowpass_apod_x'],self.params['r4_lowpass_apod_y']),"map.lowpass.apodization":"{ %s %s }" % (self.params['r4_lowpass_apod_x'],self.params['r4_lowpass_apod_y']),"window.highpass.apodization":"{ %s %s }" % (self.params['r4_highpass_apod_x'],self.params['r4_highpass_apod_y']),"window.highpass.diameter":"{ %s %s }" % (self.params['r4_highpass_diameter_x'],self.params['r4_highpass_diameter_y']),"sampling":"%s" % (self.params['r4_sampling']),"map.sampling":"%s" % (self.params['r4_sampling']),"preprocess.mask.kernel":"{ %s %s }" % (self.params['r4_kernel_x'],self.params['r4_kernel_y']),"align.peaksearch.radius":"{ %s %s }" % (self.params['r4_peak_search_radius_x'],self.params['r4_peak_search_radius_y']),"window.mask.width":"{ %s %s }" % (self.params['r4_mask_width_x'],self.params['r4_mask_width_y']),"align.mask.width":"{ %s %s }" % (self.params['r4_mask_width_x'],self.params['r4_mask_width_y']),"window.mask.apodization":"{ %s %s }" % (self.params['r4_mask_apod_x'],self.params['r4_mask_apod_y']),"align.mask.apodization":"{ %s %s }" % (self.params['r4_mask_apod_x'],self.params['r4_mask_apod_y'])}
			switches={"preprocess.mask.gradient":{"%s" % (self.params['gradient']):self.params['gradient_switch']},"preprocess.mask.iter":{"%s" % (self.params['iter_gradient']):self.params['iter_gradient_switch']},"fit.orientation":{"%s" % (self.params['orientation']):self.params['orientation_switch']},"fit.azimuth":{"%s" % (self.params['azimuth']):self.params['azimuth_switch']},"fit.elevation":{"%s" % (self.params['elevation']):self.params['elevation_switch']},"fit.rotation":{"%s" % (self.params['rotation']):self.params['rotation_switch']},"fit.scale":{"%s" % (self.params['scale']):self.params['scale_switch']}}
			
			for n in range(iters):
				#change parameters depending on rounds
				region_x=self.params['r1_region_x']
				region_y=self.params['r1_region_y']
				sampling=self.params['r1_sampling']
				if (n+1 == self.params['r1_iters']+self.params['r2_iters']):
					r=2
					region_x=self.params['r2_region_x']
					region_y=self.params['r2_region_y']
					sampling=self.params['r2_sampling']
					for val in round2:
						series.setparam(val,round2[val])
				elif (n+1 == self.params['r1_iters']+self.params['r2_iters']+self.params['r3_iters']):
					r=3
					region_x=self.params['r3_region_x']
					region_y=self.params['r3_region_y']
					sampling=self.params['r3_sampling']
					for val in round3:
						series.setparam(val,round3[val])
				elif (n+1 == self.params['r1_iters']+self.params['r2_iters']+self.params['r3_iters']+self.params['r4_iters']):
					r=4
					region_x=self.params['r4_region_x']
					region_y=self.params['r4_region_y']
					sampling=self.params['r4_sampling']
					for val in round4:
						series.setparam(val,round4[val])
				
				#change parameters depending on switches
				for switch in switches:
					for key in switches[switch]:
						if (switches[switch][key] == n+1):
							if (key == "true"):
								newval="false"
							else:
								newval="true"
							series.setparam(switch,newval)
				
				apDisplay.printMsg("Beginning Iteration #%s, Round #%s\n" % (n+1,r))
				
				#Align and restart alignment if failed
				retry=0
				brk=0
				new_region_x=region_x/sampling   #Just initializing
				new_region_y=region_y/sampling   #Just initializing
				while (retry <= self.params['retry']):
					try:
						if (retry > 0):
							new_region_x = int(new_region_x*self.params['retry_shrink'])
							new_region_y = int(new_region_y*self.params['retry_shrink'])
							apDisplay.printMsg("Refinement failed. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (retry, int(100*self.params['retry_shrink']), new_region_x*sampling, new_region_y*sampling))
							newsize = "{ %s %s }" % (new_region_x, new_region_y)
							series.setparam("window.size", newsize)
						retry+=1
						series.align()
						final_retry=retry-1
						retry = self.params['retry'] + 1 #Alignment worked, don't retry anymore
					except:
						if (retry > self.params['retry']):
							apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (n+1, retry-1))
							apDisplay.printMsg("Window Size (x) was resampled to %s" % (new_region_x*sampling))
							apDisplay.printMsg("Window Size (y) was resampled to %s" % (new_region_y*sampling))
							apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
							brk=1
						pass

				if (brk == 1):   #resampling failed, break out of all refinement iterations
					break
				
				it="%02d" % ((n+start))
				itt="%02d" % ((n+start+1))
				ite="_ite%02d" % ((n+start))
				basename='%s%s' % (name,it)
				corrfile=basename+'.corr'
				series.corr(corrfile)
				series.fit()
				series.update()

				#archive results
				tiltfile=basename+'.tlt'
				series.geom(0).write(tiltfile)
					
				# For multiprocessing
				jobs=[]
				
				# Make correlation peak gifs for depiction			
				jobs.append(mp.Process(target=apProTomo2Aligner.makeCoarseCorrPeakGifs, args=(name, it, rundir, self.params['protomo_outdir'], "Refinement")))
					
				# Make correlation plot pngs for depiction
				jobs.append(mp.Process(target=apProTomo2Aligner.makeCoarseCorrPlotImages, args=(name, it, rundir, corrfile)))
				
				# Make tiltseries gif for depiction
				apDisplay.printMsg("Creating Refinement tilt series gif for iteration #%s..." % (n+1))
				jobs.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesGifs, args=(seriesname, it, tiltfile, rawimagecount, rundir, raw_path, self.params['pixelsize'], self.params['map_sampling'], self.params['image_file_type'], "Refinement")))
				
				# Send off processes in the background
				for job in jobs:
					job.start()
				
				# Generate intermediate reconstructions and gifs for depiction
				if self.params['create_reconstruction'] == "true":			
					# Create intermediate reconstruction
					apDisplay.printMsg("Generating Refinement reconstruction for iteration #%s..." % (n+1))
					series.mapfile()
					apProTomo2Aligner.makeReconstructionGifs(name, itt, rundir, self.params['protomo_outdir'], self.params['pixelsize'], sampling, self.params['map_sampling'], self.params['gif_optimize'], self.params['keep_recons'], align_step="Refinement")
					
				else:
					apDisplay.printMsg("Skipping reconstruction depiction\n")
				
				# Join processes
				for job in jobs:
					job.join()
				
				if final_retry > 0:
					apDisplay.printMsg("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small." % (n+1, final_retry))
					apDisplay.printMsg("Window Size (x) was resampled to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was resampled to %s" % (new_region_y*sampling))
			
		
		
#=====================
#=====================
if __name__ == '__main__':
	protomo2aligner = ProTomo2Aligner()
	protomo2aligner.start()
	protomo2aligner.close()
	protomo2aligner_log=cwd+'/'+'protomo2aligner.log'
	cleanup="mv %s %s" % (protomo2aligner_log, rundir)
	os.system(cleanup)

