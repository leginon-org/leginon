#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
import time
import leginon.leginondata
import leginon.ddinfo
import pyami.fileutil

check_interval = 30  # seconds between checking for new frames

def get_source_path():
	raw_frames_path = 'RAW_FRAMES_PATH'
	try:
		source_path = os.environ[raw_frames_path]
	except:
		sys.stderr.write('specify location of raw frames in variable %s\n' % (raw_frames_path,))
		sys.exit(1)
	return source_path

image_classes = [
	leginon.leginondata.AcquisitionImageData,
	leginon.leginondata.DarkImageData,
	leginon.leginondata.BrightImageData,
	leginon.leginondata.NormImageData,
]

def query_image_by_frames_name(name):
	qcam = leginon.leginondata.CameraEMData()
	qcam['frames name'] = name
	for cls in image_classes:
		qim = cls(camera=qcam)
		results = qim.query()
		if results:
			return results[0]
	return None

def copy_and_delete(src, dst):
	## ensure a trailing / on src
	if src[-1] != '/':
		src = src + '/'
	## make dirs
	pyami.fileutil.mkdirs(dst)
	cmd = 'rsync -av --remove-sent-files %s %s' % (src, dst)
	print cmd
	p = subprocess.Popen(cmd, shell=True)
	p.wait()

	# remove the dir we just copied, assuming is and all subdirs are empty
	abspath = os.path.abspath(src)
	dirpath,basename = os.path.split(abspath)
	cmd = 'find %s -type d -empty -prune -exec rmdir --ignore-fail-on-non-empty -p \{\} \;' % (basename,)
	print 'cd', dirpath
	print cmd
	p = subprocess.Popen(cmd, shell=True, cwd=dirpath)
	p.wait()

next_time_start = 0
mtime = 0
time_expire = 300  # ignore anything older than 5 minutes
expired_names = {} # directories that have no db record after 5 minutes

def run_once(parent_src_path):
	global next_time_start
	global time_expire
	global mtime
	names = os.listdir(parent_src_path)
	time.sleep(4)  # wait for any current writes to finish
	time_start = next_time_start
	for name in names:
		src_path = os.path.join(parent_src_path, name)
		## skip empty directories
		if os.path.isdir(src_path) and not os.listdir(src_path):
			# maybe delete empty dir too?
			continue

		# skip expired dirctories
		if name in expired_names:
			continue

		# adjust next expiration timer to most recent time
		if mtime > next_time_start:
			next_time_start = mtime

		print '**running', src_path

		# query for Leginon image
		imdata = query_image_by_frames_name(name)
		if imdata is None:
			continue
		image_path = imdata['session']['image path']
		path_parts = image_path.split('/')
		print 'PATHPARTS', path_parts
		root_parts = path_parts[:-3]
		leg_part = path_parts[-3]
		ses_part = path_parts[-2]
		raw_part = path_parts[-1]
		frames_parts = root_parts + ['frames',ses_part,raw_part]
		frames_path = '/'.join(frames_parts)
		imname = imdata['filename'] + '.frames'
		dst_path = os.path.join(frames_path, imname)
		print 'DEST', dst_path

		# do actual copy and delete
		copy_and_delete(src_path, dst_path)
		leginon.ddinfo.saveImageDDinfoToDatabase(imdata,os.path.join(dst_path,'info.txt'))

def run():
	src_path = get_source_path()
	print 'Source path:  %s' % (src_path,)
	while True:
		print 'Iterating...'
		run_once(src_path)
		time.sleep(check_interval)

if __name__ == '__main__':
	run()
