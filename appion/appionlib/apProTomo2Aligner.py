#!/usr/bin/env python

from __future__ import division
import os
import sys
import scipy
import pylab
import subprocess
import numpy as np
from appionlib import apDisplay
from appionlib.apImage import imagenorm
from pyami import mrc
from pyami import imagefun as imfun
from PIL import Image

def makeCoarseCorrPeakGifs(seriesname, iteration, rundir, outdir, align_step):
	'''
	Creates Cross Correlation Peak Gifs for Coarse Alignment
	'''
	os.system("mkdir -p %s/gifs/correlations 2>/dev/null" % rundir)
	try:
		if align_step == "Coarse":
			img=seriesname+'00_cor.img'
			mrcf=seriesname+'00_cor.mrc'
			gif=seriesname+'00_cor.gif'
		else: #align_step == "Refinement"
			img=seriesname+iteration+'_cor.img'
			mrcf=seriesname+iteration+'_cor.mrc'
			gif=seriesname+iteration+'_cor.gif'
		png='*.png'
		out_path=os.path.join(rundir, outdir)
		img_full=out_path+'/'+img
		mrc_full=out_path+'/'+mrcf
		gif_path=os.path.join(rundir,'gifs','correlations')
		gif_full=gif_path+'/'+gif
		png_full=gif_path+'/'+png
		# Convert the corr peak *.img file to mrc for further processing
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		# Convert the *.mrc to a series of pngs
		apDisplay.printMsg("Creating correlation peak gif...")
		for i in range(0, slices):
			slice = os.path.join(gif_path,"slice%04d.png" % (i))
			scipy.misc.imsave(slice, volume[i])
		if align_step == "Coarse":
			command = "convert -delay 22 -loop 0 -gravity South -background white -splice 0x18 -annotate 0 'Frame: %%[fx:t+1]' %s %s" % (png_full, gif_full)
		else: #align_step == "Refinement"... Just changing the speed with the delay option
			command = "convert -delay 15 -loop 0 -gravity South -background white -splice 0x18 -annotate 0 'Frame: %%[fx:t+1]' %s %s" % (png_full, gif_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		apDisplay.printMsg("Done creating correlation peak gif!")
	except:
		apDisplay.printMsg("Alignment Correlation Peak Images could not be generated. Make sure i3 and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")
	

def makeCoarseCorrPlotImages(seriesname, iteration, rundir, corrfile):
	'''
	Creates Correlation Plot Images for Depiction
	'''
	import warnings
	warnings.filterwarnings("ignore", category=DeprecationWarning) #Otherwise matplotlib will complain to the user that something is depreciated
	try:
		apDisplay.printMsg("Creating correlation plot images...")
		os.system("mkdir -p %s/gifs/corrplots 2>/dev/null" % rundir)
		figcoa_full=rundir+'/gifs/corrplots/'+seriesname+iteration+'_coa.png'
		figcofx_full=rundir+'/gifs/corrplots/'+seriesname+iteration+'_cofx.png'
		figcofy_full=rundir+'/gifs/corrplots/'+seriesname+iteration+'_cofy.png'
		figrot_full=rundir+'/gifs/corrplots/'+seriesname+iteration+'_rot.png'
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		rot=[]
		cofx=[]
		cofy=[]
		coa=[]
		for line in lines:
			words=line.split()
			rot.append(float(words[1]))
			cofx.append(float(words[2]))
			cofy.append(float(words[3]))
			coa.append(float(words[4]))
		
		pylab.clf()
		pylab.plot(coa)
		pylab.savefig(figcoa_full)
		pylab.clf()
		pylab.plot(cofx)
		pylab.savefig(figcofx_full)
		pylab.clf()
		pylab.plot(cofy)
		pylab.savefig(figcofy_full)
		pylab.clf()
		pylab.plot(rot)
		pylab.savefig(figrot_full)
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %smv %s %smv %s %smv %s %s' % (figcoa_full,figcoa_full[:-3]+"gif",figcofx_full,figcofx_full[:-3]+"gif",figcofy_full,figcofy_full[:-3]+"gif",figrot_full,figrot_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating correlation plots!")
	except:
		apDisplay.printMsg("Correlation Plots could not be generated. Make sure pylab is in your $PYTHONPATH.\n")
	

def makeTiltSeriesGifs(seriesname, iteration, tiltfilename, rawimagecount, rundir, raw_path, pixelsize, map_sampling, image_file_type, align_step):
	'''
	Creates Tilt Series Gifs for Depiction
	'''
	try:
		for i in range(rawimagecount):
			#Get information from tlt file
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1j<=NFj++) if($j ~/FILE/) print $(j+1)}' | tr '\n' ' ' | sed 's/ //g'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(filename, err) = proc.communicate()
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1j<=NFj++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1j<=NFj++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1j<=NFj++) if($j ~/ROTATION/) print $(j+1)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(rotation, err) = proc.communicate()
			rotation=float(rotation)
			
			#Load image
			mrcf=raw_path+'/'+filename+'.'+image_file_type
			image=mrc.read(mrcf)
			image=imagenorm.normStdev(image)
		
			dimx=len(image[0])
			dimy=len(image)
			
			transx=int((dimx/2) - originx)
			transy=int((dimy/2) - originy)
			
			#Translate pixels left or right?
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
			if originy < dimy/2:    #shift up
				image=np.roll(image,-transy,axis=0)
				for k in range(-1,-transy-1,-1):
					image[k]=0
			elif originy > dimy/2:    #shift down
				image=np.roll(image,-transy,axis=0)
				for k in range(-transy):
					image[k]=0
			# dont shift if originy = dimy/2
			
			#Downsample image
			if (map_sampling != 1):
				image=imfun.bin2f(image,map_sampling)
			else:
				apDisplay.printMsg("No downsampling will be performed on the depiction images.")
				apDisplay.printMsg("Warning: Depiction images might be so large that they break your web browser!")
			
			#Write translated image
			gif_path=os.path.join(rundir,'gifs','tiltseries')
			if align_step == "Initial":
				tiltimage = os.path.join(gif_path,"initial_tilt%04d.png" % (i))
			elif align_step == "Coarse":
				tiltimage = os.path.join(gif_path,"coarse_tilt%04d.png" % (i))
			else: #align_step == "Reginement"
				tiltimage = os.path.join(gif_path,"tilt%04d.png" % (i))
			os.system("mkdir -p %s 2>/dev/null" % (gif_path))
			scipy.misc.imsave(tiltimage, image)
			
			#Rotate
			if (rotation != 0.000):
				rotation = -rotation      #PIL rotate is opposite protomo rotate
				image=Image.open(tiltimage)
				image.rotate(rotation).save(tiltimage)
			
			#Add scalebar
			scalesize=5000/(pixelsize * map_sampling)    #500nm scaled by sampling
			command = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '500 nm'\" %s %s" % (scalesize, dimy/map_sampling+3, dimy/map_sampling+3, tiltimage, tiltimage)
			os.system(command)
		
		#Turn pngs into a gif with Frame # and delete pngs
		if align_step == "Initial":
			gif='initial_'+seriesname+'.gif'
			png='initial_*.png'
		elif align_step == "Coarse":
			gif='coarse_'+seriesname+'.gif'
			png='coarse_*.png'
		else: #align_step == "Reginement"
			gif=seriesname+iteration+'.gif'
			png='*.png'
		png_full=gif_path+'/'+png
		gif_full=gif_path+'/'+gif
		command = "convert -delay 22 -loop 0 -gravity South -annotate 0 'Frame: %%[fx:t+1]' %s %s" % (png_full, gif_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		apDisplay.printMsg("Done creating tilt series gif!")
		
	except:
		apDisplay.printMsg("Tilt Series Images could not be generated. Make sure imagemagick is in your $PATH. Make sure that pyami, scipy, numpy, and PIL are in your $PYTHONPATH.\n")
		

def makeReconstructionGifs(seriesname, iteraion, rundir, outdir, pixelsize, sampling, map_sampling, optimize, keep_recons, align_step):
	'''
	Creates Tilt Series Gifs for Depiction
	'''
	try:
		os.system("mkdir -p %s/gifs/reconstructions 2>/dev/null" % rundir)
		if align_step == "Coarse":
			img=seriesname+'00_bck.img'
			mrcf=seriesname+'.mrc'
			gif=seriesname+'.gif'
		else: #align_step == "Reginement"
			img=seriesname+iteraion+'_bck.img'
		        mrcf=seriesname+iteraion+'_bck.mrc'
			gif=seriesname+iteraion+'_bck.gif'
		png='*.png'
		img_full=outdir+'/'+img
		mrc_full=outdir+'/'+mrcf
		gif_path=os.path.join(rundir,'gifs','reconstructions')
		gif_full=gif_path+'/'+gif
		png_full=gif_path+'/'+png
		
		# Convert the reconstruction *.img file to mrc for further processing
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		apDisplay.printMsg("Done!")
		
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		
		# Convert the *.mrc to a series of pngs
		apDisplay.printMsg("Creating reconstruction gif...")
		for i in range(0, slices):
			filename="slice%04d.png" % (i)
			slice = os.path.join(gif_path,filename)
			
			#Downsample image
			if (map_sampling > sampling):
				image=imfun.bin2f(volume[i],map_sampling/sampling)
				scipy.misc.imsave(slice, image)
				dimx=len(image[0])
				dimy=len(image)
			else:
				scipy.misc.imsave(slice, volume[i])
				dimx=len(volume[i][0])
				dimy=len(volume[i])
			
			#Add scalebar
			scalesize=5000/(pixelsize * map_sampling)    #500nm scaled by sampling
			command = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '500 nm'\" %s %s" % (scalesize, dimy+3, dimy+3, slice, slice)
			os.system(command)

		if optimize == "true":
			command = "convert -delay 11 -loop 0 -gravity South -annotate 0 'Z-Slice: %%[fx:t+1]' -layers Optimize %s %s" % (png_full, gif_full)
		else:
			command = "convert -delay 11 -loop 0 -gravity South -annotate 0 'Z-Slice: %%[fx:t+1]' %s %s" % (png_full, gif_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		if keep_recons == "false":
			command3 = "rm %s %s" % (img_full, mrc_full)
			os.system(command3)
		apDisplay.printMsg("Done creating reconstruction gif!")
	except:
		apDisplay.printMsg("Alignment Images could not be generated. Make sure i3 and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")
		