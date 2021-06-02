#!/usr/bin/env python
import sys, os, glob, time
import shutil
import math
import subprocess
import numpy
import datetime

from leginon import leginondata
from pyami import tiaraw, mrc, numsmv, tvips
from pyami import arraystats

DEBUG = False
check_interval = 40  # seconds between checking for new frames

class DiffractionUpload(object):
	def __init__(self, hl_id, target_number, file_pattern):
		self.dfimage = None

		self.hl_id = hl_id
		self.file_pattern = file_pattern
		self.bin_files = glob.glob(self.file_pattern)
		self.bin_files.sort()
		self.hldata = self.getHoleImageData()
		self.session = self.hldata['session']
		self.uid, self.gid = self.getUserGroup()
		self.diffr_series = self.getDiffractionSeries(target_number)
		self.preset = self.getPreset()
		self.target = self.getTarget(target_number)
		self.code = '%d_%d' % (hl_id, target_number)
		self.gun_length, self.gun_length_str = self.getGunLength(file_pattern)
		self.delta_tilt_degrees = self.diffr_series['tilt speed']*self.preset['exposure time']/1000.0
		self.dfimage = self.getDFImage()

	def getPreset(self):
		'''
		Create upload preset
		'''
		diffr_preset = self.diffr_series['preset']
		upload_presetq = leginondata.PresetData(initializer=diffr_preset)
		upload_presetq['name'] = 'upload'
		'''
		if not self.diffr_series['series length']:
			raise ValueError('Old data without series length can not be accurately assessed')
		# fudge factor +1 is needed to get better match in the reality.
		ntilt = self.diffr_series['series length'] + 1
		ms_per_tilt = 1000*abs(self.diffr_series['tilt range']) / (ntilt*self.diffr_series['tilt speed'])
		# use calculated tilt frame time if sufficiently different from DF preset
		if abs(ms_per_tilt-diffr_preset['exposure time']) > 20:
			print('ms_per_tilt=%.0f preset_exposure_time=%.0f' % (ms_per_tilt, diffr_preset['exposure time']))
			upload_presetq['exposure time'] = ms_per_tilt
		#upload_presetq.insert() # will return existing preset
		'''
		return upload_presetq

	def getGunLength(self, file_pattern):
		# use basename pattern in case that mount point include the word gl
		# as in glacios
		base_pattern = os.path.basename(file_pattern)
		if 'gl' in base_pattern:
			gl_str = base_pattern.split('gl')[1][:2]
			gl_value = float('%s.%s' % (gl_str[0],gl_str[1]))
			return gl_value, 'gl'+gl_str
		else:
			# default
			return 7.1,'gl71'

	def getHoleImageData(self):
		r = leginondata.AcquisitionImageData().direct_query(self.hl_id)
		if not r:
			raise ValueError('can not find image_id=%d' % (self.hl_id))
		return r

	def getDiffractionSeries(self, target_number):
		'''
		query diffraction series for the data.
		'''
		limit = 10
		trials = 0
		while trials < limit:
			# multiple trials.  This may be called right after the movies
			# are saved, even before DiffractionSeries is saved.
			# give it multiple chances to do this in case of delay.
			q = leginondata.DiffractionSeriesData(parent=self.hldata)
			r = q.query()
			if len(r) >= 1:
				for ds in r:
					if ds['emtarget']['target']['number'] == target_number:
						return ds
			trials += 1
			print 'failed trial %d @ %s' % (trials, datetime.datetime.now().ctime())
			time.sleep(2.0)
		raise ValueError('can not find matching target %d on %s with image_id=%d' % (target_number, self.hldata['filename'], self.hldata.dbid))

	def queryTarget(self, target_number):
		tresults = leginondata.AcquisitionImageTargetData(image=self.hldata, number=target_number,status='processing').query()
		if not tresults:
			raise ValueError('Missing targetdata')
		return tresults[0]

	def getTarget(self, target_number):
		if self.diffr_series['emtarget'] and self.diffr_series['emtarget']['target']:
			return self.diffr_series['emtarget']['target']
		else:
			return self.queryTarget(target_number)
		
	def getDFImage(self):
		'''
		Find DF preset image 
		'''
		if self.diffr_series['preset']['session'].dbid != self.session.dbid:
			raise ValueError('Series preset not consistent with parent image session')
		results = leginondata.AcquisitionImageData(session=self.session,preset=self.diffr_series['preset']).query(results=1)
		if results:
			return results[0]
		
	def getTiltSettings(self):
		tilt_start = float(raw_input('tilt_start (degs)? '))
		tilt_range = float(raw_input('tilt_range (degs)? '))
		tilt_speed = float(raw_input('tilt_speed (degs/s)? '))
		return tilt_start, tilt_range, tilt_speed

	def makeScopeEMData(self):
		scope = leginondata.ScopeEMData(initializer=self.diffr_series['parent']['scope'])
		dpreset = self.preset
		for k in dpreset.keys():
			if k in scope.keys():
				scope[k] = dpreset[k]
		scope['system time'] = time.time()
		return scope

	def makeCameraEMData(self):
		camera = leginondata.CameraEMData(initializer=self.diffr_series['parent']['camera'])
		dpreset = self.preset
		for k in dpreset.keys():
			if k in camera.keys():
				camera[k] = dpreset[k]
		return camera

	def run(self):
		print('Processing %s' % self.file_pattern)
		if DEBUG:
			print(self.diffr_series.dbid, self.diffr_series['preset']['name'],self.diffr_series['preset']['exposure time'])
			print(self.target.dbid, self.target['number'])
		self.copyAndUploadBinFiles()
		print('Successful')

	def copyAndUploadBinFiles(self):
		'''
		copy *.bin, upload to leginondb as mrc and convert to smv
		'''
		old_dir = os.path.dirname(self.file_pattern)
		bin_rootdir = self.session['image path'].replace('rawdata', 'diffraction_raw')
		smv_rootdir = self.session['image path'].replace('rawdata', 'diffraction')
		bin_dir = os.path.join(bin_rootdir, self.code)
		smv_dir = os.path.join(smv_rootdir, self.code)
		#creating directories
		for new_dir in (bin_rootdir,smv_rootdir, smv_dir):
			self.makeNewDirForUser(new_dir)
		self.handleRawBin(bin_dir, smv_dir)

	def handleRawBin(self, bin_dir, smv_dir):
		'''
		handle raw files from camera.  OverWritten by subclass.
		1. copy self.bin_files on source-path to bin_dir
		2. upload to leginon
		3. convert leginon imagedata to smv use self.imageDataToSmv
		4. clean up origina with cleanUp(self.bin_files)
		'''
		print bin_dir, smv_dir

	def imageDataToSmv(self, imagedata, smv_dir, min_value, max_of_mins):
			basename = imagedata['filename']
			mrc_path = os.path.join(self.session['image path'],imagedata['filename']+'.mrc')
			# smv
			iter_number1 = int(basename.split('_')[-1])
			iter_name = '%03d' % (iter_number1,)
			smv_name = '%s_%s_%s_%s.img' % (self.session['name'],self.code, self.gun_length_str, iter_name)
			smv_path = os.path.join(smv_dir, smv_name)
			# pedestal is relative to the zero after offset is applied.
			pedestal = -min_value + max_of_mins
			self.saveSMV(imagedata, smv_path, -min_value, pedestal)
			self.changeOwnership(smv_path)
			self.changeMode(smv_path, self.path_mode)

	def makeNewDirForUser(self, new_dir):
		uid = self.uid
		gid = self.gid
		if not os.path.isdir(new_dir):
			os.mkdir(new_dir)
		self.changeOwnership(new_dir)
		self.changeMode(new_dir, self.path_mode)

	def getUserGroup(self):
		image_path = self.session['image path']
		stat = os.stat(image_path)
		uid = stat.st_uid
		gid = stat.st_gid
		return uid, gid

	def changeOwnership(self,dirname):
		# change ownership of desintation directory and contents
		cmd = 'chown -R %s:%s %s' % (self.uid, self.gid, dirname)
		print(cmd)
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def changeMode(self,path,mode_str='g-w,o-rw'):
		# only works on linux
		if not mode_str:
			return
		cmd = 'chmod -R %s %s' % (mode_str, path)
		print(cmd)
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def cleanUp(self, paths=[]):
		for p in paths:
			if not os.path.isdir(p):
				os.remove(p)
			else:
				shutil.rmtree(p)

	def insertImage(self, a, mrc_name, iter_number0):
		if self.dfimage:
			imagedata = leginondata.AcquisitionImageData(initializer=self.dfimage)
		imagedata = leginondata.AcquisitionImageData(session=self.session)
		# in case self.dfimage is from other sessions
		imagedata['session'] = self.session
		imagedata['label'] = 'DExposure'
		imagedata['filename'] = mrc_name[:-4] # without '.mrc'
		imagedata['image'] = a
		imagedata['version'] = 0
		imagedata['target'] = self.target
		imagedata['preset'] = self.preset
		imagedata['emtarget'] = self.diffr_series['emtarget']
		imagedata['scope'] = self.makeScopeEMData()
		imagedata['camera'] = self.makeCameraEMData()
		# assume that we miss imaging the first tilt step
		tilt_degrees = self.diffr_series['tilt start'] + (iter_number0)*self.diffr_series['tilt speed']*self.preset['exposure time']/1000.0
		end_tilt_degrees =  self.diffr_series['tilt start'] + self.diffr_series['tilt range']
		if end_tilt_degrees > self.diffr_series['tilt start'] and tilt_degrees > end_tilt_degrees:
			# positive tilt has stopped
			tilt_degrees = end_tilt_degrees
		elif end_tilt_degrees < self.diffr_series['tilt start'] and tilt_degrees < end_tilt_degrees:
			# negative tilt has stopped
			tilt_degrees = end_tilt_degrees
		imagedata['scope']['stage position']['a'] = math.radians(tilt_degrees)
		if iter_number0 == 0 or iter_number0 == len(self.bin_files)-1:
			print '%d tilt %.2f' % (iter_number0,tilt_degrees)
		imagedata.insert()
		uploaded_mrc_path = os.path.join(self.session['image path'],imagedata['filename']+'.mrc')
		self.changeOwnership(uploaded_mrc_path)
		self.changeMode(uploaded_mrc_path, self.path_mode)
		return imagedata

	def insertImageStats(self, numarray, imagedata):
		allstats = arraystats.all(numarray)
		statsdata = leginondata.AcquisitionImageStatsData()
		statsdata['session'] = self.session
		statsdata['min'] = allstats['min']
		statsdata['max'] = allstats['max']
		statsdata['mean'] = allstats['mean']
		statsdata['stdev'] = allstats['std']
		statsdata['image'] = imagedata
		statsdata.insert()

	def getCameraLengthMM(self, imagedata):
		results = leginondata.CameraLengthCalibrationData(tem=imagedata['scope']['tem'],ccdcamera=imagedata['camera']['ccdcamera'], magnification=imagedata['scope']['magnification']).query(results=1)
		if not results:
			return float(imagedata['scope']['magnification'])
		return results[0]['camera length']*1000.0

	def getBeamCenterMM(self, imagedata):
		beam_center = {}
		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		r = leginondata.BeamstopCenterData(tem=tem, ccdcamera=cam).query(results=1)
		if r:
			return r[0]['beam center']
		for axis in ('x','y'):
			pixel_size = imagedata['camera']['binning'][axis]*imagedata['camera']['pixel size'][axis]
			beam_center[axis] = 1000 * pixel_size * imagedata['camera']['dimension'][axis] / 2.0
		return beam_center

	def getCameraGain(self, imagedata):
		ccdcamera = imagedata['camera']['ccdcamera']
		ht = imagedata['scope']['high tension']
		q = leginondata.CameraSensitivityCalibrationData(ccdcamera=ccdcamera)
		q['high tension'] = ht
		r = q.query(results=1)
		if r:
			# gain should be sum of the binning factors.
			# TODO: account for different camera binning count ?
			return r[0]['sensitivity']
		else:
			# no calibration.  Assume 1
			return 1.0

	def getDataProtocolName(self, imagedata):
		return "nan" #default to unknown

	def getLeginonInfoDict(self, imagedata):
		smv_dict={}
		# camera info
		smv_dict['GAIN'] = self.getCameraGain(imagedata)
		smv_dict['BEAMLINE'] = self.getDataProtocolName(imagedata)
		# collection info
		smv_dict['OSC_START'] = math.degrees(imagedata['scope']['stage position']['a'])
		smv_dict['OSC_RANGE'] = self.delta_tilt_degrees
		smv_dict['PHI'] = smv_dict['OSC_START'] # rolling shutter
		smv_dict['DISTANCE'] = self.getCameraLengthMM(imagedata)
		# pixel size needs to be after binning and in mm
		smv_dict['BIN'] = (imagedata['camera']['binning']['x'],imagedata['camera']['binning']['y'])
		smv_dict['PIXEL_SIZE'] = imagedata['camera']['pixel size']['x']*imagedata['camera']['binning']['x'] * 1000.0
		smv_dict['ACC_TIME'] = imagedata['camera']['exposure time'] # milli-seconds
		smv_dict['TIME'] = smv_dict['ACC_TIME'] / 1000.0  # rolling shutter sec
		# beam center is around zero (in mm from ?? corner)
		beam_center = self.getBeamCenterMM(imagedata)
		smv_dict['BEAM_CENTER_X'] = beam_center['x']
		smv_dict['BEAM_CENTER_Y'] = beam_center['y']
		return smv_dict

	def saveSMV(self,imagedata, smv_path, offset, pedestal=0):
		smv_dict = self.getLeginonInfoDict(imagedata)
		smv_dict['LEGINON_OFFSET'] = offset
		smv_dict['IMAGE_PEDESTAL'] = pedestal
		file_basename = os.path.basename(smv_path)
		a = imagedata['image']
		numsmv.write(a, smv_path,offset,smv_dict)
		print('saved to %s' % (smv_path,))

