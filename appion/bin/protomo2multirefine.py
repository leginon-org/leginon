#!/usr/bin/env python
# 
# This script allows the user to refine a tilt-series by running multiple instances of protomo2aligner.py with different thicknesses.
# It is highly recommended that this script be run using commands generated through the Appion-Protomo web interface.
# In the future this should be written to include differing search areas.

from __future__ import division
import os
import sys
import glob
import time
import shutil
import optparse
import subprocess
import multiprocessing as mp
from appionlib import apDisplay


def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option("--seriesname", dest="seriesname", help="Series name (for database)")
		
	parser.add_option("--sessionname", dest="sessionname", help="Session date, e.g. --sessionname=14aug02a")
	
	parser.add_option("--tiltseries", dest="tiltseries", help="Name of Protomo series, e.g. --tiltseries=31")
	
	parser.add_option("--runname", dest="runname", help="Name of protomorun directory as made by Appion")
	
	parser.add_option("--description", dest="description", default="", help="Run description")
	
	parser.add_option("--jobtype", dest="jobtype", help="Appion jobtype")
	
	parser.add_option("--projectid", dest="projectid", help="Appion project ID")
	
	parser.add_option("--expid", dest="expid", help="Appion experiment ID")
	
	parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")
	
	parser.add_option('--dimx', dest='dimx', type='int', metavar='int', help='Dimension (x) of micrographs, e.g. --dimx=4096')
	
	parser.add_option('--dimy', dest='dimy', type='int', metavar='int', help='Dimension (y) of micrographs, e.g. --dimy=4096')
	
	parser.add_option('--maxtilt', dest='maxtilt', type='int', metavar='int', help='Highest image tilt in degrees, e.g. --maxtilt=65') 
	
	parser.add_option('--shift_limit', dest='shift_limit', type='float', metavar='float', help='Percentage of image size, above which shifts with higher shifts will be discarded for all images, e.g. --shift_limit=50') 
	
	parser.add_option('--angle_limit', dest='angle_limit', type='float', metavar='float', help='Only remove images from the tilt file greater than abs(angle_limit), e.g. --angle_limit=35') 
	
	parser.add_option("--negative", dest="negative", type="float",  default="-90",
		help="Tilt angle, in degrees, below which all images will be removed, e.g. --negative=-45", metavar="float")
	
	parser.add_option("--positive", dest="positive", type="float",  default="90",
		help="Tilt angle, in degrees, above which all images will be removed, e.g. --positive=45", metavar="float")
	
	parser.add_option("--starting_tlt_file", dest="starting_tlt_file", default="Coarse",
		help="Begin refinement with coarse alignment results or initial alignment (ie. from the microscope)?, e.g. --starting_tlt_file=Coarse",)
	
	parser.add_option("--region_x", dest="region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --region=1024", metavar="int")
	
	parser.add_option("--r1_region_x", dest="r1_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r1_region=1024", metavar="int")
	
	parser.add_option("--r2_region_x", dest="r2_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r2_region=1024", metavar="int")
	
	parser.add_option("--r3_region_x", dest="r3_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r3_region=1024", metavar="int")
	
	parser.add_option("--r4_region_x", dest="r4_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r4_region=1024", metavar="int")
	
	parser.add_option("--r5_region_x", dest="r5_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r5_region=1024", metavar="int")
	
	parser.add_option("--region_y", dest="region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --region=1024", metavar="int")
	
	parser.add_option("--r1_region_y", dest="r1_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r1_region=1024", metavar="int")
	
	parser.add_option("--r2_region_y", dest="r2_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r2_region=1024", metavar="int")
	
	parser.add_option("--r3_region_y", dest="r3_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r3_region=1024", metavar="int")
	
	parser.add_option("--r4_region_y", dest="r4_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r4_region=1024", metavar="int")
	
	parser.add_option("--r5_region_y", dest="r5_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r5_region=1024", metavar="int")
	
	parser.add_option("--lowpass_diameter_x", dest="lowpass_diameter_x",  default=0.5, type="float",
		help="in fractions of nyquist, e.g. --lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r1_lowpass_diameter_x", dest="r1_lowpass_diameter_x",  default=0.5, type="float",
		help="in fractions of nyquist, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r2_lowpass_diameter_x", dest="r2_lowpass_diameter_x",  default=0.5, type="float",
		help="in fractions of nyquist, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r3_lowpass_diameter_x", dest="r3_lowpass_diameter_x",  default=0.5, type="float",
		help="in fractions of nyquist, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r4_lowpass_diameter_x", dest="r4_lowpass_diameter_x",  default=0.5, type="float",
		help="in fractions of nyquist, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r5_lowpass_diameter_x", dest="r5_lowpass_diameter_x",  default=0.5, type="float",
		help="in fractions of nyquist, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--lowpass_diameter_y", dest="lowpass_diameter_y",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r1_lowpass_diameter_y", dest="r1_lowpass_diameter_y",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r2_lowpass_diameter_y", dest="r2_lowpass_diameter_y",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r3_lowpass_diameter_y", dest="r3_lowpass_diameter_y",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r4_lowpass_diameter_y", dest="r4_lowpass_diameter_y",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r5_lowpass_diameter_y", dest="r5_lowpass_diameter_y",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--lowpass_apod_x", dest="lowpass_apod_x", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r1_lowpass_apod_x", dest="r1_lowpass_apod_x", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r2_lowpass_apod_x", dest="r2_lowpass_apod_x", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r3_lowpass_apod_x", dest="r3_lowpass_apod_x", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r4_lowpass_apod_x", dest="r4_lowpass_apod_x", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--r5_lowpass_apod_x", dest="r5_lowpass_apod_x", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
	
	parser.add_option("--lowpass_apod_y", dest="lowpass_apod_y", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r1_lowpass_apod_y", dest="r1_lowpass_apod_y", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r2_lowpass_apod_y", dest="r2_lowpass_apod_y", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r3_lowpass_apod_y", dest="r3_lowpass_apod_y", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r4_lowpass_apod_y", dest="r4_lowpass_apod_y", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--r5_lowpass_apod_y", dest="r5_lowpass_apod_y", default=0.05, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_y=0.4", metavar="float")
	
	parser.add_option("--highpass_diameter_x", dest="highpass_diameter_x", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r1_highpass_diameter_x", dest="r1_highpass_diameter_x", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r2_highpass_diameter_x", dest="r2_highpass_diameter_x", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r3_highpass_diameter_x", dest="r3_highpass_diameter_x", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r4_highpass_diameter_x", dest="r4_highpass_diameter_x", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r5_highpass_diameter_x", dest="r5_highpass_diameter_x", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--highpass_diameter_y", dest="highpass_diameter_y", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r1_highpass_diameter_y", dest="r1_highpass_diameter_y", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r2_highpass_diameter_y", dest="r2_highpass_diameter_y", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r3_highpass_diameter_y", dest="r3_highpass_diameter_y", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r4_highpass_diameter_y", dest="r4_highpass_diameter_y", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r5_highpass_diameter_y", dest="r5_highpass_diameter_y", default=0.001, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--highpass_apod_x", dest="highpass_apod_x", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r1_highpass_apod_x", dest="r1_highpass_apod_x", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r2_highpass_apod_x", dest="r2_highpass_apod_x", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r3_highpass_apod_x", dest="r3_highpass_apod_x", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r4_highpass_apod_x", dest="r4_highpass_apod_x", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--r5_highpass_apod_x", dest="r5_highpass_apod_x", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_x=0.02", metavar="float")
	
	parser.add_option("--highpass_apod_y", dest="highpass_apod_y", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r1_highpass_apod_y", dest="r1_highpass_apod_y", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r2_highpass_apod_y", dest="r2_highpass_apod_y", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r3_highpass_apod_y", dest="r3_highpass_apod_y", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r4_highpass_apod_y", dest="r4_highpass_apod_y", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--r5_highpass_apod_y", dest="r5_highpass_apod_y", default=0.002, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_y=0.02", metavar="float")

	parser.add_option("--thicknesses", dest="thicknesses",
		help="Multiple, comma-separated estimated thicknesses of unbinned specimen (in angstroms), e.g. --thicknesses=1000.0,1250.0,1500.0")
	
	parser.add_option("--pixelsize", dest="pixelsize", type="float",
		help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
	
	parser.add_option("--param", dest="param",
		help="Override other parameters and use an external paramfile. e.g. --param=/path/to/max.param", metavar="FILE")

	parser.add_option("--iters", dest="iters", default=1, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --iters=4", metavar="int")

	parser.add_option("--r1_iters", dest="r1_iters", default=1, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r1_iters=4", metavar="int")

	parser.add_option("--r2_iters", dest="r2_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r2_iters=4", metavar="int")

	parser.add_option("--r3_iters", dest="r3_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r3_iters=4", metavar="int")

	parser.add_option("--r4_iters", dest="r4_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r4_iters=4", metavar="int")

	parser.add_option("--r5_iters", dest="r5_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r5_iters=4", metavar="int")

	parser.add_option("--sampling", dest="sampling",  default=8, type="int",
		help="Sampling rate of raw data, e.g. --sampling=4")
	
	parser.add_option("--r1_sampling", dest="r1_sampling",  default=8, type="int",
		help="Sampling rate of raw data, e.g. --r1_sampling=4")
	
	parser.add_option("--r2_sampling", dest="r2_sampling",  default=6, type="int",
		help="Sampling rate of raw data, e.g. --r2_sampling=4")
	
	parser.add_option("--r3_sampling", dest="r3_sampling",  default=4, type="int",
		help="Sampling rate of raw data, e.g. --r3_sampling=4")
	
	parser.add_option("--r4_sampling", dest="r4_sampling",  default=2, type="int",
		help="Sampling rate of raw data, e.g. --r4_sampling=4")
	
	parser.add_option("--r5_sampling", dest="r5_sampling",  default=2, type="int",
		help="Sampling rate of raw data, e.g. --r5_sampling=4")
	
	parser.add_option("--map_sampling", dest="map_sampling",  default=8, type="int",
		help="Sampling rate of raw data for use in reconstruction, e.g. --map_sampling=4")
	
	parser.add_option("--r1_body", dest="r1_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	
	parser.add_option("--r2_body", dest="r2_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	
	parser.add_option("--r3_body", dest="r3_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	
	parser.add_option("--r4_body", dest="r4_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	
	parser.add_option("--r5_body", dest="r5_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	
	parser.add_option("--border", dest="border", default=100,  type="int",
		help="Width of area at the image edge to exclude from image statistics, e.g. --border=100", metavar="int")
	
	parser.add_option("--clip_low", dest="clip_low", default=999999,  type="float",
		help="Lower threshold specified as a multiple of the standard deviation, e.g. --clip_low=3.5", metavar="float")

	parser.add_option("--clip_high", dest="clip_high", default=999999,  type="float",
		help="Upper threshold specified as a multiple of the standard deviation, e.g. --clip_high=3.5", metavar="float")
	
	parser.add_option("--thr_low", dest="thr_low", default=0,  type="float",
		help="Lower threshold specified as density values, e.g. --thr_low=1.5", metavar="float")

	parser.add_option("--thr_high", dest="thr_high", default=999999,  type="float",
		help="Upper threshold specified as density values, e.g. --thr_high=2.5", metavar="float")
	
	parser.add_option("--gradient", dest="gradient",  default="true",
		help="Enable linear gradient subtraction for preprocessing masks, e.g. --gradient=false")
	
	parser.add_option("--gradient_switch", dest="gradient_switch",  type="int",
		help="Enable linear gradient subtraction for preprocessing masks, e.g. --gradient_switch=3")
	
	parser.add_option("--iter_gradient", dest="iter_gradient",  default="true",
		help="Iterate gradient subtraction once, e.g. --iter_gradient=false")
	
	parser.add_option("--iter_gradient_switch", dest="iter_gradient_switch",  type="int",
		help="Iterate gradient subtraction once, e.g. --iter_gradient_switch=3")
	
	filters = ( "median", "gauss" )
	parser.add_option("--filter", dest="filter", type="choice", choices=filters, default="median",
		help="Preprocessing filter. Options are 'median' or 'gauss', e.g. --filter=median")
	
	parser.add_option("--kernel_x", dest="kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --kernel_x=5", metavar="int")

	parser.add_option("--r1_kernel_x", dest="r1_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r1_kernel_x=5", metavar="int")

	parser.add_option("--r2_kernel_x", dest="r2_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r2_kernel_x=5", metavar="int")

	parser.add_option("--r3_kernel_x", dest="r3_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r3_kernel_x=5", metavar="int")

	parser.add_option("--r4_kernel_x", dest="r4_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r4_kernel_x=5", metavar="int")

	parser.add_option("--r5_kernel_x", dest="r5_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r5_kernel_x=5", metavar="int")

	parser.add_option("--kernel_y", dest="kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --kernel_y=5", metavar="int")
	
	parser.add_option("--r1_kernel_y", dest="r1_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r1_kernel_y=5", metavar="int")
	
	parser.add_option("--r2_kernel_y", dest="r2_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r2_kernel_y=5", metavar="int")
	
	parser.add_option("--r3_kernel_y", dest="r3_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r3_kernel_y=5", metavar="int")
	
	parser.add_option("--r4_kernel_y", dest="r4_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r4_kernel_y=5", metavar="int")
	
	parser.add_option("--r5_kernel_y", dest="r5_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r5_kernel_y=5", metavar="int")
	
	parser.add_option("--radius_x", dest="radius_x",  type="float",
		help="Widths of the Gaussian function, e.g. --radius_x=5", metavar="float")

	parser.add_option("--radius_y", dest="radius_y",  type="float",
		help="Widths of the Gaussian function, e.g. --radius_y=5", metavar="float")
	
	parser.add_option("--grow", dest="grow",  type="int",
		help="Grow the selected regions in the binary mask by the specified number of pixels. int > 0, e.g. --grow=3", metavar="int")

	parser.add_option("--do_estimation", dest="do_estimation",  default="false",
		help="Estimate geometric parameters instead of using stored values from previous cycle, e.g. --do_estimation=false")

	parser.add_option("--max_correction", dest="max_correction",  type="float",  default=999999,
		help="Terminate alignment if correction exceeds specified value e.g. --max_correction=0.04", metavar="float")

	parser.add_option("--max_shift", dest="max_shift",  type="float",  default=999999,
		help="Terminate alignment if translational shift exceeds specified value e.g. --max_shift=100", metavar="float")

	parser.add_option("--image_apodization_x", dest="image_apodization_x",  type="float",  default=None,
		help="TODO, e.g. --image_apodization_x=10.0", metavar="float")

	parser.add_option("--image_apodization_y", dest="image_apodization_y",  type="float",  default=None,
		help="TODO, e.g. --image_apodization_y=10.0", metavar="float")

	parser.add_option("--reference_apodization_x", dest="reference_apodization_x",  type="float",  default=None,
		help="TODO, e.g. --reference_apodization_x=10.0", metavar="float")

	parser.add_option("--reference_apodization_y", dest="reference_apodization_y",  type="float",  default=None,
		help="TODO, e.g. --reference_apodization_y=10.0", metavar="float")

	correlation_modes = ( "xcf", "mcf", "pcf", "dbl" )
	parser.add_option("--corr_mode", dest="corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
		type="choice", choices=correlation_modes, default="mcf" )

	parser.add_option("--r1_corr_mode", dest="r1_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
		type="choice", choices=correlation_modes, default="mcf" )
	
	parser.add_option("--r2_corr_mode", dest="r2_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
		type="choice", choices=correlation_modes, default="mcf" )
	
	parser.add_option("--r3_corr_mode", dest="r3_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
		type="choice", choices=correlation_modes, default="mcf" )
	
	parser.add_option("--r4_corr_mode", dest="r4_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
		type="choice", choices=correlation_modes, default="mcf" )
	
	parser.add_option("--r5_corr_mode", dest="r5_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf", metavar="CorrMode",
		type="choice", choices=correlation_modes, default="mcf" )
	
	parser.add_option("--correlation_size_x", dest="correlation_size_x",  type="int",  default="128",
		help="X size of cross correlation peak image, e.g. --correlation_size_x=128", metavar="int")

	parser.add_option("--correlation_size_y", dest="correlation_size_y",  type="int",  default="128",
		help="Y size of cross correlation peak image, e.g. --correlation_size_y=128", metavar="int")
	
	parser.add_option("--peak_search_radius_x", dest="peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --peak_search_radius_x=19.0", metavar="float")

	parser.add_option("--r1_peak_search_radius_x", dest="r1_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r1_peak_search_radius_x=19.0", metavar="float")

	parser.add_option("--r2_peak_search_radius_x", dest="r2_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r2_peak_search_radius_x=19.0", metavar="float")

	parser.add_option("--r3_peak_search_radius_x", dest="r3_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r3_peak_search_radius_x=19.0", metavar="float")

	parser.add_option("--r4_peak_search_radius_x", dest="r4_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r4_peak_search_radius_x=19.0", metavar="float")

	parser.add_option("--r5_peak_search_radius_x", dest="r5_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r5_peak_search_radius_x=19.0", metavar="float")

	parser.add_option("--peak_search_radius_y", dest="peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --peak_search_radius_y=19.0", metavar="float")
	
	parser.add_option("--r1_peak_search_radius_y", dest="r1_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r1_peak_search_radius_y=19.0", metavar="float")
	
	parser.add_option("--r2_peak_search_radius_y", dest="r2_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r2_peak_search_radius_y=19.0", metavar="float")
	
	parser.add_option("--r3_peak_search_radius_y", dest="r3_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r3_peak_search_radius_y=19.0", metavar="float")
	
	parser.add_option("--r4_peak_search_radius_y", dest="r4_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r4_peak_search_radius_y=19.0", metavar="float")
	
	parser.add_option("--r5_peak_search_radius_y", dest="r5_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r5_peak_search_radius_y=19.0", metavar="float")
	
	parser.add_option("--translimit", dest="translimit",  type="float",  default=999999999,
		help="Discard alignment and keep original geometric parameters if translational shift, in pixels, exceeds specified value, e.g. --translimit=19.0", metavar="float")
	
	parser.add_option("--r1_cmdiameter_x", dest="r1_cmdiameter_x",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r1_cmdiameter_x=19.0", metavar="float")

	parser.add_option("--r2_cmdiameter_x", dest="r2_cmdiameter_x",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r2_cmdiameter_x=19.0", metavar="float")

	parser.add_option("--r3_cmdiameter_x", dest="r3_cmdiameter_x",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r3_cmdiameter_x=19.0", metavar="float")

	parser.add_option("--r4_cmdiameter_x", dest="r4_cmdiameter_x",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r4_cmdiameter_x=19.0", metavar="float")

	parser.add_option("--r5_cmdiameter_x", dest="r5_cmdiameter_x",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r5_cmdiameter_x=19.0", metavar="float")

	parser.add_option("--cmdiameter_y", dest="cmdiameter_y",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --cmdiameter_y=19.0", metavar="float")
	
	parser.add_option("--r1_cmdiameter_y", dest="r1_cmdiameter_y",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r1_cmdiameter_y=19.0", metavar="float")
	
	parser.add_option("--r2_cmdiameter_y", dest="r2_cmdiameter_y",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r2_cmdiameter_y=19.0", metavar="float")
	
	parser.add_option("--r3_cmdiameter_y", dest="r3_cmdiameter_y",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r3_cmdiameter_y=19.0", metavar="float")
	
	parser.add_option("--r4_cmdiameter_y", dest="r4_cmdiameter_y",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r4_cmdiameter_y=19.0", metavar="float")
	
	parser.add_option("--r5_cmdiameter_y", dest="r5_cmdiameter_y",  type="float",  default="100",
		help="Size of region for center of mass calculation, e.g. --r5_cmdiameter_y=19.0", metavar="float")
	
	parser.add_option("--r1_cmdiameter", dest="r1_cmdiameter",
		help="Size of region for center of mass calculation switch, e.g. --r1_cmdiameter=false",)
	
	parser.add_option("--r2_cmdiameter", dest="r2_cmdiameter",
		help="Size of region for center of mass calculation switch, e.g. --r2_cmdiameter=19.0",)
	
	parser.add_option("--r3_cmdiameter", dest="r3_cmdiameter",
		help="Size of region for center of mass calculation switch, e.g. --r3_cmdiameter=19.0",)
	
	parser.add_option("--r4_cmdiameter", dest="r4_cmdiameter",
		help="Size of region for center of mass calculation switch, e.g. --r4_cmdiameter=19.0",)
	
	parser.add_option("--r5_cmdiameter", dest="r5_cmdiameter",
		help="Size of region for center of mass calculation switch, e.g. --r5_cmdiameter=19.0",)
	
	parser.add_option("--slab", dest="slab", default="true",
		help="Adjust back-projection body size for a slab-like specimen, e.g. --slab=false")

	parser.add_option("--map_size_x", dest="map_size_x",  type="int",  default="1024",
		help="Size of the reconstructed tomogram in the X direction, e.g. --map_size_x=256", metavar="int")

	parser.add_option("--map_size_y", dest="map_size_y",  type="int",  default="1024",
		help="Size of the reconstructed tomogram in the Y direction, e.g. --map_size_y=256", metavar="int")

	parser.add_option("--map_size_z", dest="map_size_z",  type="int",  default="200",
		help="Size of the reconstructed tomogram in the Z direction, e.g. --map_size_z=128", metavar="int")
	
	parser.add_option("--map_lowpass_diameter_x", dest="map_lowpass_diameter_x",  type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --map_lowpass_diameter_x=0.5", metavar="float")
	
	parser.add_option("--map_lowpass_diameter_y", dest="map_lowpass_diameter_y",  type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --map_lowpass_diameter_y=0.5", metavar="float")
	
	parser.add_option("--image_file_type", dest="image_file_type",
		help="Filetype extension for images. Protomo supports CCP4, EM, FFF, IMAGIC, MRC, SPIDER, SUPRIM,and TIFF, e.g. --image_file_type=mrc")
	
	parser.add_option("--filename_prefix", dest="filename_prefix",  default="",
		help="Prefix for input and output files, with the exception of raw image files, which are specified in the geometry file, e.g. --filename_prefix=run1")
	
	parser.add_option('--cachedir', dest='cachedir', default="cache", help="Directory where cache files are stored")
	
	parser.add_option('--protomo_outdir', dest='protomo_outdir', default="out", help="Directory where other output files are stored")
	
	parser.add_option("--preprocessing", dest="preprocessing",  default="true",
		help="Enable/disable preprocessing of raw image files, e.g. --preprocessing=false")
	
	parser.add_option("--binning", dest="binning",  default="true",
		help="Enable/disable binning of raw image files, e.g. --binning=false")
	
	parser.add_option("--tilt_azimuth", dest="tilt_azimuth",  type="float",
		help='Override the tilt-azimuth as recorded in the database. Applied before alignment, e.g. --tilt_azimuth="-57"')
	
	parser.add_option("--azimuth_stability_check", dest="azimuth_stability_check", default=False,
		help='Check whether the tilt azimuth has deviated from the initial til azimuth, e.g. --azimuth_stability_check=True')
	
	parser.add_option("--azimuth_max_deviation", dest="azimuth_max_deviation",  type="float", default=5,
		help='Maximum +-deviation allowed for the tilt-azimuth during refinement, e.g. --azimuth_max_deviation=5')
	
	# parser.add_option("--select_images", dest="select_images",  default="0-999999",
	# 	help='Select specific images in the tilt-series, e.g. --select_images="1,2,5-7"')
	
	parser.add_option("--exclude_images", dest="exclude_images",  default="999999",
		help='Select specific images in the tilt-series to remove, e.g. --exclude_images="1,2,5-7"')
	
	parser.add_option("--exclude_images_by_angle", dest="exclude_images_by_angle",  default="",
		help='Select specific tilt angles in the tilt-series to remove, e.g. --exclude_images_by_angle="-37.5,4.2,27"')
	
	parser.add_option("--exclude_images_by_angle_accuracy", dest="exclude_images_by_angle_accuracy",  type="float",  default=0.05,
		help='How accurate must your requested image removal be, in degrees?, e.g. --exclude_images_by_angle_accuracy=0.01')
	
	parser.add_option("--logging", dest="logging",  default="true",
		help="Enable diagnostic terminal output, e.g. --logging=false")
	
	parser.add_option("--loglevel", dest="loglevel",  type="int",  default=2,
		help="Increase verbosity of diagnostic output where int > 0, e.g. --loglevel=2")
	
	parser.add_option("--window_area", dest="window_area",  type="float",  default=0.95,
		help="Fraction of extracted area that must lie within the source image. Real value between 0 and 1, e.g. --window_area=0.95")
		
	parser.add_option("--orientation", dest="orientation",  default="true",
		help="Include orientation angles in refinement, e.g. --orientation=false")
		
	parser.add_option("--orientation_switch", dest="orientation_switch",  type="int",
		help="Include orientation angles in refinement, e.g. --orientation_switch=3")
	
	parser.add_option("--azimuth", dest="azimuth",  default="true",
		help="Include tilt azimuth in refinement, e.g. --azimuth=false")
	
	parser.add_option("--azimuth_switch", dest="azimuth_switch",  type="int",
		help="Include tilt azimuth in refinement, e.g. --azimuth_switch=3")
	
	parser.add_option("--elevation", dest="elevation",  default="false",
		help="Include tilt axis elevation in refinement, e.g. --elevation=true")
	
	parser.add_option("--elevation_switch", dest="elevation_switch",  type="int",
		help="Include tilt axis elevation in refinement, e.g. --elevation_switch=3")
	
	parser.add_option("--rotation", dest="rotation",  default="true",
		help="Include in-plane rotations in refinement, e.g. --rotation=false")
	
	parser.add_option("--rotation_switch", dest="rotation_switch",  type="int",
		help="Include in-plane rotations in refinement, e.g. --rotation_switch=3")
	
	parser.add_option("--scale", dest="scale",  default="false",
		help="Include scale factors (magnification) in refinement, e.g. --scale=true")
	
	parser.add_option("--scale_switch", dest="scale_switch",  type="int",
		help="Include scale factors (magnification) in refinement, e.g. --scale_switch=3")
	
	parser.add_option("--norotations", dest="norotations",  default="false",
		help="Set in-plane rotations to zero instead of using stored values, e.g. --norotations=true")
	
	parser.add_option("--mask_width_x", dest="mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --mask_width_x=2")
	
	parser.add_option("--r1_mask_width_x", dest="r1_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r1_mask_width_x=2")
	
	parser.add_option("--r2_mask_width_x", dest="r2_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r2_mask_width_x=2")
	
	parser.add_option("--r3_mask_width_x", dest="r3_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r3_mask_width_x=2")
	
	parser.add_option("--r4_mask_width_x", dest="r4_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r4_mask_width_x=2")
	
	parser.add_option("--r5_mask_width_x", dest="r5_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r5_mask_width_x=2")
	
	parser.add_option("--mask_width_y", dest="mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --mask_width_y=2")
	
	parser.add_option("--r1_mask_width_y", dest="r1_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r1_mask_width_y=2")
	
	parser.add_option("--r2_mask_width_y", dest="r2_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r2_mask_width_y=2")
	
	parser.add_option("--r3_mask_width_y", dest="r3_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r3_mask_width_y=2")
	
	parser.add_option("--r4_mask_width_y", dest="r4_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r4_mask_width_y=2")
	
	parser.add_option("--r5_mask_width_y", dest="r5_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r5_mask_width_y=2")
	
	parser.add_option("--mask_apod_x", dest="mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --mask_apod_x=10")
	
	parser.add_option("--r1_mask_apod_x", dest="r1_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r1_mask_apod_x=10")
	
	parser.add_option("--r2_mask_apod_x", dest="r2_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r2_mask_apod_x=10")
	
	parser.add_option("--r3_mask_apod_x", dest="r3_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r3_mask_apod_x=10")
	
	parser.add_option("--r4_mask_apod_x", dest="r4_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r4_mask_apod_x=10")
	
	parser.add_option("--r5_mask_apod_x", dest="r5_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r5_mask_apod_x=10")
	
	parser.add_option("--mask_apod_y", dest="mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --mask_apod_y=10")
	
	parser.add_option("--r1_mask_apod_y", dest="r1_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r1_mask_apod_y=10")
	
	parser.add_option("--r2_mask_apod_y", dest="r2_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r2_mask_apod_y=10")
	
	parser.add_option("--r3_mask_apod_y", dest="r3_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r3_mask_apod_y=10")
	
	parser.add_option("--r4_mask_apod_y", dest="r4_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r4_mask_apod_y=10")
	
	parser.add_option("--r5_mask_apod_y", dest="r5_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r5_mask_apod_y=10")
	
	parser.add_option("--coarse", dest="coarse",  default=False,
		help="To perform an initial coarse alignment, set to 'True'. Requires gridsearch, corr, and mask options, e.g. --coarse=True")
	
	parser.add_option("--further_alignment", dest="further_alignment",  default=False,
		help="Iterate Coarse Alignment once?, e.g. --further_alignment=True")
	
	parser.add_option("--gridsearch_limit", dest="gridsearch_limit",  type="float",  default=2.0,
		help="Protomo2.4 only: Gridseach +-angle limit for coarse alignment. To do a translational alignment only set to 1 and set gridsearch_limit to 0, e.g. --gridsearch_limit=2.0", metavar="float")
		
	parser.add_option("--gridsearch_step", dest="gridsearch_step",  type="float",  default=0.1,
		help="Protomo2.4 only: Gridseach angle step size for coarse alignment, e.g. --gridsearch_step=0.5", metavar="float")
	
	parser.add_option("--create_tilt_video", dest="create_tilt_video",
		help="Appion: Create a tilt-series video for depiction, e.g. --create_tilt_video=false")
	
	parser.add_option("--create_reconstruction", dest="create_reconstruction",
		help="Appion: Create a reconstruction and video for depiction, e.g. --create_reconstruction=false")
	
	parser.add_option("--show_window_size", dest="show_window_size",  default="true",
		help="Appion: Show the window size used for alignment in the reconstruction video, e.g. --show_window_size=false")
	
	parser.add_option("--keep_recons", dest="keep_recons",
		help="Appion: Keep intermediate reconstruction files, e.g. --keep_recons=true")

	parser.add_option("--tilt_clip", dest="tilt_clip",  default="true",
		help="Appion: Clip pixel values for tilt-series video to +-5 sigma, e.g. --tilt_clip=false")
	
	parser.add_option("--video_type", dest="video_type",
		help="Appion: Create either gifs or html5 videos using 'gif' or 'html5vid', respectively, e.g. --video_type=html5vid")
	
	parser.add_option("--restart_cycle", dest="restart_cycle",  type="int",  default=0,
		help="Restart a Refinement at this iteration, e.g. --restart_cycle=2", metavar="int")
	
	parser.add_option("--restart_from_run", dest="restart_from_run",  default='',
		help="Run name (if in same Output directory) or full path (if not in same Output directory) of previously Refined Appion-Protomo run from which you wish to restart the Refinement using the current, new Run name and/or Output directory e.g. --restart_from_run=tiltseries0002")
	
	parser.add_option("--restart_from_iteration", dest="restart_from_iteration",  default=0,
		help="Refinement iteration of specified previously Refined Appion-Protomo run from which you would like to restart the Refinement, e.g. --restart_from_iteration=2", metavar="int")
	
	parser.add_option("--link", dest="link",  default="False",
		help="Link raw images if True, copy if False, e.g. --link=False (NOW OBSOLETE)")
	
	parser.add_option("--ctf_correct", dest="ctf_correct",  default="False",
		help="CTF correct images before dose compensation and before coarse alignment?, e.g. --ctf_correct=True")
	
	parser.add_option('--DefocusTol', dest='DefocusTol', type="int", default=200,
		help='Defocus tolerance in nanometers that limits the width of the strips, e.g. --DefocusTol=200')
	
	parser.add_option('--iWidth', dest='iWidth', type="int", default=20,
		help='The distance in pixels between the center lines of two consecutive strips, e.g. --iWidth=20')
	
	parser.add_option('--amp_contrast_ctf', dest='amp_contrast_ctf', type="float", default=0.07,
		help='Amplitude contrast used with CTF correction, e.g. --amp_contrast_ctf=0.07')
	
	parser.add_option("--dose_presets", dest="dose_presets",  default="False",
		help="Dose compensate using equation given by Grant & Grigorieff, 2015, e.g. --dose_presets=Moderate")
	
	parser.add_option('--dose_a', dest='dose_a', type="float",  default=0.245,
		help='\'a\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_a=0.2')
	
	parser.add_option('--dose_b', dest='dose_b', type="float",  default=-1.665,
		help='\'b\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_b=-1.5')
	
	parser.add_option('--dose_c', dest='dose_c', type="float",  default=2.81,
		help='\'c\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_c=2')
	
	parser.add_option('--defocus_estimate', dest='defocus_estimate', default="False",
		help='Estimate defocus of the untilted plane using TomoCTF?, e.g. --defocus_estimate=True')
	
	parser.add_option('--defocus', dest='defocus', type="float", default=3,
		help='Defocus for search (used in Express/Basic settings), in micrometers, e.g. --defocus=2.1')
	
	parser.add_option('--defocus_min', dest='defocus_min', type="float", default=0,
		help='Initial defocus for search, in micrometers, e.g. --defocus_min=2.1')
	
	parser.add_option('--defocus_max', dest='defocus_max', type="float", default=0,
		help='Maximum defocus for search, in micrometers, e.g. --defocus_max=4.2')
	
	parser.add_option('--defocus_difference', dest='defocus_difference', type="float",  default=0.2,
		help='Defocus difference for strip extraction, in micrometers, e.g. --defocus_difference=0.5')
	
	parser.add_option('--defocus_ang_negative', dest='defocus_ang_negative', type="float", default=-90,
		help='Negative angle, in degrees, beyond which images will be excluded before defocus estimation by TomoCTF, e.g. --defocus_ang_negative=-44')

	parser.add_option('--defocus_ang_positive', dest='defocus_ang_positive', type="float", default=90,
		help='Positive angle, in degrees, beyond which images will be excluded before defocus estimation by TomoCTF, e.g. --defocus_ang_positive=62')

	parser.add_option('--amp_contrast_defocus', dest='amp_contrast_defocus', type="float", default=0.07,
		help='Amplitude contrast used with defocus estimation, e.g. --amp_contrast_defocus=0.07')
	
	parser.add_option('--res_min', dest='res_min', type="float", default=10000,
		help='Lowest resolution information, in angstroms, to use to fit the signal falloff before defocus estimation, e.g. --res_min=200')
	
	parser.add_option('--res_max', dest='res_max', type="float", default=10,
		help='Highest resolution information, in angstroms, to use to fit the signal falloff before defocus estimation, e.g. --res_max=5')
	
	parser.add_option('--defocus_save', dest='defocus_save', type="float", default=0,
		help='Save this defocus value of the untilted tilt-series plane to the disk and make a plot of an estimated CTF at this defocus. defocus_save!=0 switches to estimation, =0 only saves, e.g. --defocus_save=3.8')

	parser.add_option("--commit", dest="commit",  default="False",
		help="Commit per-iteration information to database.")
	
	parser.add_option("--parallel", dest="parallel",  default="True",
		help="Parallelize image and video production.")
	
	parser.add_option("--frame_aligned", dest="frame_aligned",  default="True",
		help="Use frame-aligned images instead of naively summed images, if present.")
	
	parser.add_option("--serialem_stack", dest="serialem_stack",  default="",
		help="SerialEM stack to be prepared for upload to Appion")
	
	parser.add_option("--serialem_mdoc", dest="serialem_mdoc",  default="",
		help="SerialEM mdoc corresponding to the SerialEM stack to be prepared for upload to Appion")

	parser.add_option("--voltage", dest="voltage",
		help="Microscope coltage in keV. Used with SerialEM uploading")
	
	parser.add_option("--my_tlt", dest="my_tlt",  default="False",
		help="Allows for manual tilt-series setup")
	
	parser.add_option("--manual_alignment", dest="manual_alignment",  default="False",
		help="Interactive manual alignment.")
	
	parser.add_option("--manual_alignment_finished", dest="manual_alignment_finished",  default="False",
		help="Internal option.")
	
	parser.add_option("--change_refimg", dest="change_refimg",  default="False",
		help="Change the Protomo Reference image? e.g. --change_refimg=True")
	
	parser.add_option("--desired_ref_tilt_angle", dest="desired_ref_tilt_angle",  type="float",  default=0,
		help="Change the Protomo Reference image to be the image closest to this tilt angle, e.g. --desired_ref_tilt_angle=17")
	
	parser.add_option("--make_searchable", dest="make_searchable",  default="True",
		help="Hidden option. Places a .tiltseries.XXXX file in the rundir so that it will be found by Batch Summary webpages.")
	
	parser.add_option("--citations", dest="citations", action='store_true',
		help="Print citations list and exit.")
	
	options, args=parser.parse_args()
	
	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options


def runCmd(cmd):
	os.system(cmd)


if __name__ == '__main__':
	options=parseOptions()
	
	rundir=options.rundir
	seriesnumber = "%04d" % int(options.tiltseries)
	seriesname='series'+seriesnumber
	backup_tiltfilename=seriesname+'.tlt_backup'
	backup_tiltfilename_full=rundir+'/'+backup_tiltfilename
	tiltfilename=seriesname+'.tlt'
	tiltfilename_full=rundir+'/'+tiltfilename
	
	#If restart is also requested, make a dummy directory with the restart files (images and restart tlt)
	if (options.restart_from_run != '' and (options.restart_from_iteration > 0 or options.restart_from_iteration == 'Manual' or options.restart_from_iteration == 'manual')):
		if os.path.exists(options.restart_from_run):
			restart_path = options.restart_from_run
		elif os.path.exists(os.path.dirname(rundir)+'/'+options.restart_from_run):
			restart_path = os.path.dirname(rundir)+'/'+options.restart_from_run
		else:
			apDisplay.printError("Restart Refinement Run not found! Aborting Refinement!")
			sys.exit()
		
		if (options.restart_from_iteration == 'Manual' or options.restart_from_iteration == 'manual'):
			restart_tlt_file = restart_path + '/manual_' + seriesname + '.tlt'
		else:
			restart_seriesnumber = "%03d" % (int(options.restart_from_iteration) - 1)
			restart_seriesname = seriesname + restart_seriesnumber
			restart_tlt_file = restart_path + '/' + restart_seriesname + '.tlt'
		
		if os.path.exists(rundir):
			apDisplay.printWarning("%s already exists! Trying a different run directory:" % rundir)
			rundir=rundir+'b'
			if os.path.exists(rundir):
				apDisplay.printError("%s already exists too! Aborting! Choose a new 'Run directory'" % restart_path)
				sys.exit()
		
		if os.path.exists(restart_tlt_file):
			os.system('mkdir %s; cp %s %s' % (rundir, restart_tlt_file, tiltfilename_full))
			if (options.restart_from_iteration == 'Manual' or options.restart_from_iteration == 'manual'):
				apDisplay.printMsg("Restarting Refinement from %s after Manual Alignment" % os.path.basename(restart_path))
				os.system('touch %s/restarted_from_%s_manual_alignment' % (rundir, os.path.basename(restart_path)))
			else:
				apDisplay.printMsg("Restarting Refinement from %s  Iteration %d" % (os.path.basename(restart_path), int(options.restart_from_iteration)))
				os.system('touch %s/restarted_from_%s_iteration_%d' % (rundir, os.path.basename(restart_path), int(options.restart_from_iteration)))
			os.system('mkdir -p %s/raw/original/; ln %s/* %s/raw/ 2>/dev/null; ln %s/original/* %s/raw/original/' % (rundir, os.path.join(restart_path,'raw'), rundir, os.path.join(restart_path,'raw'), rundir))
			os.system('cp -r %s %s 2>/dev/null' % (os.path.join(restart_path,'media','dose_compensation'), os.path.join(rundir,'media')))
			os.system('mkdir %s/defocus_estimation/; cp -r %s/defocus_estimation/* %s/defocus_estimation/ 2>/dev/null' % (rundir, restart_path, rundir))
		else:
			apDisplay.printError("Restart Refinement Iteration not found! Aborting Refinement!")
			sys.exit()
	else:
		#Different starting tilt files
		if options.starting_tlt_file == "Coarse_Iter_1":
			coarse1_tlt_file = 'coarse_'+seriesname+'.tlt'
			coarse1_tlt_filefull = rundir+'/'+coarse1_tlt_file
			os.system('cp %s %s' % (coarse1_tlt_filefull, tiltfilename_full))
		elif options.starting_tlt_file == "Coarse_Iter_2":
			coarse2_tlt_file = 'coarse_'+seriesname+'_iter2.tlt'
			coarse2_tlt_filefull = rundir+'/'+coarse2_tlt_file
			os.system('cp %s %s' % (coarse2_tlt_filefull, tiltfilename_full))
		elif options.starting_tlt_file == "Imod_Coarse":
			imod_tlt_file = 'imod_coarse_'+seriesname+'.tlt'
			imod_tlt_filefull = rundir+'/'+imod_tlt_file
			os.system("cp %s %s" % (imod_tlt_filefull, tiltfilename_full))
		elif options.starting_tlt_file == "Manual":
			manual_tlt_file = 'manual_'+seriesname+'.tlt'
			manual_tlt_filefull = rundir+'/'+manual_tlt_file
			os.system('cp %s %s' % (manual_tlt_filefull, tiltfilename_full))
		elif (options.starting_tlt_file == "More_Manual") or (options.starting_tlt_file == "MoreManual"):
			manual_tlt_file = 'more_manual_'+seriesname+'.tlt'
			if not os.path.isfile(rundir+'/'+manual_tlt_file):
				apDisplay.printWarning("%s file not found," % manual_tlt_file)
				manual_tlt_file = 'more_manual_coarse_'+seriesname+'.tlt'
				apDisplay.printWarning("Switching to %s" % manual_tlt_file)
			manual_tlt_filefull = rundir+'/'+manual_tlt_file
			os.system('cp %s %s' % (manual_tlt_filefull, tiltfilename_full))
		elif options.starting_tlt_file == "Initial":
			original_tlt_file = rundir+'/'+'original.tlt'
			os.system('cp %s %s' % (original_tlt_file, tiltfilename_full))
		else:
			pass
	
	#Generate new individual commands
	thicknesses = options.thicknesses.split(',')
	alignment_commands = []
	new_rundirs = []
	for thickness in thicknesses:
		input_command = 'protomo2aligner.py '
		for key in options.__dict__:
			if options.__dict__[key] != None:
				if key == 'thicknesses':
					input_command += '--thickness=%s ' % thickness
				elif key == 'runname':
					new_runname = options.__dict__[key] + '_thick' + thickness
					input_command += '--runname=%s ' % new_runname
				elif key == 'rundir':
					new_rundir = options.__dict__[key] + '_thick' + thickness
					new_rundirs.append(new_rundir)
					input_command += '--rundir=%s ' % new_rundir
				elif key == 'description':
					new_description = "\"%s\"" % options.__dict__[key]
					input_command += '--description=%s ' % new_description
				elif key == 'restart_from_run':
					pass
				elif key == 'restart_from_iteration':
					pass
				elif key == 'starting_tlt_file':
					if (options.restart_from_run != '' and options.restart_from_iteration > 0):
						input_command += '--starting_tlt_file=My_tlt_file '
					else:
						input_command += '--%s=%s ' % (key, options.__dict__[key])
				else:
					input_command += '--%s=%s ' % (key, options.__dict__[key])
		input_command += '--from_multirefine=True'
		alignment_commands.append(input_command)
	
	#Set up new directories
	apDisplay.printMsg("Setting up directories for runs with differing thicknesses...")
	for new_rundir in new_rundirs:
		os.system('mkdir -p %s/raw/original/ 2>/dev/null; ln %s/raw/original/* %s/raw/original/ 2>/dev/null; cp %s/raw/* %s/raw/ 2>/dev/null; cp %s %s/%s; ln %s/restarted_from_* %s 2>/dev/null; mkdir %s/defocus_estimation/; cp -r %s/defocus_estimation/* %s/defocus_estimation/ 2>/dev/null; mkdir -p %s/media/dose_compensation/; cp -r %s/media/dose_compensation/* %s/media/dose_compensation/ 2>/dev/null; mkdir -p %s/media/max_drift/; cp -r %s/media/max_drift/* %s/media/max_drift/ 2>/dev/null' % (new_rundir, rundir, new_rundir, rundir, new_rundir, tiltfilename_full, new_rundir, tiltfilename, rundir, new_rundir, new_rundir, rundir, new_rundir, new_rundir, rundir, new_rundir, new_rundir, rundir, new_rundir))
		
	#If restart is also requested, delete the dummy directory
	if (options.restart_from_run != '' and options.restart_from_iteration > 0):
		if os.path.exists(options.restart_from_run):
			restart_path = options.restart_from_run
		elif os.path.exists(os.path.dirname(rundir)+'/'+options.restart_from_run):
			restart_path = os.path.dirname(rundir)+'/'+options.restart_from_run
		else:
			apDisplay.printError("It's logically impossible to reach this statement.")
			sys.exit()
		os.system('rm -rf %s' % rundir)
	
	#Run refinements
	apDisplay.printMsg("\033[1m|------------------------------------------------|\033[0m")
	if len(str(len(options.thicknesses.split(',')))) == 1:
		apDisplay.printMsg("\033[1m| Beginning Multi-Refinement with %d Thicknesses  |\033[0m" % len(options.thicknesses.split(',')))
	elif len(str(len(options.thicknesses.split(',')))) == 2:
		apDisplay.printMsg("\033[1m| Beginning Multi-Refinement with %d Thicknesses |\033[0m" % len(options.thicknesses.split(',')))
	else:
		apDisplay.printError("More than 99 thicknesses were inputted. This will almost certainly break your computer. Aborting!")
		sys.exit()
	apDisplay.printMsg("\033[1m| (this may overload your computer, be careful!) |\033[0m")
	apDisplay.printMsg("\033[1m|------------------------------------------------|\033[0m")
	for command in alignment_commands:
		p = mp.Process(target=runCmd, args=(command,))
		p.start()
		time.sleep(2)
	[p.join() for p in mp.active_children()]
	
