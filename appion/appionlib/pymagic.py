#!/usr/bin/env python

import os
import sys
import time
import math
from struct import unpack
import re
import subprocess
import glob
from appionlib import apDisplay

"""
This is based on the spyder.py setup

There are 2 streams:
 The Python program sends commands to IMAGIC as if they were typed at the
 IMAGIC-COMMAND: prompt.

 The IMAGIC session is started by creating an instance of the ImagicSession
 class:

		im = ImagicSession()

 Then you use the instance methods (functions of im)
 - send commands to IMAGIC with im.toImagic("op", "infile","outfile","args")
"""

#=====================
def fileFilter(infile, exists=True):
	"""
	checks that the input imagic file exists, and returns the filename
	without the extension
	"""

	fname,ext=os.path.splitext(infile)
	if exists is True:
		if not (os.path.exists(fname+".hed") and os.path.exists(fname+".img")):
			apDisplay.printError("input file: '%s' does not exist in imagic format"%infile)
	fname = re.sub(os.getcwd()+"/", "", os.path.abspath(fname))
	return fname

#=====================
#=====================
class ImagicSession:
	def __init__(self, imagicexe, nproc=1, imagicprocdir="", verbose=False, log=True):
		# find imagic root	
		if os.environ.has_key('IMAGIC_ROOT'):
			self.imagicroot = os.environ['IMAGIC_ROOT']
		else:
			apDisplay.printError("$IMAGIC_ROOT directory is not specified, please specify this in your .cshrc / .bashrc")

		# make sure executable exists
		self.imagicexe = os.path.join(self.imagicroot,imagicexe)
		if not os.path.exists(self.imagicexe):
			apDisplay.printError("imagic executable: '%s' not found"%self.imagicexe)

		sys.stderr.write("\033[35m"+"executing IMAGIC command: %s\033[0m\n"%self.imagicexe)

		### for multiprocessor
		if nproc > 1:
			mpiexec = os.path.join(self.imagicroot,"openmpi/bin/mpirun")
			if not os.path.exists(mpiexec):
				apDisplay.printError("imagic MPI executable: '%s' not found"%self.imagicexe)
			os.environ['IMAGIC_BATCH']="1"
			self.imagicexe = ("%s -np %i -x IMAGIC_BATCH %s"%(mpiexec, nproc, self.imagicexe))

		### Start imagic process
		self.logf = open("imagic.log", "w")
		self.starttime = time.time()

		if verbose is True:
			self.imagicproc = subprocess.Popen(self.imagicexe, shell=True, stdin=subprocess.PIPE)
		elif log is False:
			self.imagicproc = subprocess.Popen(self.imagicexe, shell=True, 
				stdin=subprocess.PIPE, stdout=open('/dev/null', 'w')) 
		else:
			self.imagicproc = subprocess.Popen(self.imagicexe, shell=True, 
				stdin=subprocess.PIPE, stdout=self.logf)

		self.imagicin = self.imagicproc.stdin

	#=====================
	def timeString(self, tottime):
		""" 
		returns a string with the length of time scaled for clarity
		"""
		tottime = float(tottime)
		#less than 70 seconds
		if tottime < 70.0:
			timestr = str(round(tottime,2))+" sec"
		#less than 70 minutes
		elif tottime < 4200.0:
			subbase = 1.0
			base = subbase * 60.0
			majorunit = "min"
			minorunit = "sec"
			timestr = ( str(int(math.floor(tottime/base)))+" "+majorunit+" "
				+str(int(round( (tottime % base)/subbase )))+" "+minorunit )
		#less than 28 hours
		elif tottime < 100800.0:
			subbase = 60.0
			base = subbase * 60.0
			majorunit = "hr"
			minorunit = "min"
			timestr = ( str(int(math.floor(tottime/base)))+" "+majorunit+" "
				+str(int(round( (tottime % base)/subbase )))+" "+minorunit )
		#more than 28 hours (1.2 days)
		else:
			subbase = 3600.0
			base = subbase * 24.0
			majorunit = "days"
			minorunit = "hr"
			timestr = ( str(int(math.floor(tottime/base)))+" "+majorunit+" "
				+str(int(round( (tottime % base)/subbase )))+" "+minorunit )
		return str(timestr)

	#=====================
	def version(self):
		"""
		get IMAGIC version from the "version_######S" file in
		the imagicroot directory, return as an int
		"""
		time.sleep(1)
		versionstr=glob.glob(os.path.join(self.imagicroot,"version_*"))
		if versionstr:
			v = re.search('\d\d\d\d\d\d',versionstr[0]).group(0)
			return int(v)
		else:
			apDisplay.printError("Could not get version number from imagic root directory")

	#=====================
	def wait(self):
		### waits until IMAGIC quits

		### set wait times
		waittime = 2.0
		time.sleep(waittime)
		self.logf.flush()
		### check number 1
		if self.imagicproc.poll() is None:
			waiting = True
			time.sleep(waittime)
		else:
			self.imagicproc.wait()
			return
		### check number 2
		if self.imagicproc.poll() is None:
			waiting = True
			sys.stderr.write("waiting for IMAGIC")
		else:
			self.imagicproc.wait()
			return
		### continuous check
		while self.imagicproc.poll() is None:
			if waittime > 10:
				sys.stderr.write(".")
			time.sleep(waittime)
			waittime *= 1.1
			self.logf.flush()
		if waiting is True:
			tdiff = time.time()-self.starttime
			if tdiff > 20:
				tstr = self.timeString(tdiff)
				sys.stderr.write("\nIMAGIC completed in "+tstr+"\n")
			else:
				sys.stderr.write("\n")
		self.imagicproc.wait()

	#=====================
	def toImagic(self, *args):
		" each item is a line sent to IMAGIC"
		loadavg = os.getloadavg()[0]
		if loadavg > 2.0:
			sys.stderr.write("Load average is high "+str(round(loadavg,2))+"\n")
			loadcubed = loadavg*loadavg*loadavg
			time.sleep(loadcubed)
		sys.stderr.write("\033[35m"+"executing command: "+str(args)+"\033[0m\n")
		for item in args:
			self.imagicin.write(str(item) + '\n')
		self.imagicin.flush()
		self.logf.flush()

	#=====================
	def toImagicQuiet(self, *args):
		" each item is a line sent to IMAGIC"
		for item in args:
			self.imagicin.write(str(item) + '\n')

	#=====================
	def close(self):
		self.wait()

		for file in ['fort.1', 'jnkASSIGN1']: 
			if os.path.exists(file):
				try: os.remove(file)
				except: pass
		self.logf.close()
	 
# --------------------------------------------------------------
if __name__ == '__main__':
	im = ImagicSession()
	im.toImagic()
	im.close()

