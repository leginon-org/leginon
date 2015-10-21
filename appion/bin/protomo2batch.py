#!/usr/bin/env python
# 
# This script allows the user to process tilt-series in batch through Protomo.
# It is highly recommended that this script be run using commands generated
# through the Appion-Protomo web interface.

from __future__ import division
import os
import sys
import glob
import time
import optparse
import subprocess
import numpy as np
import multiprocessing as mp
from pyami import mrc
from appionlib import apDisplay
from appionlib import apProTomo2Aligner
from scipy.ndimage.interpolation import rotate as imrotate

try:
	import protomo
except:
	apDisplay.printWarning("Protomo did not get imported. Alignment and reconstruction functionality won't work.")

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--sessionname', dest='sessionname',
		help= 'Session date, e.g. --sessionname=14sep04a')
	parser.add_option('--runname', dest='runname',
		help= 'Name of protmorun directory as made by Appion, e.g. --runname=batchrun1')
	parser.add_option('--projectid', dest='projectid',
		help= 'Project id, e.g. --projectid=20')
	parser.add_option('--jobtype', dest='jobtype',
		help= 'Appion jobtype')
	parser.add_option('--expid', dest='expid',
		help= 'Appion experiment id, e.g. --expid=8514')
	parser.add_option('--DefocusTol', dest='DefocusTol', type="int", default=200,
		help= 'Defocus tolerance in nanometers that limits the width of the strips, e.g. --DefocusTol=200')
	parser.add_option('--iWidth', dest='iWidth', type="int", default=20,
		help= 'The distance in pixels between the center lines of two consecutive strips, e.g. --iWidth=20')
	parser.add_option('--voltage', dest='voltage', type="int",
		help= 'Microscope voltage in keV, e.g. --voltage=300')
	parser.add_option('--cs', dest='cs', type="float",
		help= 'Microscope spherical abberation, e.g. --cs=2.7')
	parser.add_option('--amp_contrast', dest='amp_contrast', type="float", default=0.07,
		help= 'Amplitude contrast, e.g. --amp_contrast=0.07')
	parser.add_option('--rundir', dest='rundir',
		help= 'Base run directory where all tiltseriesXXXX folders will be made, e.g. /path/to/protomodir/')
	parser.add_option('--tiltseriesranges', dest='tiltseriesranges',
		help= 'Range of tilt-series numbers to be processed. Should be in a comma/hyphen-separated list, e.g. 3,4,6-10')
	parser.add_option('--numtiltseries', dest='numtiltseries',
		help= 'Number of tilt-series in the session, e.g. --numtiltseries=42')
	parser.add_option("--link", dest="link",  default=True,
		help="Link raw images if True, copy if False, e.g. --link=False")
	parser.add_option("--procs", dest="procs", default=1,
		help="Number of processors to use, 'all' defaults to use all processors on running machine e.g. --procs=4")
	parser.add_option("--coarse_param_file", dest="coarse_param_file",
		help="External Coarse Alignment param file. e.g. --coarse_param_file=/path/to/coarse.param", metavar="FILE")
	parser.add_option("--refine_param_file", dest="refine_param_file",
		help="External Refinement param file. e.g. --refine_param_file=/path/to/refine.param", metavar="FILE")
	parser.add_option("--recon_param_file", dest="recon_param_file",
		help="External Recnostruction param file. e.g. --recon_param_file=/path/to/recon.param", metavar="FILE")
	parser.add_option("--pixelsize", dest="pixelsize", type="float",
		help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
	parser.add_option("--sampling", dest="sampling",  default="8", type="int",
		help="Sampling rate of raw data, e.g. --sampling=4")
	parser.add_option("--map_sampling", dest="map_sampling",  default="8", type="int",
		help="Sampling rate of raw data for use in reconstruction, e.g. --map_sampling=4")
	parser.add_option("--image_file_type", dest="image_file_type",  default="mrc",
		help="Filetype extension for images. Protomo supports CCP4, EM, FFF, IMAGIC, MRC, SPIDER, SUPRIM,and TIFF, e.g. --image_file_type=mrc")
	parser.add_option("--prep_files", dest="prep_files",  default="False",
		help="Access leginondb to create tlt file and link/copy raw images, e.g. --prep_files=False")
	parser.add_option("--coarse_align", dest="coarse_align",  default="False",
		help="Perform coarse alignment, e.g. --coarse_align=False")
	parser.add_option("--refine", dest="refine",  default="False",
		help="Perform refinement, e.g. --refine=True")
	parser.add_option("--reconstruct", dest="reconstruct",  default="False",
		help="Perform reconstruction, e.g. --reconstruct=True")
	parser.add_option("--all_tilt_videos", dest="all_tilt_videos",  default=False,
		help="Make tilt-series depiction videos for every iteration if True, e.g. --all_tilt_videos=False")
	parser.add_option("--all_recon_videos", dest="all_recon_videos",  default=False,
		help="Make reconstruction depiction videos for every iteration if True, e.g. --all_recon_videos=False")
	parser.add_option("--coarse_retry_align", dest="coarse_retry_align",  type="int",  default="10",
		help="Number of times to retry coarse alignment, which sometimes fails because the search area is too big, e.g. --coarse_retry_align=5", metavar="int")
	parser.add_option("--coarse_retry_shrink", dest="coarse_retry_shrink",  type="float",  default="0.9",
		help="How much to shrink the window size from the previous retry, e.g. --coarse_retry_shrink=0.75", metavar="float")
	parser.add_option("--refine_retry_align", dest="refine_retry_align",  type="int",  default="12",
		help="Number of times to retry refinement, which sometimes fails because the search area is too big, e.g. --refine_retry_align=5", metavar="int")
	parser.add_option("--refine_retry_shrink", dest="refine_retry_shrink",  type="float",  default="0.9",
		help="How much to shrink the window size from the previous retry, e.g. --refine_retry_shrink=0.75", metavar="float")
	parser.add_option("--video_type", dest="video_type",  default="html5vid",
		help="Appion: Create either gifs or html5 videos using 'gif' or 'html5vid', respectively, e.g. --video_type=html5vid")
	parser.add_option("--restart_cycle", dest="restart_cycle",
		help="Restart a Refinement at this iteration, e.g. --restart_cycle=2 or --restart_cycle=best")	
	parser.add_option('--shift_limit', dest='shift_limit', type='float', metavar='float',
		help='Percentage of image size, above which shifts with higher shifts will be discarded for all images, e.g. --shift_limit=50')
	parser.add_option('--angle_limit', dest='angle_limit', type='float', metavar='float',
		help='Only remove images from the tilt file greater than abs(angle_limit), e.g. --angle_limit=35')
	parser.add_option('--dimx', dest='dimx', type='int', metavar='int',
		help='Dimension (x) of micrographs, e.g. --dimx=4096')
	parser.add_option('--dimy', dest='dimy', type='int', metavar='int',
		help='Dimension (y) of micrographs, e.g. --dimy=4096')
	parser.add_option("--region_x", dest="region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --region_x=1024", metavar="int")
	parser.add_option("--region_y", dest="region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --region_y=1024", metavar="int")
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
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r1_lowpass_diameter_x", dest="r1_lowpass_diameter_x",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r2_lowpass_diameter_x", dest="r2_lowpass_diameter_x",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r3_lowpass_diameter_x", dest="r3_lowpass_diameter_x",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r4_lowpass_diameter_x", dest="r4_lowpass_diameter_x",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r5_lowpass_diameter_x", dest="r5_lowpass_diameter_x",  default=0.5, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
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
	parser.add_option("--thickness", dest="thickness",  default=300, type="float",
	        help="Estimated thickness of unbinned specimen (in pixels), e.g. --thickness=100.0", metavar="float")
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
	parser.add_option("--r1_sampling", dest="r1_sampling",  default=8, type="int",
		help="Sampling rate of raw data, e.g. --r1_sampling=4")
	parser.add_option("--r2_sampling", dest="r2_sampling",  default=6, type="int",
		help="Sampling rate of raw data, e.g. --r2_sampling=4")
	parser.add_option("--r3_sampling", dest="r3_sampling",  default=4, type="int",
		help="Sampling rate of raw data, e.g. --r3_sampling=4")
	parser.add_option("--r4_sampling", dest="r4_sampling",  default=2, type="int",
		help="Sampling rate of raw data, e.g. --r4_sampling=4")
	parser.add_option("--r5_sampling", dest="r5_sampling",  default=1, type="int",
		help="Sampling rate of raw data, e.g. --r5_sampling=4")
	parser.add_option("--gradient", dest="gradient",  default="true",
		help="Enable linear gradient subtraction for preprocessing masks, e.g. --gradient=false")
	parser.add_option("--gradient_switch", dest="gradient_switch",  type="int",
		help="Enable linear gradient subtraction for preprocessing masks, e.g. --gradient_switch=3")
	parser.add_option("--iter_gradient", dest="iter_gradient",  default="true",
		help="Iterate gradient subtraction once, e.g. --iter_gradient=false")
	parser.add_option("--iter_gradient_switch", dest="iter_gradient_switch",  type="int",
		help="Iterate gradient subtraction once, e.g. --iter_gradient_switch=3")
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
	parser.add_option("--show_window_size", dest="show_window_size", default="true",
		help="Appion: Show the window size used for alignment in the reconstruction video, e.g. --show_window_size=false")
	parser.add_option("--tilt_clip", dest="tilt_clip",  default="true",
		help="Appion: Clip pixel values for tilt-series video to +-5 sigma, e.g. --tilt_clip=false")
	parser.add_option("--refresh_i3t", dest="refresh_i3t",  default="False",
		help="If a Protomo run is interrupted the i3t file may be unusable. This option removes the i3t file so that protomoRefine can create a new one, e.g. --refresh_i3t=True")
	parser.add_option("--fix_images", dest="fix_images",  default="False",
		help="Internal use only")
	parser.add_option("--screening_mode", dest="screening_mode",  default="False",
		help="Protomo Screening Mode to be run during data collection. This mode will continually query leginon database for tilt-series number N+1. When tilt-series N+1 shows up, tilt-series N will be processed through coarse alignment, producing normal depiction videos. Screening mode is configured to parallelize video production just like is done in protomo2aligner.py. The coarse_param_file option must be set., e.g. --screening_mode=True")
	parser.add_option("--screening_start", dest="screening_start",  default=1,
		help="Which tilt-series number will screening mode begin on?, e.g. --screening_start=10")
	parser.add_option("--ctf_correct", dest="ctf_correct",  default="False",
		help="CTF correct images using ctf correction runs from Appion, e.g. --ctf_correct=True")
	parser.add_option("--firststep", dest="firststep",  default=1,
		help="First step in the Appion-Protomo batch workflow, e.g. --firststep=2")
	parser.add_option("--laststep", dest="laststep",  default=3,
		help="Last step in the Appion-Protomo batch workflow, e.g. --laststep=4")
	parser.add_option("--automation", dest="automation",  default="False",
		help="Full Automation Mode, e.g. --automation=True")
	parser.add_option("--auto_prep", dest="auto_prep",  default="False",
		help="Full Automation Mode, e.g. --auto_prep=True")
	parser.add_option("--auto_ctf_correct", dest="auto_ctf_correct",  default="False",
		help="Full Automation Mode, e.g. --auto_ctf_correct=True")
	parser.add_option("--auto_coarse_align", dest="auto_coarse_align",  default="False",
		help="Full Automation Mode, e.g. --auto_coarse_align=True")
	parser.add_option("--auto_refine", dest="auto_refine",  default="False",
		help="Full Automation Mode, e.g. --auto_refine=True")
	parser.add_option("--auto_reconstruct", dest="auto_reconstruct",  default="False",
		help="Full Automation Mode, e.g. --auto_reconstruct=True")
	parser.add_option("--auto_r1_iters", dest="auto_r1_iters", default=1, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r1_iters=4", metavar="int")
	parser.add_option("--auto_r2_iters", dest="auto_r2_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r2_iters=4", metavar="int")
	parser.add_option("--auto_r3_iters", dest="auto_r3_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r3_iters=4", metavar="int")
	parser.add_option("--auto_r4_iters", dest="auto_r4_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r4_iters=4", metavar="int")
	parser.add_option("--auto_r5_iters", dest="auto_r5_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r5_iters=4", metavar="int")
	parser.add_option("--auto_r6_iters", dest="auto_r6_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r6_iters=4", metavar="int")
	parser.add_option("--auto_r7_iters", dest="auto_r7_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r7_iters=4", metavar="int")
	parser.add_option("--auto_r8_iters", dest="auto_r8_iters", default=0, type="int",
		help="Full Automation Mode. Number of alignment and geometry refinement iterations, e.g. --auto_r8_iters=4", metavar="int")
	parser.add_option("--auto_r1_sampling", dest="auto_r1_sampling",  default=8, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r1_sampling=4")
	parser.add_option("--auto_r2_sampling", dest="auto_r2_sampling",  default=6, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r2_sampling=4")
	parser.add_option("--auto_r3_sampling", dest="auto_r3_sampling",  default=4, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r3_sampling=4")
	parser.add_option("--auto_r4_sampling", dest="auto_r4_sampling",  default=2, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r4_sampling=4")
	parser.add_option("--auto_r5_sampling", dest="auto_r5_sampling",  default=1, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r5_sampling=4")
	parser.add_option("--auto_r6_sampling", dest="auto_r6_sampling",  default=4, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r6_sampling=4")
	parser.add_option("--auto_r7_sampling", dest="auto_r7_sampling",  default=2, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r7_sampling=4")
	parser.add_option("--auto_r8_sampling", dest="auto_r8_sampling",  default=1, type="int",
		help="Full Automation Mode. Sampling rate of raw data, e.g. --auto_r8_sampling=4")
	parser.add_option("--auto_convergence", dest="auto_convergence",  default=0.015, type="float",
	        help="Full Automation Mode. Convergence criteria for stopping alignment, e.g. --auto_convergence=0.02", metavar="float")
	parser.add_option("--auto_convergence_iters", dest="auto_convergence_iters",  default=5, type="int",
	        help="Full Automation Mode. Number of iterations to proceed with once convergence is met, e.g. --auto_convergence_iters=2", metavar="int")
	parser.add_option("--auto_elevation", dest="auto_elevation",  default="True",
		help="Full Automation Mode. Turn on elevation if convergence wasn't reached, e.g. --auto_elevation=True")
	parser.add_option("--auto_scaling", dest="auto_scaling",  default="True",
		help="Full Automation Mode. Turn on scaling if convergence wasn't reached, e.g. --auto_scaling=True")
	
	options, args=parser.parse_args()
	
	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options


def variableSetup(rundir, tiltseriesnumber, prep):
	"""
	Sets up commonly used variables in other functions.
	"""
	tiltdirname="/tiltseries%04d" % (tiltseriesnumber)
	tiltdir=rundir+tiltdirname
	seriesnumber = "%04d" % tiltseriesnumber
	seriesname = 'series'+str(seriesnumber)
	tiltfilename = seriesname+'.tlt'
	tiltfilename_full=tiltdir+'/'+tiltfilename
	raw_path = os.path.join(tiltdir,'raw')
	if (prep is "True"):
		os.system("mkdir -p %s" % tiltdir)
		rawimagecount=0
	else:
		cmd="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(rawimagecount, err) = proc.communicate()
		rawimagecount=int(rawimagecount)
	
	return tiltdirname, tiltdir, seriesnumber, seriesname, tiltfilename, tiltfilename_full, raw_path, rawimagecount


def editParamFile(tiltdir, param_full, raw_path):
	"""
	Edit param file to replace pathlist, cachedir, and outdir.
	"""
	newcachedir=tiltdir+'/cache'
	newoutdir=tiltdir+'/out'
	command1="grep -n 'pathlist' %s | awk '{print $1}' | sed 's/://'" % (param_full)
	proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
	(pathlistline, err) = proc.communicate()
	pathlistline=int(pathlistline)
	command2="grep -n 'cachedir' %s | awk '{print $1}' | sed 's/://'" % (param_full)
	proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
	(cachedirline, err) = proc.communicate()
	cachedirline=int(cachedirline)
	command3="grep -n 'outdir' %s | awk '{print $1}' | sed 's/://'" % (param_full)
	proc=subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True)
	(outdirline, err) = proc.communicate()
	outdirline=int(outdirline)
	command11="sed -i \'%ss|.*| pathlist: \"%s\"  (* AP path to raw directory *)|\' %s" % (pathlistline, raw_path, param_full)
	os.system(command11)
	command22="sed -i \'%ss|.*| cachedir: \"%s\"  (* AP directory where cache files are stored *)|\' %s" % (cachedirline, newcachedir, param_full)
	os.system(command22)
	command33="sed -i \'%ss|.*| outdir: \"%s\"  (* AP directory where other output files are stored *)|\' %s" % (outdirline, newoutdir, param_full)
	os.system(command33)


def countDirs(rundir, count_dir):
	"""
	Counts the number of numbered directories in rundir name 'count_dir01-99'.
	"""
	num_count_dirs=0
	for i in range(1,100):
		d=count_dir+"%02d" % i
		dirname=rundir+'/'+d
		if os.path.isdir(dirname):
			num_count_dirs+=1
		else:
			break
	
	return num_count_dirs


def protomoFixFrameMrcs(tiltseriesnumber, options):
	"""
	Reads raw image mrcs into pyami and writes them back out. No transforms. This fixes a Protomo issue.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(options.rundir, tiltseriesnumber, prep="False")
	
	apProTomo2Aligner.fixImages(raw_path)
	
	apDisplay.printMsg("Done fixing mrcs for Tilt-Series #%s" % tiltseriesnumber)	


def protomoPrep(tiltseriesnumber, prep_options):
	"""
	Creates tiltseries directory, links/copies raw images, and creates series*.tlt file.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(prep_options.rundir, tiltseriesnumber, prep="True")
	
	apProTomo2Prep.prepareTiltFile(prep_options.sessionname, seriesname, tiltfilename_full, tiltseriesnumber, raw_path, prep_options.link, coarse="True")
	
	cmd="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(rawimagecount, err) = proc.communicate()
	rawimagecount=int(rawimagecount)
	
	if (prep_options.all_tilt_videos == "True"):
		apDisplay.printMsg("Creating initial tilt-series video...")
		apProTomo2Aligner.makeTiltSeriesVideos(seriesname, 0, tiltfilename_full, rawimagecount, tiltdir, raw_path, prep_options.pixelsize, prep_options.map_sampling, prep_options.image_file_type, prep_options.video_type, "False", "Initial")
	
	#Removing highly shifted images
	bad_images, bad_kept_images=apProTomo2Aligner.removeHighlyShiftedImages(tiltfilename_full, prep_options.dimx, prep_options.dimy, prep_options.shift_limit, prep_options.angle_limit)
	if bad_images:
		apDisplay.printMsg('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.' % (bad_images, prep_options.shift_limit))
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, prep_options.angle_limit))
	else:
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, prep_options.angle_limit))
		apDisplay.printMsg('No images were removed from the .tlt file due to high shifts.')
	
	apDisplay.printMsg("Finished Preparing Files and Directories for Tilt-Series #%s." % (tiltseriesnumber))
	

def protomoCoarseAlign(tiltseriesnumber, coarse_options):
	"""
	Performs Protomo gridsearch alignment, then prepares files for refinement.
	Correlation peak video is made.
	Depiction videos are made if requested.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(coarse_options.rundir, tiltseriesnumber, prep="False")
	os.chdir(tiltdir)
	name='coarse_'+seriesname
	cpparam="cp %s %s/%s.param" % (coarse_options.coarse_param_file,tiltdir,name)
	os.system(cpparam)
	coarse_param_full=tiltdir+'/'+name+'.param'
	editParamFile(tiltdir, coarse_param_full, raw_path)
	
	apDisplay.printMsg('Starting Protomo Coarse Alignment')
	coarse_seriesparam=protomo.param(coarse_param_full)
	coarse_seriesgeom=protomo.geom(tiltfilename_full)
	try:
		series=protomo.series(coarse_seriesparam,coarse_seriesgeom)
		#Align and restart alignment if failed
		retry=0
		new_region_x=coarse_options.region_x/coarse_options.sampling   #Just initializing
		new_region_y=coarse_options.region_y/coarse_options.sampling   #Just initializing
		while (retry <= coarse_options.coarse_retry_align):
			try:
				if (retry > 0):
					new_region_x = int(new_region_x*coarse_options.coarse_retry_shrink)
					new_region_y = int(new_region_y*coarse_options.coarse_retry_shrink)
					apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, 100-int(100*coarse_options.coarse_retry_shrink), new_region_x, new_region_y))
					newsize = "{ %s %s }" % (new_region_x, new_region_y)
					series.setparam("window.size", newsize)
				retry+=1
				series.align()
				final_retry=retry-1
				retry = coarse_options.coarse_retry_align + 1 #Alignment worked, don't retry anymore
			except:
				if (retry > coarse_options.coarse_retry_align):
					apDisplay.printMsg("Coarse Alignment failed after rescaling the search area %s time(s)." % (retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*coarse_options.sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*coarse_options.sampling))
					apDisplay.printMsg("Put values less than these into thesponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n")
				pass
		
		corrfile=name+'.corr'
		series.corr(corrfile)
		
		#archive results
		tiltfile=name+'.tlt'
		series.geom(1).write(tiltfile)
		
		cleanup="mkdir %s/coarse_out; cp %s/coarse*.* %s/coarse_out; rm %s/*.corr; mv %s/%s.tlt %s/coarse_out/initial_%s.tlt; cp %s/%s.tlt %s/%s.tlt" % (tiltdir, tiltdir, tiltdir, tiltdir, tiltdir, seriesname, tiltdir, seriesname, tiltdir, name, tiltdir, seriesname)
		os.system(cleanup)
	except:
		apDisplay.printMsg("Alignment failed. Skipping Tilt-Series #%s...\n" % (tiltseriesnumber))
		return
	os.system('touch %s/.tiltseries.%04d' % (coarse_options.rundir, tiltseriesnumber))
	
	apDisplay.printMsg("Creating Coarse Alignment Depictions")
	apProTomo2Aligner.makeCorrPeakVideos(name, 0, tiltdir, 'out', coarse_options.video_type, "Coarse")
	if (coarse_options.all_tilt_videos == "True"):
		apDisplay.printMsg("Creating Coarse Alignment tilt-series video...")
		apProTomo2Aligner.makeTiltSeriesVideos(seriesname, 0, tiltfile, rawimagecount, tiltdir, raw_path, coarse_options.pixelsize, coarse_options.map_sampling, coarse_options.image_file_type, coarse_options.video_type, "False", "Coarse")
	if (coarse_options.all_recon_videos == "True"):
		apDisplay.printMsg("Generating Coarse Alignment reconstruction...")
		series.mapfile()
		apProTomo2Aligner.makeReconstructionVideos(name, 0, tiltdir, 'out', coarse_options.pixelsize, coarse_options.sampling, coarse_options.map_sampling, coarse_options.video_type, "false", "False", align_step="Coarse")
		
		
def protomoRefine(tiltseriesnumber, refine_options):
	"""
	Performs Protomo area matching alignment.
	Correlation peak videos are made.
	Depiction videos are made if requested.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(refine_options.rundir, tiltseriesnumber, prep="False")
	os.chdir(tiltdir)
	name=seriesname
	cpparam="cp %s %s/%s.param" % (refine_options.refine_param_file,tiltdir,name)
	os.system(cpparam)
	refine_param_full=tiltdir+'/'+name+'.param'
	editParamFile(tiltdir, refine_param_full, raw_path)
	start=0  #Counter for prevous iterations
	i3tfile=tiltdir+'/'+seriesname+'.i3t'
	if refine_options.refresh_i3t == "True":
		os.system("rm %s" % i3tfile)
		tiltfilename=max(glob.iglob('*.tlt'), key=os.path.getctime)
		tiltfilename_full=tiltdir+'/'+tiltfilename
	refine_seriesparam=protomo.param(refine_param_full)
	if os.path.exists(i3tfile):
		series=protomo.series(refine_seriesparam)
	else:
		refine_seriesgeom=protomo.geom(tiltfilename_full)
		series=protomo.series(refine_seriesparam, refine_seriesgeom)
	
	#figure out starting number
	previters=glob.glob(name+'*.corr')
	if len(previters) > 0:
		previters.sort()
		lastiter=previters[-1]
		start=int(lastiter.split(name)[1].split('.')[0])+1
	
	#rewind to previous iteration if requested
	if (type(refine_options.restart_cycle) == int):
		apDisplay.printMsg("Rewinding to iteration %s" % (refine_options.restart_cycle))
		start=refine_options.restart_cycle
		series.setcycle(start-1)
	elif (refine_options.restart_cycle == 'best'):
		del series
		tiltfilename_full=tiltdir+'/'+name+'.tlt'
		best=glob.glob('best*')
		best=int(os.path.splitext(best[0])[1][1:])-1
		best_iteration="%03d" % best
		apDisplay.printMsg("Restarting using geometry information from iteration %s" % (best+1))
		qadir=tiltdir+'/media/quality_assessment/'
		#Move best .tlt file to series####.tlt. Move quality assessments, best tlt, corr, corrplots, corr video, tilt video, and recon video to tiltdir/media/quality_assessment/run##/
		num_run_dirs=countDirs(qadir, 'run')+1
		run_number="%02d" % num_run_dirs
		old_run_dir=qadir+'/run'+run_number+'/'
		os.system('mkdir %s' % old_run_dir)
		best_tlt=tiltdir+'/'+name+best_iteration+'.tlt'
		best_corr=tiltdir+'/'+name+best_iteration+'.corr'
		best_corr_plots=tiltdir+'/media/corrplots/'+name+best_iteration+'*'
		best_corr_video=tiltdir+'/media/correlations/'+name+best_iteration+'*'
		best_tilt_video=tiltdir+'/media/tiltseries/'+name+best_iteration+'*'
		best_recon_video=tiltdir+'/media/reconstructions/'+name+best_iteration+'*'
		cmd='cp %s %s; mv %s %s;' % (best_tlt, tiltfilename_full, best_tlt, old_run_dir)
		cmd+='mv best* %s; mv worst* %s;' % (old_run_dir, old_run_dir)
		cmd+='mv %s %s;' % (best_corr, old_run_dir)
		cmd+='mv %s %s;' % (best_corr_plots, old_run_dir)
		cmd+='mv %s %s;' % (best_corr_video, old_run_dir)
		cmd+='mv %s %s 2>/dev/null;' % (best_tilt_video, old_run_dir)
		cmd+='mv %s %s 2>/dev/null;' % (best_recon_video, old_run_dir)
		cmd+='mv media/quality_assessment/%s* %s;' % (name, old_run_dir)
		cmd+='rm %s[0,1,2,3,4,5,6,7,8,9]* %s cache/%s* 2>/dev/null;' % (name, i3tfile, name)
		cmd+='rm -r media/tiltseries/ media/reconstructions/ 2>/dev/null'
		os.system(cmd)
		
		start=0
		refine_seriesgeom=protomo.geom(tiltfilename_full)
		series=protomo.series(refine_seriesparam, refine_seriesgeom)
		
	
	# Get map sizes and map sampling from recon .param file so that the refinement reconstructions can be scaled properly for each iteration.
	cmd1="awk '/AP reconstruction map size/{print $3}' %s | sed 's/,//g'" % (refine_options.recon_param_file)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(recon_map_size_x, err) = proc.communicate()
	recon_map_size_x=int(recon_map_size_x)
	cmd2="awk '/AP reconstruction map size/{print $4}' %s | sed 's/,//g'" % (refine_options.recon_param_file)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(recon_map_size_y, err) = proc.communicate()
	recon_map_size_y=int(recon_map_size_y)
	cmd3="awk '/AP reconstruction map size/{print $5}' %s | sed 's/,//g'" % (refine_options.recon_param_file)
	proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
	(recon_map_size_z, err) = proc.communicate()
	recon_map_size_z=int(recon_map_size_z)
	cmd4="awk '/AP reconstruction map sampling/{print $2}' %s" % (refine_options.recon_param_file)
	proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
	(recon_map_sampling, err) = proc.communicate()
	recon_map_sampling=int(recon_map_sampling)

	iters=refine_options.r1_iters+refine_options.r2_iters+refine_options.r3_iters+refine_options.r4_iters+refine_options.r5_iters
	round1={"window.size":"{ %s %s }" % (refine_options.r1_region_x,refine_options.r1_region_y),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r1_lowpass_diameter_x,refine_options.r1_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r1_lowpass_diameter_x,refine_options.r1_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r1_lowpass_apod_x,refine_options.r1_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r1_highpass_apod_x,refine_options.r1_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r1_highpass_diameter_x,refine_options.r1_highpass_diameter_y),"sampling":"%s" % (refine_options.r1_sampling),"map.sampling":"%s" % (refine_options.r1_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r1_kernel_x,refine_options.r1_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r1_peak_search_radius_x,refine_options.r1_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r1_mask_width_x,refine_options.r1_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r1_mask_width_x,refine_options.r1_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r1_mask_apod_x,refine_options.r1_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r1_mask_apod_x,refine_options.r1_mask_apod_y)}#,"map.size":"{ %s, %s, %s }" % (refine_options.r1_mask_apod_x,refine_options.r1_mask_apod_y)}			
	round2={"window.size":"{ %s %s }" % (refine_options.r2_region_x,refine_options.r2_region_y),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r2_lowpass_diameter_x,refine_options.r2_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r2_lowpass_diameter_x,refine_options.r2_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r2_lowpass_apod_x,refine_options.r2_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r2_highpass_apod_x,refine_options.r2_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r2_highpass_diameter_x,refine_options.r2_highpass_diameter_y),"sampling":"%s" % (refine_options.r2_sampling),"map.sampling":"%s" % (refine_options.r2_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r2_kernel_x,refine_options.r2_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r2_peak_search_radius_x,refine_options.r2_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r2_mask_width_x,refine_options.r2_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r2_mask_width_x,refine_options.r2_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r2_mask_apod_x,refine_options.r2_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r2_mask_apod_x,refine_options.r2_mask_apod_y)}
	round3={"window.size":"{ %s %s }" % (refine_options.r3_region_x,refine_options.r3_region_y),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r3_lowpass_diameter_x,refine_options.r3_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r3_lowpass_diameter_x,refine_options.r3_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r3_lowpass_apod_x,refine_options.r3_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r3_highpass_apod_x,refine_options.r3_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r3_highpass_diameter_x,refine_options.r3_highpass_diameter_y),"sampling":"%s" % (refine_options.r3_sampling),"map.sampling":"%s" % (refine_options.r3_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r3_kernel_x,refine_options.r3_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r3_peak_search_radius_x,refine_options.r3_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r3_mask_width_x,refine_options.r3_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r3_mask_width_x,refine_options.r3_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r3_mask_apod_x,refine_options.r3_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r3_mask_apod_x,refine_options.r3_mask_apod_y)}
	round4={"window.size":"{ %s %s }" % (refine_options.r4_region_x,refine_options.r4_region_y),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r4_lowpass_diameter_x,refine_options.r4_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r4_lowpass_diameter_x,refine_options.r4_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r4_lowpass_apod_x,refine_options.r4_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r4_highpass_apod_x,refine_options.r4_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r4_highpass_diameter_x,refine_options.r4_highpass_diameter_y),"sampling":"%s" % (refine_options.r4_sampling),"map.sampling":"%s" % (refine_options.r4_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r4_kernel_x,refine_options.r4_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r4_peak_search_radius_x,refine_options.r4_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r4_mask_width_x,refine_options.r4_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r4_mask_width_x,refine_options.r4_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r4_mask_apod_x,refine_options.r4_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r4_mask_apod_x,refine_options.r4_mask_apod_y)}
	round5={"window.size":"{ %s %s }" % (refine_options.r5_region_x,refine_options.r5_region_y),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r5_lowpass_diameter_x,refine_options.r5_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r5_lowpass_diameter_x,refine_options.r5_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r5_lowpass_apod_x,refine_options.r5_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r5_highpass_apod_x,refine_options.r5_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r5_highpass_diameter_x,refine_options.r5_highpass_diameter_y),"sampling":"%s" % (refine_options.r5_sampling),"map.sampling":"%s" % (refine_options.r5_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r5_kernel_x,refine_options.r5_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r5_peak_search_radius_x,refine_options.r5_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r5_mask_width_x,refine_options.r5_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r5_mask_width_x,refine_options.r5_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r5_mask_apod_x,refine_options.r5_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r5_mask_apod_x,refine_options.r5_mask_apod_y)}
	switches={"preprocess.mask.gradient":{"%s" % (refine_options.gradient):refine_options.gradient_switch},"preprocess.mask.iter":{"%s" % (refine_options.iter_gradient):refine_options.iter_gradient_switch},"fit.orientation":{"%s" % (refine_options.orientation):refine_options.orientation_switch},"fit.azimuth":{"%s" % (refine_options.azimuth):refine_options.azimuth_switch},"fit.elevation":{"%s" % (refine_options.elevation):refine_options.elevation_switch},"fit.rotation":{"%s" % (refine_options.rotation):refine_options.rotation_switch},"fit.scale":{"%s" % (refine_options.scale):refine_options.scale_switch}}
	
	for n in range(start,iters):
		#change parameters depending on rounds
		if (n+1 <= start+refine_options.r1_iters):
			r=1  #Round number
			region_x=refine_options.r1_region_x
			region_y=refine_options.r1_region_y
			sampling=refine_options.r1_sampling
			for val in round1:
				series.setparam(val,round1[val])
		elif (n+1 == start+refine_options.r1_iters+1):
			r=2
			region_x=refine_options.r2_region_x
			region_y=refine_options.r2_region_y
			sampling=refine_options.r2_sampling
			for val in round2:
				series.setparam(val,round2[val])
		elif (n+1 == start+refine_options.r1_iters+refine_options.r2_iters+1):
			r=3
			region_x=refine_options.r3_region_x
			region_y=refine_options.r3_region_y
			sampling=refine_options.r3_sampling
			for val in round3:
				series.setparam(val,round3[val])
		elif (n+1 == start+refine_options.r1_iters+refine_options.r2_iters+refine_options.r3_iters+1):
			r=4
			region_x=refine_options.r4_region_x
			region_y=refine_options.r4_region_y
			sampling=refine_options.r4_sampling
			for val in round4:
				series.setparam(val,round4[val])
		elif (n+1 == start+refine_options.r1_iters+refine_options.r2_iters+refine_options.r3_iters+refine_options.r4_iters+1):
			r=5
			region_x=refine_options.r5_region_x
			region_y=refine_options.r5_region_y
			sampling=refine_options.r5_sampling
			for val in round5:
				series.setparam(val,round5[val])
		
		#change parameters depending on switches
		for switch in switches:
			for key in switches[switch]:
				if (switches[switch][key] == n+1-start):
					if (key == "true"):
						newval="false"
					else:
						newval="true"
					series.setparam(switch,newval)
		
		apDisplay.printMsg("Beginning Iteration #%s, Round #%s\n" % (start+n+1,r))
		#print "after:";series.setparam('map.sampling');series.setparam('sampling');
		#Align and restart alignment if failed
		retry=0
		brk=0
		new_region_x=region_x/sampling   #Just initializing
		new_region_y=region_y/sampling   #Just initializing
		while (retry <= refine_options.refine_retry_align):
			try:
				if (retry > 0):
					new_region_x = int(new_region_x*refine_options.refine_retry_shrink)
					new_region_y = int(new_region_y*refine_options.refine_retry_shrink)
					apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, 100-int(100*refine_options.refine_retry_shrink), new_region_x*sampling, new_region_y*sampling))
					newsize = "{ %s %s }" % (new_region_x, new_region_y)
					series.setparam("window.size", newsize)
				retry+=1
				series.align()
				final_retry=retry-1
				retry = refine_options.refine_retry_align + 1 #Alignment worked, don't retry anymore
			except:
				if (retry > refine_options.refine_retry_align):
					apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
					brk=1
				pass

		apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement!\n" % (start+n+1,r))
		if (brk == 1):   #resampling failed, break out of all refinement iterations
			break
		it="%03d" % ((n+start))
		itt="%02d" % ((n+start+1))
		#ite="_ite%03d" % ((n+start))
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		series.corr(corrfile)
		series.fit()
		series.update()

		#archive results
		tiltfile=basename+'.tlt'
		series.geom(0).write(tiltfile)
		tiltfilename_full=tiltdir+tiltfile
		
		#Produce quality assessment statistics and plot image using corrfile information
		apDisplay.printMsg("Creating quality assessment statistics...")
		numcorrfiles=len(glob.glob1(tiltdir,'*.corr'))
		for i in range(numcorrfiles):
			it="%03d" % (i)
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, corrfile)
			if i == numcorrfiles-1:
				apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, refine_options.sessionname, name, tiltdir, refine_options.r1_iters, refine_options.r1_sampling, refine_options.r2_iters, refine_options.r2_sampling, refine_options.r3_iters, refine_options.r3_sampling, refine_options.r4_iters, refine_options.r4_sampling, refine_options.r5_iters, refine_options.r5_sampling)
		it="%03d" % ((n+start))
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		
		apDisplay.printMsg("Creating Refinement Depictions")
		apProTomo2Aligner.makeCorrPeakVideos(name, it, tiltdir, 'out', refine_options.video_type, "Refinement")  #Correlation peak videos are always made.
		apProTomo2Aligner.makeCorrPlotImages(name, it, tiltdir, corrfile)  #Correlation plots are always made.
		if (refine_options.all_tilt_videos == "True"):  #Tilt series videos are only made if requested
			apDisplay.printMsg("Creating Refinement tilt-series video...")
			apProTomo2Aligner.makeTiltSeriesVideos(name, it, tiltfilename_full, rawimagecount, tiltdir, raw_path, refine_options.pixelsize, refine_options.map_sampling, refine_options.image_file_type, refine_options.video_type, "False", "Refinement")
		if (refine_options.all_recon_videos == "True"):  #Reconstruction videos are only made if requested
			apDisplay.printMsg("Generating Refinement reconstruction...")
			#Rescale if necessary
			s='r%s_sampling' % r
			sparam="refine_options.%s" % s
			if refine_options.map_sampling != sparam:
				new_map_sampling='%s' % self.params['map_sampling']
				series.setparam("sampling",new_map_sampling)
				series.setparam("map.sampling",new_map_sampling)
			series.mapfile()
			apProTomo2Aligner.makeReconstructionVideos(name, itt, tiltdir, 'out', refine_options.pixelsize, refine_options.sampling, refine_options.map_sampling, refine_options.video_type, "false", "False", align_step="Refinement")
	
	apDisplay.printMsg("Refinement Finished for Tilt-Series #%s!" % tiltseriesnumber)
	