class TvipsMovieUpload(DiffractionUpload):
	def getDataProtocolName(self, imagedata):
		return "TVIPS_F416_EMMENU"

	def handleRawBin(self, new_set_dir, smv_dir):
		'''
		Tvips Image set has the structure
		hlImageId_targetNumber/Image%03d.tvips
		new_set_dir is the hlImageId_targetNumber directory
		'''
		# there should only be one directory in self.bin_files
		f = self.bin_files[0]
		if f[-1] !='/':
			f += '/'
		pattern = f+'*.tvips'
		image_files = glob.glob(pattern)
		self.makeNewDirForUser(new_set_dir)
		# safer to do individually in case of interuption.
		for f in image_files:
			shutil.copy(f, new_set_dir)
		min_value = 0
		nz = tvips.readHeaderFromFile(new_set_dir)['nz']
		for i in range(nz):
			imagedata = self.uploadMrcFromTvipsSet(new_set_dir, i)
			self.imageDataToSmv(imagedata, smv_dir, min_value)
		self.cleanUp(self.bin_files)

	def uploadMrcFromTvipsSet(self, set_dir, iter_number):
		# upload mrc files
		iter_name = '%d' % (iter_number+1)
		mrc_name = '%s_%s_%s_%s.mrc' % (self.session['name'],self.code, self.gun_length_str, iter_name)
		# iter_number is base 0
		numarray = tvips.read(set_dir, iter_number)
		numarray = numpy.where(numarray < -1, -1, numarray)
		imagedata = self.insertImage(numarray, mrc_name, iter_number)
		self.insertImageStats(numarray, imagedata)
		return imagedata

