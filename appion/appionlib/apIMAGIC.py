import os
import re
import shutil
import sys
import stat
import time
import subprocess
import glob
from appionlib import apDisplay
from appionlib import apParam

#======================
def checkImagicExecutablePath():
	### check for IMAGIC installation
	d = os.environ
	if d.has_key('IMAGIC_ROOT'):
		imagicroot = d['IMAGIC_ROOT']
	else:
		apDisplay.printError("$IMAGIC_ROOT directory is not specified, please specify this in your .cshrc / .bashrc")	
	return imagicroot
	

#======================
def getImagicVersion(imagicroot):
	### get IMAGIC version from the "version_######S" file in
	### the imagicroot directory, return as an int
	versionstr=glob.glob(os.path.join(imagicroot,"version_*"))
	if versionstr:
		v = re.search('\d\d\d\d\d\d',versionstr[0]).group(0)
		return int(v)
	else:
		apDisplay.printError("Could not get version number from imagic root directory")

#======================
def executeImagicBatchFile(filename, showcmd=True, verbose=False, logfile=None):
	"""
	executes an IMAGIC batch file in a controlled fashion
	"""
	proc = subprocess.Popen("chmod 755 "+filename, shell=True)
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
			devnull = open('/dev/null', 'w')
			process = subprocess.Popen(filename, shell=True, stdout=devnull, stderr=devnull)
		else:
			process = subprocess.Popen(filename, shell=True)
		if verbose is True:
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

#======================
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
	
#======================
def takeoverHeaders(filename, numpart, boxsize, keepfiles=False):
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

	if keepfiles is not True:
		os.remove(batchfile)

#======================
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


#======================
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

#======================
def alimass(infile, maxshift=0.2, ceniter=10, path=os.path.abspath('.'), nproc=1, keepfiles=False):
	"""
	uses a rotationally averaged total sum to center particles
	default max shift is 20% of box size
	default # of centering iterations is 10
	"""
	imagicroot = checkImagicExecutablePath()

	batchfile = os.path.join(path, 'alimass.batch')
	logf = os.path.join(path, 'alimass.log')

	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)

	file_cen=fname+"_cen"

	f=open(batchfile,"w")
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	if nproc > 1:
		f.write("%s/openmpi/bin/mpirun -np %i"%(imagicroot,nproc)+\
			" -x IMAGIC_BATCH  %s/align/alimass.e_mpi <<EOF\n"%imagicroot)
		f.write("YES\n")
		f.write("%i\n"%nproc)
	else:
		f.write("%s/align/alimass.e <<EOF\n"%imagicroot)
		f.write("NO\n")
	f.write("%s\n"%fname)
	f.write("%s\n"%file_cen)
	f.write("TOTSUM\n")
	f.write("CCF\n")
	f.write("%.3f\n"%maxshift)
	f.write("%i\n"%ceniter)
	f.write("NO_FILTER\n")
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("running alimass.e")
	executeImagicBatchFile(batchfile, logfile=logf)

	### check that it ran correctly
	if not os.path.exists(file_cen+".hed"):
		apDisplay.printError("alimass.e did not execute properly")
		return None
	checkLogFileForErrors(logf)

	## remove batch & logfiles unless otherwise specified
	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)

	return file_cen


#======================
def softMask(infile, mask, falloff, path=os.path.abspath('.'), keepfiles=False):
	"""
	applies a soft mask to images in a stack
	"""
	imagicroot = checkImagicExecutablePath()
	batchfile = os.path.join(path, 'arithm.batch')
	logf = os.path.join(path, 'arithm.log')

	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)
	
	outname = fname+"_mask"

	### apply the soft mask
	f=open(batchfile,"w")
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("%s/stand/arithm.e <<EOF\n"%imagicroot)
	f.write("%s\n"%fname) # input
	f.write("%s\n"%outname) # output
	f.write("SOFT\n") # soft mask
	f.write("%.2f\n"%mask) # mask as a fraction
	f.write("%.2f\n"%falloff) # falloff as a fraction
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("running arithm.e")
	executeImagicBatchFile(batchfile, logfile=logf)

	### check that it ran correctly
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("arithm.e did not execute properly")
		return None
	checkLogFileForErrors(logf)

	## remove batch & logfiles unless otherwise specified
	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)

	return outname

