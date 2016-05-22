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
import numpy as np
import multiprocessing as mp
from pyami import mrc
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apProTomo2Aligner
from appionlib import apProTomo2Prep
from appionlib.apImage import imagefilter

try:
	import protomo
except:
	apDisplay.printError("Protomo did not get imported. Exitting.")

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
		
		self.parser.add_option("--exclude_images", dest="exclude_images",  default="999999",
			help='Select specific images in the tilt-series, e.g. --exclude_images="1,2,5-7"')
		
		self.parser.add_option("--negative_recon", dest="negative_recon", type="float",  default="-90",
			help="Tilt angle, in degrees, below which all images will be removed, e.g. --negative_recon=-45", metavar="float")
		
		self.parser.add_option("--positive_recon", dest="positive_recon", type="float",  default="90",
			help="Tilt angle, in degrees, above which all images will be removed, e.g. --positive_recon=45", metavar="float")
		
		self.parser.add_option("--tomo3d_procs", dest="tomo3d_procs", default=1,
			help="Number of cores to use in Tomo3D, e.g. --tomo3d_procs=24")

		self.parser.add_option("--tomo3d_options", dest="tomo3d_options", default='',
			help="Number of Tomo3D SIRT iterations, e.g. --tomo3d_options=-m 0.35 -A 7 -w off")

		self.parser.add_option("--tomo3d_sirt_iters", dest="tomo3d_sirt_iters",  type="int",
			help="Number of Tomo3D SIRT iterations, e.g. --tomo3d_sirt_iters=20", metavar="int")

		self.parser.add_option("--reconstruction_method", dest="reconstruction_method",  type="int",
			help="Software to use for reconstructon. 1: Protomo WBP, 2: Tomo3D WBP, 3: Tomo3D SIRT, e.g. --reconstruction_method=2", metavar="int")

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
		
		self.parser.add_option("--frame_aligned", dest="frame_aligned",  default="True",
			help="Use frame-aligned images instead of naively summed images, if present.")
		
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
	
	def rotateAndTranslateImage(self, i, tiltfilename, rundir, recon_dir, mrc_list, tilt_list):
		"""
		Rotates and tanslates a single image.
		"""
		try:
			#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/FILE/) print $(j+1)}' | tr '\n' ' ' | sed 's/ //g'" % (i, tiltfilename)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(filename, err) = proc.communicate()
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i, tiltfilename)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i, tiltfilename)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ROTATION/) print $(j+1)}'" % (i, tiltfilename)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(rotation, err) = proc.communicate()
			rotation=float(rotation)
			cmd5="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i, tiltfilename)
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			tilt_angle=float(tilt_angle)
			cmd6="awk '/AZIMUTH /{print $3}' %s" % tiltfilename
			proc=subprocess.Popen(cmd6, stdout=subprocess.PIPE, shell=True)
			(azimuth, err) = proc.communicate()
			azimuth=float(azimuth)
			tilt_list.append(tilt_angle)
			mrcf=os.path.join(rundir,'raw',filename+'.mrc')
			mrcf_out=os.path.join(recon_dir,'tomo3d',filename+'.mrc')
			mrc_list.append(mrcf_out)
			image=mrc.read(mrcf)
			dimx=len(image[0])
			dimy=len(image)
			transx=int((dimx/2) - originx)
			transy=int((dimy/2) - originy)
			
			if originx > dimx/2:    #shift left
				image=np.roll(image,transx,axis=1)
				for k in range(-1,transx-1,-1):
					image[:,k]=0
			elif originx < dimx/2:    #shift right
				image=np.roll(image,transx,axis=1)
				for k in range(transx):
					image[:,k]=0
			# dont shift if originx = dimx/2
			
			#Translate pixels up or down?
			if originy < dimy/2:    #shift down
				image=np.roll(image,transy,axis=0)
				for k in range(transy):
					image[k]=0
			elif originy > dimy/2:    #shift up
				image=np.roll(image,transy,axis=0)
				for k in range(-1,transy-1,-1):
					image[k]=0
			# dont shift if originy = dimy/2
			
			#Write temp mrc before rotation
			mrc.write(image,mrcf_out)
			
			#Rotate image
			rot = -90 - azimuth - rotation
			command1='proc2d %s %s clip=%d,%d >/dev/null' % (mrcf_out, mrcf_out, max(dimx,dimy), max(dimx,dimy))
			command2='proc2d %s %s clip=%d,%d rot=%s >/dev/null' % (mrcf_out, mrcf_out, dimy, dimx, rot)
			os.system(command1)
			os.system(command2)
			
			return dimx,dimy
		except:
			return 0,0
	
	#=====================
	def start(self):
		if (self.params['tomo3d_procs'] == "all"):
			self.params['tomo3d_procs'] = mp.cpu_count()
		else:
			self.params['tomo3d_procs'] = int(self.params['tomo3d_procs'])
		z = int(round(self.params['recon_thickness']/(self.params['pixelsize']*self.params['recon_map_sampling'])))
		it="%03d" % (self.params['recon_iter'])
		itt="%03d" % (self.params['recon_iter']-1)
		global wd
		wd=self.params['rundir']
		raw_path=os.path.join(wd, 'raw')
		os.chdir(self.params['rundir'])
		seriesnumber = "%04d" % int(self.params['tiltseries'])
		seriesname='series'+seriesnumber
		param_out=seriesname+'.param'
		param_out_full=self.params['rundir']+'/'+param_out
		tilt_out_full=self.params['rundir']+'/'+seriesname+itt+'.tlt'
		stack_dir_full=self.params['rundir']+'/stack/'
		if self.params['reconstruction_method'] == 1:
			recon_dir=self.params['rundir']+'/recons_protomo/'
		elif self.params['reconstruction_method'] == 2:
			recon_dir=self.params['rundir']+'/recons_tomo3d_WBP/'
		elif self.params['reconstruction_method'] == 3:
			recon_dir=self.params['rundir']+'/recons_tomo3d_SIRT/'
		elif self.params['reconstruction_method'] == 4:
			recon_dir=self.params['rundir']+'/stack_temp/'
		else:
			apDisplay.printMsg("Error: Must choose reconstruction_method to be either 1, 2, 3, or 4.")
			sys.exit()
		os.system('mkdir %s 2>/dev/null' % recon_dir)
		recon_param_out_full=recon_dir+'/'+param_out
		recon_tilt_out_full=recon_dir+'/'+seriesname+'.tlt'
		recon_cache_dir=recon_dir+'/cache'
		recon_out_dir=recon_dir+'out'
		os.system('cp %s %s' % (tilt_out_full, recon_tilt_out_full))
		os.system('cp %s %s' % (param_out_full,recon_param_out_full))
		
		#CTF Correction
		if (self.params['ctf_correct'] == 'True'):
			apProTomo2Prep.ctfCorrect(seriesname, self.params['rundir'], self.params['projectid'], self.params['sessionname'], int(self.params['tiltseries']), recon_tilt_out_full, self.params['frame_aligned'], self.params['pixelsize'], self.params['DefocusTol'], self.params['iWidth'], self.params['amp_contrast'])
		
		#Dose Compensation
		if (self.params['dose_presets'] != 'False'):
			if self.params['reconstruction_method'] == 4:
				apProTomo2Prep.doseCompensate(seriesname, self.params['rundir'], self.params['sessionname'], int(self.params['tiltseries']), self.params['frame_aligned'], raw_path, self.params['pixelsize'], self.params['dose_presets'], self.params['dose_a'], self.params['dose_b'], self.params['dose_c'], dose_compensate="False")
			else:
				apProTomo2Prep.doseCompensate(seriesname, self.params['rundir'], self.params['sessionname'], int(self.params['tiltseries']), self.params['frame_aligned'], raw_path, self.params['pixelsize'], self.params['dose_presets'], self.params['dose_a'], self.params['dose_b'], self.params['dose_c'])
		
		# Remove specific images if user requests
		if (self.params['exclude_images'] != "999999"):
			self.params['exclude_images'] = apProTomo2Aligner.hyphen_range(self.params['exclude_images'])
			for imagenumber in self.params['exclude_images']:
				apProTomo2Aligner.removeImageFromTiltFile(recon_tilt_out_full, imagenumber, remove_refimg="True")
			apDisplay.printMsg("Images %s have been removed from the .tlt file by user request" % self.params['exclude_images'])
		else:
			self.params['exclude_images'] = [999999]
		
		# Remove high tilts from .tlt file if user requests
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (recon_tilt_out_full)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (recon_tilt_out_full)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		cmd3="awk '/FILE/{print}' %s | wc -l" % (recon_tilt_out_full)
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(images, err) = proc.communicate()
		images=int(images) - len(self.params['exclude_images'])
		if (self.params['positive_recon'] < 90) or (self.params['negative_recon'] > -90):
			removed_images, mintilt, maxtilt = apProTomo2Aligner.removeHighTiltsFromTiltFile(recon_tilt_out_full, self.params['negative_recon'], self.params['positive_recon'])
			apDisplay.printMsg("Images %s have been removed before reconstruction by weighted back-projection" % removed_images)
		else:
			mintilt=0
			maxtilt=0
			for i in range(tiltstart-1,tiltstart+numimages):
				try: #If the image isn't in the .tlt file, skip it
					cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, recon_tilt_out_full)
					proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
					(tilt_angle, err) = proc.communicate()
					tilt_angle=float(tilt_angle)
					mintilt=min(mintilt,tilt_angle)
					maxtilt=max(maxtilt,tilt_angle)
				except:
					pass
		dim='%sx%s' % (self.params['recon_map_size_x'],self.params['recon_map_size_y'])
		ang='%sto%s' % (round(mintilt,1),round(maxtilt,1))
		
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
		command22="sed -i \"%ss/.*/   size: { %s, %s, %s }  (* AP reconstruction map size *)/\" %s" % (mapsizeline, int(self.params['recon_map_size_x']/self.params['recon_map_sampling']), int(self.params['recon_map_size_y']/self.params['recon_map_sampling']), z, recon_param_out_full)
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
		
		# Protomo Reconstruction by WBP
		if self.params['reconstruction_method'] == 1:
			#Lowpass filter reconstruction?
			cmd="grep -n 'AP lowpass map' %s | awk '{print $1}' | sed 's/://'" % (recon_param_out_full)
			proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			(lowpassmapline, err) = proc.communicate()
			lowpassmapline=int(lowpassmapline)
			if self.params['recon_lowpass'] == "False":
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
				lpavg = int((self.params['recon_lp_diam_x']+self.params['recon_lp_diam_y'])/2)
				lp='.lp%s' % lpavg
				self.params['recon_lp_diam_x'] = 2*self.params['pixelsize']*self.params['recon_map_sampling']/self.params['recon_lp_diam_x']
				self.params['recon_lp_diam_y'] = 2*self.params['pixelsize']*self.params['recon_map_sampling']/self.params['recon_lp_diam_y']
				cmd2="sed -i \"%ss/.*/     diameter:    { %s, %s } * S/\" %s" % (lowpassmapline+1, self.params['recon_lp_diam_x'], self.params['recon_lp_diam_y'], recon_param_out_full)
			os.system(cmd2)
			
			img=seriesname+'00_bck.img'
			mrcf=seriesname+'_ite'+it+'_dim'+dim+'_ang'+ang+'_bck.bin'+str(self.params['recon_map_sampling'])+lp+'_protomo.mrc'
			mrcfn=seriesname+'_ite'+it+'_dim'+dim+'_ang'+ang+'_bck.bin'+str(self.params['recon_map_sampling'])+lp+'_protomo.norm.mrc'
			img_full=recon_out_dir+'/'+img
			mrc_full=recon_out_dir+'/'+mrcf
			mrcn_full=recon_out_dir+'/'+mrcfn
			
			# AP Get param files ready for batch processing
			batchdir=self.params['rundir']+'/'+'ready_for_batch'
			coarse_param_full=self.params['rundir']+'/coarse_out/'+'coarse_'+param_out
			recon_param='recon_'+param_out
			command="mkdir %s 2>/dev/null; cp %s %s; cp %s %s; cp %s %s/%s; rm -r %s %s %s*i3t %s/cache %s/out %s 2>/dev/null" % (batchdir, coarse_param_full, batchdir, refine_param_full, batchdir, param_out_full, batchdir, recon_param, img_full, mrc_full, recon_dir, recon_dir, recon_dir, stack_dir_full)
			os.system(command)
			
			# Create reconstruction
			os.chdir(recon_dir)
			os.system("rm %s/cache/%s* %s/*i3t 2>/dev/null" % (recon_dir, seriesname, recon_dir))
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
				apDisplay.printMsg("\ne2proc3d not found or failed to process reconstruction. Trying proc3d...")
				try:
					command="proc3d %s %s norm" % (mrc_full, mrcn_full)
					proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
					(code, err) = proc.communicate()
				except:
					pass
			if proc.returncode != 0:
				apDisplay.printMsg("\nproc3d not found or failed to process reconstruction. Skipping normalization.")
			else:
				os.system('rm %s' % mrc_full)
			
			os.system("rm %s/cache/%s* %s/*i3t" % (recon_dir, seriesname, recon_dir))
		
		# Tomo3D Setup
		elif self.params['reconstruction_method'] == 2 or self.params['reconstruction_method'] == 3 or self.params['reconstruction_method'] == 4:
			apDisplay.printMsg("Translating images and rotating them with proc2d for Tomo3D/IMOD convention...")
			os.system('mkdir %s 2>/dev/null' % stack_dir_full)
			tomo3d_dir = os.path.join(recon_dir,'tomo3d')
			try:
				os.mkdir(os.path.join(tomo3d_dir))
			except OSError:
				pass
			
			mrc_list=[]
			tilt_list=[]
			dimx=0
			dimy=0
			for i in range(tiltstart,numimages+tiltstart+1):
				dx,dy = self.rotateAndTranslateImage(i, recon_tilt_out_full, self.params['rundir'], recon_dir, mrc_list, tilt_list)
				dimx=max(dx,dimx)
				dimy=max(dy,dimy)
			stack = np.zeros((len(mrc_list),dimx,dimy))
			for i in range(len(mrc_list)):
				stack[i,:,:] = mrc.read(mrc_list[i])
			stack_path = os.path.join(stack_dir_full,'stack_ite'+it+'.mrcs')
			mrc.write(stack,stack_path)
			
			tiltlist = os.path.join(stack_dir_full,'tiltlist.txt')
			f=open(tiltlist,'w')
			for tilt in tilt_list:
				f.write('%f\n' % tilt)
			f.close()
			
			os.system('rm -rf %s' % tomo3d_dir)
			
			if self.params['recon_map_sampling'] > 1:
				apDisplay.printMsg("Binning stack...")
				binned_stack = np.zeros((len(mrc_list),int(round(dimx/self.params['recon_map_sampling'])),int(round(dimy/self.params['recon_map_sampling']))))
				for i in range(len(mrc_list)):
					binned_stack[i,:,:] = imagefilter.binImg(stack[i,:,:], bin=self.params['recon_map_sampling'])
				stack_path = os.path.join(stack_dir_full,'stack_ite'+it+'_bin%s.mrcs' % self.params['recon_map_sampling'])
				mrc.write(binned_stack, stack_path)
		
		# Tomo3D Reconstruction by WBP
		if self.params['reconstruction_method'] == 2:
			z = int(math.ceil(z / 2.) * 2) # Rounds up the thickness to the nearest even number
			mrcf = seriesname+'_ite'+it+'_ang'+ang+'.bin'+str(self.params['recon_map_sampling'])+'_tomo3dWBP.mrc'
			mrc_full = recon_dir + mrcf
			os.system('rm -r %s 2>/dev/null' % mrc_full)
			cmd = 'tomo3d -a %s -i %s -t %s -v 2 -z %s %s -o %s' % (tiltlist, stack_path, self.params['tomo3d_procs'], z, self.params['tomo3d_options'], mrc_full)
		
		# Tomo3D Reconstruction by SIRT
		elif self.params['reconstruction_method'] == 3:
			z = int(math.ceil(z / 2.) * 2) # Rounds up the thickness to the nearest even number
			mrcf = seriesname+'_ite'+it+'_ang'+ang+'.bin'+str(self.params['recon_map_sampling'])+'_tomo3dSIRT_'+str(self.params['tomo3d_sirt_iters'])+'_iters.mrc'
			mrc_full = recon_dir + mrcf
			os.system('rm -r %s 2>/dev/null' % mrc_full)
			cmd = 'tomo3d -a %s -i %s -t %s -v 2 -z %s -S -l %s %s -o %s' % (tiltlist, stack_path, self.params['tomo3d_procs'], z, self.params['tomo3d_sirt_iters'], self.params['tomo3d_options'], mrc_full)
		
		if self.params['reconstruction_method'] == 2 or self.params['reconstruction_method'] == 3:
			print cmd
			os.system(cmd)
			print "Rotating reconstruction..."
			try:
				os.system('trimvol -rx %s %s' % (mrc_full, mrc_full))
				os.system('rm %s~' % mrc_full)
			except:
				apDisplay.printMsg("IMOD function \'trimvol\' not found, trying using pyami. If the file is large and your RAM is small this might not end well...")
				mrc.write(np.rot90(mrc.read(mrc_full)),mrc_full)
		
		if self.params['reconstruction_method'] == 4 and self.params['dose_presets'] != "False":
			#os.system('rm -r %s' % recon_dir)
			#Create a list of tilts, accumulated dose, and lowpass to be applied for the requested stack
			f1=open(os.path.join(self.params['rundir'],'stack','full_dose_lp_list.txt'),'r')
			f2=open(os.path.join(self.params['rundir'],'stack','stack_dose_lp_list.txt'),'w')
			for row in f1.readlines():
				if round(float(row.split(' ')[0]),3) in tilt_list:
					f2.write("%f %f %f\n" % (float(row.split(' ')[0]), float(row.split(' ')[1]), float(row.split(' ')[2])))
			f1.close()
			f2.close()
			
			#Create a small python script that, when executed on a stack, will dose compensate that stack using the values from the stack_dose_lp_list
			f=open(os.path.join(self.params['rundir'],'stack','stack_dose_compensate.py'),'w')
			f.write("#!/usr/bin/env python\n")
			f.write("# Use to dose compensate stack after you have done post processing (eg. TomoCTF correction).\n")
			f.write("# Usage: ./stack_dose_compensate.py stack_dose_lp_list.txt <input_stack> <output_stack>\n")
			f.write("import sys\n")
			f.write("import numpy as np\n")
			f.write("from pyami import mrc\n")
			f.write("from appionlib.apImage import imagefilter\n")
			f.write("f=open(sys.argv[1],'r')\n")
			f.write("stack = mrc.read(sys.argv[2])\n")
			f.write("lps=[]\n")
			f.write("for row in f.readlines():\n")
			f.write("	lps.append(row.split(' ')[2])\n")
			f.write("f.close()\n")
			f.write("new_stack=[]\n")
			f.write("for i in range(len(stack)):\n")
			f.write("	im = imagefilter.lowPassFilter(stack[i], apix=float(%s), radius=float(lps[i]), msg=False)\n" % self.params['pixelsize'])
			f.write("	new_stack.append(im)\n")
			f.write("mrc.write(np.asarray(new_stack), sys.argv[3])\n")
			f.close()
			apDisplay.printMsg("Dose compensation script created: stack_dose_compensate.py")
			os.system("chmod +x %s" % os.path.join(self.params['rundir'],'stack','stack_dose_compensate.py'))
			
			#Create a small python script that, when executed on a stack, will bin the stack
			f=open(os.path.join(self.params['rundir'],'stack','stack_binning.py'),'w')
			f.write("#!/usr/bin/env python")
			f.write("# Usage: ./stack_binning.py <stack.mrcs> <binning factor>")
			f.write("import os, sys, numpy as np")
			f.write("from pyami import mrc")
			f.write("from appionlib.apImage import imagefilter")
			f.write("stack = mrc.read(sys.argv[1])")
			f.write("sampling = int(sys.argv[2])")
			f.write("dimx = len(stack[0])")
			f.write("dimy = len(stack[0][0])")
			f.write("new_dimx = int(round(dimx/sampling))")
			f.write("new_dimy = int(round(dimy/sampling))")
			f.write("binned_stack = np.zeros((len(stack),new_dimx,new_dimy))")
			f.write("for i in range(len(stack)):")
			f.write("	binned_stack[i,:,:] = imagefilter.binImg(stack[i,:,:], bin=sampling)")
			f.write("stack_file = '%s_bin%s.mrcs' % (os.path.splitext(sys.argv[1])[0], sampling)")
			f.write("mrc.write(binned_stack, stack_file)")
			f.close()
			apDisplay.printMsg("Stack binning script created: stack_binning.py")
			os.system("chmod +x %s" % os.path.join(self.params['rundir'],'stack','stack_binning.py'))
		
		#Create two python scripts for creating either per-article or per-tomogram data-based custom fourier wedges
		os.system('mkdir %s 2>/dev/null' % os.path.join(self.params['rundir'],'SPT'))
		f=open(os.path.join(self.params['rundir'],'SPT','auto_fourier_masking_particles.py'),'w')
		f.write("#!/usr/bin/env python\n")
		f.write("# Creates a data-based fourier mask for each particle named pfmask_#####.em\n")
		f.write("# Sigma = 2.3 works for me. Run in Dynamo data folder.\n")
		f.write("# Files must be named particle_#####.em from 00001 and without gaps (ie. Dynamo format)\n")
		f.write("# Requires Appion and EMAN2\n")
		f.write("# Usage: ./auto_fourier_masking_particles.py <sigma threshold> <# procs>\n")
		f.write("import os, sys, glob, numpy as np, multiprocessing as mp\n")
		f.write("from pyami import mrc\n")
		f.write("from appionlib.apImage import imagefilter\n")
		f.write("filelist=glob.glob('particle_*.em')\n")
		f.write("def createFourierMask(i):\n")
		f.write("	fname = 'particle_%05d' % i\n")
		f.write("	mname = 'pfmask_%05d' % i\n")
		f.write("	if os.path.isfile(os.path.join(os.getcwd(),mname+'.em')) is False:\n")
		f.write("		os.system('e2proc3d.py %s.em %s.mrc' % (fname, fname))\n")
		f.write("		f = mrc.read('%s.mrc' % fname)\n")
		f.write("		ft_big = imagefilter.scaleImage(np.sqrt(np.square(np.real(np.fft.fftn(f)))),2)\n")
		f.write("		roll_length = len(ft_big)/2 - 1\n")
		f.write("		ft_big = np.roll(np.roll(np.roll(ft_big,roll_length-1),roll_length,0),roll_length-1,1)\n")
		f.write("		ft = imagefilter.scaleImage(ft_big,0.5)\n")
		f.write("		ft2 = ft\n")
		f.write("		low = ft2 < ft.mean() + float(sys.argv[1])*ft.std()\n")
		f.write("		high = ft2 >= ft.mean() + float(sys.argv[1])*ft.std()\n")
		f.write("		ft2[low] = 0\n")
		f.write("		ft2[high] = 1\n")
		f.write("		mrc.write(ft2,'%s.mrc' % mname)\n")
		f.write("		os.system('e2proc3d.py %s.mrc %s.em;rm %s.mrc %s.mrc' % (mname, mname, mname, fname))\n")
		f.write("for i in range(1,len(filelist)+1):\n")
		f.write("	p = mp.Process(target=createFourierMask, args=(i,))\n")
		f.write("	p.start()\n")
		f.write("	if (i % int(sys.argv[2]) == 0) and (i != 0):\n")
		f.write("		[p.join() for p in mp.active_children()]\n")
		f.close()
		apDisplay.printMsg("Custom per-particle fourier wedge script created: auto_fourier_masking_particles.py")
		
		f=open(os.path.join(self.params['rundir'],'SPT','auto_fourier_masking_tomogram.py'),'w')
		f.write("#!/usr/bin/env python\n")
		f.write("# Creates a data-based fourier mask for a given tomogram by averaging 9 fourier sub-tomogram transforms.\n")
		f.write("# Particle size must be even and smaller than the tomogram.\n")
		f.write("# Requires Appion, EMAN2, and IMOD\n")
		f.write("# Usage: ./auto_fourier_masking_tomogram.py <tomogram> <sigma threshold> <particle size> <distance from edges>\n")
		f.write("import os, sys, glob, subprocess, numpy as np\n")
		f.write("from pyami import mrc\n")
		f.write("from appionlib.apImage import imagefilter\n")
		f.write("proc=subprocess.Popen('header %s |grep grid>tempppp;awk \\'{print $11}\\' tempppp;rm tempppp' % sys.argv[1], stdout=subprocess.PIPE, shell=True)\n")
		f.write("(x, err) = proc.communicate()\n")
		f.write("x=int(x)\n")
		f.write("proc=subprocess.Popen('header %s |grep grid>tempppp;awk \\'{print $12}\\' tempppp;rm tempppp' % sys.argv[1], stdout=subprocess.PIPE, shell=True)\n")
		f.write("(y, err) = proc.communicate()\n")
		f.write("y=int(y)\n")
		f.write("proc=subprocess.Popen('header %s |grep grid>tempppp;awk \\'{print $13}\\' tempppp;rm tempppp' % sys.argv[1], stdout=subprocess.PIPE, shell=True)\n")
		f.write("(z, err) = proc.communicate()\n")
		f.write("z=int(z)\n")
		f.write("size = int(sys.argv[3])\n")
		f.write("dist = int(sys.argv[4])\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 1.mrc' % (dist, dist+size-1, dist, dist+size-1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 2.mrc' % (x/2 - size/2, x/2 + size/2 - 1, dist, dist+size-1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 3.mrc' % (x/2 - size/2, x/2 + size/2 - 1,y/2 - size/2, y/2 + size/2 - 1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 4.mrc' % (dist, dist+size-1, y/2 - size/2, y/2 + size/2 - 1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 5.mrc' % (x-dist-size, x-dist-1, dist, dist+size-1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 6.mrc' % (x-dist-size, x-dist-1, y/2 - size/2, y/2 + size/2 - 1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 7.mrc' % (x-dist-size, x-dist-1, y-dist-size, y-dist-1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 8.mrc' % (x/2 - size/2, x/2 + size/2 - 1, y-dist-size, y-dist-1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("os.system('trimvol -x %s,%s -y %s,%s -z %s,%s %s 9.mrc' % (dist, dist+size-1, y-dist-size, y-dist-1, z/2 - size/2, z/2 + size/2 - 1, sys.argv[1]))\n")
		f.write("fftsum = np.zeros((size,size,size))\n")
		f.write("for i in range(1,10):\n")
		f.write("	v=mrc.read('%s.mrc' % i)\n")
		f.write("	ft_big = imagefilter.scaleImage(np.square(np.real(np.fft.fftn(v))),2)\n")
		f.write("	roll_length = len(ft_big)/2 - 1\n")
		f.write("	ft_big = np.roll(np.roll(np.roll(ft_big,roll_length-1),roll_length,0),roll_length-1,1)\n")
		f.write("	ft = imagefilter.scaleImage(ft_big,0.5)\n")
		f.write("	fftsum = fftsum + ft\n")
		f.write("	os.system('rm %s.mrc' % i)\n")
		f.write("fftsum = fftsum/9\n")
		f.write("fftsum2 = fftsum\n")
		f.write("low = fftsum2 < fftsum.mean() + float(sys.argv[2])*fftsum.std()\n")
		f.write("high = fftsum2 >= fftsum.mean() + float(sys.argv[2])*fftsum.std()\n")
		f.write("fftsum2[low] = 0\n")
		f.write("fftsum2[high] = 1\n")
		f.write("mrc.write(fftsum2, '%s.pfmask%s.mrc' % (os.path.splitext(sys.argv[1])[0],size))\n")
		f.write("os.system('e2proc3d.py %s.pfmask%s.mrc %s.pfmask%s.em; rm %s.pfmask%s.mrc' % (os.path.splitext(sys.argv[1])[0],size, os.path.splitext(sys.argv[1])[0],size, os.path.splitext(sys.argv[1])[0],size))\n")
		f.write("print 'Link this fourier mask to your data folder for each particle, for example in bash:'\n")
		f.write("print 'for i in {#####..#####};do ln %s data/pfmask_${i}.em;done'\n")
		f.write("print 'where #####..##### is the particle number range for the given tomogram.'\n")
		f.close()
		apDisplay.printMsg("Custom per-tomogram fourier wedge script created: auto_fourier_masking_tomogram.py")
		os.system("chmod +x %s %s" % (os.path.join(self.params['rundir'],'SPT','auto_fourier_masking_particles.py'), os.path.join(self.params['rundir'],'SPT','auto_fourier_masking_tomogram.py')))
		
		# Link reconstruction to directory
		try:
			cmd1="mkdir -p %s 2>/dev/null; rm %s/%s %s/%s 2>/dev/null; ln -f %s %s 2>/dev/null" % (self.params['link_recon'], self.params['link_recon'], mrcf, self.params['link_recon'], mrcfn, mrc_full, self.params['link_recon'])
			cmd2="mkdir -p %s 2>/dev/null; rm %s/%s %s/%s 2>/dev/null; ln -f %s %s" % (self.params['link_recon'], self.params['link_recon'], mrcf, self.params['link_recon'], mrcfn, mrcn_full, self.params['link_recon'])
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
			if ((self.params['link_recon'] == None) or (self.params['link_recon'] == "") or (len(self.params['link_recon']) < 1) and (self.params['reconstruction_method'] == 1)):
				print "\n%s\n" % (recon_out_dir)
			elif ((self.params['link_recon'] == None) or (self.params['link_recon'] == "") or (len(self.params['link_recon']) < 1) and (self.params['reconstruction_method'] == 2 or self.params['reconstruction_method'] == 3)):
				print "\n%s\n" % (recon_dir)
			else:
				print "\n%s\n" % (self.params['link_recon'])
		except:
			apDisplay.printMsg("Reconstruction can be found in this directory:")
			if self.params['reconstruction_method'] == 1:
				print "\n%s\n" % (recon_out_dir)
				if proc.returncode != 0:
					apDisplay.printMsg("The reconstruction in the above directory is not normalized because EMAN1 and EMAN2 were either not found or failed to process the reconstruction.")
			if self.params['reconstruction_method'] == 2 or self.params['reconstruction_method'] == 3:
				print "\n%s\n" % (recon_dir)
			else:
				print "\n%s\n" % (stack_dir_full)
				os.system('rm -r %s 2>/dev/null' % recon_dir)
		
		apDisplay.printMsg("Two scripts for creating per-particle or per-tomogram custom fourier wedges for single particle tomography can be found in:")
		print "\n%s\n" % (os.path.join(self.params['rundir'],'SPT'))
		

#=====================
if __name__ == '__main__':
	protomo2reconstruction = ProTomo2Reconstruction()
	protomo2reconstruction.start()
	protomo2reconstruction.close()
	protomo2reconstruction_log=cwd+'/'+'protomo2reconstruction.log'
	cleanup="mv %s %s/protomo2reconstruction_%s.log" % (protomo2reconstruction_log, wd, timestr)
	os.system(cleanup)
