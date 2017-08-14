#!/usr/bin/env python

from __future__ import division
import math
import os
import re
import sys
import glob
import shutil
import subprocess
import scipy.misc
import scipy.interpolate
import multiprocessing as mp
import numpy as np
from pyami import mrc
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apProTomo2Aligner
from appionlib.apImage import imagenorm
from appionlib.apImage import imagefilter
from scipy.ndimage.interpolation import rotate as imrotate

try:
	import sinedon
	from appionlib import apTomo
	from appionlib import appiondata
	from appionlib import apProTomo
	from appionlib import apDatabase
	from appionlib.apCtf import ctfdb
except:
	apDisplay.printWarning("MySQLdb not found...database retrieval disabled")

		
#=====================
def setRefImg(self, tilts):
	# use the tilt geometry to set the reference image. Look for tilt angle closest to 0, may be off by .1 degree.	
	bestPosVal = 0.10
	bestNegVal = -0.10

	for tilt in tilts:
		if tilt <= bestPosVal and tilt > bestNegVal:
			self.refimg = tilts.index(tilt)
			if tilt >= 0:
				bestPosVal = tilt
			else:
				bestNegVal = tilt

#=====================
def parseCorrectionFactors(self, tiltfile):
	try:
		f=open(tiltfile)
		lines=f.readlines()
	except:
		apDisplay.printWarning("Failed to read the protomo2 Correction Factors file, %s" % (tiltfile, ))
	else:
		f.close()

		# Create a dictionary to store Correction Factor and rotation information for each image 
		imagedict = {}
		for n in lines:
			words = n.split()
			if len(words) is not 6:
				apDisplay.printError("The protomo2 correction factors file, %s, is not properly formatted." % (tiltfile, ))

			image_number = int(words[0])
			imagedict[image_number] = {}
			imagedict[image_number]['rotation'] = float(words[1])
			imagedict[image_number]['x'] = float(words[2])
			imagedict[image_number]['y'] = float(words[3])

		return imagedict

#=======================
def convertShiftsToOrigin(shifts,imagesize_x, imagesize_y):
	newshift=[]
	origin_x=imagesize_x/2.0
	origin_y=imagesize_y/2.0
	for shift in shifts:
		newx=origin_x+shift['x']
		newy=origin_y-shift['y']
		newshift.append({'x':newx,'y':newy})
	return newshift
		

#=======================
def frameOrNonFrameTiltdata(tiltdata):
	'''
	Takes tiltdata with or without frame aligned images and returns tiltdata with
	the non-frame aligned images and the most recent frame aligned images.
	'''
	#tilt image siblings are determined by their scope dbids. Another way to do this would be to group by parent image.
	scope_dbid_list=[]
	for i in range(len(tiltdata)):
		scope_dbid_list.append(tiltdata[i]['scope'].dbid)
	frame_tiltdata=[]
	non_frame_tiltdata=[]
	completed_images=[]
	for i in range(len(tiltdata)):
		if tiltdata[i]['scope'].dbid not in completed_images:
			image_dbid_list=[]
			tiltdata_list=[]
			for j in range(len(scope_dbid_list)):
				if tiltdata[i]['scope'].dbid == scope_dbid_list[j]:
					image_dbid_list.append(tiltdata[j].dbid)
					tiltdata_list.append(tiltdata[j])
			frame_tiltdata_element=[k for k, x in enumerate(image_dbid_list) if x == max(image_dbid_list)][0]
			non_frame_tiltdata_element=[k for k, x in enumerate(image_dbid_list) if x == min(image_dbid_list)][0]
			frame_tiltdata.append(tiltdata_list[frame_tiltdata_element])
			non_frame_tiltdata.append(tiltdata_list[non_frame_tiltdata_element])
			completed_images.append(tiltdata[i]['scope'].dbid)
	
	return frame_tiltdata, non_frame_tiltdata


#=======================
def frameOrNonFrameTiltdata2(tiltdata):
	'''
	Takes tiltdata with or without frame aligned images and returns tiltdata with
	the non-frame aligned images and the most recent frame aligned images. This is Anchi's version.
	'''
	aligned_images = []
	for unalignedimage in tiltdata:
		tiltpair_results = appiondata.ApDDImagePairData.query(source=unalignedimage).query(results=1)
		alignedimage = tiltpair_results[0]['result']
		aligned_images.append(alignedimage)
	return aligned_images, tiltdata


#=======================
def prepareTiltFile(sessionname, seriesname, tiltfilename, tiltseriesnumber, raw_path, frame_aligned_images, link=False, coarse=True):
	'''
	Creates tlt file from basic image information and copies raw images
	'''
	
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
	tiltdata = apTomo.getImageList([tiltseriesdata], ddstackid=None, appion_protomo=True)
	apDisplay.printMsg("getting imagelist")
	
	frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
	tilts,ordered_imagelist,accumulated_dose_list,ordered_mrc_files,refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned=frame_aligned_images)
	if frame_aligned_images == "True":  #Azimuth is only present in the non-frame aligned images
		a,ordered_imagelist_for_azimuth,c,d,e = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned="False")
	
	#tilts are tilt angles, ordered_imagelist are imagedata, ordered_mrc_files are paths to files, refimg is an int
	maxtilt = max([abs(tilts[0]),abs(tilts[-1])])
	apDisplay.printMsg("highest tilt angle is %f" % maxtilt)
	
	if coarse == "True":
		if frame_aligned_images == "True":  #Azimuth is only present in the non-frame aligned images
			azimuth = apTomo.getAverageAzimuthFromSeries(ordered_imagelist_for_azimuth)
		else:
			azimuth = apTomo.getAverageAzimuthFromSeries(ordered_imagelist)
		
		rawexists = apParam.createDirectory(raw_path)
		
		apDisplay.printMsg("Copying raw images, normalizing, and converting images to float32 for Protomo...") #Linking removed because raw images will likely be edited by the user.
		newfilenames, new_ordered_imagelist = apProTomo.getImageFiles(ordered_imagelist, raw_path, link=False, copy="True")
		apDisplay.printMsg("Creating a backup copy of the original tilt images...")
		original_raw = os.path.join(raw_path,'original')
		os.system('mkdir %s 2>/dev/null;cp %s/*mrc %s' % (original_raw,raw_path,original_raw))
		
		###create tilt file
		#get image size from the first image
		imagesizex = tiltdata[0]['image'].shape[1]
		imagesizey = tiltdata[0]['image'].shape[0]
		
		#shift half tilt series relative to eachother
		#SS I'm arbitrarily making the bin parameter here 1 because it's not necessary to sample at this point
		shifts = apTomo.getGlobalShift(ordered_imagelist, 1, refimg)
		
		#OPTION: refinement might be more robust by doing one round of IMOD aligment to prealign images before doing protomo refine
		origins = convertShiftsToOrigin(shifts, imagesizex, imagesizey)
	
		writeTiltFile2(tiltfilename, seriesname, newfilenames, origins, tilts, azimuth, refimg)
	
	return tilts, accumulated_dose_list, new_ordered_imagelist, maxtilt