def protomoReconstruct(tiltseriesnumber, recon_options):
	"""
	Reconstruct a tilt-series by back pojection.
	Options are given to specify which iteration to reconstruct
	from and whether to exclude any very high tilts.
	Options are given for filtering.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(recon_options.rundir, tiltseriesnumber, prep="False")
	os.chdir(tiltdir)
	


def protomoAutoRefine(tiltseriesnumber, auto_refine_options, CCMS):
	"""
	Performs Protomo area matching alignment automatically until convergence.
	Correlation peak videos are made.
	Depiction videos are made for best iteration after convergence.
	"""
	def saveBestIterationFromRoundAndCleanup(options, rnd, tiltdir, tiltfilename_full, name):
		best=glob.glob('best*')
		best=int(os.path.splitext(best[0])[1][1:])-1
		best_iteration="%03d" % best
		apDisplay.printMsg("Iteration #%s from Round #%s will be used to begin Round #%s." % (best+1, rnd-1, rnd))
		qadir=tiltdir+'/media/quality_assessment/'
		#Move best .tlt file to series####.tlt. Move quality assessments, best tlt, corr, corrplots, corr video, tilt video, and recon video to tiltdir/media/quality_assessment/run##/
		num_run_dirs=countDirs(qadir, 'run')+1
		run_number="%02d" % num_run_dirs
		old_run_dir=qadir+'/run'+run_number+'/'
		os.system('mkdir %s' % old_run_dir)
		i3tfile=tiltdir+'/'+name+'.i3t'
		best_tlt=tiltdir+'/'+name+best_iteration+'.tlt'
		best_corr=tiltdir+'/'+name+best_iteration+'.corr'
		best_corr_plots=tiltdir+'/media/corrplots/'+name+best_iteration+'*'
		cmd='cp %s %s; mv %s %s;' % (best_tlt, tiltfilename_full, best_tlt, old_run_dir)
		cmd+='mv best* %s; mv worst* %s;' % (old_run_dir, old_run_dir)
		cmd+='mv %s %s;' % (best_corr, old_run_dir)
		cmd+='ln %s %s;' % (best_corr_plots, old_run_dir)
		cmd+='mv media/quality_assessment/%s* %s;' % (name, old_run_dir)
		cmd+='rm %s[0,1,2,3,4,5,6,7,8,9]* %s cache/%s* 2>/dev/null;' % (name, i3tfile, name)
		cmd+='rm -r media/tiltseries/ media/reconstructions/ 2>/dev/null'
		os.system(cmd)
	
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(auto_refine_options.rundir, tiltseriesnumber, prep="False")
	os.chdir(tiltdir)
	name=seriesname
	corrdir=tiltdir+'/media/quality_assessment/auto_corr_files/'
	os.system("mkdir -p %s" % corrdir)
	cpparam="cp %s %s/%s.param" % (auto_refine_options.refine_param_file,tiltdir,name)
	os.system(cpparam)
	refine_param_full=tiltdir+'/'+name+'.param'
	editParamFile(tiltdir, refine_param_full, raw_path)
	start=0  #Counter for prevous iterations
	countdown=0  #Counter for iterations to do after convergence has been reached.
	convergence=0  #Switched to convergence=1 is convergence is reached.
	i3tfile=tiltdir+'/'+seriesname+'.i3t'
	refine_seriesparam=protomo.param(refine_param_full)
	if os.path.exists(i3tfile):
		series=protomo.series(refine_seriesparam)
	else:
		refine_seriesgeom=protomo.geom(tiltfilename_full)
		series=protomo.series(refine_seriesparam, refine_seriesgeom)
	
	# Get region sizes refine .param file so that the refinement downscaled properly if necessary.
	cmd1="awk '/AP orig window/{print $4}' %s | sed 's/,//g'" % (refine_param_full)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(region_x, err) = proc.communicate()
	region_x=int(region_x)
	cmd2="awk '/AP orig window/{print $5}' %s | sed 's/,//g'" % (refine_param_full)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(region_y, err) = proc.communicate()
	region_y=int(region_y)
	
	#First 3 rounds are processed without stopping for convergence.
	firstiters=auto_refine_options.auto_r1_iters+auto_refine_options.auto_r2_iters+auto_refine_options.auto_r3_iters
	
	for n in range(start,firstiters):
		#change parameters depending on rounds
		if (n+1 <= start+auto_refine_options.auto_r1_iters):
			r=1  #Round number
			sampling=auto_refine_options.auto_r1_sampling
			series.setparam('sampling','%s' % sampling)
			series.setparam('map.sampling','%s' % sampling)
		elif (n+1 == start+auto_refine_options.auto_r1_iters+1):
			r=2
			sampling=auto_refine_options.auto_r2_sampling
			del series
			saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
			
			refine_seriesgeom=protomo.geom(tiltfilename_full)
			series=protomo.series(refine_seriesparam, refine_seriesgeom)
			series.setparam('sampling','%s' % sampling)
			series.setparam('map.sampling','%s' % sampling)
		elif (n+1 == start+auto_refine_options.auto_r1_iters+auto_refine_options.auto_r2_iters+1):
			r=3
			sampling=auto_refine_options.auto_r3_sampling
			del series
			saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
			
			refine_seriesgeom=protomo.geom(tiltfilename_full)
			series=protomo.series(refine_seriesparam, refine_seriesgeom)
			series.setparam('sampling','%s' % sampling)
			series.setparam('map.sampling','%s' % sampling)

		apDisplay.printMsg("Beginning Iteration #%s, Round #%s for Tilt-Series #%s\n" % (start+n+1, r, tiltseriesnumber))
		
		#Align and restart alignment if failed
		retry=0
		brk=0
		new_region_x=region_x/sampling   #Just initializing
		new_region_y=region_y/sampling   #Just initializing
		while (retry <= auto_refine_options.refine_retry_align):
			try:
				if (retry > 0):
					new_region_x = int(new_region_x*auto_refine_options.refine_retry_shrink)
					new_region_y = int(new_region_y*auto_refine_options.refine_retry_shrink)
					apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, 100-int(100*auto_refine_options.refine_retry_shrink), new_region_x*sampling, new_region_y*sampling))
					newsize = "{ %s %s }" % (new_region_x, new_region_y)
					series.setparam("window.size", newsize)
				retry+=1
				series.align()
				final_retry=retry-1
				retry = auto_refine_options.refine_retry_align + 1 #Alignment worked, don't retry anymore
			except:
				if (retry > auto_refine_options.refine_retry_align):
					apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
					brk=1
				pass

		apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement for Tilt-Series #%s!\n" % (start+n+1, r, tiltseriesnumber))
		if (brk == 1):   #resampling failed, break out of all refinement iterations
			break
		it="%03d" % ((n+start))
		itt="%02d" % ((n+start+1))
		#ite="_ite%03d" % ((n+start))
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		series.corr(corrfile)
		series.fit()
		series.update()

		#archive results
		tiltfile=basename+'.tlt'
		series.geom(0).write(tiltfile)
		
		apDisplay.printMsg("Creating quality assessment statistics...")
		numcorrfiles=len(glob.glob1(corrdir,'*.corr'))
		auto_it="%03d" % numcorrfiles
		auto_corrfile_basename="%s%s" % (name, auto_it)
		auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
		cmd="cp %s %s" % (corrfile, auto_corrfile)
		os.system(cmd)
		for i in range(numcorrfiles+1):
			it="%03d" % (i)
			auto_corrfile_basename="%s%s" % (name, it)
			auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
			metric=apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, auto_corrfile)
			if i == numcorrfiles:
				best,best_CCMS=apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, auto_refine_options.sessionname, name, tiltdir, auto_refine_options.auto_r1_iters, auto_refine_options.auto_r1_sampling, auto_refine_options.auto_r2_iters, auto_refine_options.auto_r2_sampling, auto_refine_options.auto_r3_iters, auto_refine_options.auto_r3_sampling, auto_refine_options.auto_r4_iters, auto_refine_options.auto_r4_sampling, auto_refine_options.auto_r5_iters, auto_refine_options.auto_r5_sampling, auto_refine_options.auto_r6_iters, auto_refine_options.auto_r6_sampling, auto_refine_options.auto_r7_iters, auto_refine_options.auto_r7_sampling, auto_refine_options.auto_r8_iters, auto_refine_options.auto_r8_sampling)
		
		auto_it="%03d" % numcorrfiles
		auto_corrfile_basename="%s%s" % (name, auto_it)
		auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
		apProTomo2Aligner.makeCorrPlotImages(name, auto_it, tiltdir, auto_corrfile)  #Correlation plots are always made.
		
		apDisplay.printMsg("CCMS = %s for Iteration #%s of Tilt-Series #%s." % (round(metric,5), start+n+1, tiltseriesnumber))
		
	#Next 2 rounds are checked for convergence.
	nextiters=auto_refine_options.auto_r4_iters+auto_refine_options.auto_r5_iters
	
	for n in range(start+firstiters+1, start+firstiters+1+nextiters):
		#change parameters depending on rounds
		if (n+1 == start+firstiters+1):
			r=4  #Round number
			sampling=auto_refine_options.auto_r4_sampling
			del series
			saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
			
			refine_seriesgeom=protomo.geom(tiltfilename_full)
			series=protomo.series(refine_seriesparam, refine_seriesgeom)
			series.setparam('sampling','%s' % sampling)
			series.setparam('map.sampling','%s' % sampling)
		elif (n+1 == start+firstiters+auto_refine_options.auto_r4_iters+1):
			r=5
			sampling=auto_refine_options.auto_r5_sampling
			del series
			saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
			
			refine_seriesgeom=protomo.geom(tiltfilename_full)
			series=protomo.series(refine_seriesparam, refine_seriesgeom)
			series.setparam('sampling','%s' % sampling)
			series.setparam('map.sampling','%s' % sampling)

		apDisplay.printMsg("Beginning Iteration #%s, Round #%s for Tilt-Series #%s\n" % (start+n+1, r, tiltseriesnumber))
		
		#Align and restart alignment if failed
		retry=0
		brk=0
		new_region_x=region_x/sampling   #Just initializing
		new_region_y=region_y/sampling   #Just initializing
		while (retry <= auto_refine_options.refine_retry_align):
			try:
				if (retry > 0):
					new_region_x = int(new_region_x*auto_refine_options.refine_retry_shrink)
					new_region_y = int(new_region_y*auto_refine_options.refine_retry_shrink)
					apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, 100-int(100*auto_refine_options.refine_retry_shrink), new_region_x*sampling, new_region_y*sampling))
					newsize = "{ %s %s }" % (new_region_x, new_region_y)
					series.setparam("window.size", newsize)
				retry+=1
				series.align()
				final_retry=retry-1
				retry = auto_refine_options.refine_retry_align + 1 #Alignment worked, don't retry anymore
			except:
				if (retry > auto_refine_options.refine_retry_align):
					apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
					brk=1
				pass

		apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement for Tilt-Series #%s!\n" % (start+n+1, r, tiltseriesnumber))
		if (brk == 1):   #resampling failed, break out of all refinement iterations
			break
		it="%03d" % ((n+start))
		itt="%03d" % ((n+start+1))
		#ite="_ite%03d" % ((n+start))
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		series.corr(corrfile)
		series.fit()
		series.update()

		#archive results
		tiltfile=basename+'.tlt'
		series.geom(0).write(tiltfile)
		
		apDisplay.printMsg("Creating quality assessment statistics...")
		numcorrfiles=len(glob.glob1(corrdir,'*.corr'))
		auto_it="%03d" % numcorrfiles
		auto_corrfile_basename="%s%s" % (name, auto_it)
		auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
		cmd="cp %s %s" % (corrfile, auto_corrfile)
		os.system(cmd)
		for i in range(numcorrfiles+1):
			it="%03d" % (i)
			auto_corrfile_basename="%s%s" % (name, it)
			auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
			metric=apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, auto_corrfile)
			if i == numcorrfiles:
				best,best_CCMS=apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, auto_refine_options.sessionname, name, tiltdir, auto_refine_options.auto_r1_iters, auto_refine_options.auto_r1_sampling, auto_refine_options.auto_r2_iters, auto_refine_options.auto_r2_sampling, auto_refine_options.auto_r3_iters, auto_refine_options.auto_r3_sampling, auto_refine_options.auto_r4_iters, auto_refine_options.auto_r4_sampling, auto_refine_options.auto_r5_iters, auto_refine_options.auto_r5_sampling)
		
		auto_it="%03d" % numcorrfiles
		auto_corrfile_basename="%s%s" % (name, auto_it)
		auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
		apProTomo2Aligner.makeCorrPlotImages(name, auto_it, tiltdir, auto_corrfile)  #Correlation plots are always made.
		
		apDisplay.printMsg("CCMS = %s for Iteration #%s of Tilt-Series #%s." % (round(metric,5), start+n+1, tiltseriesnumber))
		
		#Check if convergence has been reached.
		if (metric <= auto_refine_options.auto_convergence and countdown == 0):  #Convergence reached. Begin iteration countdown!
			convergence=1
			countdown=auto_refine_options.auto_convergence_iters
			apDisplay.printMsg("Alignment for Tilt-Series #%s has converged! Processing %s more iterations..." % (tiltseriesnumber, countdown))
		elif countdown != 0:  #T-minus...
			countdown-=1
		elif (convergence == 1 and countdown == 0):  #Convergence was reached and extra iterations have processed. Stop alignment.
			break
		
	#Check if convergence was ever reached
	if (convergence == 0 and countdown == 0):  #Convergence was not reached. Turn on elevation and/or scaling and run more iterations!
		apDisplay.printMsg("Alignment for Tilt-Series #%s has not yet converged. Best CCMS Value was %s." % (tiltseriesnumber, round(best_CCMS,5)))
		
		finaliters=auto_refine_options.auto_r6_iters+auto_refine_options.auto_r7_iters+auto_refine_options.auto_r8_iters
		if (auto_refine_options.auto_scaling == "True" and auto_refine_options.auto_elevation == "True"):
			apDisplay.printMsg("Scaling and Elevation will be turned on for %s more iterations for Tilt-Series #%s using the best iteration from the previous %s iterations." % (finaliters, tiltseriesnumber, firstiters+nextiters))
			scaling="true"; elevation="true"
		elif (auto_refine_options.auto_scaling == "True" and auto_refine_options.auto_elevation == "False"):
			apDisplay.printMsg("Scaling will be turned on and Elevation will be turned off for %s more iterations for Tilt-Series #%s using the best iteration from the previous %s iterations." % (finaliters, tiltseriesnumber, firstiters+nextiters))
			scaling="true"; elevation="false"
		elif (auto_refine_options.auto_scaling == "False" and auto_refine_options.auto_elevation == "True"):
			apDisplay.printMsg("Scaling will be turned off and Elevation will be turned on for %s more iterations for Tilt-Series #%s using the best iteration from the previous %s iterations." % (finaliters, tiltseriesnumber, firstiters+nextiters))
			scaling="false"; elevation="true"
		else:
			apDisplay.printMsg("Scaling and Elevation will be turned off for %s more iterations for Tilt-Series #%s using the best iteration from the previous %s iterations." % (finaliters, tiltseriesnumber, firstiters+nextiters))
			scaling="false"; elevation="false"
			
		for n in range(start,firstiters):
			#change parameters depending on rounds
			if (n+1 <= start+auto_refine_options.auto_r6_iters):
				r=6  #Round number
				sampling=auto_refine_options.auto_r6_sampling
				del series
				saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
				
				refine_seriesgeom=protomo.geom(tiltfilename_full)
				series=protomo.series(refine_seriesparam, refine_seriesgeom)
				series.setparam('sampling','%s' % sampling)
				series.setparam('map.sampling','%s' % sampling)
				series.setparam('fit.elevation','%s' % elevation)
				series.setparam('fit.scale','%s' % scaling)
			elif (n+1 == start+auto_refine_options.auto_r6_iters+1):
				r=7
				sampling=auto_refine_options.auto_r7_sampling
				del series
				saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
				
				refine_seriesgeom=protomo.geom(tiltfilename_full)
				series=protomo.series(refine_seriesparam, refine_seriesgeom)
				series.setparam('sampling','%s' % sampling)
				series.setparam('map.sampling','%s' % sampling)
				series.setparam('fit.elevation','%s' % elevation)
				series.setparam('fit.scale','%s' % scaling)
			elif (n+1 == start+auto_refine_options.auto_r6_iters+auto_refine_options.auto_r7_iters+1):
				r=8
				sampling=auto_refine_options.auto_r8_sampling
				del series
				saveBestIterationFromRoundAndCleanup(auto_refine_options, r, tiltdir, tiltfilename_full, name)
				
				refine_seriesgeom=protomo.geom(tiltfilename_full)
				series=protomo.series(refine_seriesparam, refine_seriesgeom)
				series.setparam('sampling','%s' % sampling)
				series.setparam('map.sampling','%s' % sampling)
				series.setparam('fit.elevation','%s' % elevation)
				series.setparam('fit.scale','%s' % scaling)
	
			apDisplay.printMsg("Beginning Iteration #%s, Round #%s for Tilt-Series #%s\n" % (start+n+1, r, tiltseriesnumber))
			
			#Align and restart alignment if failed
			retry=0
			brk=0
			new_region_x=region_x/sampling   #Just initializing
			new_region_y=region_y/sampling   #Just initializing
			while (retry <= auto_refine_options.refine_retry_align):
				try:
					if (retry > 0):
						new_region_x = int(new_region_x*auto_refine_options.refine_retry_shrink)
						new_region_y = int(new_region_y*auto_refine_options.refine_retry_shrink)
						apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, 100-int(100*auto_refine_options.refine_retry_shrink), new_region_x*sampling, new_region_y*sampling))
						newsize = "{ %s %s }" % (new_region_x, new_region_y)
						series.setparam("window.size", newsize)
					retry+=1
					series.align()
					final_retry=retry-1
					retry = auto_refine_options.refine_retry_align + 1 #Alignment worked, don't retry anymore
				except:
					if (retry > auto_refine_options.refine_retry_align):
						apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
						apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
						apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
						apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
						brk=1
					pass
	
			apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement for Tilt-Series #%s!\n" % (start+n+1, r, tiltseriesnumber))
			if (brk == 1):   #resampling failed, break out of all refinement iterations
				break
			it="%03d" % ((n+start))
			itt="%03d" % ((n+start+1))
			#ite="_ite%03d" % ((n+start))
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			series.corr(corrfile)
			series.fit()
			series.update()
	
			#archive results
			tiltfile=basename+'.tlt'
			series.geom(0).write(tiltfile)
			
			apDisplay.printMsg("Creating quality assessment statistics...")
			numcorrfiles=len(glob.glob1(corrdir,'*.corr'))
			auto_it="%03d" % numcorrfiles
			auto_corrfile_basename="%s%s" % (name, auto_it)
			auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
			cmd="cp %s %s" % (corrfile, auto_corrfile)
			os.system(cmd)
			for i in range(numcorrfiles+1):
				it="%03d" % (i)
				auto_corrfile_basename="%s%s" % (name, it)
				auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
				metric=apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, auto_corrfile)
				if i == numcorrfiles:
					best,best_CCMS=apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, sessionname, name, tiltdir, auto_refine_options.auto_r1_iters, auto_refine_options.auto_r1_sampling, auto_refine_options.auto_r2_iters, auto_refine_options.auto_r2_sampling, auto_refine_options.auto_r3_iters, auto_refine_options.auto_r3_sampling, auto_refine_options.auto_r4_iters, auto_refine_options.auto_r4_sampling, auto_refine_options.auto_r5_iters, auto_refine_options.auto_r5_sampling, auto_refine_options.auto_r6_iters, auto_refine_options.auto_r6_sampling, auto_refine_options.auto_r7_iters, auto_refine_options.auto_r7_sampling, auto_refine_options.auto_r8_iters, auto_refine_options.auto_r8_sampling, auto_refine_options.auto_scaling, auto_refine_options.auto_elevation)
			
			auto_it="%03d" % numcorrfiles
			auto_corrfile_basename="%s%s" % (name, auto_it)
			auto_corrfile=corrdir+auto_corrfile_basename+'.corr'
			apProTomo2Aligner.makeCorrPlotImages(name, auto_it, tiltdir, auto_corrfile)  #Correlation plots are always made.
			
			apDisplay.printMsg("CCMS = %s for Iteration #%s of Tilt-Series #%s." % (round(metric,5), start+n+1, tiltseriesnumber))
			
		
	#else:  #Convergence was reached, pass best CCMS value and iteration to __main__
	#Return best iteration and its CCMS back to process handler
	CCMS['series%s_best_iteration' % tiltseriesnumber] = best
	CCMS['series%s_best' % tiltseriesnumber] = best_CCMS
	
	if best_CCMS <= auto_refine_options.auto_convergence:
		apDisplay.printMsg("Alignment for Tilt-Series #%s has converged at Iteration #%s with CCMS = %s" % (tiltseriesnumber, start+n+1, round(metric),5))
	else:
		apDisplay.printMsg("Alignment for Tilt-Series #%s has not converged. Best CCMS Value was %s." % (tiltseriesnumber, round(best_CCMS,5)))
	apDisplay.printMsg("Auto Refinement Finished for Tilt-Series #%s!" % tiltseriesnumber)


def protomoScreening(tiltseriesnumber, screening_options):
	"""
	Screening Mode. Tilt files, directories, and images will be prepared.
	Tilt-Series will be coarsely aligned and depiction videos made in parallel.
	This is intended to be used during data collection.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(screening_options.rundir, tiltseriesnumber, prep="True")
	os.chdir(tiltdir)
	apProTomo2Prep.prepareTiltFile(screening_options.sessionname, seriesname, tiltfilename_full, tiltseriesnumber, raw_path, screening_options.link, coarse="True")
	
	cmd="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(rawimagecount, err) = proc.communicate()
	rawimagecount=int(rawimagecount)
	jobs1=[]
	apDisplay.printMsg("Creating initial tilt-series video in the background...")
	jobs1.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, 0, tiltfilename_full, rawimagecount, tiltdir, raw_path, screening_options.pixelsize, screening_options.map_sampling, screening_options.image_file_type, screening_options.video_type, "True", "Initial",)))
	for job in jobs1:
		job.start()
	time.sleep(4)
	
	#Removing highly shifted images
	bad_images, bad_kept_images=apProTomo2Aligner.removeHighlyShiftedImages(tiltfilename_full, screening_options.dimx, screening_options.dimy, screening_options.shift_limit, screening_options.angle_limit)
	if bad_images:
		apDisplay.printMsg('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.' % (bad_images, screening_options.shift_limit))
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, screening_options.angle_limit))
	else:
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, screening_options.angle_limit))
		apDisplay.printMsg('No images were removed from the .tlt file due to high shifts.')
	
	apDisplay.printMsg("Finished Preparing Files and Directories for Tilt-Series #%s." % (tiltseriesnumber))
	
	name='coarse_'+seriesname
	cpparam="cp %s %s/%s.param" % (screening_options.coarse_param_file,tiltdir,name)
	os.system(cpparam)
	coarse_param_full=tiltdir+'/'+name+'.param'
	editParamFile(tiltdir, coarse_param_full, raw_path)
	
	apDisplay.printMsg('Starting Protomo Coarse Alignment')
	coarse_seriesparam=protomo.param(coarse_param_full)
	coarse_seriesgeom=protomo.geom(tiltfilename_full)
	try:
		series=protomo.series(coarse_seriesparam,coarse_seriesgeom)
		#Align and restart alignment if failed
		retry=0
		brk=0
		new_region_x=screening_options.region_x/screening_options.sampling   #Just initializing
		new_region_y=screening_options.region_y/screening_options.sampling   #Just initializing
		while (retry <= screening_options.coarse_retry_align):
			try:
				if (retry > 0):
					new_region_x = int(new_region_x*screening_options.coarse_retry_shrink)
					new_region_y = int(new_region_y*screening_options.coarse_retry_shrink)
					apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, 100-int(100*screening_options.coarse_retry_shrink), new_region_x, new_region_y))
					newsize = "{ %s %s }" % (new_region_x, new_region_y)
					series.setparam("window.size", newsize)
				retry+=1
				series.align()
				final_retry=retry-1
				retry = screening_options.coarse_retry_align + 1 #Alignment worked, don't retry anymore
			except:
				if (retry > screening_options.coarse_retry_align):
					apDisplay.printMsg("Coarse Alignment failed after rescaling the search area %s time(s)." % (retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*screening_options.sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*screening_options.sampling))
					apDisplay.printMsg("Put values less than these into thesponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n")
					brk=1
				pass
		
		if (brk == 1):   #resampling failed, break out of all refinement iterations
			#Finish background process
			for job in jobs1:
				job.join()
			return None
		
		corrfile=name+'.corr'
		series.corr(corrfile)
		
		#archive results
		tiltfile=name+'.tlt'
		series.geom(1).write(tiltfile)
		
		cleanup="mkdir %s/coarse_out; cp %s/coarse*.* %s/coarse_out; rm %s/*.corr; mv %s/%s.tlt %s/coarse_out/initial_%s.tlt; cp %s/%s.tlt %s/%s.tlt" % (tiltdir, tiltdir, tiltdir, tiltdir, tiltdir, seriesname, tiltdir, seriesname, tiltdir, name, tiltdir, seriesname)
		os.system(cleanup)
	except:
		apDisplay.printMsg("Alignment failed. Skipping Tilt-Series #%s...\n" % (tiltseriesnumber))
		return
	
	apDisplay.printMsg("Creating Coarse Alignment Depictions in Parallel")
	
	# For multiprocessing
	jobs2=[]
	
	# Make correlation peak videos for depiction			
	jobs2.append(mp.Process(target=apProTomo2Aligner.makeCorrPeakVideos, args=(name, 0, tiltdir, 'out', screening_options.video_type, "Coarse",)))
	
	# Make tiltseries video for depiction
	apDisplay.printMsg("Creating Coarse Alignment tilt-series video...")
	jobs2.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, 0, tiltfile, rawimagecount, tiltdir, raw_path, screening_options.pixelsize, screening_options.map_sampling, screening_options.image_file_type, screening_options.video_type, "True", "Coarse",)))
	
	# Send off processes in the background
	for job in jobs2:
		job.start()
	
	apDisplay.printMsg("Generating Coarse Alignment reconstruction...")
	series.mapfile()
	apProTomo2Aligner.makeReconstructionVideos(name, 0, tiltdir, 'out', screening_options.pixelsize, screening_options.sampling, screening_options.map_sampling, screening_options.video_type, "false", "True", align_step="Coarse")
	
	# Join processes
	for job in jobs1:
		job.join()
	for job in jobs2:
		job.join()
	
	apDisplay.printMsg("Coarse Alignment for tilt-series #%s finished!\n" % tiltseriesnumber)


