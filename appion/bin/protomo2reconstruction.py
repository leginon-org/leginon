#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for tilt series reconstruction.
# 
# *To be used after protomo2aligner.py


import os
import sys
import math
import subprocess
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

# Required for cleanup at end
cwd=os.getcwd()
wd=''

#=====================
class ProTomo2Reconstruction(basicScript.BasicScript):
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

		self.parser.add_option("--map_size_x", dest="map_size_x",  type="int",  default="4096",
			help="Protomo2 only: Size of the reconstructed tomogram in the X direction, e.g. --map_size_x=256", metavar="int")

		self.parser.add_option("--map_size_y", dest="map_size_y",  type="int",  default="4096",
			help="Protomo2 only: Size of the reconstructed tomogram in the Y direction, e.g. --map_size_y=256", metavar="int")

		self.parser.add_option("--map_size_z", dest="map_size_z",  type="int",  default="800",
			help="Protomo2 only: Size of the reconstructed tomogram in the Z direction, e.g. --map_size_z=128", metavar="int")
		
		self.parser.add_option("--map_sampling", dest="map_sampling",  default="1", type="int",
			help="Sampling rate of raw data for use in reconstruction, e.g. --map_sampling=4")
		
		self.parser.add_option("--recon_iter", dest="recon_iter", type="int",
			help="Refinement iteration used to make final reconstruction, e.g. --recon_iter=10", metavar="int")
			
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
	
		it="%02d" % (self.params['recon_iter'])
		global wd
		wd=self.params['rundir']
		os.chdir(self.params['rundir'])
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		seriesname='series'+seriesnumber
		param_out=seriesname+'.param'
		param_out_full=self.params['rundir']+'/'+param_out
		
		# Backup then edit the Refinement param file, changing only the map size and map sampling parameters
		refine_param_full=self.params['rundir']+'/'+'refine_'+param_out
		command="cp %s %s" % (param_out_full, refine_param_full)
		os.system(command)
		command1="grep -n 'AP sampling' %s | awk '{print $1}' | sed 's/://'" % (param_out_full)
		proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
		(samplingline, err) = proc.communicate()
		samplingline=int(samplingline)
		command2="grep -n 'AP reconstruction map size' %s | awk '{print $1}' | sed 's/://'" % (param_out_full)
		proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
		(mapsizeline, err) = proc.communicate()
		mapsizeline=int(mapsizeline)
		command3="grep -n 'AP reconstruction map sampling' %s | awk '{print $1}' | sed 's/://'" % (param_out_full)
		proc=subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True)
		(mapsamplingline, err) = proc.communicate()
		mapsamplingline=int(mapsamplingline)
		command11="sed -i \"%ss/.*/ S = %s             (* AP sampling *)/\" %s" % (samplingline, self.params['map_sampling'], param_out_full)
		os.system(command11)
		command22="sed -i \"%ss/.*/   size: { %s, %s, %s }  (* AP reconstruction map size *)/\" %s" % (mapsizeline, self.params['map_size_x'], self.params['map_size_y'], self.params['map_size_z'], param_out_full)
		os.system(command22)
		command33="sed -i \"%ss/.*/   sampling: %s  (* AP reconstruction map sampling *)/\" %s" % (mapsamplingline, self.params['map_sampling'], param_out_full)
		os.system(command33)
		
		# Create reconstruction
		seriesparam=protomo.param(param_out_full)
		series=protomo.series(seriesparam)
		series.setcycle(self.params['recon_iter'])
		series.setparam("map.logging","2")
		series.mapfile()
		
		# Convert to mrc
		img=seriesname+it+'_bck.img';
		mrcf=seriesname+it+'_bck.mrc';
		img_full=self.params['rundir']+'/'+self.params['protomo_outdir']+'/'+img;
		mrc_full=self.params['rundir']+'/'+self.params['protomo_outdir']+'/'+mrcf;
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		
		# Normalize
		err=0;
		try:
			command="e2proc3d.py --process=normalize %s %s" % (mrc_full, mrc_full)
			os.system(command)
		except:
			apDisplay.printMsg("e2proc3d not found. Trying proc3d...")
			err=1	# Error thrown. Try proc3d
		if err:
			try:
				command="proc3d %s %s norm" % (mrc_full, mrc_full)
				os.system(command)
			except:
				apDisplay.printMsg("proc3d not found. Skipping normalization.")
		
		# AP Get param files ready for batch processing
		batchdir=self.params['rundir']+'/'+'ready_for_batch'
		coarse_param_full=self.params['rundir']+'/coarse_out/'+'coarse_'+param_out
		recon_param='recon_'+param_out
		command="mkdir %s; cp %s %s; cp %s %s; cp %s %s/%s; rm %s" % (batchdir, coarse_param_full, batchdir, refine_param_full, batchdir, param_out_full, batchdir, recon_param, img_full)
		os.system(command)
		
		apDisplay.printMsg("Reconstruction can be found here:")
		print "%s" % (mrc_full)

#=====================
if __name__ == '__main__':
	protomo2reconstruction = ProTomo2Reconstruction()
	protomo2reconstruction.start()
	protomo2reconstruction.close()
	protomo2reconstruction_log=cwd+'/'+'protomo2reconstruction.log'
	cleanup="mv %s %s" % (protomo2reconstruction_log, wd)
	os.system(cleanup)