class TiaMovieUpload(DiffractionUpload):
	def getDataProtocolName(self, imagedata):
		return "CETAD_TUI"

	def handleRawBin(self, bin_dir, smv_dir):
		self.makeNewDirForUser(bin_dir)

		mins = []
		self.new_bin_files=[]
		print('Copying bin files to session/diffraction_raw....')
		for i, f in enumerate(self.bin_files):
			old_path = f
			basename = os.path.basename(old_path)
			iter_name = '%03d' % (int(basename.split('_')[-1][:-4]),)
			bin_name = '%s_%s_%s_%s.bin' % (self.session['name'],self.code, self.gun_length_str, iter_name)
			bin_path = os.path.join(bin_dir, bin_name)
			self.new_bin_files.append(bin_path)
			#print('copying %s to %s' % (old_path, bin_path))
			shutil.copy(f, bin_path)
			self.changeOwnership(bin_path)
			self.changeMode(bin_path, self.path_mode)
			numarray = tiaraw.read(bin_path)
			mins.append(numarray.min())
		# get max of the minimums as pedestal
		max_of_mins = max(mins)
		# get overall data minimums for offsetting
		# smv files that is unsigned.
		min_value =  min(mins)
		# Don't allow offset by more than 2000
		if min_value < -2000:
			print('Data minimum is %.1f. smv Offset is cut to 2000' % min_value)
			min_value = -2000
		print('Offset for smv files=%s' % (-min_value,))
		for i, bin_path in enumerate(self.new_bin_files):
			basename = os.path.basename(bin_path)
			print('converting %s' % (basename,))
			# mrc upload
			imagedata = self.uploadMrcFromBin(bin_path, i)
			self.imageDataToSmv(imagedata, smv_dir, min_value, max_of_mins)
		self.cleanUp(self.bin_files)

	def uploadMrcFromBin(self, bin_path, iter_number):
		# upload mrc files
		dirname = os.path.dirname(bin_path)
		bin_name = os.path.basename(bin_path)
		mrc_name = bin_name.replace('.bin','.mrc')
		numarray = tiaraw.read(bin_path)
		imagedata = self.insertImage(numarray, mrc_name, iter_number)
		self.insertImageStats(numarray, imagedata)
		return imagedata