def ctfCorrect(tiltseriesnumber, ctf_options):
	"""
	Leginondb will be queried to get the 'best' defocus estimate on a per-image basis.
	Confident defoci will be gathered and unconfident defoci will be interpolated.
	Images will be CTF corrected by phase flipping using ctfphaseflip from the IMOD package.
	A plot of the defocus values will is made. #TODO
	A CTF plot using the mean defocus is made. #TODO
	"""
	try:
		tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,rawimagecount = variableSetup(ctf_options.rundir, tiltseriesnumber, prep="False")
		os.chdir(tiltdir)
		ctfdir='%s/ctf_correction/' % tiltdir
		os.system("mkdir %s" % ctfdir)
		defocus_file_full=ctfdir+seriesname+'_defocus.txt'
		tilt_file_full=ctfdir+seriesname+'_tilts.txt'
		image_list_full=ctfdir+seriesname+'_images.txt'
		uncorrected_stack=ctfdir+'stack_uncorrected.mrc'
		corrected_stack=ctfdir+'stack_corrected.mrc'
		out_full=ctfdir+'out'
		log_file_full=ctfdir+'ctf_correction.log'
		
		project='ap'+ctf_options.projectid
		sinedon.setConfig('appiondata', db=project)
		sessiondata = apDatabase.getSessionDataFromSessionName(ctf_options.sessionname)
		tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
		tiltdata = apTomo.getImageList([tiltseriesdata])
		tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(tiltdata)
		if os.path.isfile(ctfdir+'out/out01.mrc'): #Throw exception if already ctf corrected
			sys.exit()
		
		#Get tilt azimuth
		cmd="awk '/TILT AZIMUTH/{print $3}' %s" % (tiltfilename)
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(tilt_azimuth, err) = proc.communicate()
		tilt_azimuth=float(tilt_azimuth)
		 
		estimated_defocus=[]
		for image in range(len(ordered_imagelist)):
			imgctfdata=ctfdb.getBestCtfValue(ordered_imagelist[image], msg=False)
			try:
				#imgctfdata['resolution_50_percent']  #If this fails then the defocus hasn't been estimated through Appion
				if imgctfdata['resolution_50_percent'] < 100.0: #if there's a yellow ring in Appion, trust defocus estimation
					estimated_defocus.append((imgctfdata['defocus1']+imgctfdata['defocus2'])*1000000000/2)
				else:  #Poorly estimated. Guess its value later
					estimated_defocus.append(999999999)
			except:  #No data. Guess its value later
				estimated_defocus.append(999999999)
		
		#Find mean and stdev to prune out confident defocus values that are way off
		defocus_stats_list=filter(lambda a: a != 999999999, estimated_defocus)
		avg=np.array(defocus_stats_list).mean()
		stdev=np.array(defocus_stats_list).std()
		
		good_tilts=[]
		good_defocus_list=[]
		for tilt, defocus in zip(tilts, estimated_defocus):
			if (defocus != 999999999) and (defocus < avg + stdev) and (defocus > avg - stdev):
				good_defocus_list.append(defocus)
				good_tilts.append(tilt)
		
		#Using a linear best fit because quadratic and cubic go off the rails. Estimation doesn't need to be extremely accurate anyways.
		x=np.linspace(int(round(tilts[0])), int(round(tilts[len(tilts)-1])), 1000)
		s=scipy.interpolate.UnivariateSpline(good_tilts,good_defocus_list,k=1)
		y=s(x)
		
		#Make defocus list with good values and interpolations for bad values
		finished_defocus_list=[]
		for tilt, defocus in zip(tilts, estimated_defocus):
			if (defocus != 999999999) and (defocus < avg + stdev) and (defocus > avg - stdev):
				finished_defocus_list.append(int(round(defocus)))
			else:  #Interpolate
				finished_defocus_list.append(int(round(y[int(round(tilt))])))
		
		new_avg=np.array(finished_defocus_list).mean()
		new_stdev=np.array(finished_defocus_list).std()
		
		#Write defocus file, tilt file, and image list file for ctfphaseflip and newstack
		f = open(defocus_file_full,'w')
		f.write("%d\t%d\t%.2f\t%.2f\t%d\t2\n" % (1,1,tilts[0],tilts[0],finished_defocus_list[0]))
		for i in range(1,len(tilts)):
			f.write("%d\t%d\t%.2f\t%.2f\t%d\n" % (i+1,i+1,tilts[i],tilts[i],finished_defocus_list[i]))
		f.close()
		
		f = open(tilt_file_full,'w')
		for tilt in tilts:
			f.write("%.2f\n" % tilt)
		f.close()
		
		mrc_list=[]
		for image in ordered_mrc_files:
			mrc_list.append(raw_path+'/'+image[-10:])
		f = open(image_list_full,'w')
		f.write("%d\n" % len(tilts))
		for filename in mrc_list:
			f.write(filename+'\n')
			f.write("%d\n" % 0)
		f.close()
		
		#Rotate and pad images so that they are treated properly by ctfphaseflip.
		apDisplay.printMsg("Preparing images for IMOD...")
		for filename in mrc_list:
			image=mrc.read(filename)
			dimx=len(image[0])
			dimy=len(image)
			#First rotate 90 degrees in clockwise direction. This makes it so positive angle images are higher defocused on the right side of the image
			image=np.rot90(image, k=1)
			#Rotate image and write
			image=imrotate(image, -tilt_azimuth, order=1) #Linear interpolation is fastest and there is barely a difference between linear and cubic
			mrc.write(image, filename)
			
		f = open(log_file_full,'w')
		#Make stack for correction,phase flip, extract images, replace images
		cmd1="newstack -fileinlist %s -output %s > %s" % (image_list_full, uncorrected_stack, log_file_full)
		f.write("%s\n\n" % cmd1)
		print cmd1
		subprocess.check_call([cmd1], shell=True)
		
		cmd2="ctfphaseflip -input %s -output %s -AngleFile %s -defFn %s -pixelSize %s -volt %s -DefocusTol %s -iWidth %s -SphericalAberration %s -AmplitudeContrast %s 2>&1 | tee %s" % (uncorrected_stack, corrected_stack, tilt_file_full, defocus_file_full, ctf_options.pixelsize/10, ctf_options.voltage, ctf_options.DefocusTol, ctf_options.iWidth, ctf_options.cs, ctf_options.amp_contrast, log_file_full)
		f.write("\n\n%s\n\n" % cmd2)
		print cmd2
		subprocess.check_call([cmd2], shell=True)
		
		cmd3="newstack -split 1 -append mrc %s %s >> %s" % (corrected_stack, out_full, log_file_full)
		f.write("\n\n%s\n\n" % cmd3)
		print cmd3
		subprocess.check_call([cmd3], shell=True)
		f.write("\n\n")
		
		apDisplay.printMsg("Overwriting uncorrected raw images with CTF corrected images")
		new_images=glob.glob(ctfdir+'out*mrc')
		new_images.sort()
		
		#Unrotate and unpad images
		for filename in new_images:
			image=mrc.read(filename)
			image=imrotate(image, tilt_azimuth, order=1)
			image=np.rot90(image, k=3)
			big_dimx=len(image[0])
			big_dimy=len(image)
			cropx1=int((big_dimx-dimx)/2)
			cropx2=int(dimx+(big_dimx-dimx)/2)
			cropy1=int((big_dimy-dimy)/2)
			cropy2=int(dimy+(big_dimy-dimy)/2)
			image=image[cropy1:cropy2,cropx1:cropx2]
			mrc.write(image, filename)
		
		for i in range(len(new_images)):
			cmd4="rm %s; ln %s %s" % (mrc_list[i], new_images[i], mrc_list[i])
			f.write("%s\n" % cmd4)
			os.system(cmd4)
		
		cleanup="rm %s %s" % (uncorrected_stack, corrected_stack)
		os.system(cleanup)
		output1="%.2f%% of the images for tilt-series #%s had poor defocus estimates or fell outside of one standard deviation from the original mean." % (100*(len(estimated_defocus)-len(defocus_stats_list))/len(estimated_defocus), tiltseriesnumber)
		output2="The defocus mean and standard deviation for tilt-series #%s after interpolating poor values is %.2f and %.2f microns, respectively." % (tiltseriesnumber, new_avg/1000, new_stdev/1000)
		f.write("\n");f.write(output1);f.write("\n");f.write(output2);f.write("\n");f.close()
		apDisplay.printMsg(output1)
		apDisplay.printMsg(output2)
		apDisplay.printMsg("CTF correction finished for tilt-series #%s!" % tiltseriesnumber)
		
	except SystemExit:
		apDisplay.printMsg("It looks like you've already CTF corrected tilt-series #%s. Aborting!" % tiltseriesnumber)
	
	except subprocess.CalledProcessError:
		apDisplay.printMsg("An IMOD command failed. Make sure IMOD is in your $PATH.")
	
	except:
		apDisplay.printMsg("CTF correction could not be completed. Make sure IMOD, numpy, and scipy are in your $PATH. Make sure defocus has been estimated through Appion.\n")


