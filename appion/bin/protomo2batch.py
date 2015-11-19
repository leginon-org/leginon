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
import shutil
import optparse
import subprocess
import numpy as np
import multiprocessing as mp
from pyami import mrc
from appionlib import apDisplay
from appionlib import apProTomo2Prep
from appionlib import apProTomo2Aligner
from scipy.ndimage.interpolation import rotate as imrotate

try:
	import protomo
except:
	apDisplay.printWarning("Protomo did not get imported. Alignment and reconstruction functionality won't work.")

try:
	from appionlib import apDatabase
except:
	apDisplay.printWarning("MySQLdb not found. Screening Mode functionality won't work.")


def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--sessionname', dest='sessionname',
		help= 'Session date, e.g. --sessionname=14sep04a')
	parser.add_option('--runname', dest='runname',
		help= 'Name of protmorun directory as made by Appion, e.g. --runname=batchrun1')
	parser.add_option("--description", dest="description", default="",
		help="Run description")
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
	parser.add_option('--tiltseriesranges', dest='tiltseriesranges', default="1-999999",
		help= 'Range of tilt-series numbers to be processed. Should be in a comma/hyphen-separated list, e.g. 3,4,6-10')
	parser.add_option('--numtiltseries', dest='numtiltseries',
		help= 'Number of tilt-series in the session, e.g. --numtiltseries=42')
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
		help="Access leginondb to create tlt file and copy raw images, e.g. --prep_files=False")
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
	parser.add_option("--video_type", dest="video_type",  default="html5vid",
		help="Appion: Create either gifs or html5 videos using 'gif' or 'html5vid', respectively, e.g. --video_type=html5vid")
	parser.add_option("--restart_cycle", dest="restart_cycle",
		help="Restart a Refinement at this iteration, e.g. --restart_cycle=2 or --restart_cycle=best")	
	parser.add_option('--shift_limit', dest='shift_limit', type='float', metavar='float', default=30,
		help='Percentage of image size, above which shifts with higher shifts will be discarded for all images, e.g. --shift_limit=50')
	parser.add_option('--angle_limit', dest='angle_limit', type='float', metavar='float', default=40,
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
	parser.add_option("--r6_region_x", dest="r6_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r6_region=1024", metavar="int")
	parser.add_option("--r7_region_x", dest="r7_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r7_region=1024", metavar="int")
	parser.add_option("--r8_region_x", dest="r8_region_x", default=512, type="int",
		help="Pixels in x to use for region matching, e.g. --r8_region=1024", metavar="int")
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
	parser.add_option("--r6_region_y", dest="r6_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r6_region=1024", metavar="int")
	parser.add_option("--r7_region_y", dest="r7_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r7_region=1024", metavar="int")
	parser.add_option("--r8_region_y", dest="r8_region_y", default=512, type="int",
		help="Pixels in y to use for region matching, e.g. --r8_region=1024", metavar="int")
	parser.add_option("--lowpass_diameter_x", dest="lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r1_lowpass_diameter_x", dest="r1_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r2_lowpass_diameter_x", dest="r2_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r3_lowpass_diameter_x", dest="r3_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r4_lowpass_diameter_x", dest="r4_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r5_lowpass_diameter_x", dest="r5_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r6_lowpass_diameter_x", dest="r6_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r7_lowpass_diameter_x", dest="r7_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r8_lowpass_diameter_x", dest="r8_lowpass_diameter_x",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--lowpass_diameter_y", dest="lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r1_lowpass_diameter_y", dest="r1_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r2_lowpass_diameter_y", dest="r2_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r3_lowpass_diameter_y", dest="r3_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r4_lowpass_diameter_y", dest="r4_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r5_lowpass_diameter_y", dest="r5_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r6_lowpass_diameter_y", dest="r6_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r7_lowpass_diameter_y", dest="r7_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r8_lowpass_diameter_y", dest="r8_lowpass_diameter_y",  default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--lowpass_apod_x", dest="lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r1_lowpass_apod_x", dest="r1_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r2_lowpass_apod_x", dest="r2_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r3_lowpass_apod_x", dest="r3_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r4_lowpass_apod_x", dest="r4_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r5_lowpass_apod_x", dest="r5_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r6_lowpass_apod_x", dest="r6_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r7_lowpass_apod_x", dest="r7_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--r8_lowpass_apod_x", dest="r8_lowpass_apod_x", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_lowpass_diameter_x=0.4", metavar="float")
	parser.add_option("--lowpass_apod_y", dest="lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r1_lowpass_apod_y", dest="r1_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r2_lowpass_apod_y", dest="r2_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r3_lowpass_apod_y", dest="r3_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r4_lowpass_apod_y", dest="r4_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r5_lowpass_apod_y", dest="r5_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r6_lowpass_apod_y", dest="r6_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r7_lowpass_apod_y", dest="r7_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--r8_lowpass_apod_y", dest="r8_lowpass_apod_y", default=20, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_lowpass_diameter_y=0.4", metavar="float")
	parser.add_option("--highpass_diameter_x", dest="highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r1_highpass_diameter_x", dest="r1_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r2_highpass_diameter_x", dest="r2_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r3_highpass_diameter_x", dest="r3_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r4_highpass_diameter_x", dest="r4_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r5_highpass_diameter_x", dest="r5_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r6_highpass_diameter_x", dest="r6_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r7_highpass_diameter_x", dest="r7_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r8_highpass_diameter_x", dest="r8_highpass_diameter_x", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--highpass_diameter_y", dest="highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r1_highpass_diameter_y", dest="r1_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r2_highpass_diameter_y", dest="r2_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r3_highpass_diameter_y", dest="r3_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r4_highpass_diameter_y", dest="r4_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r5_highpass_diameter_y", dest="r5_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r6_highpass_diameter_y", dest="r6_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r7_highpass_diameter_y", dest="r7_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r8_highpass_diameter_y", dest="r8_highpass_diameter_y", default=2000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--highpass_apod_x", dest="highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r1_highpass_apod_x", dest="r1_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r2_highpass_apod_x", dest="r2_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r3_highpass_apod_x", dest="r3_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r4_highpass_apod_x", dest="r4_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r5_highpass_apod_x", dest="r5_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r6_highpass_apod_x", dest="r6_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r7_highpass_apod_x", dest="r7_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--r8_highpass_apod_x", dest="r8_highpass_apod_x", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_highpass_diameter_x=0.02", metavar="float")
	parser.add_option("--highpass_apod_y", dest="highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r1_highpass_apod_y", dest="r1_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r1_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r2_highpass_apod_y", dest="r2_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r2_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r3_highpass_apod_y", dest="r3_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r3_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r4_highpass_apod_y", dest="r4_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r4_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r5_highpass_apod_y", dest="r5_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r5_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r6_highpass_apod_y", dest="r6_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r6_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r7_highpass_apod_y", dest="r7_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r7_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--r8_highpass_apod_y", dest="r8_highpass_apod_y", default=1000, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --r8_highpass_diameter_y=0.02", metavar="float")
	parser.add_option("--thickness", dest="thickness",  default=1500, type="float",
	        help="Estimated thickness of unbinned specimen (in angstroms), e.g. --thickness=100.0", metavar="float")
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
	parser.add_option("--r6_iters", dest="r6_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r6_iters=4", metavar="int")
	parser.add_option("--r7_iters", dest="r7_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r7_iters=4", metavar="int")
	parser.add_option("--r8_iters", dest="r8_iters", default=0, type="int",
		help="Number of alignment and geometry refinement iterations, e.g. --r8_iters=4", metavar="int")
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
	parser.add_option("--r6_sampling", dest="r6_sampling",  default=4, type="int",
		help="Sampling rate of raw data, e.g. --r6_sampling=4")
	parser.add_option("--r7_sampling", dest="r7_sampling",  default=2, type="int",
		help="Sampling rate of raw data, e.g. --r7_sampling=4")
	parser.add_option("--r8_sampling", dest="r8_sampling",  default=1, type="int",
		help="Sampling rate of raw data, e.g. --r8_sampling=4")
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
	parser.add_option("--r6_body", dest="r6_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	parser.add_option("--r7_body", dest="r7_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	parser.add_option("--r8_body", dest="r8_body",  default=0, type="float",
		help="Body size (see Protomo docs). For internal use only.")
	correlation_modes = ( "xcf", "mcf", "pcf", "dbl" )
	parser.add_option("--r1_corr_mode", dest="r1_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r2_corr_mode", dest="r2_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r3_corr_mode", dest="r3_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r4_corr_mode", dest="r4_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r5_corr_mode", dest="r5_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r6_corr_mode", dest="r6_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r7_corr_mode", dest="r7_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
	parser.add_option("--r8_corr_mode", dest="r8_corr_mode",
		help="Correlation mode, standard (xcf), mutual (mcf), phase only (pcf), phase doubled (dbl), e.g. --correlation_mode=xcf",
		type="choice", choices=correlation_modes, default="mcf" )
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
	parser.add_option("--r6_kernel_x", dest="r6_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r6_kernel_x=5", metavar="int")
	parser.add_option("--r7_kernel_x", dest="r7_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r7_kernel_x=5", metavar="int")
	parser.add_option("--r8_kernel_x", dest="r8_kernel_x", default=3,  type="int",
		help="Filter window size, e.g. --r8_kernel_x=5", metavar="int")
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
	parser.add_option("--r6_kernel_y", dest="r6_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r6_kernel_y=5", metavar="int")
	parser.add_option("--r7_kernel_y", dest="r7_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r7_kernel_y=5", metavar="int")
	parser.add_option("--r8_kernel_y", dest="r8_kernel_y", default=3,  type="int",
		help="Filter window size, e.g. --r8_kernel_y=5", metavar="int")
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
	parser.add_option("--r6_peak_search_radius_x", dest="r6_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r6_peak_search_radius_x=19.0", metavar="float")
	parser.add_option("--r7_peak_search_radius_x", dest="r7_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r7_peak_search_radius_x=19.0", metavar="float")
	parser.add_option("--r8_peak_search_radius_x", dest="r8_peak_search_radius_x",  type="float",  default="100",
		help="Defines peak search region, e.g. --r8_peak_search_radius_x=19.0", metavar="float")
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
	parser.add_option("--r6_peak_search_radius_y", dest="r6_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r6_peak_search_radius_y=19.0", metavar="float")
	parser.add_option("--r7_peak_search_radius_y", dest="r7_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r7_peak_search_radius_y=19.0", metavar="float")
	parser.add_option("--r8_peak_search_radius_y", dest="r8_peak_search_radius_y",  type="float",  default="100",
		help="Defines peak search region, e.g. --r8_peak_search_radius_y=19.0", metavar="float")
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
	parser.add_option("--r6_mask_width_x", dest="r6_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r6_mask_width_x=2")
	parser.add_option("--r7_mask_width_x", dest="r7_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r7_mask_width_x=2")
	parser.add_option("--r8_mask_width_x", dest="r8_mask_width_x",  default="1024",
		help="Rectangular mask width (x), e.g. --r8_mask_width_x=2")
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
	parser.add_option("--r6_mask_width_y", dest="r6_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r6_mask_width_y=2")
	parser.add_option("--r7_mask_width_y", dest="r7_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r7_mask_width_y=2")
	parser.add_option("--r8_mask_width_y", dest="r8_mask_width_y",  default="1024",
		help="Rectangular mask width (y), e.g. --r8_mask_width_y=2")
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
	parser.add_option("--r6_mask_apod_x", dest="r6_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r6_mask_apod_x=10")
	parser.add_option("--r7_mask_apod_x", dest="r7_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r7_mask_apod_x=10")
	parser.add_option("--r8_mask_apod_x", dest="r8_mask_apod_x",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r8_mask_apod_x=10")
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
	parser.add_option("--r6_mask_apod_y", dest="r6_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r6_mask_apod_y=10")
	parser.add_option("--r7_mask_apod_y", dest="r7_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r7_mask_apod_y=10")
	parser.add_option("--r8_mask_apod_y", dest="r8_mask_apod_y",  default="10",
		help="Apodization for rectangular and ellipsoidal masks, e.g. --r8_mask_apod_y=10")
	parser.add_option("--show_window_size", dest="show_window_size", default="true",
		help="Appion: Show the window size used for alignment in the reconstruction video, e.g. --show_window_size=false")
	parser.add_option("--tilt_clip", dest="tilt_clip",  default="true",
		help="Appion: Clip pixel values for tilt-series video to +-5 sigma, e.g. --tilt_clip=false")
	parser.add_option("--refresh_i3t", dest="refresh_i3t",  default="False",
		help="If a Protomo run is interrupted the i3t file may be unusable. This option removes the i3t file so that protomoRefine can create a new one, e.g. --refresh_i3t=True")
	parser.add_option("--fix_images", dest="fix_images",  default="False",
		help="Internal use only")
	parser.add_option("--recon_iter", dest="recon_iter", type="int",
		help="Refinement iteration used to make final reconstruction, e.g. --recon_iter=10", metavar="int")
	parser.add_option("--recon_iter_presets", dest="recon_iter_presets",
		help="Presets for determining which Refinement iteration to reconstruct from. Options: Best, Worst, Last, or Custom. Best and Worst are determined from the CCMS(summed) values, e.g. --recon_iter_presets=Best")
	parser.add_option("--negative", dest="negative", type="float",  default="-90",
		help="Tilt angle, in degrees, below which all images will be removed, e.g. --negative=-45", metavar="float")
	parser.add_option("--positive", dest="positive", type="float",  default="90",
		help="Tilt angle, in degrees, above which all images will be removed, e.g. --positive=45", metavar="float")
	parser.add_option("--recon_map_size_x", dest="recon_map_size_x",  type="int",  default="2048",
		help="Size of the reconstructed tomogram in the X direction, e.g. --recon_map_size_x=256", metavar="int")
	parser.add_option("--recon_map_size_y", dest="recon_map_size_y",  type="int",  default="2048",
		help="Size of the reconstructed tomogram in the Y direction, e.g. --recon_map_size_y=256", metavar="int")
	parser.add_option("--recon_thickness", dest="recon_thickness",  type="float",  default="2000",
		help="Thickness of the reconstructed tomogram in the Z direction, in angstroms, e.g. --recon_thickness=1000", metavar="float")
	parser.add_option("--recon_map_sampling", dest="recon_map_sampling",  default="2", type="int",
		help="Sampling rate of raw data for use in reconstruction, e.g. --recon_map_sampling=4")
	parser.add_option("--recon_lowpass", dest="recon_lowpass",  default=False, 
		help="Lowpass filter the reconstruction?, e.g. --recon_lowpass=True")
	parser.add_option("--recon_lp_diam_x", dest="recon_lp_diam_x",  default=15, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --recon_lp_diam_x=10", metavar="float")
	parser.add_option("--recon_lp_diam_y", dest="recon_lp_diam_y",  default=15, type="float",
		help="Provide in angstroms. This will be converted to Protomo units, e.g. --recon_lp_diam_y=10", metavar="float")
	parser.add_option("--link_recons", dest="link_recons",  default="",
		help="Path to link reconstruction, e.g. --link_recons=/full/path/")
	parser.add_option("--screening_mode", dest="screening_mode",  default="False",
		help="Protomo Screening Mode to be run during data collection. This mode will continually query leginon database for tilt-series number N+1. When tilt-series N+1 shows up, tilt-series N will be processed through coarse alignment, producing normal depiction videos. Screening mode is configured to parallelize video production just like is done in protomo2aligner.py. The coarse_param_file option must be set., e.g. --screening_mode=True")
	parser.add_option("--screening_start", dest="screening_start",  default=1,
		help="Which tilt-series number will screening mode begin on?, e.g. --screening_start=10")
	parser.add_option("--ctf_correct", dest="ctf_correct",  default="False",
		help="CTF correct images using ctf correction runs from Appion, e.g. --ctf_correct=True")
	parser.add_option("--dose_presets", dest="dose_presets",  default="False",
		help="Dose compensate using equation given by Grant & Grigorieff, 2015, e.g. --dose_presets=Moderate")
	parser.add_option('--dose_a', dest='dose_a', type="float",  default=0.245,
		help='\'a\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_a=0.2')
	parser.add_option('--dose_b', dest='dose_b', type="float",  default=-1.665,
		help='\'b\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_b=-1.5')
	parser.add_option('--dose_c', dest='dose_c', type="float",  default=2.81,
		help='\'c\' variable in equation (3) of Grant & Grigorieff, 2015, e.g. --dose_c=2')
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
	parser.add_option("--auto_convergence", dest="auto_convergence",  default=0.015, type="float",
	        help="Full Automation Mode. Convergence criteria for stopping alignment, e.g. --auto_convergence=0.02", metavar="float")
	parser.add_option("--auto_convergence_iters", dest="auto_convergence_iters",  default=5, type="int",
	        help="Full Automation Mode. Number of iterations to proceed with once convergence is met, e.g. --auto_convergence_iters=2", metavar="int")
	parser.add_option("--auto_elevation", dest="auto_elevation",  default="True",
		help="Full Automation Mode. Turn on elevation if convergence wasn't reached, e.g. --auto_elevation=True")
	parser.add_option("--auto_scaling", dest="auto_scaling",  default="True",
		help="Full Automation Mode. Turn on scaling if convergence wasn't reached, e.g. --auto_scaling=True")
	parser.add_option("--parallel", dest="parallel",  default="False",
		help="Parallelize while you parallelize (parallelizes image and video production). This could break your machine.")
	parser.add_option("--frame_aligned", dest="frame_aligned",  default="True",
		help="Use frame-aligned images instead of naively summed images, if present.")
	
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
		tiltstart=0
		maxtilt=0
	else:
		cmd="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
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
	
	return tiltdirname, tiltdir, seriesnumber, seriesname, tiltfilename, tiltfilename_full, raw_path, tiltstart, rawimagecount, maxtilt


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


def getParamValues(coarse_param_full, cos_alpha, new_sampling):
	"""
	Determines the body size from the .param file and the cos_alpha of the corresponding .tlt file.
	Returns sampling, original thickness, map_sampling, and lowpass unconverted.
	"""
	cmd="awk '/(* AP sampling *)/{print $3}' %s" % (coarse_param_full)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(sampling, err) = proc.communicate()
	sampling=int(sampling)
	cmd2="awk '/(* AP orig thickness *)/{print $3}' %s" % (coarse_param_full)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(orig_thickness, err) = proc.communicate()
	orig_thickness=float(orig_thickness)
	cmd3="awk '/(* AP reconstruction map sampling *)/{print $2}' %s" % (coarse_param_full)
	proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
	(map_sampling, err) = proc.communicate()
	map_sampling=int(map_sampling)
	cmd4="awk '/(* AP lowpass diameter *)/{print $3}' %s | sed 's/,$//'" % (coarse_param_full)
	proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
	(lpx, err) = proc.communicate()
	lpx=float(lpx)
	cmd5="awk '/(* AP lowpass diameter *)/{print $4}' %s" % (coarse_param_full)
	proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
	(lpy, err) = proc.communicate()
	lpy=float(lpy)
	lp=(lpx+lpy)/2
	cmd6="awk '/(* AP orig window *)/{print $4}' %s | sed 's/,$//'" % (coarse_param_full)
	proc=subprocess.Popen(cmd6, stdout=subprocess.PIPE, shell=True)
	(region_x, err) = proc.communicate()
	region_x=int(region_x)
	cmd7="awk '/(* AP orig window *)/{print $5}' %s" % (coarse_param_full)
	proc=subprocess.Popen(cmd7, stdout=subprocess.PIPE, shell=True)
	(region_y, err) = proc.communicate()
	region_y=int(region_y)
	
	if new_sampling == "no change":  #Doesn't change for Coarse Alignment
		body = (orig_thickness/sampling)/cos_alpha
	else:
		body = (orig_thickness/new_sampling)/cos_alpha
	
	return body, sampling, orig_thickness, map_sampling, lp, region_x, region_y


def protomoPrep(log_file, tiltseriesnumber, prep_options):
	"""
	Creates tilt-series directory, links raw images, creates series*.tlt file,
	and optionally creates an initial tilt-series video.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(prep_options.rundir, tiltseriesnumber, prep="True")
	f = open(log_file,'a')
	
	apDisplay.printMsg('Preparing Tilt-Series #%s Images and .tlt File...' % tiltseriesnumber)
	f.write('Preparing Tilt-Series #%s Images and .tlt File...\n' % tiltseriesnumber)
	tilts,accumulated_dose_list,new_ordered_imagelist,maxtilt = apProTomo2Prep.prepareTiltFile(prep_options.sessionname, seriesname, tiltfilename_full, tiltseriesnumber, raw_path, prep_options.frame_aligned, link=False, coarse="True")
	
	cmd="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)  #rawimagecount is zero before this
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(rawimagecount, err) = proc.communicate()
	rawimagecount=int(rawimagecount)
	
	if (prep_options.all_tilt_videos == "true"):
		apDisplay.printMsg("Creating initial tilt-series video...")
		f.write("Creating initial tilt-series video...\n")
		apProTomo2Aligner.makeTiltSeriesVideos(seriesname, 0, tiltfilename_full, rawimagecount, tiltdir, raw_path, prep_options.pixelsize, prep_options.map_sampling, prep_options.image_file_type, prep_options.video_type, "true", prep_options.parallel, "Initial")
	
	#Removing highly shifted images
	bad_images, bad_kept_images=apProTomo2Aligner.removeHighlyShiftedImages(tiltfilename_full, prep_options.dimx, prep_options.dimy, prep_options.shift_limit, prep_options.angle_limit)
	if bad_images:
		apDisplay.printMsg('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.' % (bad_images, prep_options.shift_limit))
		f.write('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.\n' % (bad_images, prep_options.shift_limit))
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, prep_options.angle_limit))
			f.write('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.\n' % (bad_kept_images, prep_options.angle_limit))
	else:
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, prep_options.angle_limit))
			f.write('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.\n' % (bad_kept_images, prep_options.angle_limit))
		apDisplay.printMsg('No images were removed from the .tlt file due to high shifts.')
		f.write('No images were removed from the .tlt file due to high shifts.\n')
	
	apDisplay.printMsg("Finished Preparing Files and Directories for Tilt-Series #%s." % (tiltseriesnumber))
	f.write("Finished Preparing Files and Directories for Tilt-Series #%s.\n" % (tiltseriesnumber))
	f.close()
	

def protomoCoarseAlign(log_file, tiltseriesnumber, coarse_options):
	"""
	Performs Protomo gridsearch alignment, then prepares files for Refinement.
	Correlation peak video is made.
	Depiction videos are made if requested.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(coarse_options.rundir, tiltseriesnumber, prep="False")
	f = open(log_file,'a')
	os.chdir(tiltdir)
	cos_alpha=np.cos(maxtilt*np.pi/180)
	name='coarse_'+seriesname
	coarse_param_full=tiltdir+'/'+name+'.param'
	cpparam="cp %s %s" % (coarse_options.coarse_param_file, coarse_param_full)
	os.system(cpparam)
	body,sampling,orig_thickness,map_sampling,orig_lp,region_x,region_y = getParamValues(coarse_param_full, cos_alpha, "no change")
	thickness=int(round(orig_thickness*coarse_options.pixelsize))
	lp=round(2*coarse_options.pixelsize*sampling/orig_lp,2)
	editParamFile(tiltdir, coarse_param_full, raw_path)
	apDisplay.printMsg('Starting Protomo Coarse Alignment')
	f.write('Starting Protomo Coarse Alignment\n')
	coarse_seriesparam=protomo.param(coarse_param_full)
	coarse_seriesgeom=protomo.geom(tiltfilename_full)
	try:
		series=protomo.series(coarse_seriesparam,coarse_seriesgeom)
		series.setparam("reference.body", "%s" % body)
		series.setparam("map.body", "%s" % body)
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
					apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)..." % (tiltseriesnumber, retry, new_region_x, new_region_y, sampling))
					f.write("Coarse Alignment for Tilt-Series #%s failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)...\n" % (tiltseriesnumber, retry, new_region_x, new_region_y, sampling))
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
					apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed after rescaling the search area %s time(s)." % (tiltseriesnumber, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n")
					f.write("Coarse Alignment for Tilt-Series #%s failed after rescaling the search area %s time(s).\n" % (tiltseriesnumber, retry-1))
					f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
					f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
					f.write("Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n\n")
					brk=1
				pass
		
		if (brk != None):   #resampling failed, break out of all refinement iterations
			return None
		
		corrfile=name+'.corr'
		series.corr(corrfile)
		
		#archive results
		tiltfile=name+'.tlt'
		series.geom(1).write(tiltfile)
		
		cleanup="mkdir %s/coarse_out; cp %s/coarse*.* %s/coarse_out; rm %s/*.corr; mv %s/%s.tlt %s/coarse_out/initial_%s.tlt; cp %s/%s.tlt %s/%s.tlt" % (tiltdir, tiltdir, tiltdir, tiltdir, tiltdir, seriesname, tiltdir, seriesname, tiltdir, name, tiltdir, seriesname)
		os.system(cleanup)
	except:
		apDisplay.printWarning("Coarse Alignment failed. Skipping Tilt-Series #%s...\n" % (tiltseriesnumber))
		f.write("Coarse Alignment failed. Skipping Tilt-Series #%s...\n\n" % (tiltseriesnumber))
		return
	os.system('touch %s/.tiltseries.%04d' % (tiltdir, tiltseriesnumber))  #Internal tracker for what has been batch processed through alignments
	
	apDisplay.printMsg("Creating Coarse Alignment Depiction Videos")
	f.write("Creating Coarse Alignment Depiction Videos\n")
	apProTomo2Aligner.makeCorrPeakVideos(name, 0, tiltdir, 'out', coarse_options.video_type, "Coarse")
	if (coarse_options.all_tilt_videos == "true"):
		apDisplay.printMsg("Creating Coarse Alignment tilt-series video...")
		f.write("Creating Coarse Alignment tilt-series video...\n")
		apProTomo2Aligner.makeTiltSeriesVideos(seriesname, 0, tiltfile, rawimagecount, tiltdir, raw_path, coarse_options.pixelsize, map_sampling, coarse_options.image_file_type, coarse_options.video_type, "true", coarse_options.parallel, "Coarse")
	if (coarse_options.all_recon_videos == "true"):
		apDisplay.printMsg("Generating Coarse Alignment reconstruction...")
		f.write("Generating Coarse Alignment reconstruction...\n")
		series.mapfile()
		apProTomo2Aligner.makeReconstructionVideos(name, 0, tiltdir, region_x, region_y, "true", 'out', coarse_options.pixelsize, sampling, map_sampling, lp, thickness, coarse_options.video_type, "false", coarse_options.parallel, align_step="Coarse")
	
	apDisplay.printMsg("Coarse Alignment finished for Tilt-Series #%s!\n" % (tiltseriesnumber))
	f.write("Coarse Alignment finished for Tilt-Series #%s!\n\n" % (tiltseriesnumber))
	f.close()

	
def protomoRefine(log_file, tiltseriesnumber, refine_options):
	"""
	Performs Protomo area matching alignment.
	Correlation peak videos are made.
	Quality assessment statistics and images are made.
	Depiction videos are made if requested.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(refine_options.rundir, tiltseriesnumber, prep="False")
	os.system('touch %s/.tiltseries.%04d' % (tiltdir, tiltseriesnumber))  #Internal tracker for what has been processed through alignment
	f = open(log_file,'a')
	os.chdir(tiltdir)
	cos_alpha=np.cos(maxtilt*np.pi/180)
	name=seriesname
	refine_param_full=tiltdir+'/'+name+'.param'
	cpparam="cp %s %s/%s.param" % (refine_options.refine_param_file,tiltdir,name)
	os.system(cpparam)
	body,sampling,orig_thickness,map_sampling,orig_lp,region_x,region_y = getParamValues(refine_param_full, cos_alpha, "no change")
	thickness=int(round(orig_thickness*refine_options.pixelsize))
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
		f.write("Rewinding to iteration %s\n" % (refine_options.restart_cycle))
		start=refine_options.restart_cycle
		series.setcycle(start-1)
	elif (refine_options.restart_cycle == 'best'):
		del series
		tiltfilename_full=tiltdir+'/'+name+'.tlt'
		best=glob.glob('best*')
		best=int(os.path.splitext(best[0])[1][1:])-1
		best_iteration="%03d" % best
		apDisplay.printMsg("Restarting using geometry information from iteration %s" % (best+1))
		f.write("Restarting using geometry information from iteration %s\n" % (best+1))
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
		
	r1_body=float((orig_thickness/refine_options.r1_sampling)/cos_alpha)
	r2_body=float((orig_thickness/refine_options.r2_sampling)/cos_alpha)
	r3_body=float((orig_thickness/refine_options.r3_sampling)/cos_alpha)
	r4_body=float((orig_thickness/refine_options.r4_sampling)/cos_alpha)
	r5_body=float((orig_thickness/refine_options.r5_sampling)/cos_alpha)
	
	iters=refine_options.r1_iters+refine_options.r2_iters+refine_options.r3_iters+refine_options.r4_iters+refine_options.r5_iters
	round1={"window.size":"{ %s %s }" % (int(refine_options.r1_region_x/refine_options.r1_sampling),int(refine_options.r1_region_y/refine_options.r1_sampling)),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r1_lowpass_diameter_x,refine_options.r1_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r1_lowpass_diameter_x,refine_options.r1_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r1_lowpass_apod_x,refine_options.r1_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r1_highpass_apod_x,refine_options.r1_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r1_highpass_diameter_x,refine_options.r1_highpass_diameter_y),"sampling":"%s" % (refine_options.r1_sampling),"map.sampling":"%s" % (refine_options.r1_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r1_kernel_x,refine_options.r1_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r1_peak_search_radius_x,refine_options.r1_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r1_mask_width_x,refine_options.r1_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r1_mask_width_x,refine_options.r1_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r1_mask_apod_x,refine_options.r1_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r1_mask_apod_x,refine_options.r1_mask_apod_y),"reference.body":"%s" % (r1_body),"map.body":"%s" % (r1_body),"align.correlation.mode":"%s" % (refine_options.r1_corr_mode)}
	round2={"window.size":"{ %s %s }" % (int(refine_options.r2_region_x/refine_options.r2_sampling),int(refine_options.r2_region_y/refine_options.r2_sampling)),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r2_lowpass_diameter_x,refine_options.r2_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r2_lowpass_diameter_x,refine_options.r2_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r2_lowpass_apod_x,refine_options.r2_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r2_highpass_apod_x,refine_options.r2_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r2_highpass_diameter_x,refine_options.r2_highpass_diameter_y),"sampling":"%s" % (refine_options.r2_sampling),"map.sampling":"%s" % (refine_options.r2_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r2_kernel_x,refine_options.r2_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r2_peak_search_radius_x,refine_options.r2_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r2_mask_width_x,refine_options.r2_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r2_mask_width_x,refine_options.r2_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r2_mask_apod_x,refine_options.r2_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r2_mask_apod_x,refine_options.r2_mask_apod_y),"reference.body":"%s" % (r2_body),"map.body":"%s" % (r2_body),"align.correlation.mode":"%s" % (refine_options.r2_corr_mode)}
	round3={"window.size":"{ %s %s }" % (int(refine_options.r3_region_x/refine_options.r3_sampling),int(refine_options.r3_region_y/refine_options.r3_sampling)),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r3_lowpass_diameter_x,refine_options.r3_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r3_lowpass_diameter_x,refine_options.r3_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r3_lowpass_apod_x,refine_options.r3_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r3_highpass_apod_x,refine_options.r3_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r3_highpass_diameter_x,refine_options.r3_highpass_diameter_y),"sampling":"%s" % (refine_options.r3_sampling),"map.sampling":"%s" % (refine_options.r3_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r3_kernel_x,refine_options.r3_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r3_peak_search_radius_x,refine_options.r3_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r3_mask_width_x,refine_options.r3_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r3_mask_width_x,refine_options.r3_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r3_mask_apod_x,refine_options.r3_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r3_mask_apod_x,refine_options.r3_mask_apod_y),"reference.body":"%s" % (r3_body),"map.body":"%s" % (r3_body),"align.correlation.mode":"%s" % (refine_options.r3_corr_mode)}
	round4={"window.size":"{ %s %s }" % (int(refine_options.r4_region_x/refine_options.r4_sampling),int(refine_options.r4_region_y/refine_options.r4_sampling)),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r4_lowpass_diameter_x,refine_options.r4_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r4_lowpass_diameter_x,refine_options.r4_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r4_lowpass_apod_x,refine_options.r4_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r4_highpass_apod_x,refine_options.r4_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r4_highpass_diameter_x,refine_options.r4_highpass_diameter_y),"sampling":"%s" % (refine_options.r4_sampling),"map.sampling":"%s" % (refine_options.r4_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r4_kernel_x,refine_options.r4_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r4_peak_search_radius_x,refine_options.r4_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r4_mask_width_x,refine_options.r4_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r4_mask_width_x,refine_options.r4_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r4_mask_apod_x,refine_options.r4_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r4_mask_apod_x,refine_options.r4_mask_apod_y),"reference.body":"%s" % (r4_body),"map.body":"%s" % (r4_body),"align.correlation.mode":"%s" % (refine_options.r4_corr_mode)}
	round5={"window.size":"{ %s %s }" % (int(refine_options.r5_region_x/refine_options.r5_sampling),int(refine_options.r5_region_y/refine_options.r5_sampling)),"window.lowpass.diameter":"{ %s %s }" % (refine_options.r5_lowpass_diameter_x,refine_options.r5_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (refine_options.r5_lowpass_diameter_x,refine_options.r5_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (refine_options.r5_lowpass_apod_x,refine_options.r5_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (refine_options.r5_highpass_apod_x,refine_options.r5_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (refine_options.r5_highpass_diameter_x,refine_options.r5_highpass_diameter_y),"sampling":"%s" % (refine_options.r5_sampling),"map.sampling":"%s" % (refine_options.r5_sampling),"preprocess.mask.kernel":"{ %s %s }" % (refine_options.r5_kernel_x,refine_options.r5_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (refine_options.r5_peak_search_radius_x,refine_options.r5_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (refine_options.r5_mask_width_x,refine_options.r5_mask_width_y),"align.mask.width":"{ %s %s }" % (refine_options.r5_mask_width_x,refine_options.r5_mask_width_y),"window.mask.apodization":"{ %s %s }" % (refine_options.r5_mask_apod_x,refine_options.r5_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (refine_options.r5_mask_apod_x,refine_options.r5_mask_apod_y),"reference.body":"%s" % (r5_body),"map.body":"%s" % (r5_body),"align.correlation.mode":"%s" % (refine_options.r5_corr_mode)}
	switches={"preprocess.mask.gradient":{"%s" % (refine_options.gradient):refine_options.gradient_switch},"preprocess.mask.iter":{"%s" % (refine_options.iter_gradient):refine_options.iter_gradient_switch},"fit.orientation":{"%s" % (refine_options.orientation):refine_options.orientation_switch},"fit.azimuth":{"%s" % (refine_options.azimuth):refine_options.azimuth_switch},"fit.elevation":{"%s" % (refine_options.elevation):refine_options.elevation_switch},"fit.rotation":{"%s" % (refine_options.rotation):refine_options.rotation_switch},"fit.scale":{"%s" % (refine_options.scale):refine_options.scale_switch}}
	
	for n in range(start,start+iters):
		#change parameters depending on rounds
		if (n+1 <= start+1):
			r=1  #Round number
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % refine_options.r1_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % refine_options.r1_lp)
			lp=refine_options.r1_lp  #in angstroms
			lpx=options.r1_lowpass_diameter_x  #in Protomo units
			lpy=options.r1_lowpass_diameter_y
			body=r1_body
			region_x=refine_options.r1_region_x
			region_y=refine_options.r1_region_y
			sampling=refine_options.r1_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			for val in round1:
				apDisplay.printMsg("%s = %s" % (val,round1[val]))
				f.write("%s = %s\n" % (val,round1[val]))
				series.setparam(val,round1[val])
		elif (n+1 == start+refine_options.r1_iters+1):
			r=2
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % refine_options.r2_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % refine_options.r2_lp)
			lp=refine_options.r2_lp
			lpx=options.r2_lowpass_diameter_x
			lpy=options.r2_lowpass_diameter_y
			body=r2_body
			region_x=refine_options.r2_region_x
			region_y=refine_options.r2_region_y
			sampling=refine_options.r2_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			for val in round2:
				apDisplay.printMsg("%s = %s" % (val,round2[val]))
				f.write("%s = %s\n" % (val,round2[val]))
				series.setparam(val,round2[val])
		elif (n+1 == start+refine_options.r1_iters+refine_options.r2_iters+1):
			r=3
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % refine_options.r3_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % refine_options.r3_lp)
			lp=refine_options.r3_lp
			lpx=options.r3_lowpass_diameter_x
			lpy=options.r3_lowpass_diameter_y
			body=r3_body
			region_x=refine_options.r3_region_x
			region_y=refine_options.r3_region_y
			sampling=refine_options.r3_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			for val in round3:
				apDisplay.printMsg("%s = %s" % (val,round3[val]))
				f.write("%s = %s\n" % (val,round3[val]))
				series.setparam(val,round3[val])
		elif (n+1 == start+refine_options.r1_iters+refine_options.r2_iters+refine_options.r3_iters+1):
			r=4
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % refine_options.r4_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % refine_options.r4_lp)
			lp=refine_options.r4_lp
			lpx=options.r4_lowpass_diameter_x
			lpy=options.r4_lowpass_diameter_y
			body=r4_body
			region_x=refine_options.r4_region_x
			region_y=refine_options.r4_region_y
			sampling=refine_options.r4_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			for val in round4:
				apDisplay.printMsg("%s = %s" % (val,round4[val]))
				f.write("%s = %s\n" % (val,round4[val]))
				series.setparam(val,round4[val])
		elif (n+1 == start+refine_options.r1_iters+refine_options.r2_iters+refine_options.r3_iters+refine_options.r4_iters+1):
			r=5
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % refine_options.r5_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % refine_options.r5_lp)
			lp=refine_options.r5_lp
			lpx=options.r5_lowpass_diameter_x
			lpy=options.r5_lowpass_diameter_y
			body=r5_body
			region_x=refine_options.r5_region_x
			region_y=refine_options.r5_region_y
			sampling=refine_options.r5_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*refine_options.pixelsize, 2*sampling*refine_options.pixelsize))
			for val in round5:
				apDisplay.printMsg("%s = %s" % (val,round5[val]))
				f.write("%s = %s\n" % (val,round5[val]))
				series.setparam(val,round5[val])
		else:
			apDisplay.printMsg("No Round parameters changed for Iteration #%s\n" % (n+1))
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			f.write("No Round parameters changed for Iteration #%s\n\n" % (n+1))
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
		
		#change parameters depending on switches
		toggle=0
		for switch in switches:
			for key in switches[switch]:
				if (switches[switch][key] == n+1-start):
					toggle=1
					if (key == "true"):
						newval="false"
						apDisplay.printMsg("%s switched from true to false on Iteration #%s" % (switch, n+1))
						f.write("%s switched from true to false on Iteration #%s\n" % (switch, n+1))
					else:
						newval="true"
						apDisplay.printMsg("%s switched from false to true on Iteration #%s" % (switch, n+1))
						f.write("%s switched from false to true on Iteration #%s\n" % (switch, n+1))
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
					apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
					f.write("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)...\n" % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
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
					apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
					f.write("Refinement Iteration #%s failed after resampling the search area %s time(s).\n" % (start+n+1, retry-1))
					f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
					f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
					f.write("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n\n")
					brk=1
				pass
		
		apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement!\n" % (n+1,r))
		f.write("Finished Iteration #%s, Round #%s Refinement!\n\n" % (n+1,r))
		if (brk != None):   #resampling failed, break out of all refinement iterations
			return
		
		it="%03d" % (n)
		itt="%02d" % (n+1)
		ittt="%02d" % (n)
		#ite="_ite%03d" % (n+start)
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		series.corr(corrfile)
		series.fit()
		series.update()

		#archive results
		tiltfile=basename+'.tlt'
		series.geom(0).write(tiltfile)
		tiltfilename_full=tiltdir+'/'+tiltfile
		
		#Produce quality assessment statistics and plot image using corrfile information
		apDisplay.printMsg("Creating quality assessment statistics...")
		f.write("Creating quality assessment statistics...\n")
		numcorrfiles=len(glob.glob1(tiltdir,'*.corr'))
		for i in range(numcorrfiles):
			it="%03d" % (i)
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			try:  #Sometimes Protomo fails to write a corr file correctly...I don't understand this
				CCMS_shift, CCMS_rots, CCMS_scale, CCMS_sum = apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, corrfile)
			except NoneType:
				apDisplay.printMsg("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.")
				f.write("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.\n")
			if i == numcorrfiles-1:
				apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, refine_options.sessionname, name, tiltdir, start+refine_options.r1_iters, refine_options.r1_sampling, refine_options.r1_lp, start+refine_options.r2_iters, refine_options.r2_sampling, refine_options.r2_lp, start+refine_options.r3_iters, refine_options.r3_sampling, refine_options.r3_lp, start+refine_options.r4_iters, refine_options.r4_sampling, refine_options.r4_lp, start+refine_options.r5_iters, refine_options.r5_sampling, refine_options.r5_lp)
		it="%03d" % (n)
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		
		apDisplay.printMsg("\033[43mCCMS(shift) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_shift,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[46mCCMS(rotations) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_rots,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[43mCCMS(scale) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_scale,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[1mThe scaled sum of CCMS values is %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_sum,5), n+1, tiltseriesnumber))
		f.write("CCMS(shift) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_shift,5), n+1, tiltseriesnumber))
		f.write("CCMS(rotations) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_rots,5), n+1, tiltseriesnumber))
		f.write("CCMS(scale) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_scale,5), n+1, tiltseriesnumber))
		f.write("The scaled sum of CCMS values is %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_sum,5), n+1, tiltseriesnumber))
		
		apDisplay.printMsg("Creating Refinement Depiction Videos")
		f.write("Creating Refinement Depiction Videos\n")
		apProTomo2Aligner.makeCorrPeakVideos(name, it, tiltdir, 'out', refine_options.video_type, "Refinement")  #Correlation peak videos are always made.
		apProTomo2Aligner.makeCorrPlotImages(name, it, tiltdir, corrfile)  #Correlation plots are always made.
		apProTomo2Aligner.makeAngleRefinementPlots(tiltdir, name)  #Refinement plots are always made.
		if (refine_options.all_tilt_videos == "true"):  #Tilt series videos are only made if requested
			apDisplay.printMsg("Creating Refinement tilt-series video...")
			f.write("Creating Refinement tilt-series video...\n")
			apProTomo2Aligner.makeTiltSeriesVideos(name, it, tiltfilename_full, rawimagecount, tiltdir, raw_path, refine_options.pixelsize, refine_options.map_sampling, refine_options.image_file_type, refine_options.video_type, "true", refine_options.parallel, "Refinement")
		if (refine_options.all_recon_videos == "true"):  #Reconstruction videos are only made if requested
			apDisplay.printMsg("Generating Refinement reconstruction...")
			f.write("Generating Refinement reconstruction...\n")
			#Rescale if necessary
			if refine_options.map_sampling != sampling:
				new_map_sampling='%s' % refine_options.map_sampling
				series.setparam("sampling",new_map_sampling)
				series.setparam("map.sampling",new_map_sampling)
				
				#Rescale the lowpass and body for depiction
				new_lp_x = lpx*refine_options.map_sampling/sampling
				new_lp_y = lpy*refine_options.map_sampling/sampling
				new_body = body*sampling/refine_options.map_sampling
				series.setparam("map.lowpass.diameter", "{ %s %s }" % (new_lp_x, new_lp_y))
				series.setparam("map.body", "%s" % (new_body))
				
				series.mapfile()
				
				#Reset sampling values for next iteration
				series.setparam("sampling",'%s' % sampling)
				series.setparam("map.sampling",'%s' % sampling)
			else:
				series.mapfile()
			
			apProTomo2Aligner.makeReconstructionVideos(name, itt, tiltdir, region_x, region_y, 'true', 'out', refine_options.pixelsize, sampling, refine_options.map_sampling, lp, thickness, refine_options.video_type, "false", refine_options.parallel, align_step="Refinement")
	
		if final_retry > 0:
			apDisplay.printMsg("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small." % (n+1, final_retry))
			apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
			apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
			f.write("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small.\n" % (n+1, final_retry))
			f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
			f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
	apDisplay.printMsg("Refinement Finished for Tilt-Series #%s!" % tiltseriesnumber)
	f.write("Refinement Finished for Tilt-Series #%s!\n" % tiltseriesnumber)
	f.close()
	
	
def protomoReconstruct(log_file, tiltseriesnumber, recon_options):
	"""
	Reconstruct a tilt-series by Protomo weighted back-pojection.
	Options are given to specify which iteration to reconstruct
	from and whether to exclude any very high tilts.
	Options are given for filtering.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(recon_options.rundir, tiltseriesnumber, prep="False")
	f = open(log_file,'a')
	os.chdir(tiltdir)
	
	if recon_options.recon_iter_presets == "BestBin1or2":
		try:
			best=glob.glob(tiltdir+'/best_bin1or2*')
			filename, recon_iter = os.path.splitext(best[0])
			recon_iter=int(recon_iter[1:])
		except:
			apDisplay.printWarning("A binned by 1 or 2 iteration hasn't been run. Reconstructing with the best iteration overall...")
			f.write("A binned by 1 or 2 iteration hasn't been run. Reconstructing with the best iteration overall...\n")
			best=glob.glob(tiltdir+'/best.*')
			filename, recon_iter = os.path.splitext(best[0])
			recon_iter=int(recon_iter[1:])
	elif recon_options.recon_iter_presets == "Best":
		best=glob.glob(tiltdir+'/best.*')
		filename, recon_iter = os.path.splitext(best[0])
		recon_iter=int(recon_iter[1:])
	elif recon_options.recon_iter_presets == "Worst":
		worst=glob.glob(tiltdir+'/worst*')
		filename, recon_iter = os.path.splitext(worst[0])
		recon_iter=int(recon_iter[1:])
	elif recon_options.recon_iter_presets == "Last":
		numtiltfiles = len(glob.glob(tiltdir+'/s*tlt'))
		recon_iter = int(numtiltfiles)-1  #Minus 1 because seriesXXX.tlt also exists
	elif recon_options.recon_iter_presets == "Custom":
		recon_iter = recon_options.recon_iter
	else: #User failed
		apDisplay.printError("You must either choose a preset for the reconstruction iteration, or choose a specific iteration.")
		f.write("You must either choose a preset for the reconstruction iteration, or choose a specific iteration.\n")
		sys.exit()
	
	apDisplay.printMsg("Tilt-Series #%s Reconstructing by weighted back-projection from iteration #%s" % (tiltseriesnumber, recon_iter))
	f.write("Tilt-Series #%s Reconstructing by weighted back-projection from iteration #%s" % (tiltseriesnumber, recon_iter))
	it="%03d" % (recon_iter)
	itt="%03d" % (recon_iter-1)  #Minus 1 because Protomo starts counting with zero
	param_out=seriesname+'.param'
	param_out_full=tiltdir+'/'+param_out
	tilt_out_full=tiltdir+'/'+seriesname+itt+'.tlt'
	recon_dir=tiltdir+'/recons/'
	os.system('mkdir %s 2>/dev/null' % recon_dir)
	recon_param_out_full=recon_dir+'/'+param_out
	recon_tilt_out_full=recon_dir+'/'+seriesname+'.tlt'
	recon_cache_dir=recon_dir+'/cache'
	recon_out_dir=recon_dir+'out'
	os.system('cp %s %s' % (tilt_out_full, recon_tilt_out_full))
	os.system('cp %s %s' % (param_out_full,recon_param_out_full))
	
	# Remove high tilts from .tlt file if user requests
	if (recon_options.positive < 90) or (recon_options.negative > -90):
		removed_images, mintilt, maxtilt = apProTomo2Aligner.removeHighTiltsFromTiltFile(recon_tilt_out_full, recon_options.negative, recon_options.positive)
		apDisplay.printMsg("Images %s have been removed before reconstruction by weighted back-projection" % removed_images)
		f.write("Images %s have been removed before reconstruction by weighted back-projection\n" % removed_images)
	else:
		mintilt=0
		maxtilt=0
		for i in range(tiltstart-1,tiltstart+rawimagecount-1):
			cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, recon_tilt_out_full)
			proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			tilt_angle=float(tilt_angle)
			mintilt=min(mintilt,tilt_angle)
			maxtilt=max(maxtilt,tilt_angle)
	
	# Backup then edit the Refinement param file, changing the map size, map sampling, cache dir, and out dir
	refine_param_full=tiltdir+'/'+'refine_'+param_out
	command="cp %s %s" % (param_out_full, refine_param_full)
	os.system(command)
	command1="grep -n 'AP sampling' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
	proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
	(samplingline, err) = proc.communicate()
	samplingline=int(samplingline)
	command2="grep -n 'AP reconstruction map size' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
	proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
	(mapsizeline, err) = proc.communicate()
	mapsizeline=int(mapsizeline)
	command3="grep -n 'AP reconstruction map sampling' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
	proc=subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True)
	(mapsamplingline, err) = proc.communicate()
	mapsamplingline=int(mapsamplingline)
	command11="sed -i \"%ss/.*/ S = %s             (* AP sampling *)/\" %s" % (samplingline, recon_options.recon_map_sampling, recon_param_out_full)
	os.system(command11)
	command22="sed -i \"%ss/.*/   size: { %s, %s, %s }  (* AP reconstruction map size *)/\" %s" % (mapsizeline, int(recon_options.recon_map_size_x/recon_options.recon_map_sampling), int(recon_options.recon_map_size_y/recon_options.recon_map_sampling), int(round(recon_options.recon_thickness/(recon_options.pixelsize*recon_options.recon_map_sampling))), recon_param_out_full)
	os.system(command22)
	command33="sed -i \"%ss/.*/   sampling: %s  (* AP reconstruction map sampling *)/\" %s" % (mapsamplingline, recon_options.recon_map_sampling, recon_param_out_full)
	os.system(command33)
	command4="grep -n 'cachedir' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
	proc=subprocess.Popen(command4, stdout=subprocess.PIPE, shell=True)
	(cachedirline, err) = proc.communicate()
	cachedirline=int(cachedirline)
	command5="grep -n 'outdir' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
	proc=subprocess.Popen(command5, stdout=subprocess.PIPE, shell=True)
	(outdirline, err) = proc.communicate()
	outdirline=int(outdirline)
	command44="sed -i \'%ss|.*| cachedir: \"%s\"  (* AP directory where cache files are stored *)|\' %s" % (cachedirline, recon_cache_dir, recon_param_out_full)
	os.system(command44)
	command55="sed -i \'%ss|.*| outdir: \"%s\"  (* AP directory where other output files are stored *)|\' %s" % (outdirline, recon_out_dir, recon_param_out_full)
	os.system(command55)
	
	#Lowpass filter reconstruction?
	cmd="grep -n 'AP lowpass map' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(lowpassmapline, err) = proc.communicate()
	lowpassmapline=int(lowpassmapline)
	if recon_options.recon_lowpass == "False":
		lp=''
		#Remove lowpass filter from param
		cmd2="sed -i \"%ss/.*//\" %s;" % (lowpassmapline, recon_param_out_full)
		cmd2+="sed -i \"%ss/.*//\" %s;" % (lowpassmapline+1, recon_param_out_full)
		cmd2+="sed -i \"%ss/.*//\" %s;" % (lowpassmapline+2, recon_param_out_full)
		cmd2+="sed -i \"%ss/.*//\" %s" % (lowpassmapline+3, recon_param_out_full)
		
		#Set preprocessing to false
		cmd3="grep -n 'AP enable or disable preprocessing of raw images' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(preprocessingline, err) = proc.communicate()
		preprocessingline=int(preprocessingline)
		
		cmd33="sed -i \'%ss|.*| preprocessing: false  (* AP enable or disable preprocessing of raw images *)|\' %s" % (preprocessingline, recon_param_out_full)
		os.system(cmd33)
	else:
		lpavg = int((recon_options.recon_lp_diam_x+recon_options.recon_lp_diam_y)/2)
		lp='.lp%s' % lpavg
		recon_options.recon_lp_diam_x = 2*recon_options.pixelsize*recon_options.recon_map_sampling/recon_options.recon_lp_diam_x
		recon_options.recon_lp_diam_y = 2*recon_options.pixelsize*recon_options.recon_map_sampling/recon_options.recon_lp_diam_y
		cmd2="sed -i \"%ss/.*/     diameter:    { %s, %s } * S/\" %s" % (lowpassmapline+1, recon_options.recon_lp_diam_x, recon_options.recon_lp_diam_y, recon_param_out_full)
	os.system(cmd2)
		
	dim='%sx%s' % (recon_options.recon_map_size_x,recon_options.recon_map_size_y)
	ang='%sto%s' % (round(mintilt,1),round(maxtilt,1))
	img=seriesname+'00_bck.img'
	mrcf=seriesname+'_ite'+it+'_dim'+dim+'_ang'+ang+'_bck.bin'+str(recon_options.recon_map_sampling)+lp+'.mrc'
	mrcfn=seriesname+'_ite'+it+'_dim'+dim+'_ang'+ang+'_bck.bin'+str(recon_options.recon_map_sampling)+lp+'.norm.mrc'
	img_full=recon_out_dir+'/'+img
	mrc_full=recon_out_dir+'/'+mrcf
	mrcn_full=recon_out_dir+'/'+mrcfn
	
	# Create reconstruction
	os.chdir(recon_dir)
	os.system("rm %s/cache/%s* %s/*i3t 2>/dev/null" % (recon_dir, seriesname, recon_dir))
	seriesparam=protomo.param(recon_param_out_full)
	seriesgeom=protomo.geom(recon_tilt_out_full)
	series=protomo.series(seriesparam,seriesgeom)
	series.setparam("map.logging","true")
	series.mapfile()
	os.chdir(tiltdir)
	
	# Restore refine param file
	command="cp %s %s" % (refine_param_full, param_out_full)
	os.system(command)
	
	# Convert to mrc
	os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
	os.system("rm %s" % img_full)
	
	# Normalize
	try:
		command="e2proc3d.py %s %s --process=normalize" % (mrc_full, mrcn_full)
		proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		(code, err) = proc.communicate()
	except:
		pass
	
	if proc.returncode != 0:
		apDisplay.printMsg("\ne2proc3d not found or failed to process reconstruction. Trying proc3d...")
		f.write("\ne2proc3d not found or failed to process reconstruction. Trying proc3d...\n")
		try:
			command="proc3d %s %s norm" % (mrc_full, mrcn_full)
			proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
			(code, err) = proc.communicate()
		except:
			pass
	if proc.returncode != 0:
		apDisplay.printMsg("\nproc3d not found or failed to process reconstruction. Skipping normalization.")
		f.write("\nproc3d not found or failed to process reconstruction. Skipping normalization.\n")
	else:
		os.system('rm %s' % mrc_full)
	
	# Link reconstruction to directory
	try:
		cmd1="mkdir -p %s 2>/dev/null; rm %s/%s %s/%s 2>/dev/null; ln -f %s %s 2>/dev/null" % (recon_options.link_recons, recon_options.link_recons, mrcf, recon_options.link_recons, mrcfn, mrc_full, recon_options.link_recons)
		cmd2="mkdir -p %s 2>/dev/null; rm %s/%s %s/%s 2>/dev/null; ln -f %s %s" % (recon_options.link_recons, recon_options.link_recons, mrcf, recon_options.link_recons, mrcfn, mrcn_full, recon_options.link_recons)
		try:
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(code, err) = proc.communicate()
		except:
			pass
		if proc.returncode != 0:
			try:
				proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
				(code, err) = proc.communicate()
			except:
				pass
		
		apDisplay.printMsg("Reconstruction can be found in this directory:")
		f.write("Reconstruction can be found in this directory:\n")
		if (recon_options.link_recons == None) or (recon_options.link_recons == "") or (len(recon_options.link_recons) < 1):
			print "\n%s\n" % (recon_out_dir)
		else:
			print "\n%s\n" % (recon_options.link_recons)
	except:
		apDisplay.printMsg("Reconstruction can be found in this directory:")
		f.write("Reconstruction can be found in this directory:\n")
		print "\n%s\n" % (recon_out_dir)
		if proc.returncode != 0:
			apDisplay.printMsg("The reconstruction in the above directory is not normalized because EMAN1 and EMAN2 were either not found or failed to process the reconstruction.")
			f.write("The reconstruction in the above directory is not normalized because EMAN1 and EMAN2 were either not found or failed to process the reconstruction.\n")
		
	os.system("rm %s/cache/%s* %s/*i3t" % (recon_dir, seriesname, recon_dir))
	f.close()


def ctfCorrect(tiltseriesnumber, ctf_options):
	"""
	This corrects for ctf using ctfphaseflip. A defocus plot and a CTF plot are made.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(ctf_options.rundir, tiltseriesnumber, prep="False")
	os.chdir(tiltdir)
	apProTomo2Prep.ctfCorrect(seriesname, tiltdir, ctf_options.projectid, ctf_options.sessionname, tiltseriesnumber, tiltfilename_full, ctf_options.frame_aligned, ctf_options.pixelsize, ctf_options.DefocusTol, ctf_options.iWidth, ctf_options.amp_contrast)


def doseCompensate(tiltseriesnumber, dose_options):
	"""
	This compensates for dose using equation (3) from Grant & Grigorieff, 2015.
	A dose plot and a dose compensation plot are made.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(dose_options.rundir, tiltseriesnumber, prep="False")
	os.chdir(tiltdir)
	apProTomo2Prep.doseCompensate(seriesname, tiltdir, dose_options.sessionname, tiltseriesnumber, dose_options.frame_aligned, raw_path, dose_options.pixelsize, dose_options.dose_presets, dose_options.dose_a, dose_options.dose_b, dose_options.dose_c)


def protomoAutoRefine(log_file, tiltseriesnumber, auto_refine_options):
	"""
	Performs Protomo area matching alignment in a fully automated fashion:
		The first 3 rounds are performed as usual.
		The 4th and 5th rounds test for convergence.
		If convergence is not met, rounds 6-8 are performed with scaling turned on and elevation turned on half way.
	Correlation peak videos are made.
	Quality assessment statistics and images are made.
	Depiction videos are made if requested.
	"""
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(auto_refine_options.rundir, tiltseriesnumber, prep="False")
	f = open(log_file,'a')
	os.chdir(tiltdir)
	cos_alpha=np.cos(maxtilt*np.pi/180)
	name=seriesname
	refine_param_full=tiltdir+'/'+name+'.param'
	cpparam="cp %s %s/%s.param" % (auto_refine_options.refine_param_file,tiltdir,name)
	os.system(cpparam)
	body,sampling,orig_thickness,map_sampling,orig_lp,region_x,region_y = getParamValues(refine_param_full, cos_alpha, "no change")
	thickness=int(round(orig_thickness*auto_refine_options.pixelsize))
	editParamFile(tiltdir, refine_param_full, raw_path)
	start=0  #Counter for prevous iterations
	i3tfile=tiltdir+'/'+seriesname+'.i3t'
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
	
	#Next two rounds are tested for convergence
	r1_body=float((orig_thickness/auto_refine_options.r1_sampling)/cos_alpha)
	r2_body=float((orig_thickness/auto_refine_options.r2_sampling)/cos_alpha)
	r3_body=float((orig_thickness/auto_refine_options.r3_sampling)/cos_alpha)
	
	iters=auto_refine_options.r1_iters+auto_refine_options.r2_iters+auto_refine_options.r3_iters
	round1={"window.size":"{ %s %s }" % (int(auto_refine_options.r1_region_x/auto_refine_options.r1_sampling),int(auto_refine_options.r1_region_y/auto_refine_options.r1_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r1_lowpass_diameter_x,auto_refine_options.r1_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r1_lowpass_diameter_x,auto_refine_options.r1_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r1_lowpass_apod_x,auto_refine_options.r1_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r1_highpass_apod_x,auto_refine_options.r1_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r1_highpass_diameter_x,auto_refine_options.r1_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r1_sampling),"map.sampling":"%s" % (auto_refine_options.r1_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r1_kernel_x,auto_refine_options.r1_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r1_peak_search_radius_x,auto_refine_options.r1_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r1_mask_width_x,auto_refine_options.r1_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r1_mask_width_x,auto_refine_options.r1_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r1_mask_apod_x,auto_refine_options.r1_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r1_mask_apod_x,auto_refine_options.r1_mask_apod_y),"reference.body":"%s" % (r1_body),"map.body":"%s" % (r1_body),"align.correlation.mode":"%s" % (auto_refine_options.r1_corr_mode)}
	round2={"window.size":"{ %s %s }" % (int(auto_refine_options.r2_region_x/auto_refine_options.r2_sampling),int(auto_refine_options.r2_region_y/auto_refine_options.r2_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r2_lowpass_diameter_x,auto_refine_options.r2_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r2_lowpass_diameter_x,auto_refine_options.r2_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r2_lowpass_apod_x,auto_refine_options.r2_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r2_highpass_apod_x,auto_refine_options.r2_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r2_highpass_diameter_x,auto_refine_options.r2_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r2_sampling),"map.sampling":"%s" % (auto_refine_options.r2_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r2_kernel_x,auto_refine_options.r2_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r2_peak_search_radius_x,auto_refine_options.r2_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r2_mask_width_x,auto_refine_options.r2_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r2_mask_width_x,auto_refine_options.r2_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r2_mask_apod_x,auto_refine_options.r2_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r2_mask_apod_x,auto_refine_options.r2_mask_apod_y),"reference.body":"%s" % (r2_body),"map.body":"%s" % (r2_body),"align.correlation.mode":"%s" % (auto_refine_options.r2_corr_mode)}
	round3={"window.size":"{ %s %s }" % (int(auto_refine_options.r3_region_x/auto_refine_options.r3_sampling),int(auto_refine_options.r3_region_y/auto_refine_options.r3_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r3_lowpass_diameter_x,auto_refine_options.r3_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r3_lowpass_diameter_x,auto_refine_options.r3_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r3_lowpass_apod_x,auto_refine_options.r3_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r3_highpass_apod_x,auto_refine_options.r3_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r3_highpass_diameter_x,auto_refine_options.r3_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r3_sampling),"map.sampling":"%s" % (auto_refine_options.r3_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r3_kernel_x,auto_refine_options.r3_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r3_peak_search_radius_x,auto_refine_options.r3_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r3_mask_width_x,auto_refine_options.r3_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r3_mask_width_x,auto_refine_options.r3_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r3_mask_apod_x,auto_refine_options.r3_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r3_mask_apod_x,auto_refine_options.r3_mask_apod_y),"reference.body":"%s" % (r3_body),"map.body":"%s" % (r3_body),"align.correlation.mode":"%s" % (auto_refine_options.r3_corr_mode)}
	
	for n in range(start,start+iters):
		#change parameters depending on rounds
		if (n+1 <= start+1):
			r=1  #Round number
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r1_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r1_lp)
			lp=auto_refine_options.r1_lp  #in angstroms
			lpx=options.r1_lowpass_diameter_x  #in Protomo units
			lpy=options.r1_lowpass_diameter_y
			body=r1_body
			region_x=auto_refine_options.r1_region_x
			region_y=auto_refine_options.r1_region_y
			sampling=auto_refine_options.r1_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			for val in round1:
				apDisplay.printMsg("%s = %s" % (val,round1[val]))
				f.write("%s = %s\n" % (val,round1[val]))
				series.setparam(val,round1[val])
		elif (n+1 == start+auto_refine_options.r1_iters+1):
			r=2
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r2_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r2_lp)
			lp=auto_refine_options.r2_lp
			lpx=options.r2_lowpass_diameter_x
			lpy=options.r2_lowpass_diameter_y
			body=r2_body
			region_x=auto_refine_options.r2_region_x
			region_y=auto_refine_options.r2_region_y
			sampling=auto_refine_options.r2_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			for val in round2:
				apDisplay.printMsg("%s = %s" % (val,round2[val]))
				f.write("%s = %s\n" % (val,round2[val]))
				series.setparam(val,round2[val])
		elif (n+1 == start+auto_refine_options.r1_iters+auto_refine_options.r2_iters+1):
			r=3
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r3_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r3_lp)
			lp=auto_refine_options.r3_lp
			lpx=options.r3_lowpass_diameter_x
			lpy=options.r3_lowpass_diameter_y
			body=r3_body
			region_x=auto_refine_options.r3_region_x
			region_y=auto_refine_options.r3_region_y
			sampling=auto_refine_options.r3_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			for val in round3:
				apDisplay.printMsg("%s = %s" % (val,round3[val]))
				f.write("%s = %s\n" % (val,round3[val]))
				series.setparam(val,round3[val])
		else:
			apDisplay.printMsg("No Round parameters changed for Iteration #%s\n" % (n+1))
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			f.write("No Round parameters changed for Iteration #%s\n\n" % (n+1))
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
		
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
					apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
					f.write("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)...\n" % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
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
					apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
					f.write("Refinement Iteration #%s failed after resampling the search area %s time(s).\n" % (start+n+1, retry-1))
					f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
					f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
					f.write("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n\n")
					brk=1
				pass
		
		apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement!\n" % (n+1,r))
		f.write("Finished Iteration #%s, Round #%s Refinement!\n\n" % (n+1,r))
		if (brk != None):   #resampling failed, break out of all refinement iterations
			return
		
		it="%03d" % (n)
		itt="%02d" % (n+1)
		ittt="%02d" % (n)
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		series.corr(corrfile)
		series.fit()
		series.update()

		#archive results
		tiltfile=basename+'.tlt'
		series.geom(0).write(tiltfile)
		tiltfilename_full=tiltdir+'/'+tiltfile
		
		#Produce quality assessment statistics and plot image using corrfile information
		apDisplay.printMsg("Creating quality assessment statistics...")
		f.write("Creating quality assessment statistics...\n")
		numcorrfiles=len(glob.glob1(tiltdir,'*.corr'))
		for i in range(numcorrfiles):
			it="%03d" % (i)
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			try:  #Sometimes Protomo fails to write a corr file correctly...I don't understand this
				CCMS_shift, CCMS_rots, CCMS_scale, CCMS_sum = apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, corrfile)
			except NoneType:
				apDisplay.printMsg("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.")
				f.write("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.\n")
			if i == numcorrfiles-1:
				apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, auto_refine_options.sessionname, name, tiltdir, start+auto_refine_options.r1_iters, auto_refine_options.r1_sampling, auto_refine_options.r1_lp, start+auto_refine_options.r2_iters, auto_refine_options.r2_sampling, auto_refine_options.r2_lp, start+auto_refine_options.r3_iters, auto_refine_options.r3_sampling, auto_refine_options.r3_lp, start+auto_refine_options.r4_iters, auto_refine_options.r4_sampling, auto_refine_options.r4_lp, start+auto_refine_options.r5_iters, auto_refine_options.r5_sampling, auto_refine_options.r5_lp)
		it="%03d" % (n)
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		
		apDisplay.printMsg("\033[43mCCMS(shift) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_shift,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[46mCCMS(rotations) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_rots,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[43mCCMS(scale) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_scale,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[1mThe scaled sum of CCMS values is %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_sum,5), n+1, tiltseriesnumber))
		f.write("CCMS(shift) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_shift,5), n+1, tiltseriesnumber))
		f.write("CCMS(rotations) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_rots,5), n+1, tiltseriesnumber))
		f.write("CCMS(scale) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_scale,5), n+1, tiltseriesnumber))
		f.write("The scaled sum of CCMS values is %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_sum,5), n+1, tiltseriesnumber))
		
		apDisplay.printMsg("Creating Refinement Depiction Videos")
		f.write("Creating Refinement Depiction Videos\n")
		apProTomo2Aligner.makeCorrPeakVideos(name, it, tiltdir, 'out', auto_refine_options.video_type, "Refinement")  #Correlation peak videos are always made.
		apProTomo2Aligner.makeCorrPlotImages(name, it, tiltdir, corrfile)  #Correlation plots are always made.
		apProTomo2Aligner.makeAngleRefinementPlots(tiltdir, name)  #Refinement plots are always made.
		if (auto_refine_options.all_tilt_videos == "true"):  #Tilt series videos are only made if requested
			apDisplay.printMsg("Creating Refinement tilt-series video...")
			f.write("Creating Refinement tilt-series video...\n")
			apProTomo2Aligner.makeTiltSeriesVideos(name, it, tiltfilename_full, rawimagecount, tiltdir, raw_path, auto_refine_options.pixelsize, auto_refine_options.map_sampling, auto_refine_options.image_file_type, auto_refine_options.video_type, "true", auto_refine_options.parallel, "Refinement")
		if (auto_refine_options.all_recon_videos == "true"):  #Reconstruction videos are only made if requested
			apDisplay.printMsg("Generating Refinement reconstruction...")
			f.write("Generating Refinement reconstruction...\n")
			#Rescale if necessary
			if auto_refine_options.map_sampling != sampling:
				new_map_sampling='%s' % auto_refine_options.map_sampling
				series.setparam("sampling",new_map_sampling)
				series.setparam("map.sampling",new_map_sampling)
				
				#Rescale the lowpass and body for depiction
				new_lp_x = lpx*auto_refine_options.map_sampling/sampling
				new_lp_y = lpy*auto_refine_options.map_sampling/sampling
				new_body = body*sampling/auto_refine_options.map_sampling
				series.setparam("map.lowpass.diameter", "{ %s %s }" % (new_lp_x, new_lp_y))
				series.setparam("map.body", "%s" % (new_body))
				
				series.mapfile()
				
				#Reset sampling values for next iteration
				series.setparam("sampling",'%s' % sampling)
				series.setparam("map.sampling",'%s' % sampling)
			else:
				series.mapfile()
			
			apProTomo2Aligner.makeReconstructionVideos(name, itt, tiltdir, region_x, region_y, 'true', 'out', auto_refine_options.pixelsize, sampling, auto_refine_options.map_sampling, lp, thickness, auto_refine_options.video_type, "false", auto_refine_options.parallel, align_step="Refinement")
	
		if final_retry > 0:
			apDisplay.printMsg("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small." % (n+1, final_retry))
			apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
			apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
			f.write("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small.\n" % (n+1, final_retry))
			f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
			f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
	
	#Next two rounds are tested for convergence
	start = start + iters
	iteration_countdown=0
	countdown_flag=0
	
	r4_body=float((orig_thickness/auto_refine_options.r4_sampling)/cos_alpha)
	r5_body=float((orig_thickness/auto_refine_options.r5_sampling)/cos_alpha)
	
	iters=auto_refine_options.r4_iters+auto_refine_options.r5_iters
	round4={"window.size":"{ %s %s }" % (int(auto_refine_options.r4_region_x/auto_refine_options.r4_sampling),int(auto_refine_options.r4_region_y/auto_refine_options.r4_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r4_lowpass_diameter_x,auto_refine_options.r4_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r4_lowpass_diameter_x,auto_refine_options.r4_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r4_lowpass_apod_x,auto_refine_options.r4_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r4_highpass_apod_x,auto_refine_options.r4_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r4_highpass_diameter_x,auto_refine_options.r4_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r4_sampling),"map.sampling":"%s" % (auto_refine_options.r4_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r4_kernel_x,auto_refine_options.r4_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r4_peak_search_radius_x,auto_refine_options.r4_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r4_mask_width_x,auto_refine_options.r4_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r4_mask_width_x,auto_refine_options.r4_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r4_mask_apod_x,auto_refine_options.r4_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r4_mask_apod_x,auto_refine_options.r4_mask_apod_y),"reference.body":"%s" % (r4_body),"map.body":"%s" % (r4_body),"align.correlation.mode":"%s" % (auto_refine_options.r4_corr_mode)}
	round5={"window.size":"{ %s %s }" % (int(auto_refine_options.r5_region_x/auto_refine_options.r5_sampling),int(auto_refine_options.r5_region_y/auto_refine_options.r5_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r5_lowpass_diameter_x,auto_refine_options.r5_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r5_lowpass_diameter_x,auto_refine_options.r5_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r5_lowpass_apod_x,auto_refine_options.r5_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r5_highpass_apod_x,auto_refine_options.r5_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r5_highpass_diameter_x,auto_refine_options.r5_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r5_sampling),"map.sampling":"%s" % (auto_refine_options.r5_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r5_kernel_x,auto_refine_options.r5_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r5_peak_search_radius_x,auto_refine_options.r5_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r5_mask_width_x,auto_refine_options.r5_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r5_mask_width_x,auto_refine_options.r5_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r5_mask_apod_x,auto_refine_options.r5_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r5_mask_apod_x,auto_refine_options.r5_mask_apod_y),"reference.body":"%s" % (r5_body),"map.body":"%s" % (r5_body),"align.correlation.mode":"%s" % (auto_refine_options.r5_corr_mode)}
	
	for n in range(start,start+iters):
		#change parameters depending on rounds
		if (n+1 <= start+1):
			r=4
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r4_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r4_lp)
			lp=auto_refine_options.r4_lp
			lpx=options.r4_lowpass_diameter_x
			lpy=options.r4_lowpass_diameter_y
			body=r4_body
			region_x=auto_refine_options.r4_region_x
			region_y=auto_refine_options.r4_region_y
			sampling=auto_refine_options.r4_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			for val in round4:
				apDisplay.printMsg("%s = %s" % (val,round4[val]))
				f.write("%s = %s\n" % (val,round4[val]))
				series.setparam(val,round4[val])
		elif (n+1 == start+auto_refine_options.r4_iters+1):
			r=5
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r5_lp)
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r5_lp)
			lp=auto_refine_options.r5_lp
			lpx=options.r5_lowpass_diameter_x
			lpy=options.r5_lowpass_diameter_y
			body=r5_body
			region_x=auto_refine_options.r5_region_x
			region_y=auto_refine_options.r5_region_y
			sampling=auto_refine_options.r5_sampling
			apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
			for val in round5:
				apDisplay.printMsg("%s = %s" % (val,round5[val]))
				f.write("%s = %s\n" % (val,round5[val]))
				series.setparam(val,round5[val])
		else:
			apDisplay.printMsg("No Round parameters changed for Iteration #%s\n" % (n+1))
			apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
			f.write("No Round parameters changed for Iteration #%s\n\n" % (n+1))
			f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
		
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
					apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
					f.write("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)...\n" % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
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
					apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
					f.write("Refinement Iteration #%s failed after resampling the search area %s time(s).\n" % (start+n+1, retry-1))
					f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
					f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
					f.write("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n\n")
					brk=1
				pass
		
		apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement!\n" % (n+1,r))
		f.write("Finished Iteration #%s, Round #%s Refinement!\n\n" % (n+1,r))
		if (brk != None):   #resampling failed, break out of all refinement iterations
			return
		
		it="%03d" % (n)
		itt="%02d" % (n+1)
		ittt="%02d" % (n)
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		series.corr(corrfile)
		series.fit()
		series.update()

		#archive results
		tiltfile=basename+'.tlt'
		series.geom(0).write(tiltfile)
		tiltfilename_full=tiltdir+'/'+tiltfile
		
		#Produce quality assessment statistics and plot image using corrfile information
		apDisplay.printMsg("Creating quality assessment statistics...")
		f.write("Creating quality assessment statistics...\n")
		numcorrfiles=len(glob.glob1(tiltdir,'*.corr'))
		for i in range(numcorrfiles):
			it="%03d" % (i)
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			try:  #Sometimes Protomo fails to write a corr file correctly...I don't understand this
				CCMS_shift, CCMS_rots, CCMS_scale, CCMS_sum = apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, corrfile)
			except NoneType:
				apDisplay.printMsg("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.")
				f.write("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.\n")
			if i == numcorrfiles-1:
				apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, auto_refine_options.sessionname, name, tiltdir, auto_refine_options.r1_iters, auto_refine_options.r1_sampling, auto_refine_options.r1_lp, auto_refine_options.r2_iters, auto_refine_options.r2_sampling, auto_refine_options.r2_lp, auto_refine_options.r3_iters, auto_refine_options.r3_sampling, auto_refine_options.r3_lp, auto_refine_options.r4_iters, auto_refine_options.r4_sampling, auto_refine_options.r4_lp, auto_refine_options.r5_iters, auto_refine_options.r5_sampling, auto_refine_options.r5_lp)
		it="%03d" % (n)
		basename='%s%s' % (name,it)
		corrfile=basename+'.corr'
		
		apDisplay.printMsg("\033[43mCCMS(shift) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_shift,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[46mCCMS(rotations) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_rots,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[43mCCMS(scale) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_scale,5), n+1, tiltseriesnumber))
		apDisplay.printMsg("\033[1mThe scaled sum of CCMS values is %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_sum,5), n+1, tiltseriesnumber))
		f.write("CCMS(shift) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_shift,5), n+1, tiltseriesnumber))
		f.write("CCMS(rotations) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_rots,5), n+1, tiltseriesnumber))
		f.write("CCMS(scale) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_scale,5), n+1, tiltseriesnumber))
		f.write("The scaled sum of CCMS values is %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_sum,5), n+1, tiltseriesnumber))
		
		if countdown_flag == 1:
			iteration_countdown+=1
		if (iteration_countdown == 0 and CCMS_shift <= auto_refine_options.auto_convergence and CCMS_rots*14.4/360 <= auto_refine_options.auto_convergence and CCMS_scale <= auto_refine_options.auto_convergence):
			apDisplay.printMsg("Convergence has been reached at iteration #%s for Tilt-Series #%s! Continuing for another %s iterations." % (n+1, tiltseriesnumber, auto_refine_options.auto_convergence_iters))
			f.write("Convergence has been reached at iteration #%s for Tilt-Series #%s! Continuing for another %s iterations.\n" % (n+1, tiltseriesnumber, auto_refine_options.auto_convergence_iters))
			countdown_flag=1
		elif iteration_countdown == 0:
			apDisplay.printMsg("Convergence not reached.")
			f.write("Convergence not reached.")
		if (iteration_countdown == auto_refine_options.auto_convergence_iters and iteration_countdown != 0):
			apDisplay.printMsg("Finished %s post-convergence iterations!" % auto_refine_options.auto_convergence_iters)
			f.write("Finished %s post-convergence iterations!\n" % auto_refine_options.auto_convergence_iters)
			return
		
		apDisplay.printMsg("Creating Refinement Depiction Videos")
		f.write("Creating Refinement Depiction Videos\n")
		apProTomo2Aligner.makeCorrPeakVideos(name, it, tiltdir, 'out', auto_refine_options.video_type, "Refinement")  #Correlation peak videos are always made.
		apProTomo2Aligner.makeCorrPlotImages(name, it, tiltdir, corrfile)  #Correlation plots are always made.
		apProTomo2Aligner.makeAngleRefinementPlots(tiltdir, name)  #Refinement plots are always made.
		if (auto_refine_options.all_tilt_videos == "true"):  #Tilt series videos are only made if requested
			apDisplay.printMsg("Creating Refinement tilt-series video...")
			f.write("Creating Refinement tilt-series video...\n")
			apProTomo2Aligner.makeTiltSeriesVideos(name, it, tiltfilename_full, rawimagecount, tiltdir, raw_path, auto_refine_options.pixelsize, auto_refine_options.map_sampling, auto_refine_options.image_file_type, auto_refine_options.video_type, "true", auto_refine_options.parallel, "Refinement")
		if (auto_refine_options.all_recon_videos == "true"):  #Reconstruction videos are only made if requested
			apDisplay.printMsg("Generating Refinement reconstruction...")
			f.write("Generating Refinement reconstruction...\n")
			#Rescale if necessary
			if auto_refine_options.map_sampling != sampling:
				new_map_sampling='%s' % auto_refine_options.map_sampling
				series.setparam("sampling",new_map_sampling)
				series.setparam("map.sampling",new_map_sampling)
				
				#Rescale the lowpass and body for depiction
				new_lp_x = lpx*auto_refine_options.map_sampling/sampling
				new_lp_y = lpy*auto_refine_options.map_sampling/sampling
				new_body = body*sampling/auto_refine_options.map_sampling
				series.setparam("map.lowpass.diameter", "{ %s %s }" % (new_lp_x, new_lp_y))
				series.setparam("map.body", "%s" % (new_body))
				
				series.mapfile()
				
				#Reset sampling values for next iteration
				series.setparam("sampling",'%s' % sampling)
				series.setparam("map.sampling",'%s' % sampling)
			else:
				series.mapfile()
			
			apProTomo2Aligner.makeReconstructionVideos(name, itt, tiltdir, region_x, region_y, 'true', 'out', auto_refine_options.pixelsize, sampling, auto_refine_options.map_sampling, lp, thickness, auto_refine_options.video_type, "false", auto_refine_options.parallel, align_step="Refinement")
	
		if final_retry > 0:
			apDisplay.printMsg("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small." % (n+1, final_retry))
			apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
			apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
			f.write("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small.\n" % (n+1, final_retry))
			f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
			f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
	
	#Next three rounds are run to completion if convergence wasn't met
	start = start + iters
	r6_body=float((orig_thickness/auto_refine_options.r6_sampling)/cos_alpha)
	r7_body=float((orig_thickness/auto_refine_options.r7_sampling)/cos_alpha)
	r8_body=float((orig_thickness/auto_refine_options.r8_sampling)/cos_alpha)
	
	iters=auto_refine_options.r6_iters+auto_refine_options.r7_iters+auto_refine_options.r8_iters
	round1={"window.size":"{ %s %s }" % (int(auto_refine_options.r6_region_x/auto_refine_options.r6_sampling),int(auto_refine_options.r6_region_y/auto_refine_options.r6_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r6_lowpass_diameter_x,auto_refine_options.r6_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r6_lowpass_diameter_x,auto_refine_options.r6_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r6_lowpass_apod_x,auto_refine_options.r6_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r6_highpass_apod_x,auto_refine_options.r6_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r6_highpass_diameter_x,auto_refine_options.r6_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r6_sampling),"map.sampling":"%s" % (auto_refine_options.r6_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r6_kernel_x,auto_refine_options.r6_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r6_peak_search_radius_x,auto_refine_options.r6_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r6_mask_width_x,auto_refine_options.r6_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r6_mask_width_x,auto_refine_options.r6_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r6_mask_apod_x,auto_refine_options.r6_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r6_mask_apod_x,auto_refine_options.r6_mask_apod_y),"reference.body":"%s" % (r6_body),"map.body":"%s" % (r6_body),"align.correlation.mode":"%s" % (auto_refine_options.r6_corr_mode)}
	round2={"window.size":"{ %s %s }" % (int(auto_refine_options.r7_region_x/auto_refine_options.r7_sampling),int(auto_refine_options.r7_region_y/auto_refine_options.r7_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r7_lowpass_diameter_x,auto_refine_options.r7_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r7_lowpass_diameter_x,auto_refine_options.r7_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r7_lowpass_apod_x,auto_refine_options.r7_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r7_highpass_apod_x,auto_refine_options.r7_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r7_highpass_diameter_x,auto_refine_options.r7_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r7_sampling),"map.sampling":"%s" % (auto_refine_options.r7_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r7_kernel_x,auto_refine_options.r7_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r7_peak_search_radius_x,auto_refine_options.r7_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r7_mask_width_x,auto_refine_options.r7_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r7_mask_width_x,auto_refine_options.r7_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r7_mask_apod_x,auto_refine_options.r7_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r7_mask_apod_x,auto_refine_options.r7_mask_apod_y),"reference.body":"%s" % (r7_body),"map.body":"%s" % (r7_body),"align.correlation.mode":"%s" % (auto_refine_options.r7_corr_mode)}
	round3={"window.size":"{ %s %s }" % (int(auto_refine_options.r8_region_x/auto_refine_options.r8_sampling),int(auto_refine_options.r8_region_y/auto_refine_options.r8_sampling)),"window.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r8_lowpass_diameter_x,auto_refine_options.r8_lowpass_diameter_y),"map.lowpass.diameter":"{ %s %s }" % (auto_refine_options.r8_lowpass_diameter_x,auto_refine_options.r8_lowpass_diameter_y),"window.lowpass.apodization":"{ %s %s }" % (auto_refine_options.r8_lowpass_apod_x,auto_refine_options.r8_lowpass_apod_y),"window.highpass.apodization":"{ %s %s }" % (auto_refine_options.r8_highpass_apod_x,auto_refine_options.r8_highpass_apod_y),"window.highpass.diameter":"{ %s %s }" % (auto_refine_options.r8_highpass_diameter_x,auto_refine_options.r8_highpass_diameter_y),"sampling":"%s" % (auto_refine_options.r8_sampling),"map.sampling":"%s" % (auto_refine_options.r8_sampling),"preprocess.mask.kernel":"{ %s %s }" % (auto_refine_options.r8_kernel_x,auto_refine_options.r8_kernel_y),"align.peaksearch.radius":"{ %s %s }" % (auto_refine_options.r8_peak_search_radius_x,auto_refine_options.r8_peak_search_radius_y),"window.mask.width":"{ %s %s }" % (auto_refine_options.r8_mask_width_x,auto_refine_options.r8_mask_width_y),"align.mask.width":"{ %s %s }" % (auto_refine_options.r8_mask_width_x,auto_refine_options.r8_mask_width_y),"window.mask.apodization":"{ %s %s }" % (auto_refine_options.r8_mask_apod_x,auto_refine_options.r8_mask_apod_y),"align.mask.apodization":"{ %s %s }" % (auto_refine_options.r8_mask_apod_x,auto_refine_options.r8_mask_apod_y),"reference.body":"%s" % (r8_body),"map.body":"%s" % (r8_body),"align.correlation.mode":"%s" % (auto_refine_options.r8_corr_mode)}
	
	if countdown_flag == 0:
		series.setparam("fit.scale","true")
		elevation_start=start+int(iters/2)
		apDisplay.printMsg("Convergence was not reached.\nTurning Scaling on. Tilt elevation will be turned on at iteration %s" % elevation_start)
		f.write("Convergence was not reached.\nTurning Scaling on. Tilt elevation will be turned on at iteration %s\n" % elevation_start)
		for n in range(start,start+iters):
			#change parameters depending on rounds
			if (n+1 <= start+1):
				r=6  #Round number
				apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
				apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r6_lp)
				f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
				f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r6_lp)
				lp=auto_refine_options.r6_lp  #in angstroms
				lpx=options.r6_lowpass_diameter_x  #in Protomo units
				lpy=options.r6_lowpass_diameter_y
				body=r6_body
				region_x=auto_refine_options.r6_region_x
				region_y=auto_refine_options.r6_region_y
				sampling=auto_refine_options.r6_sampling
				apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
				f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
				for val in round1:
					apDisplay.printMsg("%s = %s" % (val,round1[val]))
					f.write("%s = %s\n" % (val,round1[val]))
					series.setparam(val,round1[val])
			elif (n+1 == start+auto_refine_options.r6_iters+1):
				r=7
				apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
				apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r7_lp)
				f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
				f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r7_lp)
				lp=auto_refine_options.r7_lp
				lpx=options.r7_lowpass_diameter_x
				lpy=options.r7_lowpass_diameter_y
				body=r7_body
				region_x=auto_refine_options.r7_region_x
				region_y=auto_refine_options.r7_region_y
				sampling=auto_refine_options.r7_sampling
				apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
				f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
				for val in round2:
					apDisplay.printMsg("%s = %s" % (val,round2[val]))
					f.write("%s = %s\n" % (val,round2[val]))
					series.setparam(val,round2[val])
			elif (n+1 == start+auto_refine_options.r6_iters+auto_refine_options.r7_iters+1):
				r=8
				apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
				apDisplay.printMsg("lowpass = %s Angstroms\n" % auto_refine_options.r8_lp)
				f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
				f.write("lowpass = %s Angstroms\n\n" % auto_refine_options.r8_lp)
				lp=auto_refine_options.r8_lp
				lpx=options.r8_lowpass_diameter_x
				lpy=options.r8_lowpass_diameter_y
				body=r8_body
				region_x=auto_refine_options.r8_region_x
				region_y=auto_refine_options.r8_region_y
				sampling=auto_refine_options.r8_sampling
				apDisplay.printMsg("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
				f.write("Round #%s. Parameters in Protomo units:\n(Note: At binned by %s, pixelsize is %s Angstroms, Nyquist is %s Angstroms)\n\n" % (r, sampling, sampling*auto_refine_options.pixelsize, 2*sampling*auto_refine_options.pixelsize))
				for val in round3:
					apDisplay.printMsg("%s = %s" % (val,round3[val]))
					f.write("%s = %s\n" % (val,round3[val]))
					series.setparam(val,round3[val])
			else:
				apDisplay.printMsg("No Round parameters changed for Iteration #%s\n" % (n+1))
				apDisplay.printMsg("Beginning Refinement Iteration #%s, Round #%s\n" % (n+1,r))
				f.write("No Round parameters changed for Iteration #%s\n\n" % (n+1))
				f.write("Beginning Refinement Iteration #%s, Round #%s\n\n" % (n+1,r))
			
			if elevation_start == n:
				series.setparam("fit.elevation","true")
			
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
						apDisplay.printMsg("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)..." % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
						f.write("Refinement failed for Tilt-Series #%s. Retry #%s with %s%% smaller Window Size: (%s, %s)...\n" % (tiltseriesnumber, retry, new_region_x*sampling, new_region_y*sampling, sampling))
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
						apDisplay.printMsg("Refinement Iteration #%s failed after resampling the search area %s time(s)." % (start+n+1, retry-1))
						apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
						apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
						apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n")
						f.write("Refinement Iteration #%s failed after resampling the search area %s time(s).\n" % (start+n+1, retry-1))
						f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
						f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
						f.write("Put values less than these into the corresponding parameter boxes on the Protomo Refinement Appion webpage and try again.\n\n")
						brk=1
					pass
			
			apDisplay.printMsg("Finished Iteration #%s, Round #%s Refinement!\n" % (n+1,r))
			f.write("Finished Iteration #%s, Round #%s Refinement!\n\n" % (n+1,r))
			if (brk != None):   #resampling failed, break out of all refinement iterations
				return
			
			it="%03d" % (n)
			itt="%02d" % (n+1)
			ittt="%02d" % (n)
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			series.corr(corrfile)
			series.fit()
			series.update()
	
			#archive results
			tiltfile=basename+'.tlt'
			series.geom(0).write(tiltfile)
			tiltfilename_full=tiltdir+'/'+tiltfile
			
			#Produce quality assessment statistics and plot image using corrfile information
			apDisplay.printMsg("Creating quality assessment statistics...")
			f.write("Creating quality assessment statistics...\n")
			numcorrfiles=len(glob.glob1(tiltdir,'*.corr'))
			for i in range(numcorrfiles):
				it="%03d" % (i)
				basename='%s%s' % (name,it)
				corrfile=basename+'.corr'
				try:  #Sometimes Protomo fails to write a corr file correctly...I don't understand this
					CCMS_shift, CCMS_rots, CCMS_scale, CCMS_sum = apProTomo2Aligner.makeQualityAssessment(name, i, tiltdir, corrfile)
				except NoneType:
					apDisplay.printMsg("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.")
					f.write("Protomo Failed to Write the correction factor file correctly, usually due to a failed alignment.\n")
				if i == numcorrfiles-1:
					apProTomo2Aligner.makeQualityAssessmentImage(tiltseriesnumber, auto_refine_options.sessionname, name, tiltdir, auto_refine_options.r1_iters, auto_refine_options.r1_sampling, auto_refine_options.r1_lp, auto_refine_options.r2_iters, auto_refine_options.r2_sampling, auto_refine_options.r2_lp, auto_refine_options.r3_iters, auto_refine_options.r3_sampling, auto_refine_options.r3_lp, auto_refine_options.r4_iters, auto_refine_options.r4_sampling, auto_refine_options.r4_lp, auto_refine_options.r5_iters, auto_refine_options.r5_sampling, auto_refine_options.r5_lp, auto_refine_options.r6_iters, auto_refine_options.r6_sampling, auto_refine_options.r6_lp, auto_refine_options.r7_iters, auto_refine_options.r7_sampling, auto_refine_options.r7_lp, auto_refine_options.r8_iters, auto_refine_options.r8_sampling, auto_refine_options.r8_lp)
			it="%03d" % (n)
			basename='%s%s' % (name,it)
			corrfile=basename+'.corr'
			
			apDisplay.printMsg("\033[43mCCMS(shift) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_shift,5), n+1, tiltseriesnumber))
			apDisplay.printMsg("\033[46mCCMS(rotations) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_rots,5), n+1, tiltseriesnumber))
			apDisplay.printMsg("\033[43mCCMS(scale) = %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_scale,5), n+1, tiltseriesnumber))
			apDisplay.printMsg("\033[1mThe scaled sum of CCMS values is %s\033[0m for Iteration #%s of Tilt-Series #%s." % (round(CCMS_sum,5), n+1, tiltseriesnumber))
			f.write("CCMS(shift) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_shift,5), n+1, tiltseriesnumber))
			f.write("CCMS(rotations) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_rots,5), n+1, tiltseriesnumber))
			f.write("CCMS(scale) = %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_scale,5), n+1, tiltseriesnumber))
			f.write("The scaled sum of CCMS values is %s for Iteration #%s of Tilt-Series #%s.\n" % (round(CCMS_sum,5), n+1, tiltseriesnumber))
			
			apDisplay.printMsg("Creating Refinement Depiction Videos")
			f.write("Creating Refinement Depiction Videos\n")
			apProTomo2Aligner.makeCorrPeakVideos(name, it, tiltdir, 'out', auto_refine_options.video_type, "Refinement")  #Correlation peak videos are always made.
			apProTomo2Aligner.makeCorrPlotImages(name, it, tiltdir, corrfile)  #Correlation plots are always made.
			apProTomo2Aligner.makeAngleRefinementPlots(tiltdir, name)  #Refinement plots are always made.
			if (auto_refine_options.all_tilt_videos == "true"):  #Tilt series videos are only made if requested
				apDisplay.printMsg("Creating Refinement tilt-series video...")
				f.write("Creating Refinement tilt-series video...\n")
				apProTomo2Aligner.makeTiltSeriesVideos(name, it, tiltfilename_full, rawimagecount, tiltdir, raw_path, auto_refine_options.pixelsize, auto_refine_options.map_sampling, auto_refine_options.image_file_type, auto_refine_options.video_type, "true", auto_refine_options.parallel, "Refinement")
			if (auto_refine_options.all_recon_videos == "true"):  #Reconstruction videos are only made if requested
				apDisplay.printMsg("Generating Refinement reconstruction...")
				f.write("Generating Refinement reconstruction...\n")
				#Rescale if necessary
				if auto_refine_options.map_sampling != sampling:
					new_map_sampling='%s' % auto_refine_options.map_sampling
					series.setparam("sampling",new_map_sampling)
					series.setparam("map.sampling",new_map_sampling)
					
					#Rescale the lowpass and body for depiction
					new_lp_x = lpx*auto_refine_options.map_sampling/sampling
					new_lp_y = lpy*auto_refine_options.map_sampling/sampling
					new_body = body*sampling/auto_refine_options.map_sampling
					series.setparam("map.lowpass.diameter", "{ %s %s }" % (new_lp_x, new_lp_y))
					series.setparam("map.body", "%s" % (new_body))
					
					series.mapfile()
					
					#Reset sampling values for next iteration
					series.setparam("sampling",'%s' % sampling)
					series.setparam("map.sampling",'%s' % sampling)
				else:
					series.mapfile()
				
				apProTomo2Aligner.makeReconstructionVideos(name, itt, tiltdir, region_x, region_y, 'true', 'out', auto_refine_options.pixelsize, sampling, auto_refine_options.map_sampling, lp, thickness, auto_refine_options.video_type, "false", auto_refine_options.parallel, align_step="Refinement")
		
			if final_retry > 0:
				apDisplay.printMsg("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small." % (n+1, final_retry))
				apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
				apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
				f.write("Refinement Iteration #%s finished after retrying %s time(s) due to the sampled search area being too small.\n" % (n+1, final_retry))
				f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
				f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
	
	apDisplay.printMsg("Auto Refinement Finished for Tilt-Series #%s!" % tiltseriesnumber)
	f.write("Auto Refinement Finished for Tilt-Series #%s!\n" % tiltseriesnumber)
	f.close()


def protomoScreening(log_file, tiltseriesnumber, screening_options):
	"""
	Runs a tilt-series through File Preparation and Coarse Alignment.
	These are explicit for parallelization reasons.
	"""
	#Prep
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(screening_options.rundir, tiltseriesnumber, prep="True")
	f = open(log_file,'a')
	
	apDisplay.printMsg('Preparing Tilt-Series #%s Images and .tlt File...' % tiltseriesnumber)
	f.write('Preparing Tilt-Series #%s Images and .tlt File...\n' % tiltseriesnumber)
	tilts,accumulated_dose_list,new_ordered_imagelist,maxtilt = apProTomo2Prep.prepareTiltFile(screening_options.sessionname, seriesname, tiltfilename_full, tiltseriesnumber, raw_path, "False", link=False, coarse="True")
	os.chdir(tiltdir)
	
	cmd="awk '/FILE /{print}' %s | wc -l" % (tiltfilename_full)  #rawimagecount is zero before this
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(rawimagecount, err) = proc.communicate()
	rawimagecount=int(rawimagecount)
	
	apDisplay.printMsg("Creating initial tilt-series video...")
	f.write("Creating initial tilt-series video...\n")
	jobs1=[]
	jobs1.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, 0, tiltfilename_full, rawimagecount, tiltdir, raw_path, screening_options.pixelsize, screening_options.map_sampling, screening_options.image_file_type, screening_options.video_type, "true", "True", "Initial",)))
	for job in jobs1:
		job.start()
	
	#Removing highly shifted images
	bad_images, bad_kept_images=apProTomo2Aligner.removeHighlyShiftedImages(tiltfilename_full, screening_options.dimx, screening_options.dimy, screening_options.shift_limit, screening_options.angle_limit)
	if bad_images:
		apDisplay.printMsg('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.' % (bad_images, screening_options.shift_limit))
		f.write('Images %s were removed from the tilt file because their shifts exceed %s%% of the (x) and/or (y) dimensions.\n' % (bad_images, screening_options.shift_limit))
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, screening_options.angle_limit))
			f.write('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.\n' % (bad_kept_images, screening_options.angle_limit))
		if len(bad_images) >= 4:
			apDisplay.printWarning('%s high-tilt images were removed for Protomo processing. Check Leginon to make sure that all of your images are tracking well!' % len(bad_images))
			f.write('%s high-tilt images were removed for Protomo processing. Check Leginon to make sure that all of your images are tracking well!\n' % len(bad_images))
	else:
		if bad_kept_images:
			apDisplay.printMsg('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.' % (bad_kept_images, screening_options.angle_limit))
			f.write('Images %s exceeded the allowed shift, but were at tilt angles less than the %s degree angle limit.\n' % (bad_kept_images, screening_options.angle_limit))
		apDisplay.printMsg('No images were removed from the .tlt file due to high shifts.')
		f.write('No images were removed from the .tlt file due to high shifts.\n')
	
	apDisplay.printMsg("Finished Preparing Files and Directories for Tilt-Series #%s." % (tiltseriesnumber))
	f.write("Finished Preparing Files and Directories for Tilt-Series #%s.\n" % (tiltseriesnumber))
	
	#Coarse Alignment
	tiltdirname,tiltdir,seriesnumber,seriesname,tiltfilename,tiltfilename_full,raw_path,tiltstart,rawimagecount,maxtilt = variableSetup(screening_options.rundir, tiltseriesnumber, prep="False")
	cos_alpha=np.cos(maxtilt*np.pi/180)
	name='coarse_'+seriesname
	coarse_param_full=tiltdir+'/'+name+'.param'
	cpparam="cp %s %s" % (screening_options.coarse_param_file, coarse_param_full)
	os.system(cpparam)
	body,sampling,orig_thickness,map_sampling,orig_lp,region_x,region_y = getParamValues(coarse_param_full, cos_alpha, "no change")
	thickness=int(round(orig_thickness*screening_options.pixelsize))
	lp=round(2*screening_options.pixelsize*sampling/orig_lp,2)
	editParamFile(tiltdir, coarse_param_full, raw_path)
	apDisplay.printMsg('Starting Protomo Coarse Alignment')
	f.write('Starting Protomo Coarse Alignment\n')
	coarse_seriesparam=protomo.param(coarse_param_full)
	coarse_seriesgeom=protomo.geom(tiltfilename_full)
	try:
		series=protomo.series(coarse_seriesparam,coarse_seriesgeom)
		series.setparam("reference.body", "%s" % body)
		series.setparam("map.body", "%s" % body)
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
					apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)..." % (tiltseriesnumber, retry, new_region_x, new_region_y, sampling))
					f.write("Coarse Alignment for Tilt-Series #%s failed. Retry #%s with Window Size: (%s, %s) (at sampling %s)...\n" % (tiltseriesnumber, retry, new_region_x, new_region_y, sampling))
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
					apDisplay.printMsg("Coarse Alignment for Tilt-Series #%s failed after rescaling the search area %s time(s)." % (tiltseriesnumber, retry-1))
					apDisplay.printMsg("Window Size (x) was windowed down to %s" % (new_region_x*sampling))
					apDisplay.printMsg("Window Size (y) was windowed down to %s" % (new_region_y*sampling))
					apDisplay.printMsg("Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n")
					f.write("Coarse Alignment for Tilt-Series #%s failed after rescaling the search area %s time(s).\n" % (tiltseriesnumber, retry-1))
					f.write("Window Size (x) was windowed down to %s\n" % (new_region_x*sampling))
					f.write("Window Size (y) was windowed down to %s\n" % (new_region_y*sampling))
					f.write("Put values less than these into the corresponding parameter boxes on the Protomo Coarse Alignment Appion webpage and try again.\n\n")
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
		
		cleanup="mkdir %s/coarse_out; cp %s/coarse*.* %s/coarse_out; rm %s/*.corr; mv %s/%s.tlt %s/coarse_out/initial_%s.tlt; cp %s/%s.tlt %s/%s.tlt" % (tiltdir, tiltdir, tiltdir, tiltdir, tiltdir, seriesname, tiltdir, seriesname, tiltdir, name, tiltdir, seriesname)
		os.system(cleanup)
	except:
		apDisplay.printWarning("Coarse Alignment failed. Skipping Tilt-Series #%s...\n" % (tiltseriesnumber))
		f.write("Coarse Alignment failed. Skipping Tilt-Series #%s...\n\n" % (tiltseriesnumber))
		return
	os.system('touch %s/.tiltseries.%04d' % (tiltdir, tiltseriesnumber))  #Internal tracker for what has been processed through alignment
	
	jobs2=[]
	apDisplay.printMsg("Creating Coarse Alignment Depiction Videos")
	f.write("Creating Coarse Alignment Depiction Videos\n")
	jobs2.append(mp.Process(target=apProTomo2Aligner.makeCorrPeakVideos, args=(name, 0, tiltdir, 'out', screening_options.video_type, "Coarse",)))
	apDisplay.printMsg("Creating Coarse Alignment tilt-series video...")
	f.write("Creating Coarse Alignment tilt-series video...\n")
	jobs2.append(mp.Process(target=apProTomo2Aligner.makeTiltSeriesVideos, args=(seriesname, 0, tiltfile, rawimagecount, tiltdir, raw_path, screening_options.pixelsize, map_sampling, screening_options.image_file_type, screening_options.video_type, "true", "True", "Coarse",)))
	for job in jobs2:
		job.start()
	
	apDisplay.printMsg("Generating Coarse Alignment reconstruction...")
	f.write("Generating Coarse Alignment reconstruction...\n")
	series.mapfile()
	apProTomo2Aligner.makeReconstructionVideos(name, 0, tiltdir, 1024, 1024, "true", 'out', screening_options.pixelsize, sampling, map_sampling, lp, thickness, screening_options.video_type, "false", "True", align_step="Coarse")
	
	for job in jobs1:
		job.join()
	for job in jobs2:
		job.join()
	
	apDisplay.printMsg("Coarse Alignment finished for Tilt-Series #%s!\n" % (tiltseriesnumber))
	f.write("Coarse Alignment finished for Tilt-Series #%s!\n\n" % (tiltseriesnumber))
	f.close()
	


if __name__ == '__main__':
	options=parseOptions()
	options=apProTomo2Aligner.angstromsToProtomo(options)
	options.rundir = os.path.abspath(os.path.join(options.rundir, os.pardir))  #Can't get the parent directory for rundir in the PHP, so this is the next best thing
	tiltseriesranges=apProTomo2Aligner.hyphen_range(options.tiltseriesranges)
	cwd=os.getcwd()
	os.system("mkdir -p %s 2>/dev/null" % options.rundir)
	time_start = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")
	log_file = "%s/protomo2batch_%s.log" % (options.rundir, time_start)
	log = open(log_file,'w')
	log.write('Start time: %s\n\n' % time_start)
	log.write('Description: %s\n' % options.description)
	apDisplay.printMsg("Writing to log %s" % log_file)
	input_command='protomo2batch.py '	
	for key in options.__dict__:
		if options.__dict__[key] != None:
			input_command += '--%s=%s ' % (key, options.__dict__[key])
	log.write('%s\n\n' % input_command)
	
	if (options.procs == "all"):
		options.procs=mp.cpu_count()
	else:
		options.procs=int(options.procs)
	
	
	#File Preparation
	if (options.prep_files == "True" and options.automation == "False"):
		apDisplay.printMsg("Preparing Files and Directories for Protomo")
		log.write("Preparing Files and Directories for Protomo\n")
		
		if (options.procs > 5): #For tilt-series of size 5k x 4k by 37 tilts, each protomoPrep process will consume over 6GB of ram. If the ram is maxed out, the system will revert to disk swap and slow down this step considerably.
			procs=5
		else:
			procs=options.procs
		
		log.close()
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoPrep, args=(log_file, i, options,))
			p.start()
			
			#If max number of processors is reached, wait for them to finish. This isn't the most efficient way, but it's the only way I know how to accomplish this right now...
			if (j % procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		log = open(log_file,'a')
		
		if (options.ctf_correct == "True"):
			apDisplay.printMsg("Performing CTF Correction")
			log.write("Performing CTF Correction\n")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=ctfCorrect, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("CTF Correction Finished for Tilt-Series %s!" % options.tiltseriesranges)
			log.write("CTF Correction Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Files and Directories Prepared for Tilt-Series %s!" % options.tiltseriesranges)
		log.write("Files and Directories Prepared for Tilt-Series %s!" % options.tiltseriesranges)
	
	#Coarse Alignment
	if (options.coarse_align == "True" and options.automation == "False"):
		apDisplay.printMsg("Performing Coarse Alignments")
		log.write("Performing Coarse Alignments\n")
		log.close()
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoCoarseAlign, args=(log_file, i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		log = open(log_file,'a')
		apDisplay.printMsg("Coarse Alignments Finished for Tilt-Series %s!" % options.tiltseriesranges)
		log.write("Coarse Alignments Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
	
	
	#Refinement
	if (options.refine == "True" and options.automation == "False"):
		apDisplay.printMsg("Performing Refinements")
		log.write("Performing Refinements\n")
		log.close()
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoRefine, args=(log_file, i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		log = open(log_file,'a')
		apDisplay.printMsg("Refinements Finished for Tilt-Series %s!" % options.tiltseriesranges)
		log.write("Refinements Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
	
	
	#Reconstruction
	if (options.reconstruct == "True" and options.automation == "False"):
		if (options.dose_presets != "False"):
			apDisplay.printMsg("Performing Dose Compensation")
			log.write("Performing Dose Compensation\n")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=doseCompensate, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("Dose Compensation Finished for Tilt-Series %s!" % options.tiltseriesranges)
			log.write("Dose Compensation Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
		
		apDisplay.printMsg("Creating Reconstructions")
		log.write("Creating Reconstructions\n")
		log.close()
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=protomoReconstruct, args=(log_file, i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		log = open(log_file,'a')
		apDisplay.printMsg("Reconstructions Finished for Tilt-Series %s!" % options.tiltseriesranges)
		log.write("Reconstructions Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
		if (options.link_recons != None) or (options.link_recons != "") or (len(options.link_recons) > 1):
			apDisplay.printMsg("Reconstructions can be found in this directory:")
			log.write("Reconstructions can be found in this directory:\n%s\n" % options.link_recons)
			print "\n%s\n" % options.link_recons
	
	
	#CTF Correction
	if (options.ctf_correct == "True" and options.automation == "False" and options.prep_files == "False" and options.reconstruct == "False"):
		apDisplay.printMsg("Performing CTF Correction")
		log.write("Performing CTF Correction\n")
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=ctfCorrect, args=(i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("CTF Correction Finished for Tilt-Series %s!" % options.tiltseriesranges)
		log.write("CTF Correction Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
	
	
	#Dose Compensation
	if (options.dose_presets != "False" and options.automation == "False" and options.prep_files == "False" and options.reconstruct == "False"):
		apDisplay.printMsg("Performing Dose Compensation")
		log.write("Performing Dose Compensation\n")
		for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
			p = mp.Process(target=doseCompensate, args=(i, options,))
			p.start()
			
			if (j % options.procs == 0) and (j != 0):
				[p.join() for p in mp.active_children()]
		
		[p.join() for p in mp.active_children()]
		apDisplay.printMsg("Dose Compensation Finished for Tilt-Series %s!" % options.tiltseriesranges)
		log.write("Dose Compensation Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
	
	
	#Full Automation mode needs to be run by itself. It has its own self-contained calls to all primary Appion-Protomo functions.
	if (options.automation == "True" and options.prep_files == "False" and options.coarse_align == "False" and options.refine == "False" and options.reconstruct == "False" and options.ctf_correct == "False" and options.screening_mode == "False"):
		#File Preparation
		if (options.auto_prep == "True"):
			apDisplay.printMsg("Preparing Files and Directories for Protomo")
			log.write("Preparing Files and Directories for Protomo\n")
			
			if (options.procs > 5):
				procs=5
			else:
				procs=options.procs
			
			log.close()
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoPrep, args=(log_file, i, options,))
				p.start()
				
				if (j % procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			log = open(log_file,'a')
			apDisplay.printMsg("Files and Directories Prepared for tilt-series %s!" % options.tiltseriesranges)
			log.write("Files and Directories Prepared for Tilt-Series %s!" % options.tiltseriesranges)
		
		#CTF Correction
		if (options.auto_ctf_correct == "True"):
			apDisplay.printMsg("Performing CTF Correction")
			log.write("Performing CTF Correction\n")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=ctfCorrect, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("CTF Correction Finished for tilt-series %s!" % options.tiltseriesranges)
			log.write("CTF Correction Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
		
		#Coarse Alignment
		if (options.auto_coarse_align == "True"):
			apDisplay.printMsg("Performing Coarse Alignments")
			log.write("Performing Coarse Alignments\n")
			log.close()
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoCoarseAlign, args=(log_file, i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			log = open(log_file,'a')
			apDisplay.printMsg("Coarse Alignments Finished for tilt-series %s!" % options.tiltseriesranges)
			log.write("Coarse Alignments Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
		
		#Auto-Refinement
		if (options.auto_refine == "True"):
			apDisplay.printMsg("Performing Refinements")
			log.write("Performing Refinements\n")
			log.close()
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoAutoRefine, args=(log_file, i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			log = open(log_file,'a')
			apDisplay.printMsg("Auto Refinement Finished for tilt-series %s!" % options.tiltseriesranges)
		
		#Dose Compensation
		if (options.dose_presets != "False"):
			apDisplay.printMsg("Performing Dose Compensation")
			log.write("Performing Dose Compensation\n")
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=doseCompensate, args=(i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			apDisplay.printMsg("Dose Compensation Finished for Tilt-Series %s!" % options.tiltseriesranges)
			log.write("Dose Compensation Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
		
		#Reconstruction
		if (options.auto_reconstruct == "True"):
			apDisplay.printMsg("Creating Reconstructions")
			log.write("Creating Reconstructions\n")
			log.close()
			for i, j in zip(tiltseriesranges, range(1,len(tiltseriesranges)+1)):
				p = mp.Process(target=protomoReconstruct, args=(log_file, i, options,))
				p.start()
				
				if (j % options.procs == 0) and (j != 0):
					[p.join() for p in mp.active_children()]
			
			[p.join() for p in mp.active_children()]
			log = open(log_file,'a')
			apDisplay.printMsg("Reconstructions Finished for Tilt-Series %s!" % options.tiltseriesranges)
			log.write("Reconstructions Finished for Tilt-Series %s!\n" % options.tiltseriesranges)
			if (options.link_recons != None) or (options.link_recons != "") or (len(options.link_recons) > 1):
				apDisplay.printMsg("Reconstructions can be found in this directory:")
				log.write("Reconstructions can be found in this directory:\n%s\n" % options.link_recons)
				print "\n%s\n" % options.link_recons
		
	
	#Screening mode needs to be run by itself.
	if (options.screening_mode == "True" and options.automation == "False" and options.prep_files == "False" and options.coarse_align == "False" and options.refine == "False" and options.reconstruct == "False" and options.ctf_correct == "False" and options.dose_presets == "False"):
		apDisplay.printMsg("Appion-Protomo Screening Mode")
		apDisplay.printMsg("Tilt files, directories, and images will be prepared.")
		apDisplay.printMsg("Tilt-Series will be coarsely aligned and depiction videos made in parallel.")
		apDisplay.printMsg("This is intended to be used during data collection.")
		log.write("Appion-Protomo Screening Mode\n")
		log.write("Tilt files, directories, and images will be prepared.\n")
		log.write("Tilt-Series will be coarsely aligned and depiction videos made in parallel.\n")
		log.write("This is intended to be used during data collection.\n")
		
		tiltseriesnumber=int(options.screening_start)
		while True:
			try:
				sessiondata = apDatabase.getSessionDataFromSessionName(options.sessionname)
				nexttiltseriesnumber = tiltseriesnumber+1
				tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(nexttiltseriesnumber,sessiondata)
				#If tilt-series N+1 exists, then tilt-series N is ready to be processed
				log.close()
				protomoScreening(log_file, tiltseriesnumber, options)
				log = open(log_file,'a')
				tiltseriesnumber+=1
			except KeyboardInterrupt:
				apDisplay.printMsg("Keyboard Interrupt!")
				log.write("Keyboard Interrupt!\n")
				time_end = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")
				log.write("\nEnd time: %s" % time_end)
				log.close()
				sys.exit()
			except:
				#Wait for tilt-series N to finish collecting
				apDisplay.printMsg("Waiting for Tilt-Series #%s to finish being collected. Sleeping for 1 minute..." % tiltseriesnumber)
				log.write("Waiting for Tilt-Series #%s to finish being collected. Sleeping for 1 minute...\n" % tiltseriesnumber)
				time.sleep(60)
	
	
	time_end = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")
	apDisplay.printMsg('Did everything blow up and now you\'re yelling at your computer screen?')
	apDisplay.printMsg('If so, kindly email Alex at ajn10d@fsu.edu and include this log file.')
	apDisplay.printMsg('If everything worked beautifully and you publish it, please use the appropriate citations listed on the Appion webpage!')
	log.write('Did everything blow up and now you\'re yelling at your computer screen?\n')
	log.write('If so, kindly email Alex at ajn10d@fsu.edu and include this log file.\n')
	log.write('If everything worked beautifully and you publish it, please use the appropriate citations listed on the Appion webpage!\n')
	print "\n"
	apDisplay.printMsg("Closing log file %s\n" % log_file)
	log.write("\nEnd time: %s" % time_end)
	log.close()