#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for tilt series reconstruction.
# 
# *To be used after protomo2aligner.py

from __future__ import division
import os
import sys
import math
import time
import subprocess
from appionlib import basicScript
from appionlib import apDisplay

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
	
		it="%03d" % (self.params['recon_iter'])
		itt="%03d" % (self.params['recon_iter']-1)
		global wd
		wd=self.params['rundir']
		os.chdir(self.params['rundir'])
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		seriesname='series'+seriesnumber
		param_out=seriesname+'.param'
		param_out_full=self.params['rundir']+'/'+param_out
		tilt_out_full=self.params['rundir']+'/'+seriesname+itt+'.tlt'
		recon_dir=self.params['rundir']+'/recons/'
		os.system('mkdir %s 2>/dev/null' % recon_dir)
		recon_param_out_full=recon_dir+'/'+param_out
		recon_tilt_out_full=recon_dir+'/'+seriesname+'.tlt'
		recon_cache_dir=recon_dir+'/cache'
		recon_out_dir=recon_dir+'/out'
		os.system('cp %s %s' % (tilt_out_full, recon_tilt_out_full))
		os.system('cp %s %s' % (param_out_full,recon_param_out_full))
		
		# Backup then edit the Refinement param file, changing the map size, map sampling, cache dir, and out dir
		refine_param_full=self.params['rundir']+'/'+'refine_'+param_out
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
		command11="sed -i \"%ss/.*/ S = %s             (* AP sampling *)/\" %s" % (samplingline, self.params['recon_map_sampling'], recon_param_out_full)
		os.system(command11)
		command22="sed -i \"%ss/.*/   size: { %s, %s, %s }  (* AP reconstruction map size *)/\" %s" % (mapsizeline, int(self.params['recon_map_size_x']/self.params['recon_map_sampling']), int(self.params['recon_map_size_y']/self.params['recon_map_sampling']), int(round(self.params['recon_thickness']/(self.params['pixelsize']*self.params['recon_map_sampling']))), recon_param_out_full)
		os.system(command22)
		command33="sed -i \"%ss/.*/   sampling: %s  (* AP reconstruction map sampling *)/\" %s" % (mapsamplingline, self.params['recon_map_sampling'], recon_param_out_full)
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
		if self.params['recon_lowpass'] == "False":
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
			lpavg = int((self.params['recon_lp_diam_x']+self.params['recon_lp_diam_y'])/2)
			self.params['recon_lp_diam_x'] = 2*self.params['pixelsize']*self.params['recon_map_sampling']/self.params['recon_lp_diam_x']
			self.params['recon_lp_diam_y'] = 2*self.params['pixelsize']*self.params['recon_map_sampling']/self.params['recon_lp_diam_y']
			cmd2="sed -i \"%ss/.*/     diameter:    { %s, %s } * S/\" %s" % (lowpassmapline+1, self.params['recon_lp_diam_x'], self.params['recon_lp_diam_y'], recon_param_out_full)
		os.system(cmd2)
		
		# AP Get param files ready for batch processing
		if self.params['recon_lowpass'] == "False":
			lp=''
		else:
			lp='.lp%s' % lpavg
		dim='%sx%s' % (self.params['recon_map_size_x'],self.params['recon_map_size_y'])
		img=seriesname+'00_bck.img'
		mrcf=seriesname+'_ite'+it+'_dim'+dim+'_bck.bin'+str(self.params['recon_map_sampling'])+lp+'.mrc'
		mrcfn=seriesname+'_ite'+it+'_dim'+dim+'_bck.bin'+str(self.params['recon_map_sampling'])+lp+'.norm.mrc'
		img_full=recon_out_dir+'/'+img
		mrc_full=recon_out_dir+'/'+mrcf
		mrcn_full=recon_out_dir+'/'+mrcfn
		batchdir=self.params['rundir']+'/'+'ready_for_batch'
		coarse_param_full=self.params['rundir']+'/coarse_out/'+'coarse_'+param_out
		recon_param='recon_'+param_out
		command="mkdir %s 2>/dev/null; cp %s %s; cp %s %s; cp %s %s/%s; rm -r %s %s %s*i3t %s/cache %s/out 2>/dev/null" % (batchdir, coarse_param_full, batchdir, refine_param_full, batchdir, param_out_full, batchdir, recon_param, img_full, mrc_full, recon_dir, recon_dir, recon_dir)
		os.system(command)
		
		# Create reconstruction
		os.chdir(recon_dir)
		seriesparam=protomo.param(recon_param_out_full)
		seriesgeom=protomo.geom(recon_tilt_out_full)
		series=protomo.series(seriesparam,seriesgeom)
		series.setparam("map.logging","true")
		series.mapfile()
		os.chdir(self.params['rundir'])
		
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
			print ""
			apDisplay.printMsg("e2proc3d not found or failed to process reconstruction. Trying proc3d...")
			try:
				command="proc3d %s %s norm" % (mrc_full, mrcn_full)
				proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
				(code, err) = proc.communicate()
			except:
				pass
		if proc.returncode != 0:
			print ""		
			apDisplay.printMsg("proc3d not found or failed to process reconstruction. Skipping normalization.")
		else:
			os.system('rm %s' % mrc_full)
		
		# Link reconstruction to directory
		try:
			cmd1="mkdir -p %s 2>/dev/null; rm %s/%s %s/%s 2>/dev/null; ln %s %s 2>/dev/null" % (self.params['link_recon'], self.params['link_recon'], mrcf, self.params['link_recon'], mrcfn, mrc_full, self.params['link_recon'])
			cmd2="mkdir -p %s 2>/dev/null; rm %s/%s %s/%s 2>/dev/null; ln %s %s" % (self.params['link_recon'], self.params['link_recon'], mrcf, self.params['link_recon'], mrcfn, mrcn_full, self.params['link_recon'])
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
			print "\n%s\n" % (self.params['link_recon'])
		except:
			apDisplay.printMsg("Reconstruction can be found in this directory:")
			print "\n%s\n" % (recon_out_dir)
			if proc.returncode != 0:
				apDisplay.printMsg("The reconstruction in the above directory is not normalized because EMAN1 and EMAN2 were either not found or failed to process the reconstruction.")
			
		os.system("rm %s/cache/%s*" % (recon_dir, seriesname))

#=====================
if __name__ == '__main__':
	protomo2reconstruction = ProTomo2Reconstruction()
	protomo2reconstruction.start()
	protomo2reconstruction.close()
	protomo2reconstruction_log=cwd+'/'+'protomo2reconstruction.log'
	cleanup="mv %s %s/protomo2reconstruction_%s.log" % (protomo2reconstruction_log, wd, timestr)
	os.system(cleanup)