def slackNotification(msg):
	import socket
	host = socket.gethostname()
	msg = '%s %s' % (host, msg)
	try:
		from slack import slack_interface
		slack_inst = slack_interface.SlackInterface()
		channel = slack_inst.getDefaultChannel()
		slack_inst.sendMessage(channel,'%s ' % (msg))
	except:
		print msg

def handleBadFiles(datapath, code, file_pattern, error=''):
	newpath = os.path.join(datapath,'bad_%s' % code)
	if not os.path.isdir(newpath):
		os.mkdir(newpath)
	files = glob.glob(file_pattern)
	for f in files:
		shutil.move(f, newpath)
	print error
	msg = "microed invalid file pattern %s are moved to %s" % (os.path.basename(file_pattern), newpath)
	print(msg)
	#slackNotification(msg)

def decodeTvipsImageSet(f):
	bits = os.path.splitext(os.path.basename(f))[0].split('_')
	file_pattern = f
	return file_pattern

def decodeTiaRaw(f):
	bits = os.path.splitext(os.path.basename(f))[0].split('_')
	# files have the format of %d_%d_%03d.bin
	file_pattern = os.path.join(os.path.dirname(f),'_'.join(bits[:-1]))+'*.bin'
	return file_pattern

def checkAllImages(datapath):
	'''
	Check all images in datapath for parent_target.bin files and
	group them
	'''
	if datapath[-1] !='/':
		datapath += '/'
	pattern = datapath + '*_*'
	paths = glob.glob(pattern)
	#bad
	bad_pattern = datapath + 'bad*_*'
	bad_paths = glob.glob(bad_pattern)
	pathset = set(paths)
	pathset.difference_update(bad_paths)
	groups = {}
	bad_groups = {}
	movie_format = ''
	for f in pathset:
		valid_target_code = True
		bits = os.path.splitext(os.path.basename(f))[0].split('_')
		if not bits[1].isdigit():
			print 'bad name %s', os.path.splitext(os.path.basename(f))[0]
			valid_target_code = False
			code = '_'.join(bits[:2])
		else:
			target_number=int(bits[1])
			code = '%s_%d' % (bits[0],target_number)
		# different formats
		if os.path.isdir(f):
			movie_format = 'Tvips'
			file_pattern = decodeTvipsImageSet(f)
			# tvips imageset directory
		else:
			# tiaraw files
			movie_format = 'Tia'
			file_pattern = decodeTiaRaw(f)
		# divide in groups
		if not valid_target_code:
			if code not in bad_groups.keys():
				bad_groups[code]=file_pattern
			continue
		if code not in groups.keys():
			groups[code]=file_pattern
		print code
	# handle bad images at the end to get all patterned file
	for c in bad_groups.keys():
		handleBadFiles(datapath, c, bad_groups[c])
	return groups, movie_format

