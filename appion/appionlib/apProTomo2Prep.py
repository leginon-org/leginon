#!/usr/bin/env python

from __future__ import division
import math
import os
import re
import sys
import glob
import shutil
import subprocess
import scipy.interpolate
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
def prepareTiltFile(sessionname, seriesname, tiltfilename, tiltseriesnumber, raw_path, frame_aligned_images, link=False, coarse=True):
	'''
	Creates tlt file from basic image information and copies raw images
	'''
	
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
	tiltdata = apTomo.getImageList([tiltseriesdata])
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
		
		apDisplay.printMsg("Copying raw images, y-flipping, normalizing, and converting images to float32 for Protomo...") #Linking removed because raw images need to be y-flipped for Protomo:(.
		newfilenames, new_ordered_imagelist = apProTomo.getImageFiles(ordered_imagelist, raw_path, link=False, copy="True")
		
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


#=====================
def ctfCorrect(seriesname, rundir, projectid, sessionname, tiltseriesnumber, tiltfilename, frame_aligned_images, pixelsize, DefocusTol, iWidth, amp_contrast):
	"""
	Leginondb will be queried to get the 'best' defocus estimate on a per-image basis.
	Confident defoci will be gathered and unconfident defoci will be interpolated.
	Images will be CTF corrected by phase flipping using ctfphaseflip from the IMOD package.
	A plot of the defocus values will is made.
	A CTF plot using the mean defocus is made.
	"""
	try:
		apDisplay.printMsg('CTF correcting all tilt images using defocus values from Leginon database...')
		os.chdir(rundir)
		raw_path=rundir+'/raw/'
		ctfdir='%s/ctf_correction/' % rundir
		os.system("mkdir %s" % ctfdir)
		defocus_file_full=ctfdir+seriesname+'_defocus.txt'
		tilt_file_full=ctfdir+seriesname+'_tilts.txt'
		image_list_full=ctfdir+seriesname+'_images.txt'
		uncorrected_stack=ctfdir+'stack_uncorrected.mrc'
		corrected_stack=ctfdir+'stack_corrected.mrc'
		out_full=ctfdir+'out'
		log_file_full=ctfdir+'ctf_correction.log'
		
		project='ap'+projectid
		sinedon.setConfig('appiondata', db=project)
		sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
		tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
		tiltdata = apTomo.getImageList([tiltseriesdata])
		
		frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
		tilts,ordered_imagelist,accumulated_dose_list,ordered_mrc_files,refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned=frame_aligned_images)
		cs = tiltdata[0]['scope']['tem']['cs']*1000
		voltage = int(tiltdata[0]['scope']['high tension']/1000)
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
		for filename in mrc_list:
			image=mrc.read(filename)
			dimx=len(image[0])
			dimy=len(image)
			#First rotate 90 degrees in counter-clockwise direction. This makes it so positive angle images are higher defocused on the right side of the image
			image=np.rot90(image, k=-1)
			#Rotate image and write
			image=imrotate(image, -tilt_azimuth, order=1) #Linear interpolation is fastest and there is barely a difference between linear and cubic
			mrc.write(image, filename)
		
		f = open(log_file_full,'w')
		#Make stack for correction,phase flip, extract images, replace images
		cmd1="newstack -fileinlist %s -output %s > %s" % (image_list_full, uncorrected_stack, log_file_full)
		f.write("%s\n\n" % cmd1)
		print cmd1
		subprocess.check_call([cmd1], shell=True)
		
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
			image=imrotate(image, tilt_azimuth, order=1)
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
			cmd4="rm %s; ln %s %s" % (mrc_list[i], new_images[i], mrc_list[i])
			f.write("%s\n" % cmd4)
			os.system(cmd4)
		
		#Make plots
		apProTomo2Aligner.makeDefocusPlot(rundir, seriesname, defocus_file_full)
		apProTomo2Aligner.makeCTFPlot(rundir, seriesname, defocus_file_full, voltage, cs)
		
		cleanup="rm %s %s" % (uncorrected_stack, corrected_stack)
		os.system(cleanup)
		output1="%.2f%% of the images for tilt-series #%s had poor defocus estimates or fell outside of one standard deviation from the original mean." % (100*(len(estimated_defocus)-len(defocus_stats_list))/len(estimated_defocus), tiltseriesnumber)
		output2="The defocus mean and standard deviation for tilt-series #%s after interpolating poor values is %.2f and %.2f microns, respectively." % (tiltseriesnumber, new_avg/1000, new_stdev/1000)
		f.write("\n");f.write(output1);f.write("\n");f.write(output2);f.write("\n");f.close()
		apDisplay.printMsg(output1)
		apDisplay.printMsg(output2)
		apDisplay.printMsg("CTF correction finished for tilt-series #%s!" % tiltseriesnumber)
		
	except subprocess.CalledProcessError:
		apDisplay.printError("An IMOD command failed, so CTF correction could not be completed. Make sure IMOD is in your $PATH.")
	
	except SystemExit:
		apDisplay.printWarning("It looks like you've already CTF corrected tilt-series #%s. Skipping CTF correction!" % tiltseriesnumber)

	except:
		apDisplay.printError("CTF correction could not be completed. Make sure IMOD, numpy, and scipy are in your $PATH. Make sure defocus has been estimated through Appion.\n")


