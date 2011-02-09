import os
import subprocess

from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apDisplay


def alignAndRecon(stackdir, stackname, processdir, markersize_pixel, reconbin, thickness_binnedpixel, markernumber, commit):
	# the place to convert the parameters and run the subprocess that
	# runs raptor see appionlib/appionScript.py runAppionScriptInSubprocess
	# for an example
	### make standard input for ctftilt
	programname = 'raptor'
	currentdir = os.getcwd()
	os.chdir(processdir)
	cmd = 'RAPTOR -execpath /usr/local/ -path '+stackdir+' -input '+stackname+' -output '+processdir
	cmd += ' -diameter %d' % (markersize_pixel)+' -bin %d' % (reconbin)+ '-rec 0 -thickness %d' % (thickness_binnedpixel)
	cmd += ' -markers %d' % markernumber
	
	print cmd
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	proc.wait()

	stdout_value = proc.communicate()[0]
	while proc.returncode is None:
		time.wait(60)
		stdout_value = proc.communicate()[0]
	if proc.returncode != 0:
		pieces = cmd.split(' ')
		apDisplay.printWarning('%s had an error. Please check its log file: \n' % programname)
	else:
		apDisplay.printMsg('Raptor ran successfully')
	apDisplay.printMsg('------------------------------------------------')

	# When it is possible to extract alignment, we will return a committed alignment result and return that
	# Returns None for now.
	raptoraligndata = None
	return proc.returncode, raptoraligndata

def insertRaptorParams(markersize,markernumber):
	# insert parameters used in raptor alignment such as markersize
	# markernumber
	q = appiondata.ApRaptorParamsData(markersize=markersize,markernumber=markernumber)
	q.insert()
	return q

def linkStToMrcExtension(stackdir,seriesname):
	#create symlinks to files
	linkedpath = os.path.join(stackdir,seriesname+'.mrc')
	if os.path.islink(linkedpath):
		os.remove(linkedpath)
	if not os.path.isfile(linkedpath):
		os.symlink(os.path.join(stackdir,seriesname+'.st'),linkedpath)