def loop(check_path, check_interval,no_wait=False,mode_str=''):
	while True:
		print 'Iterating...'
		groups, movie_format = checkAllImages(check_path)
		sorted_keys = list(groups.keys())
		sorted_keys.sort()
		for k in sorted_keys:
			bits = k.split('_')
			hl_id = int(bits[0])
			target_number=int(bits[1])
			if not no_wait:
				# Don't start processing until all images are there.
				image_count = len(glob.glob(groups[k]))
				last_count = 0
				while image_count != last_count:
					print('Checking series %d_%d for completeness' % (hl_id, target_number))
					last_count = image_count
					# shutil.mv should be done quickly
					print('Wait 5 second in case series writing is not finished - current count=%d' % image_count)
					time.sleep(5)
					image_count = len(glob.glob(groups[k]))
			print('Processing series %d_%d' % (hl_id, target_number))
			try:
				if movie_format == 'Tia':
					app = TiaMovieUpload(hl_id,target_number,groups[k])
				elif movie_format == 'Tvips':
					app = TvipsMovieUpload(hl_id,target_number,groups[k])
				else:
					app = DiffractionUpload(hl_id,target_number,groups[k])
				app.path_mode = mode_str
				app.run()
			except ValueError as e:
				# no diffraction series saved.  For example, where there is a leginon side
				# crash while the movie is being recorded.
				handleBadFiles(check_path, k, groups[k], e)
		if no_wait:
			break
		print 'Sleeping...'
		time.sleep(check_interval)

