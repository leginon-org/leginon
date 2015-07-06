#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for tilt series reconstruction.
# 
# *To be used after protomo2aligner.py


import os
import sys
import math
import time
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
timestr = time.strftime("%Yyr%mm%dd-%Hhr%Mm%Ss")

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

		self.parser.add_option("--pixelsize", dest="pixelsize", type="float",
			help="Pixelsize of raw images in angstroms/pixel, e.g. --pixelsize=3.5", metavar="float")
		
		self.parser.add_option("--recon_map_size_x", dest="recon_map_size_x",  type="int",  default="2048",
			help="Size of the reconstructed tomogram in the X direction, e.g. --recon_map_size_x=256", metavar="int")

		self.parser.add_option("--recon_map_size_y", dest="recon_map_size_y",  type="int",  default="2048",
			help="Size of the reconstructed tomogram in the Y direction, e.g. --recon_map_size_y=256", metavar="int")

		self.parser.add_option("--recon_map_size_z", dest="recon_map_size_z",  type="int",  default="800",
			help="Size of the reconstructed tomogram in the Z direction, e.g. --recon_map_size_z=128", metavar="int")
		
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
			
		self.parser.add_option("--link_recon", dest="link_recon",
			help="Path to link reconstruction, e.g. --link_recon=/full/path/")
			
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
		command11="sed -i \"%ss/.*/ S = %s             (* AP sampling *)/\" %s" % (samplingline, self.params['recon_map_sampling'], param_out_full)
		os.system(command11)
		command22="sed -i \"%ss/.*/   size: { %s, %s, %s }  (* AP reconstruction map size *)/\" %s" % (mapsizeline, self.params['recon_map_size_x'], self.params['recon_map_size_y'], self.params['recon_map_size_z'], param_out_full)
		os.system(command22)
		command33="sed -i \"%ss/.*/   sampling: %s  (* AP reconstruction map sampling *)/\" %s" % (mapsamplingline, self.params['recon_map_sampling'], param_out_full)
		os.system(command33)
		
		#Lowpass filter reconstruction?
		cmd="grep -n 'AP lowpass map' %s | awk '{print $1}' | sed 's/://'" % (param_out_full)
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(lowpassmapline, err) = proc.communicate()
		lowpassmapline=int(lowpassmapline)
		if self.params['recon_lowpass'] == False:
			#Remove lowpass filter from param
			cmd2="sed -i \"%ss/.*//\" %s;" % (lowpassmapline, param_out_full)
			cmd2+="sed -i \"%ss/.*//\" %s;" % (lowpassmapline+1, param_out_full)
			cmd2+="sed -i \"%ss/.*//\" %s" % (lowpassmapline+2, param_out_full)
			
			cmd3="grep -n 'AP enable or disable preprocessing of raw images' %s | awk '{print $1}' | sed 's/://'" % (param_out_full)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(preprocessingline, err) = proc.communicate()
			preprocessingline=int(preprocessingline)
			
			cmd33="sed -i \'%ss|.*| preprocessing: false  (* AP enable or disable preprocessing of raw images *)|\' %s" % (preprocessingline, param_out_full)
			os.system(cmd33)
		else:
			self.params['recon_lp_diam_x'] = 2*self.params['pixelsize']/self.params['recon_lp_diam_x']
			self.params['recon_lp_diam_y'] = 2*self.params['pixelsize']/self.params['recon_lp_diam_y']
			cmd2="sed -i \"%ss/.*/     diameter:    { %s, %s } * S/\" %s" % (lowpassmapline+1, self.params['recon_lp_diam_x'], self.params['recon_lp_diam_y'], param_out_full)
		os.system(cmd2)
		
		# AP Get param files ready for batch processing
		img=seriesname+it+'_bck.img';
		mrcf=seriesname+it+'_bck.mrc';
		img_full=self.params['rundir']+'/'+self.params['protomo_outdir']+'/'+img;
		mrc_full=self.params['rundir']+'/'+self.params['protomo_outdir']+'/'+mrcf;
		batchdir=self.params['rundir']+'/'+'ready_for_batch'
		coarse_param_full=self.params['rundir']+'/coarse_out/'+'coarse_'+param_out
		recon_param='recon_'+param_out
		command="mkdir %s; cp %s %s; cp %s %s; cp %s %s/%s; rm %s %s 2>/dev/null" % (batchdir, coarse_param_full, batchdir, refine_param_full, batchdir, param_out_full, batchdir, recon_param, img_full, mrc_full)
		os.system(command)
		
		# Create reconstruction
		seriesparam=protomo.param(param_out_full)
		series=protomo.series(seriesparam)
		series.setcycle(self.params['recon_iter'])
		series.setparam("map.logging","true")
		series.mapfile()
		
		# Restore refine param file
		command="cp %s %s" % (refine_param_full, param_out_full)
		os.system(command)
		
		# Convert to mrc
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		os.system("rm %s" % img_full)
		
		# Normalize
		try:
			command="e2proc3d.py %s %s --process=normalize" % (mrc_full, mrc_full)
			proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
			(code, err) = proc.communicate()
		except:
			pass
		
		if proc.returncode != 0:
			apDisplay.printMsg("e2proc3d not found. Trying proc3d...")
			try:
				command="proc3d %s %s norm" % (mrc_full, mrc_full)
				proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
				(code, err) = proc.communicate()
			except:
				pass
		if proc.returncode != 0:		
			apDisplay.printMsg("proc3d not found. Skipping normalization.")
		
		# Link reconstruction to directory
		try:
			test=len(self.params['link_recon'])
			cmd="mkdir -p %s 2>/dev/null; rm %s/%s 2>/dev/null; ln %s %s" % (self.params['link_recon'], self.params['link_recon'], mrcf, mrc_full, self.params['link_recon'])
			os.system(cmd)
			apDisplay.printMsg("Reconstruction can be found here:")
			mrc_full=self.params['link_recon']+'/'+mrcf;
			print "\n%s\n" % (mrc_full)
		except:
			apDisplay.printMsg("Reconstruction can be found here:")
			print "\n%s\n" % (mrc_full)
			
		os.system("rm %s/cache/%s*" % (self.params['rundir'], seriesname))

#=====================
if __name__ == '__main__':
	protomo2reconstruction = ProTomo2Reconstruction()
	protomo2reconstruction.start()
	protomo2reconstruction.close()
	protomo2reconstruction_log=cwd+'/'+'protomo2reconstruction.log'
	cleanup="mv %s %s/protomo2reconstruction_%s.log" % (protomo2reconstruction_log, wd, timestr)
	os.system(cleanup)
