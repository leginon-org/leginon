#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
import time
import leginon.leginondata
import leginon.ddinfo

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

def run_once(parent_src_path):
	names = os.listdir(parent_src_path)
	time.sleep(4)  # wait for any current writes to finish
	for name in names:
		imdata = query_image_by_frames_name(name)
		if imdata is None:
			continue
		image_path = imdata['session']['image path']
		imname = imdata['filename'] + '.frames'
		src_path = os.path.join(parent_src_path, name)
		dst_path = os.path.join(image_path, imname)
		copy_and_delete(src_path, dst_path)
		ddinfo.saveDDinfoTODatabase(imdata,os.path.join(dst_path,'info.txt'))

def run():
	src_path = get_source_path()
	print 'Source path:  %s' % (src_path,)
	while True:
		run_once(src_path)
		time.sleep(check_interval)

if __name__ == '__main__':
	run()
