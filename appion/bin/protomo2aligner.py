#!/usr/bin/env python

import os
import sys
import math
import glob
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apProTomo2Prep
from appionlib import apTomo
from appionlib import apProTomo
from appionlib import apParam

try:
	import protomo
except:
	print "protomo did not get imported"

#=====================
class ProTomo2Aligner(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")
			
		#self.parser.add_option("--refimg", dest="refimg", type="int",
		#	help="Protomo only: custom reference image number, e.g. --refimg=20", metavar="int")
		self.parser.add_option("--seriesname", dest="seriesname", help="Name of Protomo series, e.g. --seriesname=series1")

		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")

		self.parser.add_option('--maxtilt', dest='maxtilt', type='int', metavar='int', help='Highest image tilt in degrees, e.g. --maxtilt=65') 

		self.parser.add_option("--region_x", dest="region_x", default=512, type="int",
			help="Pixels in x to use for region matching, e.g. --region=1024", metavar="int")
		
		self.parser.add_option("--region_y", dest="region_y", default=512, type="int",
			help="Pixels in y to use for region matching, e.g. --region=1024", metavar="int")
		
		self.parser.add_option("--lowpass_diameter_x", dest="lowpass_diameter_x",  default=0.5, type="float",
			help="in fractions of nyquist, e.g. --lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_diameter_y", dest="lowpass_diameter_y",  default=0.5, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_apod_x", dest="lowpass_apod_x", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_x=0.4", metavar="float")
		
		self.parser.add_option("--lowpass_apod_y", dest="lowpass_apod_y", default=0.05, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --lowpass_diameter_y=0.4", metavar="float")
		
		self.parser.add_option("--highpass_diameter_x", dest="highpass_diameter_x", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_diameter_y", dest="highpass_diameter_y", default=0.001, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--highpass_apod_x", dest="highpass_apod_x", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_x=0.02", metavar="float")
		
		self.parser.add_option("--highpass_apod_y", dest="highpass_apod_y", default=0.002, type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --highpass_diameter_y=0.02", metavar="float")

		self.parser.add_option("--thickness", dest="thickness",  default=100, type="float",
			help="estimated thickness of unbinned specimen (in pixels), e.g. --thickness=100.0", metavar="float")
		
		self.parser.add_option("--param", dest="param",
			help="Override other parameters and use an external paramfile. e.g. --param=/path/to/max.param", metavar="FILE")

		self.parser.add_option("--iters", dest="iters", default=1, type="int",
			help="Number of alignment and geometry refinement iterations, e.g. --iter=4", metavar="int")

		self.parser.add_option("--sampling", dest="sampling",  default="4", type="int",
			help="Sampling rate of raw data, e.g. --sampling=4")
				
		self.parser.add_option("--border", dest="border", default=100,  type="int",
			help="Width of area at the image edge to exclude from image statistics, e.g. --border=100", metavar="int")
		
		self.parser.add_option("--clip_low", dest="clip_low",  type="float",
			help="Lower threshold specified as a multiple of the standard deviation, e.g. --clip_low=3.5", metavar="float")

		self.parser.add_option("--clip_high", dest="clip_high",  type="float",
			help="Upper threshold specified as a multiple of the standard deviation, e.g. --clip_high=3.5", metavar="float")

#		self.parser.add_option("--do_estimation", dest="do_estimation",  default="true", action="store_true",
#			help="Enables alignment parameter prediction, e.g. --do_estimation")

		self.parser.add_option("--max_correction", dest="max_correction",  type="float",
			help="Protomo2 only: TODO, e.g. --max_correction=0.04", metavar="float")

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
		
		self.parser.add_option("--correlation_size_x", dest="correlation_size_x",  type="int",
			help="Protomo2 only: X size of cross correlation peak image, e.g. --correlation_size_x=128", metavar="int")

		self.parser.add_option("--correlation_size_y", dest="correlation_size_y",  type="int",
			help="Protomo2 only: Y size of cross correlation peak image, e.g. --correlation_size_y=128", metavar="int")
		
		self.parser.add_option("--peak_search_radius_x", dest="peak_search_radius_x",  type="float",
			help="Protomo2 only: TODO, e.g. --peak_search_radius_x=19.0", metavar="float")

		self.parser.add_option("--peak_search_radius_y", dest="peak_search_radius_y",  type="float",
			help="Protomo2 only: TODO, e.g. --peak_search_radius_y=19.0", metavar="float")

		self.parser.add_option("--map_size_x", dest="map_size_x",  type="int",
			help="Protomo2 only: Size of the reconstructed tomogram in the X direction, e.g. --map_size_x=256", metavar="int")

		self.parser.add_option("--map_size_y", dest="map_size_y",  type="int",
			help="Protomo2 only: Size of the reconstructed tomogram in the Y direction, e.g. --map_size_y=256", metavar="int")

		self.parser.add_option("--map_size_z", dest="map_size_z",  type="int",
			help="Protomo2 only: Size of the reconstructed tomogram in the Z direction, e.g. --map_size_z=128", metavar="int")
		
		self.parser.add_option("--map_lowpass_diameter_x", dest="map_lowpass_diameter_x",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --map_lowpass_diameter_x=0.5", metavar="float")
		
		self.parser.add_option("--map_lowpass_diameter_y", dest="map_lowpass_diameter_y",  type="float",
			help="Protomo2 only: TODO: To be determined (in reciprical pixels), e.g. --map_lowpass_diameter_y=0.5", metavar="float")

	#=====================
	def checkConflicts(self):
		pass

		return True

	#=====================
	def setRunDir(self):
#		"""
#		This function is only run, if --rundir is not defined on the commandline
#
#		This function decides when the results will be stored. You can do some complicated
#		things to set a directory.
#
#		Here I will use information about the stack to set the directory
#		"""
#		### get the path to input stack
#		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
#		stackpath = os.path.abspath(stackdata['path']['path'])
#		### go down two directories
#		uponepath = os.path.join(stackpath, "..")
#		uptwopath = os.path.join(uponepath, "..")
#		### add path strings; always add runname to end!!!
#		rundir = os.path.join(uptwopath, "example", self.params['runname'])
#		### same thing in one step
#		rundir = os.path.join(stackpath, "../../example", self.params['runname'])
#		### good idea to set absolute path,
#		### cleans up 'path/stack/stack1/../../example/ex1' -> 'path/example/ex1'
#		self.params['rundir'] = os.path.abspath(rundir)
		"""
		In all cases, we set the value for self.params['rundir']
		"""

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
	
		### some of this should go in preloop functions

		###create param file
		param_out=self.params['seriesname']+'.param'
		tiltfilename=self.params['seriesname']+'.tlt'
		iters = self.params['iters']
		self.params['cos_alpha']=math.cos(self.params['maxtilt']*math.pi/180)
		self.params['raw_path']=os.path.join(self.params['rundir'],'raw')
		param_in=apProTomo2Prep.getPrototypeParamPath()
		paramdict = apProTomo2Prep.createParamDict(self.params)
		apProTomo2Prep.modifyParamFile(param_in, param_out, paramdict)
		seriesparam=protomo.param(param_out)

		apDisplay.printMsg('Starting protomo alignment')

		###using presence of i3t to determine if protomo has been run once already

		#create series object
		i3tfile=self.params['seriesname']+'.i3t'
		
		if os.path.exists(i3tfile):
			series=protomo.series(seriesparam)
		else:
			seriesgeom=protomo.geom(tiltfilename)
			series=protomo.series(seriesparam,seriesgeom)

		#figure out starting number
		start=0
		previters=glob.glob(self.params['seriesname']+'*.corr')
		if len(previters) > 0:
			previters.sort()
			lastiter=previters[-1]
			start=int(lastiter.split(self.params['seriesname'])[1].split('.')[0])+1
		
		for n in range(iters):
			series.align()
			basename='%s%02d' % (self.params['seriesname'],(n+start))

			corrfile=basename+'.corr'
			series.corr(corrfile)
			series.fit()
			series.update()

			#archive results
			tiltfile=basename+'.tlt'
			geom=series.geom()
			geom.write(tiltfile)
		
			###next I want to do some file conversions and upload metadata to the db. What I want to do is different from what tomoaligner does
			
			#convert correlation peak file to mrc
			# outpath = os.path.join((self.params['rundir'],'out')
			#'i3cut -fmt mrc %s %s' % (os.path.join(outpath,basename+'.img'), os.path.join(outpath,basename+'.mrc'))
			
			#read in correlation peak mrc
			
			#convert to animated gif
			#I found some PIL code for this on the web and will put it on redmine
			
			#upload metadata to db 
			

#=====================
#=====================
if __name__ == '__main__':
	protomo2aligner = ProTomo2Aligner()
	protomo2aligner.start()
	protomo2aligner.close()