#======================
def mask2D(boxsz, mask, infile=False, maskfile="mask2Dimgfile", path=os.path.abspath('.'), keepfiles=False):
	"""
	creates a 2d circular mask
	if infile is specified, mask is applied to stack & then mask is deleted
	boxsz is the box size in pixels
	mask is the size of the mask to apply as a fraction
	"""
	imagicroot = checkImagicExecutablePath()

	batchfile = os.path.join(path, 'maskimg.batch')
	logf = os.path.join(path, 'maskimg.log')

	### generate a 2D mask
	f=open(batchfile,"w")
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("%s/stand/testim.e <<EOF\n"%imagicroot)
	f.write("%s\n"%maskfile)
	f.write("%i,%i\n"%(boxsz,boxsz))
	f.write("real\n")
	f.write("disc\n")
	f.write("%.3f\n"%mask)
	f.write("EOF\n")

	if not infile:
		f.close()
		apDisplay.printMsg("creating 2D mask")
		executeImagicBatchFile(batchfile, logfile=logf)
		# check proper execution
		if not os.path.exists(maskfile+".hed"):
			apDisplay.printError("mask generation did not execute properly")
		checkLogFileForErrors(logf)

		if keepfiles is not True:
			os.remove(batchfile)
			os.remove(logf)
		return maskfile+".hed"

	### if infile is specified, apply mask to images
	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)

	file_ma=fname+"_ma"

	f.write("%s/stand/twoimag.e <<EOF\n"%imagicroot)
	f.write("mul\n")
	f.write("%s\n"%fname)
	f.write("%s\n"%maskfile)
	f.write("%s\n"%file_ma)
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("applying 2D mask")
	executeImagicBatchFile(batchfile, logfile=logf)
	# check proper execution
	if not os.path.exists(file_ma+".hed"):
		apDisplay.printError("masking did not execute properly")
	checkLogFileForErrors(logf)

	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)

	return file_ma

#======================
def normalize(infile, sigma=10.0, path=os.path.abspath('.'), keepfiles=False):
	"""
	normalize images in a stack
	"""

	imagicroot = checkImagicExecutablePath()
	imagicv = getImagicVersion(imagicroot)

	batchfile = os.path.join(path, 'rotate.batch')
	logf = os.path.join(path, 'rotate.log')

	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)
	
	outname=fname+"_norm"

	### normalize batch
	f=open(batchfile,'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("%s/stand/pretreat.e << EOF\n"%imagicroot)
	f.write("%s\n"%fname) # input
	f.write("%s\n"%outname) # output
	f.write("NORM_VARIANCE\n") # mode
	f.write("WHOLE\n") # mask to be used
	f.write("%.2f\n"%sigma) # desired sigma
	f.write("NO\n") # remove dust outliers
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("running pretreat.e")
	executeImagicBatchFile(batchfile, logfile=logf)
	# check proper execution
	if not os.path.exists(outname+".hed"):
		apDisplay.printError("normalization did not execute properly")
	checkLogFileForErrors(logf)

	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)

	return outname

#======================
def rotateStack(infile, ang, path=os.path.abspath('.'), keepfiles=False):
	"""
	creates a rotated copy of a stack
	"""
	imagicroot = checkImagicExecutablePath()
	imagicv = getImagicVersion(imagicroot)

	batchfile = os.path.join(path, 'rotate.batch')
	logf = os.path.join(path, 'rotate.log')

	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)
	
	file_rot=fname+"_rot"

	### rotate batch
	f=open(batchfile,'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("%s/stand/rotate.e MODE ROTATE << EOF\n"%imagicroot)
	f.write("NO\n")
	f.write("%s\n"%fname)
	f.write("%s\n"%file_rot)
	if imagicv < 100312:
		f.write("NO\n")
	f.write("%.3f\n"%ang)
	f.write("NO\n")
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("rotating particles by %.3f degrees"%ang)
	executeImagicBatchFile(batchfile, logfile=logf)
	# check proper execution
	if not os.path.exists(file_rot+".hed"):
		apDisplay.printError("rotate.e did not execute properly")
	checkLogFileForErrors(logf)

	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)
	return file_rot

