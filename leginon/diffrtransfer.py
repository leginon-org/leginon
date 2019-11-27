#!/usr/bin/env python
import sys, os, glob, time
import shutil
import math
import subprocess

from leginon import leginondata
from pyami import tiaraw, mrc, numsmv

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
		ntilt = len(self.bin_files)+1
		ms_per_tilt = 1000*abs(self.diffr_series['tilt range']) / (ntilt*self.diffr_series['tilt speed'])
		# use calculated tilt frame time if sufficiently different from DF preset
		if abs(ms_per_tilt-diffr_preset['exposure time']) > 20:
			print('ms_per_tilt=%.0f preset_exposure_time=%.0f' % (ms_per_tilt, diffr_preset['exposure time']))
			upload_presetq['exposure time'] = ms_per_tilt
		#upload_presetq.insert() # will return existing preset
		return upload_presetq

	def getGunLength(self, file_pattern):
		if 'gl' in file_pattern:
			gl_str = file_pattern.split('gl')[1][:2]
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
		q = leginondata.DiffractionSeriesData(parent=self.hldata)
		r = q.query()
		if len(r) >= 1:
			for ds in r:
				if ds['emtarget']['target']['number'] == target_number:
					return ds
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
		uid = self.uid
		gid = self.gid
		#creating directories
		for new_dir in (bin_rootdir,bin_dir,smv_rootdir, smv_dir):
			if not os.path.isdir(new_dir):
				os.mkdir(new_dir)
			self.changeOwnership(uid, gid, new_dir)
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
			numarray = tiaraw.read(bin_path)
			mins.append(numarray.min())
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
			mrc_path = os.path.join(self.session['image path'],imagedata['filename']+'.mrc')
			# smv
			iter_name = '%03d' % (int(basename.split('_')[-1][:-4]),)
			smv_name = '%s_%s_%s_%s.img' % (self.session['name'],self.code, self.gun_length_str, iter_name)
			smv_path = os.path.join(smv_dir, smv_name)
			self.saveSMV(imagedata, smv_path, i, -min_value)
			self.changeOwnership(uid, gid, bin_path)
			self.changeOwnership(uid, gid, mrc_path)
			self.changeOwnership(uid, gid, smv_path)
		self.cleanUp(self.bin_files)

	def getUserGroup(self):
		image_path = self.session['image path']
		stat = os.stat(image_path)
		uid = stat.st_uid
		gid = stat.st_gid
		return uid, gid

	def changeOwnership(self,uid,gid,dirname):
		# change ownership of desintation directory and contents
		cmd = 'chown -R %s:%s %s' % (uid, gid, dirname)
		print(cmd)
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def changeMode(self,path,mode_str='g-w,o-rw'):
		# only works on linux
		cmd = 'chmod -R %s %s' % (mode_str, path)
		print(cmd)
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def cleanUp(self, paths=[]):
		for p in paths:
			os.remove(p)

	def uploadMrcFromBin(self, bin_path, iter_number):
		# upload mrc files
		dirname = os.path.dirname(bin_path)
		bin_name = os.path.basename(bin_path)
		mrc_name = bin_name.replace('.bin','.mrc')
		numarray = tiaraw.read(bin_path)
		imagedata = self.insertImage(numarray, mrc_name, iter_number)
		return imagedata

	def insertImage(self, a, mrc_name, iter_number):
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
		tilt_degrees = self.diffr_series['tilt start'] + (iter_number+1)*self.diffr_series['tilt speed']*self.preset['exposure time']/1000.0
		imagedata['scope']['stage position']['a'] = math.radians(tilt_degrees)
		if iter_number == 0 or iter_number == len(self.bin_files)-1:
			print '%d tilt %.2f' % (iter_number,tilt_degrees)
		imagedata.insert()
		return imagedata

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

	def getLeginonInfoDict(self, imagedata):
		smv_dict={}
		smv_dict['OSC_START'] = math.degrees(imagedata['scope']['stage position']['a'])
		smv_dict['OSC_RANGE'] = self.delta_tilt_degrees
		smv_dict['PHI'] = smv_dict['OSC_START'] # rolling shutter
		smv_dict['DISTANCE'] = self.getCameraLengthMM(imagedata)
		# pixel size needs to be after binning and in mm
		smv_dict['PIXEL_SIZE'] = imagedata['camera']['pixel size']['x']*imagedata['camera']['binning']['x'] * 1000.0
		smv_dict['ACC_TIME'] = imagedata['camera']['exposure time'] # milli-seconds
		smv_dict['TIME'] = smv_dict['ACC_TIME'] / 1000.0  # rolling shutter sec
		# beam center is around zero (in mm from ?? corner)
		beam_center = self.getBeamCenterMM(imagedata)
		smv_dict['BEAM_CENTER_X'] = beam_center['x']
		smv_dict['BEAM_CENTER_Y'] = beam_center['y']
		return smv_dict

	def saveSMV(self,imagedata, smv_path, iter_number, offset):
		smv_dict = self.getLeginonInfoDict(imagedata)
		file_basename = os.path.basename(smv_path)
		a = imagedata['image']
		numsmv.write(a, smv_path,offset,smv_dict)
		print('saved to %s' % (smv_path,))

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
	
def checkAllImages(datapath):
	'''
	Check all images in datapath for parent_target.bin files and
	group them
	'''
	if datapath[-1] !='/':
		datapath += '/'
	pattern = datapath + '*.bin'
	files = glob.glob(pattern)
	groups = {}
	bad_groups = {}
	for f in files:
		bits = os.path.splitext(os.path.basename(f))[0].split('_')
		if bits[1] not in '123456789' or len(bits[1])!=1:
			code = '%s_%s' % (bits[0],bits[1])
			has_target_number = False
		else:
			target_number=int(bits[1])
			has_target_number = True
			code = '%s_%d' % (bits[0],target_number)
		file_pattern = os.path.join(os.path.dirname(f),'_'.join(bits[:-1]))+'*.bin'
		if not has_target_number:
			if code not in bad_groups.keys():
				bad_groups[code]=file_pattern
			continue
		if code not in groups.keys():
			groups[code]=file_pattern
	# handle bad images at the end to get all patterned file
	for c in bad_groups.keys():
		handleBadFiles(datapath, c, bad_groups[c])
	return groups

def loop(check_path, check_interval,no_wait=False):
	while True:
		print 'Iterating...'
		groups = checkAllImages(check_path)
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
					# robocopy minimal monitor cycle is 1 min
					print('Wait 70 second in case series writing is not finished - current count=%d' % image_count)
					time.sleep(70)
					image_count = len(glob.glob(groups[k]))
			print('Processing series %d_%d' % (hl_id, target_number))
			try:
				app = DiffractionUpload(hl_id,target_number,groups[k])
				app.run()
			except ValueError as e:
				handleBadFiles(check_path, k, groups[k], e)
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


if __name__=='__main__':
	params = parseParams()
	print "Look into directory %s" % params['source_path']
	loop(params['source_path'], params['check_interval'], params['no_wait'])