#=====================
def writeTiltFile(tiltfile, seriesname, imagedict, azimuth, refimg ):
	'''
	Create the geometry object (tilt angles, dir of tilt axis, origins of ROI) ---
	1. read the params from the database 
	2. write params to text file
	'''


	try:
		f = open(tiltfile,'w')
	except:
		apDisplay.printWarning("Failed to create %s for writing the protomo2 tilt geometry parameter file" % (tiltfile, ))
		raise

	f.write('\n')


	f.write ("TILT SERIES %s\n" % seriesname)
	f.write ("\n") 
	f.write ("   AXIS\n")
	f.write ("\n")
	f.write ("     TILT AZIMUTH    %g\n" % azimuth)
	f.write ("\n")

	keys = imagedict.keys()
	keys.sort()
	for n in keys:
		f.write ("   IMAGE %-5d     FILE %s       ORIGIN [ %8.3f %8.3f ]    TILT ANGLE    %8.3f    ROTATION     %8.3f\n" % (n, imagedict[n]['filename'], imagedict[n]['x'], imagedict[n]['y'], imagedict[n]['tilt'], imagedict[n]['rotation']))

	f.write ("\n")
	f.write ("   REFERENCE IMAGE %d\n" % refimg)
	f.write ("\n")
	f.write ("\n")
	f.write (" END\n")
	f.close()

#====================
# This function duplicates the one above. Should migrate to this one in the future. 
def writeTiltFile2(tiltfile, seriesname, imagelist, origins, tilts, azimuth, refimg):
	
	try:
		f = open(tiltfile,'w')
	except:
		apDisplay.printWarning("Failed to create %s for writing the protomo2 tilt geometry parameter file" % (tiltfile, ))
		raise
	
	f.write('\n')


	f.write ("TILT SERIES %s\n" % seriesname)
	f.write ("\n") 
	f.write ("   AXIS\n")
	f.write ("\n")
	f.write ("     TILT AZIMUTH    %g\n" % azimuth)
	f.write ("\n")
	for n in range(len(imagelist)):
		imagename=os.path.splitext(os.path.basename(imagelist[n]))[0] #strip off path and extension from mrc file
		f.write ("   IMAGE %-5d     FILE %s       ORIGIN [ %8.3f %8.3f ]    TILT ANGLE    %8.3f    ROTATION     %8.3f\n" % (n+1, imagename, origins[n]['x'], origins[n]['y'], tilts[n], 0))

	f.write ("\n")
	f.write ("   REFERENCE IMAGE %d\n" % refimg)
	f.write ("\n")
	f.write ("\n")
	f.write (" END\n")
	f.close()