#======================
def runMSA(infile, maskf="none.hed", iter=50, numeig=69, overcor=0.8, nproc=1, path=os.path.abspath('.'), keepfiles=False):
	"""
	performs multivariate statistical analysis
	"""
	imagicroot = checkImagicExecutablePath()
	imagicv = getImagicVersion(imagicroot)

	batchfile = os.path.join(path, 'msa.batch')
	logf = os.path.join(path, 'msa.log')

	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)
	if maskf is not False:
		mname,ext=os.path.splitext(maskf)
		if not os.path.exists(mname+".hed"):
			apDisplay.printError("input mask file: '%s' is not in imagic format"%infile)
	outbase = os.path.join(path,"my_msa")

	### msa batch
	f=open(batchfile,'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	if nproc > 1:
		f.write("%s/openmpi/bin/mpirun -np %i"%(imagicroot,nproc)+\
			" -x IMAGIC_BATCH  %s/msa/msa.e_mpi <<EOF\n"%imagicroot)
		f.write("YES\n")
		f.write("%i\n"%nproc)
	else:
		f.write("%s/msa/msa.e << EOF\n"%imagicroot)
		f.write("NO\n")
	f.write("FRESH\n")
	f.write("MODULATION\n")
	f.write("%s\n"%fname)
	if nproc > 1:
		f.write("NO\n")
	f.write("%s\n"%mname)
	f.write("%s\n"%os.path.join(path,"eigenim"))
	f.write("%s\n"%os.path.join(path,"pixcoos"))
	f.write("%s\n"%os.path.join(path,"eigenpix"))
	f.write("%i\n"%iter)
	f.write("%i\n"%numeig)
	f.write("%.2f\n"%overcor)
	f.write("%s\n"%outbase)
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("running IMAGIC MSA")
	executeImagicBatchFile(batchfile, logfile=logf)
	# check proper execution
	if not os.path.exists(outbase+".plt"):
		apDisplay.printError("msa.e did not execute properly")
	checkLogFileForErrors(logf)

	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)
	return outbase

#======================
def classifyAndAvg(infile, numcls, path=os.path.abspath('.'), keepfiles=False):
	"""
	classify particles using eigenvectors
	and create class averages
	"""
	imagicroot = checkImagicExecutablePath()
	imagicv = getImagicVersion(imagicroot)

	batchfile = os.path.join(path, 'classify.batch')
	logf = os.path.join(path, 'classify.log')

	fname,ext=os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)

	classlist=os.path.join(path,"classlist")
	classavgs=os.path.join(path,"classes")

	### classify batch
	f=open(batchfile,'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("%s/msa/classify.e <<EOF\n"%imagicroot)
	f.write("IMAGES/VOLUMES\n")
	f.write("%s\n"%fname)
	f.write("0\n")
	f.write("69\n")
	f.write("YES\n")
	f.write("%i\n"%numcls)
	f.write("%s\n"%classlist)
	f.write("EOF\n")

	f.write("%s/msa/classum.e << EOF\n"%imagicroot)
	f.write("%s\n"%fname)
	f.write("%s\n"%classlist)
	f.write("%s\n"%classavgs)
	f.write("YES\n")
	f.write("NONE\n")
	f.write("0\n")
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("running IMAGIC classification")
	executeImagicBatchFile(batchfile, logfile=logf)
	# check proper execution
	if not os.path.exists(classavgs+".hed"):
		apDisplay.printError("classification did not execute properly")
	checkLogFileForErrors(logf)

	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)
	return classavgs


#======================
def alirefs(infile, mask=0.99, maxshift=0.3, minrot=-180.0, maxrot=180.0, iter=5, path=os.path.abspath('.'), keepfiles=False):
	"""
	align a stack of references to each other
	"""

	imagicroot = checkImagicExecutablePath()
	imagicv = getImagicVersion(imagicroot)

	batchfile = os.path.join(path, 'alirefs.batch')
	logf = os.path.join(path, 'alirefs.log')

	fname,ext = os.path.splitext(infile)
	if not os.path.exists(fname+".hed"):
		apDisplay.printError("input file: '%s' is not in imagic format"%infile)

	outname = fname+"_ali"
	### alirefs batch
	f=open(batchfile,'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("%s/align/alirefs.e <<EOF\n"%imagicroot)
	f.write("ALL\n") # translation & rotation
	f.write("CCF\n") # CCF or MCF
	f.write("%s\n"%fname) # input
	f.write("NO\n") # no contours on reference imgs
	f.write("%.2f\n"%mask) # mask as fraction
	f.write("%s\n"%outname) # output
	f.write("-999.\n") # density for thresholding
	f.write("%.2f\n"%maxshift) # max shift
	f.write("%.2f,%.2f\n"%(minrot,maxrot)) # min max rot angle
	f.write("NO\n") # create mirrors
	f.write("%i\n"%iter) # alignment iterations
	f.write("NO\n") # full output of all parameters
	f.write("EOF\n")
	f.close()

	apDisplay.printMsg("running IMAGIC alirefs")
	executeImagicBatchFile(batchfile, logfile=logf)
	# check proper execution
	if not os.path.exists(infile+"_ali.hed"):
		apDisplay.printError("alirefs did not execute properly")
	checkLogFileForErrors(logf)

	if keepfiles is not True:
		os.remove(batchfile)
		os.remove(logf)
	return outname

