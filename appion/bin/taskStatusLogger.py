#!/usr/bin/env python
import os
import sys
import subprocess

class loggerPasser(object):
	'''
	loggerPasser is called to create subprocess of _taskStatusLogger.py command
	so that the system stdout can be redirected to joblogfile
	'''
	def __init__(self):
		prog = sys.argv[0]
		dirname = os.path.dirname(prog)
		newprog = os.path.join(dirname,'_taskStatusLogger.py')
		opts = sys.argv[1:]
		cmd = '%s %s' % (newprog,' '.join(opts))
		outf = self.__getJobLogFile(opts)
		f = open(outf, "a")
		proc = subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
		proc.wait()

		f.close()

	def __getJobLogFile(self, command):
		joblogfile = None

		#Search for the command option that specified the job type
		for option in command:
			if option.startswith(r'--joblogfile='):
				#We only need the part after the '='
				joblogfile = option.split('=')[1]
				#Don't process anymore of the list then needed
				break
		joblogfile = os.path.abspath(joblogfile)
		return joblogfile
			

if __name__ == '__main__':
	script = loggerPasser()