#=====================
def doseCompensate(seriesname, rundir, sessionname, tiltseriesnumber, frame_aligned_images, raw_path, pixelsize, dose_presets, dose_a, dose_b, dose_c):
	"""
	Images will be lowpass filtered using equation (3) from Grant & Grigorieff, 2015.
	No changes to the database are made. No backups are made.
	"""
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)
	tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(tiltseriesnumber,sessiondata)
	tiltdata = apTomo.getImageList([tiltseriesdata])
	
	frame_tiltdata, non_frame_tiltdata = frameOrNonFrameTiltdata(tiltdata)
	tilts, ordered_imagelist, accumulated_dose_list, ordered_mrc_files, refimg = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned="False")
	if frame_aligned_images == "True":  #For different image filenames
		a, ordered_imagelist, c, d, e = apTomo.orderImageList(frame_tiltdata, non_frame_tiltdata, frame_aligned=frame_aligned_images)
	newfilenames, new_ordered_imagelist = apProTomo.getImageFiles(ordered_imagelist, raw_path, link=False, copy=False)
	if (dose_presets == "Light"):
		dose_a = 0.245
		dose_b = -1.6
		dose_c = 12
	elif (dose_presets == "Moderate"):
		dose_a = 0.245
		dose_b = -1.665
		dose_c = 2.81
	elif (dose_presets == "Heavy"):
		dose_a = 0.245
		dose_b = -1.4
		dose_c = 2
	
	apDisplay.printMsg('Dose compensating all tilt images with a=%s, b=%s, and c=%s...' % (dose_a, dose_b, dose_c))
	
	for image, j in zip(new_ordered_imagelist, range(len(new_ordered_imagelist))):
		lowpass = float(np.real(complex(dose_a/(accumulated_dose_list[j] - dose_c))**(1/dose_b)))  #equation (3) from Grant & Grigorieff, 2015
		if lowpass < 0.0:
			lowpass = 0.0
		im = mrc.read(image)
		im = imagefilter.lowPassFilter(im, apix=pixelsize, radius=lowpass, msg=False)
		im=imagenorm.normStdev(im)
		mrc.write(im, image)
	
	#Make plots
	apProTomo2Aligner.makeDosePlots(rundir, seriesname, tilts, accumulated_dose_list, dose_a, dose_b, dose_c)
	
	apDisplay.printMsg("Dose compensation finished for tilt-series #%s!" % tiltseriesnumber)
	
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
		
		
