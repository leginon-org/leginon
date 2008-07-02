#!/usr/bin/env python

import os
import sys
import time
import math
from struct import unpack
import re
import subprocess

"""
Downloaded from:
 http://www.wadsworth.org/spider_doc/spider/proc/spyder.py
Documentation:
 http://www.wadsworth.org/spider_doc/spider/docs/scripting2.html
by Neil on Feb 12, 2008
"""

"""
There are 2 streams:
 The Python program sends commands to Spider as if they were typed at the
 .OPERATION: prompt.

 The only information Python gets from Spider are register values, via
 an external fifo pipe.

 The spider session is started by creating an instance of the SpiderSession
 class:

		sp = SpiderSession(dataext='dat')

 Then you use the instance methods (functions of sp)
 - send commands to Spider with sp.toSpider("op", "infile","outfile","args")
 - get register values from Spider w/ sp.getreg("[var]")
"""


class SpiderSession:
	def __init__(self, spiderexec=None, dataext='.spi', projext=".bat", logo=True):
		# spider executable		
		if spiderexec is None:
			if os.environ.has_key('SPIDER_LOC'):
					self.spiderexec = os.path.join(os.environ['SPIDER_LOC'],'spider')
			else:
					try:
						self.spiderexec =	subprocess.Popen("which spider", shell=True, stdout=subprocess.PIPE).stdout.read().strip()
					except:
						self.spiderexec = '/usr/local/spider/bin/spider'
			#print "using spider executable: ",self.spiderexec
		else:
			self.spiderexec = spiderexec

		self.logo = logo
		self.dataext = dataext
		if dataext[0] == '.': self.dataext = dataext[1:]
		self.projext = projext
		if projext[0] == '.': self.projext = projext[1:]

		### Start spider process, initialize with some MD commands.
		#self.spiderin = os.popen(self.spiderexec, 'w')
		self.logf = open("spider.log", "a")
		self.starttime = time.time()
		self.spiderproc = subprocess.Popen(self.spiderexec, shell=True, 
			stdin=subprocess.PIPE, stdout=self.logf, stderr=subprocess.PIPE)
		self.spiderin = self.spiderproc.stdin
		#self.spiderout = self.spiderproc.stdout
		self.spidererr = self.spiderproc.stderr

		self.toSpiderQuiet(self.projext+"/"+self.dataext)
		self.toSpiderQuiet("MD", "TERM OFF")
		self.toSpiderQuiet("MD", "RESULTS OFF")
		if self.logo is True:
			self.showlogo()

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


	def showlogo(self):
		time.sleep(1)
		self.logf.flush()
		f = open("spider.log", "r")
		for i in range(7):
			sys.stderr.write(f.readline())
		f.close()

	def wait(self):
		### waits until spider quits

		### set wait times
		if self.logo is True:
			waittime = 15.0
		else:
			waittime = 2.0
		self.logf.flush()
		### check number 1
		if self.spiderproc.poll() is None:
			waiting = True
			time.sleep(2.0)
		else:
			self.spiderproc.wait()
			return
		### check number 2
		if self.spiderproc.poll() is None:
			waiting = True
			sys.stderr.write("waiting for spider")
		else:
			self.spiderproc.wait()
			return
		### continuous check
		while self.spiderproc.poll() is None:
			if waittime > 10:
				sys.stderr.write(".")
			time.sleep(waittime)
			waittime *= 1.1
			self.logf.flush()
		if waiting is True:
			tdiff = time.time()-self.starttime
			if tdiff > 20:
				tstr = self.timeString(tdiff)
				sys.stderr.write("\nSPIDER completed in "+tstr+"\n")
			else:
				sys.stderr.write("\n")
		self.spiderproc.wait()

	def toSpider(self, *args):
		" each item is a line sent to Spider"
		sys.stderr.write("\033[35m"+"executing command: "+str(args)+"\033[0m\n")
		for item in args:
			self.spiderin.write(str(item) + '\n')
		self.spiderin.flush()
		self.logf.flush()

	def toSpiderQuiet(self, *args):
		" each item is a line sent to Spider"
		for item in args:
			self.spiderin.write(str(item) + '\n')
		#self.spiderin.flush()

	def close(self, delturds=1):
		self.toSpiderQuiet("EN D")			 # end the spider process,
		self.toSpiderQuiet("EN D")			 # end the spider process,
		self.wait()

		for file in ['fort.1', 'jnkASSIGN1', 
		 'LOG.'+self.dataext, 'LOG.'+self.projext, 
		 "results."+self.projext+".0", "results."+self.projext+".1"]:
			if os.path.exists(file):
				try: os.remove(file)
				except: pass
		#self.logf = open("spider.log", "a")
		#for line in self.spiderout.readlines():
		#	self.logf.write(line)
		self.logf.close()
		if self.logo is True:
			print self.spidererr.readline()
	 
# --------------------------------------------------------------
if __name__ == '__main__':
	sp = SpiderSession(dataext='dat')
	sp.toSpider("[size]=117")
	s = sp.getreg('size')
	print "---------------------- size =  %f" % s
	sp.toSpider("x11=7.7")
	s = sp.getreg('x11')
	print "---------------------- x11 =  %f" % s
	sp.close()

