#!/usr/bin/env python
#
import os
import re
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParam



#=====================
#=====================

class LoadDek(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--infile", dest="infile", type="str",
			help="Final average file to plot ranges over", metavar="NAME")
		self.parser.add_option("--dekfile", dest="dekfile", type="str",
			help="Cutfit filename", metavar="NAME")

	#=====================
	def setPhoelixPath(self):
		pathvars = os.environ['PATH']
		if not re.search("apPhoelix", pathvars):
			apDisplay.printMsg("apPhoelix path not found in Appion directory, setting path now")
			appiondir = apParam.getAppionDirectory()
			appiondir = os.path.join(appiondir, "appionlib", "apPhoelix")
			os.environ['PATH'] = appiondir+":"+os.environ['PATH']
		else:
			apDisplay.printMsg("apPhoelix path found")

	#=====================
	def start(self):
		self.setPhoelixPath()
		cmd = "s_loaddek"
		cmd2 = cmd+" "+self.params['infile']+self.params['dekfile']
		split_cmd = shlex.split(cmd2)
		proc = subprocess.Popen(cmd)
		proc.wait()

#=====================
if __name__ == "__main__":
	ld = LoadDek()
	ld.start()
