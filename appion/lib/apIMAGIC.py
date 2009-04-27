import os
import sys
import stat
import time
import apDisplay
import subprocess

def executeImagicBatchFile(filename, verbose=False, logfile=None):
	"""
	executes an IMAGIC batch file in a controlled fashion
	"""
	proc = subprocess.Popen("chmod 775 "+filename, shell=True)
	proc.wait()
	path = os.path.dirname(filename)
	os.chdir(path)
	waited = False
	t0 = time.time()
	try:
		if logfile is not None:
			logf = open(logfile, 'a')
			process = subprocess.Popen(filename, shell=True, stdout=logf, stderr=logf)
		elif verbose is False:
			process = subprocess.Popen(filename, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		else:
			process = subprocess.Popen(filename, shell=True)
		if verbose is True:
			process.wait()
		else:
			### continuous check
			waittime = 0.01
			while process.poll() is None:
				if waittime > 0.05:
					waited = True
					sys.stderr.write(".")
				waittime *= 1.02
				time.sleep(waittime)
	except:
		apDisplay.printWarning("could not run IMAGIC batchfile: "+filename)
		raise
	tdiff = time.time() - t0
	if tdiff > 20:
		apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
	elif waited is True:
		print ""


def copyFile(path, file, headers=False):
	# THERE IS A REALLY STUPID IMAGIC ERROR WHERE IT DOESN'T READ IMAGIC FORMAT CREATED BY OTHER 
	# PROGRAMS, AND SO FAR THE ONLY WAY I CAN DEAL WITH IT IS BY WIPING OUT THE HEADERS!
	#
	# 			WORKS WITH BOTH .IMG AND .HED FILES
	#	

	batchfile = os.path.join(path, 'copyImage.batch')

	if file[-4:] == ".img" or file[-4:] == ".hed":
		stripped_file = file[:-4]
	else:
		 stripped_file = file

	f = open(batchfile, 'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")	 
	f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF \n")
	f.write(stripped_file+"\n")
	f.write(stripped_file+"_copy\n")
	f.write("EOF\n")
	f.write("/usr/local/IMAGIC/stand/imdel.e <<EOF \n")
	f.write(stripped_file+"\n")
	f.write("EOF\n")
	f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF \n")
	f.write(stripped_file+"_copy\n")
	f.write(stripped_file+"\n")
	f.write("EOF\n")
	if headers is True:
		f.write("/usr/local/IMAGIC/stand/headers.e <<EOF \n")
		f.write(stripped_file+"\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("all\n")
		f.write("EOF\n")
	f.close()

	executeImagicBatchFile(batchfile)

def convertFilteringParameters(hpfilt, lpfilt, apix):
	### CONVERT FILTERING PARAMETERS TO IMAGIC FORMAT BETWEEN 0-1
	if lpfilt is not "" and apix is not "":
		lpfilt_imagic = 2 * float(apix) / int(lpfilt)
	else:
		lpfilt_imagic = False
	if float(lpfilt_imagic) > 1:
		lpfilt_imagic = 1	# imagic cannot perform job when lowpass > 1
	if hpfilt is not "" and apix is not "":
		hpfilt_imagic = 2 * float(apix) / int(hpfilt)
	else:
		hpfilt_imagic = False

	return hpfilt_imagic, lpfilt_imagic
