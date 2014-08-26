import os
import subprocess

from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apTomo

#for Jensen lab only
upload_to_Jensen_database = True

def alignAndRecon(stackdir, stackname, processdir, markersize_pixel, reconbin, thickness_binnedpixel, markernumber, commit):
	# the place to convert the parameters and run the subprocess that
	# runs raptor see appionlib/appionScript.py runAppionScriptInSubprocess
	# for an example
	### make standard input for ctftilt
	programname = 'raptor'
	currentdir = os.getcwd()
	os.chdir(processdir)
	raptorbin = os.getenv('RAPTORBIN')
	if raptorbin[-1] != '/':
		raptorbin = raptorbin +'/'	
	cmd = raptorbin + 'RAPTOR -execPath ' + raptorbin  + ' -path '+stackdir+' -input '+stackname+' -output '+processdir
	cmd += ' -diameter %d' % (markersize_pixel)+' -bin %d' % (reconbin)+ ' -rec 0 -thickness %d' % (thickness_binnedpixel)
	if markernumber != 0:
		cmd += ' -markers %d' % markernumber
	
	apDisplay.printMsg(cmd)
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	proc.wait()

	stdout_value = proc.communicate()[0]
	while proc.returncode is None:
		time.wait(60)
		stdout_value = proc.communicate()[0]

	raptorfailed = True
	if proc.returncode != 0:
		pieces = cmd.split(' ')
		apDisplay.printWarning('%s had an error. Please check its log file: \n' % programname)
	else:
		apDisplay.printMsg('Raptor ran successfully')
		mrcbase = processdir + '/align/' + stackname[0:-3]
		mrcpath = mrcbase + '_full.rec'
		if not os.path.exists(mrcpath):
			mrcpath = mrcbase + '_part.rec'
			if not os.path.exists(mrcpath):
				mrcpath = ''
		if mrcpath == '':
			apDisplay.printWarning('No output full or part mrc found.')
		else:
			cmd = 'ln -s ' + mrcpath + ' ' + processdir + '/' + stackname[0:-3]  + '_full.rec'              
			apDisplay.printMsg(cmd)
			proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			proc.wait()
			apDisplay.printMsg('Raptor completed.')
			raptorfailed = False
	apDisplay.printMsg('------------------------------------------------')

	# When it is possible to extract alignment, we will return a committed alignment result and return that
	# Returns None for now.
	raptoraligndata = None
	return proc.returncode, raptoraligndata, raptorfailed

def insertRaptorParams(markersize,markernumber):
	# insert parameters used in raptor alignment such as markersize
	# markernumber
	q = appiondata.ApRaptorParamsData()
	q['markersize']=markersize
	q['markernumber']=markernumber
	q.insert()
	return q

def linkStToMrcExtension(stackdir,seriesname):
	#create symlinks to files
	linkedpath = os.path.join(stackdir,seriesname+'.mrc')
	if os.path.islink(linkedpath):
		os.remove(linkedpath)
	if not os.path.isfile(linkedpath):
		os.symlink(os.path.join(stackdir,seriesname+'.st'),linkedpath)


def commitToJensenDatabase (session_time, fulltomodata, stackdir, processdir, stackname, description ):
	if not upload_to_Jensen_database:
		return

	raptordatabase = 0
	apDisplay.printMsg("Uploding to Jensen tomography database")

	alignrun = fulltomodata['alignrun']
	tiltseries = fulltomodata['tiltseries']

	nn = len(stackname)
	mrcbase = processdir + '/align/' + stackname[0:-3]
	mrcpath = mrcbase + '_full.rec'
	if not os.path.exists(mrcpath):
		mrcpath = mrcbase + '_part.rec'
		if not os.path.exists(mrcpath):
			mrcpath = ''
	if mrcpath == '':
		apDisplay.printWarning('No output full or part mrc found.')
		raptordatabase = 1
	else:
		print '!!!0', ' mrcpath=', mrcpath
		print '!!!1', ' stackdir=', stackdir, ' stackname=', stackname, ' processdir=', processdir, ' description=',description
		imagelist = apTomo.getImageList([tiltseries])
		defocus = imagelist[0]['preset']['defocus']
		magnification = imagelist[0]['preset']['magnification']
		q = appiondata.ApTiltsInAlignRunData(alignrun=alignrun)
		r = q.query()
		tomosettings = r[0]['settings']
		tilt_min = tomosettings['tilt min']
		tilt_max = tomosettings['tilt max']
		tilt_step = tomosettings['tilt step']
		dose = tomosettings['dose']
		print '!!!2', ' defocus=', defocus, ' magnification=', magnification, ' tilt_min=', tilt_min, ' tilt_max=', tilt_max, ' tilt_step=', tilt_step, ' dose=', dose
	        #sessiondata = tiltdatalist[0]['session']
		session_id = tiltseries.dbid
		print '!!!3', ' session_id=', session_id, ' session_time=', session_time

	return raptordatabase
