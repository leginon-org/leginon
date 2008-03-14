#!/usr/bin/env python

import os, sys
import time
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
	def __init__(self, spiderexec=None, dataext='.spi', projext=".dat"):
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

		self.dataext = dataext
		if dataext[0] == '.': self.dataext = dataext[1:]
		self.projext = projext
		if projext[0] == '.': self.projext = projext[1:]

		### Start spider process, initialize with some MD commands.
		#self.spiderin = os.popen(self.spiderexec, 'w')
		self.spiderproc = subprocess.Popen(self.spiderexec, shell=True, 
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.spiderin = self.spiderproc.stdin
		self.spiderout = self.spiderproc.stdout

		self.toSpiderQuiet(self.projext+"/"+self.dataext)
		for i in range(7):
			sys.stderr.write(self.spiderout.readline())
		self.toSpiderQuiet("MD", "TERM OFF")
		self.toSpiderQuiet("MD", "RESULTS OFF")

	def wait(self):
		### waits until spider quits	
		self.spiderproc.wait()

	def toSpider(self, *args):
		" each item is a line sent to Spider"
		sys.stderr.write("\033[35m"+"executing command: "+str(args)+"\033[0m")
		for item in args:
			self.spiderin.write(str(item) + '\n')
		self.spiderin.flush()

	def toSpiderQuiet(self, *args):
		" each item is a line sent to Spider"
		for item in args:
			self.spiderin.write(str(item) + '\n')
		self.spiderin.flush()

	def close(self, delturds=1):
		self.toSpiderQuiet("EN D")			 # end the spider process,
		if delturds:
			for file in ['fort.1', 'jnkASSIGN1', 
			 'LOG.'+self.dataext, 'LOG.'+self.projext, 
			 "results."+self.projext+".0", "results."+self.projext+".1"]:
				if os.path.exists(file):
					try: os.remove(file)
					except: pass
		self.spiderproc.wait()
		logf = open("spider.log", "a")
		for line in self.spiderout.readlines():
			logf.write(line)
		logf.close()

	 
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