if __name__ == '__main__':
	options=parseOptions()
	options=apProTomo2Aligner.angstromsToProtomo(options)
	tiltseriesranges=apProTomo2Aligner.hyphen_range(options.tiltseriesranges)
	
	if (options.procs == "all"):
		options.procs=mp.cpu_count()
	else:
		options.procs=int(options.procs)
	
	
	#File Preparation
	if (options.prep_files == "True" and options.automation == "False"):
		from appionlib import apProTomo2Prep   #If you want to run protomo on a machine that doesn't have MYSQL/leginondb access, then this will fail to import
		
		apDisplay.printMsg("Preparing Files and Directories for Protomo")
		
		if (options.procs > 5): #For tilt-series of size 5k x 4k by 37 tilts, each protomoPrep process will consume over 6GB of ram. If the ram is maxed out, the system will revert to disk swap and slow down this step considerably.
			procs=5
		else:
			procs=options.procs
		
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoPrep, args=(i, options,))
			p.start()
			
			#If max number of processors is reached, wait for them to finish. This isn't the most efficient way, but it's the only way I know how to accomplish this right now...
			if (j % procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Files and Directories Prepared for tilt-series %s!" % options.tiltseriesranges)
	
	
	#Protomo doesn't like how proc2d writes mrc files. Our frame alignment script uses proc2d. This function and its options are hidden from general users.
	if (options.fix_images == "True" and options.link == "False"):
		apDisplay.printMsg("Fixing raw image mrcs...")
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoFixFrameMrcs, args=(i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Fixed Raw Images for Tilt-Series %s!" % options.tiltseriesranges)
	
	
	#Coarse Alignment
	if (options.coarse_align == "True" and options.automation == "False"):
		apDisplay.printMsg("Performing Coarse Alignments")
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoCoarseAlign, args=(i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Coarse Alignments Finished for tilt-series %s!" % options.tiltseriesranges)
	
	
	#Refinement
	if (options.refine == "True" and options.automation == "False"):
		apDisplay.printMsg("Performing Refinements")
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoRefine, args=(i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Refinements Finished for tilt-series %s!" % options.tiltseriesranges)
	
	
	#Reconstruction
	if (options.reconstruct == "True" and options.automation == "False"):
		apDisplay.printMsg("Creating Reconstructions")
		for i, j in zip(tiltseriesranges, range(len(tiltseriesranges))):
			p = mp.Process(target=protomoReconstruct, args=(i, options,))
			p.start()
			
			if (j % (options.procs-1) == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Reconstructions Finished for tilt-series %s!" % options.tiltseriesranges)
	
	
	#CTF Correction
	if (options.ctf_correct == "True" and options.automation == "False"):
		import sinedon   #If you want to run protomo on a machine that doesn't have MYSQL/leginondb access, then these will fail to import
		import numpy as np
		import scipy.interpolate
		from appionlib import apDatabase
		from appionlib import apTomo
		from appionlib.apCtf import ctfdb
		
		apDisplay.printMsg("Performing CTF Correction")
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=ctfCorrect, args=(i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("CTF Correction Finished for tilt-series %s!" % options.tiltseriesranges)
	
	
	#Full Automation mode needs to be run by itself. It has its own self-contained calls to all primary Appion-Protomo functions.
	if (options.automation == "True" and options.prep_files == "False" and options.coarse_align == "False" and options.refine == "False" and options.reconstruct == "False" and options.ctf_correct == "False" and options.screening_mode == "False"):
		#File Preparation
		if (options.auto_prep == "True"):
			from appionlib import apProTomo2Prep   #If you want to run protomo on a machine that doesn't have MYSQL/leginondb access, then this will fail to import
		
			apDisplay.printMsg("Preparing Files and Directories for Protomo")
			
			if (options.procs > 5): #For tilt-series of size 5k x 4k by 37 tilts, each protomoPrep process will consume over 6GB of ram. If the ram is maxed out, the system will revert to disk swap and slow down this step considerably.
				procs=5
			else:
				procs=options.procs
			
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoPrep, args=(i, options,))
				p.start()
				
				#If max number of processors is reached, wait for them to finish. This isn't the most efficient way, but it's the only way I know how to accomplish this right now...
				if (j % procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("Files and Directories Prepared for tilt-series %s!" % options.tiltseriesranges)
		else:
			apDisplay.printMsg("Skipping File Preparation. If you haven't prepared files for processing, you should set --auto_prep=True")
		
		#CTF Correction
		if (options.auto_ctf_correct == "True"):
			import sinedon   #If you want to run protomo on a machine that doesn't have MYSQL/leginondb access, then these will fail to import
			import numpy as np
			import scipy.interpolate
			from appionlib import apDatabase
			from appionlib import apTomo
			from appionlib.apCtf import ctfdb
			
			apDisplay.printMsg("Performing CTF Correction")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=ctfCorrect, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("CTF Correction Finished for tilt-series %s!" % options.tiltseriesranges)
		else:
			apDisplay.printMsg("Skipping CTF Correction. If you would like to CTF your raw images, make sure the defocus has been estimated from within Appion, then set --auto_ctf_correct=True")
		
		#Coarse Alignment
		if (options.auto_coarse_align == "True"):
			apDisplay.printMsg("Performing Coarse Alignments")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoCoarseAlign, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("Coarse Alignments Finished for tilt-series %s!" % options.tiltseriesranges)
		else:
			apDisplay.printMsg("Skipping Coarse Alignment. If you haven't Coarse Aligned these tilt-series yet, then set --auto_coarse_align=True. You must coarsly align tilt-series before proceeding to refinement.")
		
		#Refinement
		if (options.auto_refine == "True"):
			apDisplay.printMsg("Performing Refinements")
			CCMS={}
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoAutoRefine, args=(i, options, CCMS))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("Auto Refinement Finished for tilt-series %s!" % options.tiltseriesranges)
			apDisplay.printMsg("Check the Batch Summary page for results.")
		else:
			apDisplay.printMsg("Skipping Refinement completely defeats the purpose of Full Automation! Consider setting --auto_refine=True")

		#print CCMS

		#Reconstruction
		if (options.auto_reconstruct == "True"):
			apDisplay.printMsg("Creating Reconstructions by Back-Projection")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoCoarseAlign, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("Coarse Alignments Finished for tilt-series %s!" % options.tiltseriesranges)
		else:
			apDisplay.printMsg("Skipping Reconstruction.")
		
	
	#Screening mode needs to be run by itself.
	if (options.screening_mode == "True" and options.automation == "False" and options.prep_files == "False" and options.coarse_align == "False" and options.refine == "False" and options.reconstruct == "False" and options.ctf_correct == "False"):
		from appionlib import apDatabase   #If you want to run protomo on a machine that doesn't have MYSQL/leginondb access, then these will fail to import
		from appionlib import apProTomo2Prep
		
		apDisplay.printMsg("Appion-Protomo Screening Mode")
		apDisplay.printMsg("Tilt files, directories, and images will be prepared.")
		apDisplay.printMsg("Tilt-Series will be coarsely aligned and depiction videos made in parallel.")
		apDisplay.printMsg("This is intended to be used during data collection.")
		
		tiltseriesnumber=options.screening_start
		while True:
			try:
				sessiondata = apDatabase.getSessionDataFromSessionName(options.sessionname)
				tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber+1,sessiondata)
				
				#If tilt-series N+1 exists, then tilt-series N is ready to be processed
				protomoScreening(tiltseriesnumber, options)
				
				tiltseriesnumber+=1
			except:
				#Wait for tilt-series N to finish collecting
				apDisplay.printMsg("Waiting for tilt-series #%s to finish being collected. Sleeping for 1 minute..." % tiltseriesnumber)
				time.sleep(60)
		
	