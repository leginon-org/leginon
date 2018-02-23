#!/usr/bin/env python
# This script wraps tilt-series upload to Appion to streamline the uploading of
# one or more SerialEM tilt-series with one command.
# 
# Converts one or more SerialEM-formatted image stacks and mdoc files to be Appion-uploadable.
# A temporary directory is made and then removed for each stack.
# The stack is unstacked into the temp directory.
# Information is stripped from the mdoc to make a text file for upload to Appion.
# If the tilt-series is the first in a session, it is uploaded alone.
# Serially uploads each tilt-series if they are not the first in the session.
# Usage: Only use the webforms to generate commands because sessions are reserved.

import os
import sys
import time
import optparse
import subprocess
from glob import glob
from pyami import mrc
from datetime import datetime
from appionlib import apDisplay


def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--session', dest='session',
		help= 'Session date, e.g. --sessionname=14sep04a')
	parser.add_option("--description", dest="description", default="",
		help="Run description")
	parser.add_option('--projectid', dest='projectid',
		help= 'Project id, e.g. --projectid=20')
	parser.add_option('--jobtype', dest='jobtype',
		help= 'Appion jobtype')
	parser.add_option('--expid', dest='expid',
		help= 'Appion experiment id, e.g. --expid=8514')
	parser.add_option('--voltage', dest='voltage', type="int",
		help= 'Microscope voltage in keV, e.g. --voltage=300')
	parser.add_option('--cs', dest='cs', type="float",
		help= 'Microscope spherical abberation, e.g. --cs=2.7')
	parser.add_option('--serialem_stack', dest='serialem_stack', default="",
		help= 'SerialEM stack path, e.g. --serialem_stack=<path_to_stack>')
	parser.add_option('--serialem_mdoc', dest='serialem_mdoc', default="",
		help= 'SerialEM-formatted mdoc path, e.g. --serialem_mdoc=<path_to_mdoc>')
	parser.add_option('--serialem_dir', dest='serialem_dir', default="",
		help= 'SerialEM path to stack and mdoc files, e.g. --serialem_mdoc=<path_to_dir>')
	
	
	options, args=parser.parse_args()
	
	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options


def serialEM2Appion(stack, mdoc, voltage):
	'''
	Unstacks SerialEM stack and creates Appion-formatted info file for upload from mdoc.
	'''
	prefix = os.path.splitext(os.path.basename(stack))[0]
	prefix = prefix.replace('.','_')
	apDisplay.printMsg("Preparing %s for upload to Appion..." % prefix)
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
	binning = int(round(binning))
	cmd3="awk '/Magnification /{print}' %s | head -1 | awk '{print $3}'" % mdoc
	proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
	(mag, err) = proc.communicate()
	mag = int(mag)
	
	image_list=[]
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
		cmd7="awk '/DateTime /{print}' %s | awk '{print $3}' | head -%s | tail -1" % (mdoc, image_number)
		proc=subprocess.Popen(cmd7, stdout=subprocess.PIPE, shell=True)
		(datestamp, err) = proc.communicate()
		cmd8="awk '/DateTime /{print}' %s | awk '{print $4}' | head -%s | tail -1" % (mdoc, image_number)
		proc=subprocess.Popen(cmd8, stdout=subprocess.PIPE, shell=True)
		(timestamp, err) = proc.communicate()
		full_timestamp = '%s %s' % (datestamp.rstrip('\n'), timestamp.rstrip('\n').rstrip())
		full_timestamp = time.mktime(datetime.strptime(full_timestamp, "%d-%b-%y %H:%M:%S").timetuple())
		
		filename = "%s/%s_%04d.mrc" % (temp_image_dir, prefix, image_number)
		
		tilt_info = '%s\t%fe-10\t%d\t%d\t%d\t%fe-6\t%d\t%f\t%f\n' % (filename, pixelsize, binning, binning, mag, defocus, int(voltage)*1000, tiltangle, dose)
		image_list.append({'timestamp':full_timestamp, 'tilt_info':tilt_info})
	
	time_sorted_image_list = sorted(image_list, key=lambda k: k['timestamp'])
	info_file = os.path.join(temp_image_dir,'%s_info.txt' % prefix)
	info=open(info_file,'w')
	
	for image_number in range(0,len(stack)):
		info.write(time_sorted_image_list[image_number]['tilt_info'])
	info.close()
	
	return image_number+1, info_file, temp_image_dir


if __name__ == '__main__':
	options=parseOptions()
	
	if ((options.serialem_stack != "" and options.serialem_mdoc != "") or (options.serialem_dir != "")):
		if ((options.serialem_stack != "" and options.serialem_mdoc != "") and (options.serialem_dir == "")):
			#Uploading first tilt-series in a session
			num_images, info_file, temp_image_dir = serialEM2Appion(options.serialem_stack, options.serialem_mdoc, options.voltage)
			
			cmd = 'imageloader.py --projectid='+options.projectid+' --session='+options.session+' --cs='+str(options.cs)+' --batchparams='+info_file+' --tiltgroup='+str(num_images)+' --description="'+options.description+'" --jobtype='+options.jobtype
			print cmd
			proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()
			os.system("rm -rf %s" % temp_image_dir)
		else: #Uploading one or more tilt-series to an existing session
			#Check that there are an equal number of .st/.mrc files and .mdoc files
			stack_files = glob("%s/*.st" % options.serialem_dir)
			stack_files.extend(glob("%s/*.mrc" % options.serialem_dir))
			stack_files = sorted(stack_files)
			mdoc_files = glob("%s/*.mdoc" % options.serialem_dir)
			if len(stack_files) == len(mdoc_files):
				num_uploads = len(stack_files)
				for tiltseries in range(num_uploads):
					stack_file = stack_files[tiltseries]
					if os.path.exists(stack_file+'.mdoc'): #Check for file.st.mdoc
						mdoc_file = stack_file+'.mdoc'
					else: #Check for file.mdoc
						mdoc_file = os.path.dirname(os.path.abspath(stack_file))+'/'+os.path.splitext(os.path.basename(stack_file))[0]+'.mdoc'
					num_images, info_file, temp_image_dir = serialEM2Appion(stack_file, mdoc_file, options.voltage)
					cmd = 'imageloader.py --projectid='+options.projectid+' --session='+options.session+' --cs='+str(options.cs)+' --batchparams='+info_file+' --tiltgroup='+str(num_images)+' --description="'+options.description+'" --expid='+options.expid+' --jobtype='+options.jobtype
					print cmd
					proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
					(out, err) = proc.communicate()
					os.system("rm -rf %s" % temp_image_dir)
			else:
				apDisplay.printError("--serialem_dir must contain an equal number of .st/.mrc and .mdoc files.")
	else:
		apDisplay.printError("You must provide either a path to a SerialEM stack and mdoc or to a directory with multiple stacks and mdocs.")
	
