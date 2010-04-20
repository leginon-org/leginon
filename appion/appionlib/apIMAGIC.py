import os
import re
import shutil
import sys
import stat
import time
import subprocess
from appionlib import apDisplay
from appionlib import apParam

def checkImagicExecutablePath():
	### check for IMAGIC installation
	d = os.environ
	if d.has_key('IMAGIC_ROOT'):
		imagicroot = d['IMAGIC_ROOT']
	else:
		apDisplay.printError("$IMAGIC_ROOT directory is not specified, please specify this in your .cshrc / .bashrc")	
	return imagicroot
	

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
#			process = subprocess.Popen(filename, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			devnull = open('/dev/null', 'w')
			process = subprocess.Popen(filename, shell=True, stdout=devnull, stderr=devnull)
		else:
			process = subprocess.Popen(filename, shell=True)
		if verbose is True:
#			process.wait()
			out, err = process.communicate()
			if out is not None and err is not None:
				print "IMAGIC error", out, err
		else:
			out, err = process.communicate()
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
	# used if conversion from EMAN does not write appropriate headers

	imagicroot = checkImagicExecutablePath()

	batchfile = os.path.join(path, 'copyImage.batch')

	if file[-4:] == ".img" or file[-4:] == ".hed":
		stripped_file = file[:-4]
	else:
		 stripped_file = file

	f = open(batchfile, 'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")	 
	f.write("cd %s\n" % (path))
	f.write(str(imagicroot)+"/stand/copyim.e <<EOF \n")
	f.write(stripped_file+"\n")
	f.write(stripped_file+"_copy\n")
	f.write("EOF\n")
	f.write(str(imagicroot)+"/stand/imdel.e <<EOF \n")
	f.write(stripped_file+"\n")
	f.write("EOF\n")
	f.write(str(imagicroot)+"/stand/im_rename.e <<EOF \n")
	f.write(stripped_file+"_copy\n")
	f.write(stripped_file+"\n")
	f.write("EOF\n")
	if headers is True:
		f.write(str(imagicroot)+"/stand/headers.e <<EOF \n")
		f.write(stripped_file+"\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("all\n")
		f.write("EOF\n")
	f.close()

	executeImagicBatchFile(batchfile)
	
def takeoverHeaders(filename, numpart, boxsize):
	### better workaround than copyFile ... still a workaround though

	imagicroot = checkImagicExecutablePath()
	basedir = os.path.split(filename)[0]
	basename = os.path.split(filename)[1]
	batchfile = os.path.join(basedir, "takeoverHeaders.batch")
	if basename[-4:] == ".img" or basename[-4:] == ".hed":
		stripped_file = basename[:-4]
	else:
		 stripped_file = basename

	f = open(batchfile, 'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")	 
	f.write("cd %s\n" % (basedir))
	f.write(str(imagicroot)+"/stand/testim.e <<EOF\n")
	f.write("test,1,%d\n" % (numpart))
	f.write("%d,%d\n" % (boxsize, boxsize))
	f.write("REAL\n")
	f.write("BLOBS\n")
	f.write("EOF\n")
	f.close()
	
	proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
	proc.wait()
	apParam.runCmd(batchfile, "IMAGIC")
	shutil.move(os.path.join(basedir, "test.hed"), os.path.join(basedir, stripped_file+".hed"))
	os.remove(os.path.join(basedir, "test.img"))

def convertFilteringParameters(hpfilt, lpfilt, apix):
	### CONVERT FILTERING PARAMETERS TO IMAGIC FORMAT BETWEEN 0-1
	if lpfilt is not "" and apix is not "":
		lpfilt_imagic = 2 * float(apix) / int(lpfilt)
	else:
		lpfilt_imagic = 1
	if float(lpfilt_imagic) > 1 or float(lpfilt_imagic) < 0:
		lpfilt_imagic = 1	# imagic cannot perform job when lowpass > 1

	if hpfilt is not "" and apix is not "":
		hpfilt_imagic = 2 * float(apix) / int(hpfilt)
	else:
		hpfilt_imagic = 0.01
	if float(hpfilt_imagic) > 1 or float(hpfilt_imagic) < 0:
		hpfilt_imagic = 0.01

	return hpfilt_imagic, lpfilt_imagic

def checkLogFileForErrors(logfile):
	"""
	checks for any errors arising in IMAGIC log file, provided as a full path & filename
	"""
	logf = open(logfile)
	loglines = logf.readlines()
	for line in loglines:
		if re.search("ERROR in program", line):
			apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: "+logfile)
	logf.close()