def checkOptionConflicts(params):
	if not os.path.isdir(params['source_path']):
		raise ValueError('source_path not a directory')

def parseParams():
	global check_interval

	from optparse import OptionParser
	parser = OptionParser()
	# options
	parser.add_option("--source_path", dest="source_path",
		help="Mounted parent path to transfer, e.g. --source_path=/mnt/microed", metavar="PATH")
	parser.add_option("--check_interval", dest="check_interval", help="Seconds between checking for new data", type="int", default=check_interval)
	parser.add_option("--no_wait", dest="no_wait", help="Catch up upload without waiting for more images to come per series", action="store_true", default=False)
	parser.add_option("--path_mode", dest="mode_str", 
		help="recursive session permission modification by chmod if specified, default means not to modify e.g. --path_mode=g-w,o-rw")
	# parsing options
	(options, optargs) = parser.parse_args(sys.argv[1:])
	if len(optargs) > 0:
		print "Unknown commandline options: "+str(optargs)
		sys.exit()
	if len(sys.argv) < 2:
		parser.print_help()
		sys.exit()
	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	checkOptionConflicts(params)
	# set global variable check_interval
	check_interval = options.check_interval
	return params

def test(check_path, check_interval=10):
	groups, movie_format = checkAllImages(check_path)

if __name__=='__main__':
	params = parseParams()
	print "Look into directory %s" % params['source_path']
	#test(params['source_path'])
	loop(params['source_path'], params['check_interval'], params['no_wait'], params['mode_str'])