def rotateAndTranslateImage(i, tiltfilename, rundir, recon_dir, mrc_list, tilt_list):
		"""
		Rotates and tanslates a single image from Protomo orientation to IMOD orientation.
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
			mrcf=os.path.join(rundir,'raw','original',filename+'.mrc')
			mrcf_out=os.path.join(recon_dir,filename+'.mrc')
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
			#rot = -azimuth - rotation
			command1='proc2d %s %s clip=%d,%d >/dev/null' % (mrcf_out, mrcf_out, max(dimx,dimy), max(dimx,dimy))
			command2='proc2d %s %s clip=%d,%d rot=%s >/dev/null' % (mrcf_out, mrcf_out, dimy, dimx, rot)
			os.system(command1)
			os.system(command2)
			
			return dimx,dimy
		except:
			return 0,0


#=====================
def determineTomoctfDirection(rundir, stack_path, tilt_angles_path, defocus, cs, voltage, amp_contrast, pixelsize):
	'''
	Determines the direction of the defocus gradient using tomoctfgrad.exe by running
	the software on the given orientation and on the orientation with negative tilt
	angles, checking that one is correct and the other is not, then overwrites the
	given tilt file with the proper one.
	'''
	def runTomoCTFGrad(job):
		os.system(job)
		return
	apDisplay.printMsg('Determining the direction of the defocus gradient of the stack...')
	
	#Make a new tilt file with the tilts all negative of the original
	filename, extension = os.path.splitext(tilt_angles_path)
	negative_tilt_angles_path = tilt_angles_path.replace(tilt_angles_path,filename+'_negative'+extension)
	cmd="awk '{p=-1*$0;$0=p>1000?1:p}7' %s > %s" % (tilt_angles_path,negative_tilt_angles_path)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	
	tomoctfgrad_file=os.path.join(rundir,'tomoctfgrad.csh')
	f=open(tomoctfgrad_file,'w')
	f.write("#!/bin/csh -f\n")
	f.write("time `which tomoctfgrad.exe` << eof\n")
	f.write("%s\n" % stack_path)
	f.write("%s\n" % tilt_angles_path)
	f.write("%s/diagnostic.mrc\n" % rundir)
	f.write("384\n")
	f.write("%f %f %f %d %f\n" % (cs, voltage, amp_contrast, 10000, pixelsize))
	f.write("0.5 100000 %f\n" % (pixelsize*4))
	f.write("%f %f 500\n" % (defocus*0.8*10000, defocus*1.2*10000))
	f.write("eof\n")
	f.close()
	
	tomoctfgrad_file_negative=os.path.join(rundir,'tomoctfgrad_negative.csh')
	f=open(tomoctfgrad_file_negative,'w')
	f.write("#!/bin/csh -f\n")
	f.write("time `which tomoctfgrad.exe` << eof\n")
	f.write("%s\n" % stack_path)
	f.write("%s\n" % negative_tilt_angles_path)
	f.write("%s/diagnostic_negative.mrc\n" % rundir)
	f.write("384\n")
	f.write("%f %f %f %d %f\n" % (cs, voltage, amp_contrast, 10000, pixelsize))
	f.write("0.5 100000 %f\n" % (pixelsize*4))
	f.write("%f %f 500\n" % (defocus*0.8*10000, defocus*1.2*10000))
	f.write("eof\n")
	f.close()
	
	os.system('chmod +x %s %s' % (tomoctfgrad_file,tomoctfgrad_file_negative))
	
	jobs=[]
	jobs.append('%s > %s/tomoctfgrad.log' % (tomoctfgrad_file,rundir))
	jobs.append('%s > %s/tomoctfgrad_negative.log' % (tomoctfgrad_file_negative,rundir))
	#jobs.append('%s' % (tomoctfgrad_file))
	#jobs.append('%s' % (tomoctfgrad_file_negative))
	
	for i in range(len(jobs)):
		p = mp.Process(target=runTomoCTFGrad, args=(jobs[i],))
		p.start()
	[p.join() for p in mp.active_children()]
	
	os.system('rm %s/diagnostic.mrc "%s/diagnostic_negative.mrc' % (rundir,rundir))
	
	if ('NOT' in open('%s/tomoctfgrad_negative.log' % rundir).read()) and not ('NOT' in open('%s/tomoctfgrad.log' % rundir).read()):
		apDisplay.printMsg('The stack is oriented as per TomoCTF defocus gradient requrements.')
	elif ('NOT' in open('%s/tomoctfgrad.log' % rundir).read()) and not ('NOT' in open('%s/tomoctfgrad_negative.log' % rundir).read()):
		apDisplay.printMsg('The stack is not oriented as per TomoCTF defocus gradient requrements. Tilt angles will be multiplied by -1.')
		os.system('mv %s %s' % (negative_tilt_angles_path, tilt_angles_path))
	else:
		apDisplay.printWarning('Defocus gradient could not be determined. Using tilt angles as in database.')
	

#=====================
def defocusEstimate(seriesname, rundir, projectid, sessionname, procs, tiltseriesnumber, tiltfilename, frame_aligned_images, pixelsize, defocus_ang_negative, defocus_ang_positive, amp_contrast, res_min, res_max, defocus, defocus_difference, defocus_min=0, defocus_max=0, defocus_save=0):
	"""
	TomoCTFps and TomoCTFFind will be used to estimate the defocus of the untilted plane.
	These functions will be run with varying defocus, tile size, and CTFmin values.
	If not specified, the search range will be between +-20% of the defocus.
	"""
	os.chdir(rundir)
	raw_path = rundir+'/raw/'
	defocusdir = '%s/defocus_estimation/' % rundir
	if (defocus_save != 0 and isinstance(defocus_save,float)):
		os.system("mkdir %s;rm %sdefocus_*" % (defocusdir, defocusdir))
		os.system("touch %sdefocus_%f" % (defocusdir, defocus_save))
		apDisplay.printMsg("Defocus value %f saved to disk." % defocus_save)
		
		#apDisplay.printMsg("Estimated CTF plot with defocus value %f created." % defocus_save)
	else:
		def runTomoCTF(job):
			os.system(job)
			return
		apDisplay.printMsg('Estimating the defocus of the untilted tilt-series plane with varying tile size and CTFmin values...')
		os.system("rm -rf %s 2>/dev/null; mkdir %s" % (defocusdir, defocusdir))
		tilt_file = seriesname+'_tilts.txt'
		tilt_file_full=defocusdir+seriesname+'_tilts.txt'
		stack_path = os.path.join(defocusdir,'stack_for_defocus_estimation.mrcs')
		log_file_full = os.path.join(defocusdir,'defocus_estimation.log')
		shutil.copy(tiltfilename,defocusdir)
		tiltfilename = os.path.join(defocusdir,tiltfilename)
		log = open(log_file_full,'w')
		defocus_difference = defocus_difference*1000
		if (defocus_min == 0) or (defocus_max == 0):
			defocus_min = defocus*0.8
			defocus_max = defocus*1.2
		
		if (procs == "True") or (procs == "all"):
			procs = mp.cpu_count()
		elif procs == "False":
			procs = 1
		
		#Get image count from tlt file by counting how many lines have ORIGIN in them.
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfilename)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfilename)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		cmd3="awk '/AZIMUTH /{print $3}' %s" % (tiltfilename)
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(azimuth, err) = proc.communicate()
		azimuth=float(azimuth)
		
		if os.path.basename(tiltfilename) == 'original.tlt':
			apDisplay.printMsg("Using tilt-azimuth of %f as recorded in the original .tlt file..." % azimuth)
		elif re.findall(r"[^\W\d_]+|\d+", os.path.basename(tiltfilename.split('.')[0])[0:6])[0] == 'series':
			apDisplay.printMsg("Using tilt-azimuth of %f as recorded in the .tlt file from the database..." % azimuth)
		else:
			apDisplay.printMsg("Using tilt-azimuth of %f as recorded in iteration %d..." % (azimuth,int(tiltfilename.split('.')[0][-3:])+1))
		
		project='ap'+projectid
		sinedon.setConfig('appiondata', db=project)
		sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
		tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
		tiltdata = apTomo.getImageList([tiltseriesdata], ddstackid=None, appion_protomo=True)
		
		frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
		tilts,ordered_imagelist,accumulated_dose_list,ordered_mrc_files,refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned=frame_aligned_images)
		cs = tiltdata[0]['scope']['tem']['cs']*1000
		voltage = int(tiltdata[0]['scope']['high tension']/1000)
		
		if (defocus_ang_positive < 90) or (defocus_ang_negative > -90):
			removed_images, mintilt, maxtilt = apProTomo2Aligner.removeHighTiltsFromTiltFile(tiltfilename, defocus_ang_negative, defocus_ang_positive)
			apDisplay.printMsg("High tilt images %s have been removed for defocus estimation by request" % removed_images)
			log.write("High tilt images %s have been removed for defocus estimation by request\n" % removed_images)
		
		mrc_list=[]
		tilt_list=[]
		dimx=0
		dimy=0
		for i in range(tiltstart,numimages+tiltstart+1):
			dx,dy = rotateAndTranslateImage(i, tiltfilename, rundir, defocusdir, mrc_list, tilt_list)
			dimx=max(dx,dimx)
			dimy=max(dy,dimy)
		stack = np.zeros((len(mrc_list),dimx,dimy))
		for i in range(len(mrc_list)):
			stack[i,:,:] = mrc.read(mrc_list[i])
			os.system('rm %s' % mrc_list[i])
		mrc.write(stack,stack_path)
		
		f=open(tilt_file_full,'w')
		for tilt in tilt_list:
			f.write('%f\n' % tilt)
		f.close()
		
		determineTomoctfDirection(defocusdir, stack_path, tilt_file_full, (defocus_min+defocus_max)/2, cs, voltage, amp_contrast, pixelsize)
		
		tomoctf_jobs=[]
		for tilesize in [256,384,512]:
			os.system("rm -rf %s/%s 2>/dev/null" % (defocusdir, tilesize))
			os.mkdir("%s/%s" % (defocusdir, tilesize))
			for ctf_min in [0,0.33,0.67,1]:
				tomoctf_rundir = "%s/%s/%s" % (defocusdir, tilesize, ctf_min)
				os.mkdir(tomoctf_rundir)
				os.system("ln %s %s;ln %s %s" % (stack_path, tomoctf_rundir, tilt_file_full, tomoctf_rundir))
				tomops_file=os.path.join(tomoctf_rundir,'tomops.csh')
				f=open(tomops_file,'w')
				f.write("#!/bin/csh -f\n")
				f.write("time `which tomops.exe` << eof\n")
				f.write("0\n")
				f.write("stack_for_defocus_estimation.mrcs\n")
				f.write("%s\n" % tilt_file)
				f.write("power.mrc\n")
				f.write("%f\n" % defocus_difference)
				f.write("%d,%f\n" % (10000,pixelsize))
				f.write("%d\n" % tilesize)
				f.write("eof\n")
				f.close()
				tomoctffind_file=os.path.join(tomoctf_rundir,'tomoctffind.csh')
				f=open(tomoctffind_file,'w')
				f.write("#!/bin/csh -f\n")
				f.write("time `which tomoctffind.exe` << eof\n")
				f.write("power.mrc\n")
				f.write("diagnostic.mrc\n")
				f.write("%f,%f,%f,10000,%f\n" % (cs, voltage, amp_contrast, pixelsize))
				if tilesize == 512: #tomoctffind.exe will segfault if res_max is too close to Nyquist with tilesize 512...
					f.write("%f,%f,%f\n" % (ctf_min, max(res_min, 2*pixelsize) , max(res_max, 1.3*2*pixelsize)))
				else:
					f.write("%f,%f,%f\n" % (ctf_min, max(res_min, 2*pixelsize), max(res_max, 2*pixelsize)))
				f.write("%f,%f,0.5\n" % (defocus_min*10000, defocus_max*10000))
				f.write("eof\n")
				f.close()
				os.system("chmod +x %s %s" % (tomops_file, tomoctffind_file))
				tomoctf_jobs.append("cd %s;%s 2>/dev/null;%s 2>/dev/null" % (tomoctf_rundir, tomops_file, tomoctffind_file))
		
		for i in range(len(tomoctf_jobs)):
				p = mp.Process(target=runTomoCTF, args=(tomoctf_jobs[i],))
				p.start()
				
				if (i % procs == 0) and (i != 0):
					[p.join() for p in mp.active_children()]
		[p.join() for p in mp.active_children()]
		
		def_avg=0
		for ctf_min in [0,0.33,0.67,1]:
			try:
				tomoctf_rundir256="%s/256/%s" % (defocusdir, ctf_min)
				tomoctf_rundir384="%s/384/%s" % (defocusdir, ctf_min)
				tomoctf_rundir512="%s/512/%s" % (defocusdir, ctf_min)
				diag256=mrc.read(os.path.join(tomoctf_rundir256,'diagnostic.mrc'))
				diag384=mrc.read(os.path.join(tomoctf_rundir384,'diagnostic.mrc'))
				diag512=mrc.read(os.path.join(tomoctf_rundir512,'diagnostic.mrc'))
				slice256=imagenorm.normStdev(np.rot90(diag256[118:256,116:140]))
				slice384=imagenorm.normStdev(np.rot90(diag384[182:384,180:204]))
				slice512=imagenorm.normStdev(np.rot90(diag512[246:512,244:268]))
				mrc.write(slice256,os.path.join(tomoctf_rundir256,'slice256.mrc'))
				mrc.write(slice384,os.path.join(tomoctf_rundir384,'slice384.mrc'))
				mrc.write(slice512,os.path.join(tomoctf_rundir512,'slice512.mrc'))
				slice256[13:24]=slice256[13:24]-2*(slice256[13:24,:].mean()-slice256[0:12,:].mean())
				slice384[13:24]=slice384[13:24]-2*(slice384[13:24,:].mean()-slice384[0:12,:].mean())
				slice512[13:24]=slice512[13:24]-2*(slice512[13:24,:].mean()-slice512[0:12,:].mean())
				#scipy.misc.toimage(slice256, cmin=0, cmax=100).save(os.path.join(tomoctf_rundir256,'diagnostic.png'),'PNG')
				#scipy.misc.toimage(slice384, cmin=0, cmax=150).save(os.path.join(tomoctf_rundir384,'diagnostic.png'),'PNG')
				#scipy.misc.toimage(slice512, cmin=0, cmax=200).save(os.path.join(tomoctf_rundir512,'diagnostic.png'),'PNG')
				scipy.misc.imsave(os.path.join(tomoctf_rundir256,'diagnostic.png'),slice256)
				scipy.misc.imsave(os.path.join(tomoctf_rundir384,'diagnostic.png'),slice384)
				scipy.misc.imsave(os.path.join(tomoctf_rundir512,'diagnostic.png'),slice512)
				def256=float(open(os.path.join(tomoctf_rundir256,'tomoctf.param')).read().split()[-1])*10
				def384=float(open(os.path.join(tomoctf_rundir384,'tomoctf.param')).read().split()[-1])*10
				def512=float(open(os.path.join(tomoctf_rundir512,'tomoctf.param')).read().split()[-1])*10
				cmd256 = "convert -gravity South -background white -splice 0x15 -annotate 0 '%.2f angstroms' %s %s;mv %s %s" % (def256, os.path.join(tomoctf_rundir256,'diagnostic.png'), os.path.join(tomoctf_rundir256,'diagnostic.png'), os.path.join(tomoctf_rundir256,'diagnostic.png'), os.path.join(tomoctf_rundir256,'diagnostic.gif'))
				cmd384 = "convert -gravity South -background white -splice 0x15 -annotate 0 '%.2f angstroms' %s %s;mv %s %s" % (def384, os.path.join(tomoctf_rundir384,'diagnostic.png'), os.path.join(tomoctf_rundir384,'diagnostic.png'), os.path.join(tomoctf_rundir384,'diagnostic.png'), os.path.join(tomoctf_rundir384,'diagnostic.gif'))
				cmd512 = "convert -gravity South -background white -splice 0x15 -annotate 0 '%.2f angstroms' %s %s;mv %s %s" % (def512, os.path.join(tomoctf_rundir512,'diagnostic.png'), os.path.join(tomoctf_rundir512,'diagnostic.png'), os.path.join(tomoctf_rundir512,'diagnostic.png'), os.path.join(tomoctf_rundir512,'diagnostic.gif'))
				os.system(cmd256)
				os.system(cmd384)
				os.system(cmd512)
				def_avg = def_avg+def256+def384+def512
			except IOError:
				apDisplay.printWarning("Intermediate files during defocus estimation were not created properly...")
		def_avg = round((def_avg/12),2)
		os.system("rm %sdefocus_*; touch %sdefocus_%f" % (defocusdir, defocusdir, def_avg))
		os.system('rm %s %s/[2,3,5]*/*/stack*mrcs %s/[2,3,5]*/*/slice*' % (stack_path, defocusdir, defocusdir))


#=====================
def imodCtfCorrect(seriesname, rundir, projectid, sessionname, tiltseriesnumber, tiltfilename, frame_aligned_images, pixelsize, DefocusTol, iWidth, amp_contrast):
	"""
	Leginondb will be queried to get the 'best' defocus estimate on a per-image basis.
	Confident defoci will be gathered and unconfident defoci will be interpolated.
	Images will be CTF corrected by phase flipping using ctfphaseflip from the IMOD package.
	A plot of the defocus values will is made.
	A CTF plot using the mean defocus is made.
	"""
	try:
		apDisplay.printMsg('CTF correcting all tilt images using per-image defocus values from Leginon database...')
		os.chdir(rundir)
		raw_path=rundir+'/raw/'
		ctfdir='%s/imod_ctf_correction/' % rundir
		os.system("mkdir %s" % ctfdir)
		defocus_file_full=ctfdir+seriesname+'_defocus.txt'
		tilt_file_full=ctfdir+seriesname+'_tilts.txt'
		image_list_full=ctfdir+seriesname+'_images.txt'
		out_full=ctfdir+'out'
		log_file_full=ctfdir+'ctf_correction.log'
		if os.path.isfile(raw_path+'ctf_*'): #Throw exception if already ctf corrected
			sys.exit()
		
		project='ap'+projectid
		sinedon.setConfig('appiondata', db=project)
		sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
		tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
		tiltdata = apTomo.getImageList([tiltseriesdata], ddstackid=None, appion_protomo=True)
		
		frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
		tilts,ordered_imagelist,accumulated_dose_list,ordered_mrc_files,refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned=frame_aligned_images)
		cs = tiltdata[0]['scope']['tem']['cs']*1000
		voltage = int(tiltdata[0]['scope']['high tension']/1000)
		
		#Get tilt azimuth
		cmd="awk '/TILT AZIMUTH/{print $3}' %s" % (tiltfilename)
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(tilt_azimuth, err) = proc.communicate()
		tilt_azimuth=float(tilt_azimuth)
		
		estimated_defocus=[]
		for image in range(len(ordered_imagelist)):
			imgctfdata=ctfdb.getBestCtfValue(ordered_imagelist[image], msg=False)
			try:
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
		
		uncorrected_stack=ctfdir+'stack_uncorrected.mrcs'
		corrected_stack=ctfdir+'stack_imodctfcorrected%.2fmicrons.mrcs' % new_avg/10000
		
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
		presetname=tiltdata[0]['preset']['name']
		for image in ordered_mrc_files:
			mrcname=presetname+image.split(presetname)[-1]
			mrc_list.append(raw_path+'/'+mrcname)
		f = open(image_list_full,'w')
		f.write("%d\n" % len(tilts))
		for filename in mrc_list:
			f.write(filename+'\n')
			f.write("%d\n" % 0)
		f.close()
		
		#Rotate and pad images so that they are treated properly by ctfphaseflip.
		apDisplay.printMsg("Preparing images for IMOD...")
		for i in range(len(mrc_list)):
			p = mp.Process(target=apProTomo2Aligner.rotateImageForIMOD, args=(mrc_list[i], azimuth,))
			p.start()
			
			if (i+1 % procs == 0) and (i+1 != 0):
				[p.join() for p in mp.active_children()]
		[p.join() for p in mp.active_children()]
		
		f = open(log_file_full,'w')
		#Make stack for correction,phase flip, extract images, replace images
		cmd1="newstack -fileinlist %s -output %s > %s" % (image_list_full, uncorrected_stack, log_file_full)
		f.write("%s\n\n" % cmd1)
		print cmd1
		subprocess.check_call([cmd1], shell=True)
		
		determineTomoctfDirection(ctfdir, uncorrected_stack, tilt_file_full, (new_avg*10000), cs, voltage, amp_contrast, pixelsize)
		
		cmd2="ctfphaseflip -input %s -output %s -AngleFile %s -defFn %s -pixelSize %s -volt %s -DefocusTol %s -iWidth %s -SphericalAberration %s -AmplitudeContrast %s 2>&1 | tee %s" % (uncorrected_stack, corrected_stack, tilt_file_full, defocus_file_full, pixelsize/10, voltage, DefocusTol, iWidth, cs, amp_contrast, log_file_full)
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
			image=imrotate(image, tilt_azimuth, order=5)
			image=np.rot90(image, k=1)
			big_dimx=len(image[0])
			big_dimy=len(image)
			cropx1=int((big_dimx-dimx)/2)
			cropx2=int(dimx+(big_dimx-dimx)/2)
			cropy1=int((big_dimy-dimy)/2)
			cropy2=int(dimy+(big_dimy-dimy)/2)
			image=image[cropy1:cropy2,cropx1:cropx2]
			mrc.write(image, filename)
		
		for i in range(len(new_images)):
			cmd4="rm %s; mv %s %s" % (mrc_list[i], new_images[i], mrc_list[i])
			f.write("%s\n" % cmd4)
			os.system(cmd4)
		
		#Make plots
		apProTomo2Aligner.makeDefocusPlot(rundir, seriesname, defocus_file_full)
		apProTomo2Aligner.makeCTFPlot(rundir, seriesname, defocus_file_full, voltage, cs)
		
		intermediate_stack_dir = rundir + '/stack/intermediate/'
		os.system('rm -rf %s;mkdir -p %s ' % (intermediate_stack_dir,intermediate_stack_dir))
		cleanup="rm %s;mv %s %s" % (uncorrected_stack, corrected_stack, intermediate_stack_dir)
		os.system(cleanup)
		output1="%.2f%% of the images for tilt-series #%s had poor defocus estimates or fell outside of one standard deviation from the original mean." % (100*(len(estimated_defocus)-len(defocus_stats_list))/len(estimated_defocus), tiltseriesnumber)
		output2="The defocus mean and standard deviation for tilt-series #%s after interpolating poor values is %.2f and %.2f microns, respectively." % (tiltseriesnumber, new_avg/1000, new_stdev/1000)
		f.write("\n");f.write(output1);f.write("\n");f.write(output2);f.write("\n");f.close()
		apDisplay.printMsg(output1)
		apDisplay.printMsg(output2)
		os.system('touch %s/ctf_corrected_with_ctfphaseflip_avg_def_%f' % (raw_path, new_avg))
		apDisplay.printMsg("CTF correction finished for tilt-series #%s!" % tiltseriesnumber)
		
	except subprocess.CalledProcessError:
		apDisplay.printError("An IMOD command failed, so CTF correction could not be completed. Make sure IMOD is in your $PATH.")
	
	except SystemExit:
		apDisplay.printWarning("It looks like you've already CTF corrected tilt-series #%s. Skipping CTF correction!" % tiltseriesnumber)

	except:
		apDisplay.printError("CTF correction could not be completed. Make sure IMOD, numpy, and scipy are in your $PATH. Make sure defocus has been estimated through Appion.\n")


#=====================
def tomoCtfCorrect(seriesname, rundir, projectid, sessionname, tiltseriesnumber, tiltfilename, procs, pixelsize, amp_contrast_ctf, amp_correct, amp_correct_w1, amp_correct_w2, defocus_difference):
	"""
	The user-recorded defocus value will be read from the defocus_estimation directory and used to
	correct for CTF using TomoCTF
	"""
	#try:
	apDisplay.printMsg('CTF correcting all tilt images using per-image defocus values from Leginon database...')
	os.chdir(rundir)
	raw_path=rundir+'/raw/'
	ctfdir='%s/tomoctf_ctf_correction/' % rundir
	os.system("mkdir %s" % ctfdir)
	tilt_file = seriesname+'_tilts.txt'
	tilt_file_full=ctfdir+seriesname+'_tilts.txt'
	image_list_full=ctfdir+seriesname+'_images.txt'
	out_full=ctfdir+'out'
	log_file_full=ctfdir+'ctf_correction.log'
	defocus=os.path.basename(glob.glob(rundir+'/defocus_estimation/defocus_*')[0]).split('_')[1]
	defocus_microns=float(defocus)/10000
	uncorrected_stack = os.path.join(ctfdir,'stack_uncorrected.mrcs')
	if amp_correct == 'off':
		corrected_stack = os.path.join(ctfdir,'stack_tomoctfcorrected%.2fmicrons.mrcs' % defocus_microns)
	else:
		corrected_stack = os.path.join(ctfdir,'stack_tomoctfcorrected%.2fmicrons_ampcorrectedw1%.2fw2%.2f.mrcs' % (defocus_microns, amp_correct_w1, amp_correct_w2))
	log_file_full = os.path.join(ctfdir,'defocus_estimation.log')
	shutil.copy(tiltfilename,ctfdir)
	tiltfilename = os.path.join(ctfdir,tiltfilename)
	log = open(log_file_full,'w')
	if os.path.isfile(raw_path+'ctf_*'): #Throw exception if already ctf corrected
		sys.exit()
	
	if (procs == "True") or (procs == "all"):
		procs = mp.cpu_count()
	elif procs == "False":
		procs = 1
	
	cmd="awk '/AZIMUTH /{print $3}' %s" % (tiltfilename)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(azimuth, err) = proc.communicate()
	azimuth=float(azimuth)
	
	if tiltfilename != 'original.tlt':
		apDisplay.printMsg("Using tilt-azimuth of %f as recorded in iteration %d..." % (azimuth,int(tiltfilename.split('.')[0][-3:])+1))
	else:
		apDisplay.printMsg("Using tilt-azimuth of %f as recorded in the original .tlt file from the database..." % azimuth)
	
	project='ap'+projectid
	sinedon.setConfig('appiondata', db=project)
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
	tiltdata = apTomo.getImageList([tiltseriesdata], ddstackid=None, appion_protomo=True)
	
	frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
	tilts,ordered_imagelist,accumulated_dose_list,ordered_mrc_files,refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned="True")
	cs = tiltdata[0]['scope']['tem']['cs']*1000
	voltage = int(tiltdata[0]['scope']['high tension']/1000)
	
	f = open(tilt_file_full,'w')
	for tilt in tilts:
		f.write("%.2f\n" % tilt)
	f.close()
	
	mrc_list=[]
	presetname=tiltdata[0]['preset']['name']
	for image in ordered_mrc_files:
		mrcname=presetname+image.split(presetname)[-1]
		mrc_list.append(raw_path+'/'+mrcname)
	f = open(image_list_full,'w')
	f.write("%d\n" % len(tilts))
	for filename in mrc_list:
		f.write(filename+'\n')
		f.write("%d\n" % 0)
	f.close()
	
	#Rotate and pad images so that they are treated properly by TomoCTF.
	apDisplay.printMsg("Preparing images for TomoCTF...")
	for i in range(len(mrc_list)):
		p = mp.Process(target=apProTomo2Aligner.rotateImageForIMOD, args=(mrc_list[i], azimuth,))
		p.start()
		
		if (i+1 % procs == 0) and (i+1 != 0):
			[p.join() for p in mp.active_children()]
	[p.join() for p in mp.active_children()]
	
	dim_image = mrc.read(mrc_list[0])
	dimx=len(dim_image[0])
	dimy=len(dim_image)
	
	f = open(log_file_full,'w')
	#Make stack for correction,phase flip, extract images, replace images
	cmd1="newstack -fileinlist %s -output %s > %s" % (image_list_full, uncorrected_stack, log_file_full)
	f.write("%s\n\n" % cmd1)
	print cmd1
	subprocess.check_call([cmd1], shell=True)
	
	determineTomoctfDirection(ctfdir, uncorrected_stack, tilt_file_full, defocus, cs, voltage, amp_contrast_ctf, pixelsize)
	
	CTFcorrect_file=os.path.join(ctfdir,'CTFcorrect.csh')
	f=open(CTFcorrect_file,'w')
	f.write("#!/bin/csh -f\n")
	f.write("`which CTFcorrect.exe` $1 $2 $3 << eof!\n")
	f.write("%s\n" % defocus)
	f.write("%f\n" % defocus_difference)
	f.write("%f,%f,%f,10000,%f\n" % (cs, voltage, amp_contrast_ctf, pixelsize))
	if amp_correct == 'on':
		f.write("y\n")
	else:
		f.write("n\n")
	f.write("%f, %f\n" % (amp_correct_w1,amp_correct_w2 ))
	f.write("eof!\n")
	f.close()
	
	CTFcorrect_stack_file=os.path.join(ctfdir,'CTFcorrectstack.csh')
	f=open(CTFcorrect_stack_file,'w')
	f.write("#!/bin/csh -f\n")
	f.write("set stack=$1\n")
	f.write("set CTFstack=$2\n")
	f.write("set tiltfile=$3\n")
	f.write("set Nprocs=%d\n" % procs)
	f.write("set Nimgs=%d\n" % len(mrc_list))
	f.write("echo Stacked tilt series $stack containing $Nimgs images\n")
	f.write("set j=0\n")
	f.write("set i=1\n")
	f.write("while ($i <= $Nimgs)\n")
	f.write("    set i3=`printf \"%03d\" $i`\n")
	f.write("    set tiltangle=`head -n $i $tiltfile | tail -n 1`\n")
	f.write("    echo Correcting image $i for the CTF, tilt angle = $tiltangle\n")
	f.write("    newstack -verbose 0 -secs $j $stack %s/__image$i3.mrc > __ctfimage$i3.log\n" % ctfdir)
	f.write("    set running=`ps -c | grep CTFcorrect.exe | wc -l | awk '{printf(\"%d\",$1+1)}'`\n")
	f.write("    if($running < $Nprocs) then\n")
	f.write("        %s %s/__image$i3.mrc %s/__ctfimage$i3.mrc $tiltangle >> %s/__ctfimage$i3.log  ; rm -f %s/__image$i3.mrc &\n" % (CTFcorrect_file,ctfdir,ctfdir,ctfdir,ctfdir))
	f.write("    else\n")
	f.write("        %s %s/__image$i3.mrc %s/__ctfimage$i3.mrc $tiltangle >> %s/__ctfimage$i3.log  ; rm -f %s/__image$i3.mrc\n" % (CTFcorrect_file,ctfdir,ctfdir,ctfdir,ctfdir))
	f.write("    endif\n")
	f.write("@ j ++\n")
	f.write("@ i ++\n")
	f.write("end\n")
	f.write("wait\n")
	f.write("newstack %s/__ctfimage???.mrc $CTFstack\n" % ctfdir)
	f.write("cat %s/__ctfimage???.log > %s/$CTFstack.log\n" % (ctfdir, ctfdir))
	f.write("rm -f %s/__ctfimage???.mrc*  %s/__image???.mrc* %s/__ctfimage???.log\n" % (ctfdir, ctfdir, ctfdir))
	f.close()
	
	os.system('chmod +x %s %s' % (CTFcorrect_file, CTFcorrect_stack_file))
	os.system('%s %s %s %s %d' % (CTFcorrect_stack_file, uncorrected_stack, corrected_stack, tilt_file_full, procs))
	
	cmd3="newstack -split 1 -append mrc %s %s >> %s" % (corrected_stack, out_full, log_file_full)
	print cmd3
	subprocess.check_call([cmd3], shell=True)
	
	apDisplay.printMsg("Overwriting uncorrected raw images with CTF corrected images")
	new_images=glob.glob(ctfdir+'out*mrc')
	new_images.sort()
	
	#Unrotate and unpad images
	for filename in new_images:
		image=mrc.read(filename)
		image=imrotate(image, azimuth, order=5)
		image=np.rot90(image, k=1)
		big_dimx=len(image[0])
		big_dimy=len(image)
		print big_dimx,big_dimy,dimx,dimy
		cropx1=int((big_dimx-dimx)/2)
		cropx2=int(dimx+(big_dimx-dimx)/2)
		cropy1=int((big_dimy-dimy)/2)
		cropy2=int(dimy+(big_dimy-dimy)/2)
		print cropy2-cropy1, cropx2-cropx1
		image=image[cropy1:cropy2,cropx1:cropx2]
		mrc.write(image, filename)
	
	for i in range(len(new_images)):
		cmd4="rm %s; mv %s %s" % (mrc_list[i], new_images[i], mrc_list[i])
		os.system(cmd4)
	
	apProTomo2Aligner.makeCTFPlot(rundir, seriesname, "defocus_file_full", voltage, cs, defocus_value=defocus)
	
	intermediate_stack_dir = rundir + '/stack/intermediate/'
	os.system('rm -rf %s;mkdir -p %s ' % (intermediate_stack_dir, intermediate_stack_dir))
	cleanup="rm %s %s/~*;mv %s %s" % (uncorrected_stack, ctfdir, corrected_stack, intermediate_stack_dir)
	os.system('touch %s/ctf_corrected_with_ctfphaseflip_avg_def_%s' % (raw_path, defocus))
	try:
		pass
	except SystemExit:
		apDisplay.printWarning("It looks like you've already CTF corrected tilt-series #%s. Skipping CTF correction!" % tiltseriesnumber)

	except:
		apDisplay.printError("CTF correction could not be completed. Make sure TomoCTF, numpy, and scipy are in your $PATH. Make sure defocus has been recorded in Appion-Protomo.\n")


#=====================
def doseCompensate(seriesname, rundir, sessionname, tiltseriesnumber, frame_aligned_images, raw_path, pixelsize, dose_presets, dose_a, dose_b, dose_c, dose_compensate="True"):
	"""
	Images will be lowpass filtered using equation (3) from Grant & Grigorieff, 2015.
	No changes to the database are made. A backup is made.
	"""
	intermediate_stack_dir = rundir + '/stack/intermediate/'
	if len(glob.glob(intermediate_stack_dir+'*.mrcs')) > 0:
		sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
		tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
		tiltdata = apTomo.getImageList([tiltseriesdata], ddstackid=None, appion_protomo=True)
		
		frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
		tilts, ordered_imagelist, accumulated_dose_list, ordered_mrc_files, refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned="False")
		if (dose_presets == "Light"):
			dose_a = 0.245
			dose_b = -1.8
			dose_c = 12.0
		elif (dose_presets == "Moderate"):
			dose_a = 0.245
			dose_b = -1.665
			dose_c = 2.81
		elif (dose_presets == "Heavy"):
			dose_a = 0.245
			dose_b = -1.4
			dose_c = 2.0
		stack_file = glob.glob(intermediate_stack_dir+'*.mrcs')[0]
		stack = mrc.read(stack_file)
		dose_a_str = ('%f' % dose_a).rstrip('0')
		dose_b_str = ('%f' % dose_b).rstrip('0')
		dose_c_str = ('%f' % dose_c).rstrip('0')
		stack_file_dose_comped = stackpath.replace('.mrcs','_dose_comp_a=%f_b=%f_c=%f.mrcs' % (dose_a_str, dose_b_str, dose_c_str))
		apDisplay.printMsg('Dose compensating all tilt images with a=%s, b=%s, and c=%s...' % (dose_a_str, dose_b_str, dose_c_str))
		stack_path=os.path.join(rundir,'stack')
		os.system('mkdir %s 2>/dev/null' % stack_path)
		
		new_stack = []
		for image, j in zip(ordered_imagelist, range(len(ordered_imagelist))):
			lowpass = float(np.real(complex(dose_a/(accumulated_dose_list[j] - dose_c))**(1/dose_b)))  #equation (3) from Grant & Grigorieff, 2015
			if lowpass < 0.0:
				lowpass = 0.0
			im = mrc.read(image)
			im = imagefilter.lowPassFilter(stack[j], apix=pixelsize, radius=lowpass, msg=False)
			im = imagenorm.normStdev(im)
			new_stack.append(im)
		mrc.write(np.asarray(new_stack), stack_file_dose_comped)
		os.system('rm %s' % stack_file)
		os.system("touch %s/dose_comp_a%s_b%s_c%s" % (raw_path,dose_a_str, dose_b_str, dose_c_str))
		apDisplay.printMsg("Dose compensation finished for tilt-series #%s!" % tiltseriesnumber)
		
	else:
		dose_file = glob.glob(os.path.join(raw_path,'dose*'))
		if len(dose_file) == 0:
			sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
			tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
			tiltdata = apTomo.getImageList([tiltseriesdata], ddstackid=None, appion_protomo=True)
			
			frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
			tilts, ordered_imagelist, accumulated_dose_list, ordered_mrc_files, refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned="False")
			if frame_aligned_images == "True":  #For different image filenames
				a, ordered_imagelist, c, d, e = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned=frame_aligned_images)
			newfilenames, new_ordered_imagelist = apProTomo.getImageFiles(ordered_imagelist, raw_path, link=False, copy=False)
			if (dose_presets == "Light"):
				dose_a = 0.245
				dose_b = -1.8
				dose_c = 12
			elif (dose_presets == "Moderate"):
				dose_a = 0.245
				dose_b = -1.665
				dose_c = 2.81
			elif (dose_presets == "Heavy"):
				dose_a = 0.245
				dose_b = -1.4
				dose_c = 2
			if dose_compensate == "True":
				dose_a_str = ('%f' % dose_a).rstrip('0')
				dose_b_str = ('%f' % dose_b).rstrip('0')
				dose_c_str = ('%f' % dose_c).rstrip('0')
				apDisplay.printMsg('Dose compensating all tilt images with a=%s, b=%s, and c=%s...' % (dose_a_str, dose_b_str, dose_c_str))
			else:
				apDisplay.printMsg('Creating dose compensation list with a=%s, b=%s, and c=%s...' % (dose_a_str, dose_b_str, dose_c_str))
				stack_path=os.path.join(rundir,'stack')
				os.system('mkdir %s 2>/dev/null' % stack_path)
				dose_lp_file = open(os.path.join(stack_path,'full_dose_lp_list.txt'), 'w')
			
			for image, j in zip(new_ordered_imagelist, range(len(new_ordered_imagelist))):
				if accumulated_dose_list[j] == dose_c: #No divide by zero
					lowpass = float(np.real(complex(dose_a/(accumulated_dose_list[j] - dose_c + 0.01))**(1/dose_b)))  #equation (3) from Grant & Grigorieff, 2015 with an extra term to avoid divide by zero
				else:
					lowpass = float(np.real(complex(dose_a/(accumulated_dose_list[j] - dose_c))**(1/dose_b)))  #equation (3) from Grant & Grigorieff, 2015
				if lowpass < 0.0:
					lowpass = 0.0
				if dose_compensate == "True":
					im = mrc.read(image)
					im = imagefilter.lowPassFilter(im, apix=pixelsize, radius=lowpass, msg=False)
					im = imagenorm.normStdev(im)
					mrc.write(im, image)
				else:
					dose_lp_file.write("%f %f %f\n" % (tilts[j], accumulated_dose_list[j], lowpass))
			if dose_compensate == "True":
				apProTomo2Aligner.makeDosePlots(rundir, seriesname, tilts, accumulated_dose_list, dose_a, dose_b, dose_c)
			else:
				dose_lp_file.close()
			
			if dose_compensate == "True":
				os.system("touch %s/dose_comp_a%s_b%s_c%s" % (raw_path,dose_a_str,dose_b_str,dose_c_str))
				apDisplay.printMsg("Dose compensation finished for tilt-series #%s!" % tiltseriesnumber)
			else:
				apDisplay.printMsg("Dose compensation list created")
		else:
			apDisplay.printMsg("Images have already been dose compensated. Skipping dose compensation.")
		
		return


#=====================
def modifyParamFile(filein, fileout, paramdict):
	f = open(filein, 'r')
	filestring = f.read()
	f.close()
	
	for key, value in paramdict.iteritems():
		filestring = re.sub(key, str(value), filestring)
	
	f = open(fileout, 'w')
	f.write(filestring)
	f.close()
	
#=====================
def createParamDict(params):
	paramdict = { 'AP_windowsize_x':params['r1_region_x'],
		'AP_windowsize_y':params['r1_region_y'],
		'APc_windowsize_x':params['region_x'],
		'APc_windowsize_y':params['region_y'],
		'AP_sampling': params['r1_sampling'],
		'APc_sampling': params['sampling'],
		'AP_map_sampling': params['map_sampling'],
		'AP_thickness': params['thickness'],
		'AP_cos_alpha': params['cos_alpha'],
		'AP_lp_diam_x': params['r1_lowpass_diameter_x'],
		'AP_lp_diam_y': params['r1_lowpass_diameter_y'],
		'AP_lp_apod_x': params['r1_lowpass_apod_x'],
		'AP_lp_apod_y': params['r1_lowpass_apod_y'],
		'AP_hp_diam_x': params['r1_highpass_diameter_x'],
		'AP_hp_diam_y': params['r1_highpass_diameter_y'],
		'AP_hp_apod_x': params['r1_highpass_apod_x'],
		'AP_hp_apod_y': params['r1_highpass_apod_y'],
		'APc_lp_diam_x': params['lowpass_diameter_x'],
		'APc_lp_diam_y': params['lowpass_diameter_y'],
		'APc_lp_apod_x': params['lowpass_apod_x'],
		'APc_lp_apod_y': params['lowpass_apod_y'],
		'APc_hp_diam_x': params['highpass_diameter_x'],
		'APc_hp_diam_y': params['highpass_diameter_y'],
		'APc_hp_apod_x': params['highpass_apod_x'],
		'APc_hp_apod_y': params['highpass_apod_y'],
		'AP_corr_mode': params['corr_mode'],
		'AP_raw_path': params['raw_path'],
		'AP_binning': params['binning'],
		'AP_preprocessing': params['preprocessing'],
		#'AP_select_images': params['select_images'],  #Hardcoded to 0-999999 due to redundancy
		#'AP_exclude_images': params['exclude_images'],  #Hardcoded to 999999. Images are now removed from the .tlt file...I don't trust Protomo
		'AP_border': params['border'],
		'AP_clip_low': params['clip_low'],
		'AP_clip_high': params['clip_high'],
		'AP_thr_low': params['thr_low'],
		'AP_thr_high': params['thr_high'],
		'AP_gradient': params['gradient'],
		'AP_iter_gradient': params['iter_gradient'],
		'AP_filter': params['filter'],
		'AP_kernel_x': params['r1_kernel_x'],
		'AP_kernel_y': params['r1_kernel_y'],
		'APc_kernel_x': params['kernel_x'],
		'APc_kernel_y': params['kernel_y'],
		'AP_grow': params['grow'],
		'AP_window_area': params['window_area'],
		'AP_mask_apod_x': params['r1_mask_apod_x'],
		'AP_mask_apod_y': params['r1_mask_apod_y'],
		'AP_mask_width_x': params['r1_mask_width_x'],
		'AP_mask_width_y': params['r1_mask_width_y'],
		'APc_mask_apod_x': params['mask_apod_x'],
		'APc_mask_apod_y': params['mask_apod_y'],
		'APc_mask_width_x': params['mask_width_x'],
		'APc_mask_width_y': params['mask_width_y'],
		'AP_do_estimation': params['do_estimation'],
		'AP_translimit': params['translimit'],
		'AP_max_correction': params['max_correction'],
		'AP_max_shift': params['max_shift'],
		'AP_correlation_size_x': params['correlation_size_x'],
		'AP_correlation_size_y': params['correlation_size_y'],
		'AP_peak_search_radius_x': params['r1_peak_search_radius_x'],
		'AP_peak_search_radius_y': params['r1_peak_search_radius_y'],
		'APc_peak_search_radius_x': params['peak_search_radius_x'],
		'APc_peak_search_radius_y': params['peak_search_radius_y'],
		'AP_orientation': params['orientation'],
		'AP_azimuth': params['azimuth'],
		'AP_elevation': params['elevation'],
		'AP_rotation': params['rotation'],
		'AP_scale': params['scale'],
		'AP_norotations': params['norotations'],
		'AP_logging': params['logging'],
		'AP_loglevel': params['loglevel'],
		'AP_slab': params['slab'],
		'AP_map_size_x': params['map_size_x'],
		'AP_map_size_y': params['map_size_y'],
		'AP_map_size_z': params['map_size_z'],
		'AP_filename_prefix': params['filename_prefix'],
		'AP_image_extension': params['image_file_type'],
		'AP_cachedir': params['cachedir'],
		'AP_protomo_outdir': params['protomo_outdir'],
		'AP_grid_limit': params['gridsearch_limit'],
		'AP_grid_step': params['gridsearch_step'] }
	return paramdict				
	
#=====================
def getTiltGeom(ordered_imagelist, bin, refimg):
	# get the tilt geometry parameters
	#self.params['aligndir'],self.params['imagedir'] = apProTomo.setProtomoDir(self.params['rundir'])

	# self.params['imagedir'] when not testing with renamed images
	rawimagenames = apProTomo.linkImageFiles(ordered_imagelist, "/ami/data17/leginon/10nov10z/rawdatatest")
	shifts = apTomo.getGlobalShift(ordered_imagelist, corr_bin, refimg)

	tltparams = apProTomo.convertShiftsToParams(self.tilts, shifts, self.center, rawimagenames)
	return tltparams


	
#=====================
def buildTiltGeomFile(self, imagedict, parameterdict=False):

	tiltText = "TILT SERIES %s\n" % self.seriesname
	tiltText += "\n" 
	tiltText += "   AXIS\n"
	tiltText += "\n"
	tiltText += "     TILT AZIMUTH    %g\n" % parameterdict['azimuth']
	tiltText += "\n"

	# Loop through the images to format the tilt geometry for each one
	# TODO: check this...not sure if it is getting the right filenames
	keys = imagedict.keys()
	keys.sort()
	for n in keys:
		tiltText += "   IMAGE %-5d     FILE %s       ORIGIN [ %8.3f %8.3f ]    TILT ANGLE    %8.3f    ROTATION     %8.3f\n" % (n, imagedict[n]['filename'], imagedict[n]['x'], imagedict[n]['y'], imagedict[n]['tilt'], imagedict[n]['rotation'])

	tiltText += "\n"
	tiltText += "   REFERENCE IMAGE %d\n" % self.refimg
	tiltText += "\n"
	tiltText += "\n"
	tiltText += " END\n"

	return tiltText



#=====================
def writeDefaultParamFile(self):

	# Set the default protomo2 parameter file location if it is not provided by the user
	if self.params['protomo2paramfile'] is None:
		self.params['protomo2paramfile'] = os.path.join(self.processingDir,'protomo2.param')

	# Try to open the param file. If it fails (first time through), write out a default parameter file.
	try:
		protomo2params = open(self.params['protomo2paramfile'],'r')
	except:
		try:
			protomo2params = open(self.params['protomo2paramfile'],'w')
		except:
			apDisplay.printWarning("Failed to create %s for writing the default protomo2 parameter file" % (self.params['protomo2paramfile'], ))
			raise
		paramtext = self.buildParamFile()
		# using print instead of .write so that message is converted to a string if needed 
		print >> protomo2params, paramtext

	# Close the parameter file
	protomo2params.close()

	return self.params['protomo2paramfile']

#=====================
def getPrototypeParamFile(outparamfile):
	
	#TODO: expand on this later
	appiondir=apParam.getAppionDirectory()
	origparamfile=os.path.join(appiondir,'appionlib','data','protomo.param')
	newparamfile=os.path.join(os.getcwd(),outparamfile)
	shutil.copyfile(origparamfile,newparamfile)

def getPrototypeParamPath():
	appiondir=apParam.getAppionDirectory()
	origparamfile=os.path.join(appiondir,'appionlib','data','protomo.param')
	coarse_origparamfile=os.path.join(appiondir,'appionlib','data','protomo_coarse_align.param')
	return coarse_origparamfile, origparamfile
		
		
def serialEM2Appion(stack, mdoc, voltage):
	prefix = os.path.splitext(os.path.basename(stack))[0]
	prefix = prefix.replace('.','_')
	stack_path = os.path.dirname(os.path.abspath(stack))
	temp_image_dir = "%s/%s_tmp" % (stack_path, prefix)
	os.system('mkdir %s 2>/dev/null' % temp_image_dir)
	stack = mrc.read(stack)
	for tilt_image in range(1,len(stack)+1):
		filename = "%s/%s_%04d.mrc" % (temp_image_dir, prefix, tilt_image)
		mrc.write(stack[tilt_image-1], filename)
	
	cmd1="awk '/PixelSpacing /{print}' %s | head -1 | awk '{print $3}'" % mdoc
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(pixelsize, err) = proc.communicate()
	pixelsize = float(pixelsize)
	cmd2="awk '/Binning /{print}' %s | head -1 | awk '{print $3}'" % mdoc
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(binning, err) = proc.communicate()
	binning = int(binning)
	cmd3="awk '/Magnification /{print}' %s | head -1 | awk '{print $3}'" % mdoc
	proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
	(mag, err) = proc.communicate()
	mag = int(mag)
	
	info_file = os.path.join(temp_image_dir,'%s_info.txt' % prefix)
	info=open(info_file,'w')
	for image_number in range(1,len(stack)+1):
		cmd4="awk '/TiltAngle /{print}' %s | awk '{print $3}' | head -%s | tail -1" % (mdoc, image_number)
		proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
		(tiltangle, err) = proc.communicate()
		tiltangle = float(tiltangle)
		cmd5="awk '/Defocus /{print}' %s | grep -v TargetDefocus | awk '{print $3}' | head -%s | tail -1" % (mdoc, image_number)
		proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
		(defocus, err) = proc.communicate()
		defocus = float(defocus)
		cmd6="awk '/ExposureDose /{print}' %s | awk '{print $3}' | head -%s | tail -1" % (mdoc, image_number)
		proc=subprocess.Popen(cmd6, stdout=subprocess.PIPE, shell=True)
		(dose, err) = proc.communicate()
		dose = float(dose)
		filename = "%s/%s_%04d.mrc" % (temp_image_dir, prefix, image_number)
		
		info.write('%s\t%fe-10\t%d\t%d\t%d\t%fe-6\t%d\t%f\t%f\n' % (filename, pixelsize, binning, binning, mag, defocus, int(voltage)*1000, tiltangle, dose))
	info.close()
	apDisplay.printMsg("Number of tilt-images: %d" % image_number)
	apDisplay.printMsg("Tilt info path: %s" % info_file)
	apDisplay.printMsg("Input these parameters into the Appion upload tilt-series interface.")
	print ""