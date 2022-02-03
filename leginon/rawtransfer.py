#!/usr/bin/env python

import os
import sys
import shutil
import filecmp
import subprocess
import time
import numpy
import leginon.leginondata
import leginon.ddinfo
import pyami.fileutil, pyami.mrc
from leginon import filetransfer

next_time_start = 0
mtime = 0
query_day_limit = 10 # ignore database query for older dates
expired_names = ['.DS_Store',] # files that should not be transferred
check_interval = 20  # seconds between checking for new frames
max_image_query_delay = 1200 # seconds before an image query by CameraEMData.'frames name' should be queryable. Need to account for difference in the clocks of the camera computer and where this script is running.

class RawTransfer(filetransfer.FileTransfer):
	def setOptions(self, parser):
		super(RawTransfer, self).setOptions(parser)
		# options
		parser.add_option("--cleanup_delay_minutes", dest="cleanup_delay_minutes", help="Delay non-database recorded images clean up by this. default is 20 min", type="float", default=max_image_query_delay/60.0)

	def query_image_by_frames_name(self,name,cam_host,dest_head):
		# speed up query by adding time limit Issue #6127
		time_limit = '-%d 0:0:0' % self.params['check_days']
		qccd = leginon.leginondata.InstrumentData(hostname=cam_host)
		qcam = leginon.leginondata.CameraEMData(ccdcamera=qccd)
		qcam['frames name'] = name
		for cls in self.image_classes:
			qim = cls(camera=qcam)
			results = qim.query(timelimit=time_limit)
			if results:
				if len(results) > 1:
					only_non_dest_head = False
					# fix for issue #3967. Not to work on the aligned images
					for r in results:
						if r['camera']['align frames']:
							continue
						# Issue 10371
						if dest_head:
							frames_path = self.getSessionFramePath(r)
							# only process destination frames_path starting with chosen head
							if sys.platform != 'win32' and not frames_path.startswith(dest_head):
								only_non_dest_head = True
								continue
						return r
					if only_non_dest_head:
						# prevent file from being cleanup
						return True
				else:
					# If there is just one, transfer regardlessly.
					return results[0]
		return None

	def isRecentCreation(self,path):
		'''
		This is called after a file is not found in the database CameraEMData.
		A created frames should be recorded in the database in seconds.
		If not, it is a rouge one and should not be kept for more checking
		since too much checking slow the workflow down.
		The default time is 20 minutes now and is much longer than it needs to.
		But if the Windows and Linux clocks are not synced, it will appears to
		be longer.
		'''
		ctime = os.path.getctime(path)
		t0 = time.time()
		is_recent =  t0 - ctime <= self.params['cleanup_delay_minutes']*60
		if not is_recent:
			print 'File was created %d minutes ago. Should be in database by now if ever.' % (int((t0-ctime)/60),)
		return is_recent

	def transfer(self, src, dst, uid, gid, method, mode_str):
		'''
		This function at minimal organize and rename the time-stamped file
		to match the Leginon session and integrated image.  If the source is
		saved on the local drive of the camera computer, rsync (default) is
		used to copy the file off and the time-stamped file on the camera
		local drive removed to make room for more data collection.
		'''
		# make destination dirs
		dirname,basename = os.path.split(os.path.abspath(dst))

		# get path of the session, e.g. /data/frames/joeuser/17nov06a
		sessionpath = os.path.abspath(os.path.join(dirname,'..'))

		self.makeDirWithOwnershipChange(sessionpath,uid,gid)
		self.makeDirWithOwnershipChange(dirname,uid,gid)

		if method == 'rsync' and not self.is_win32:
			# safer method but slower
			self._rsyncWithOwnershipChange(src,dst,uid,gid,method)
		else:
			# move does only rename and therefore will be faster if on the same device
			# but could have problem if dropped during the process between devices.
			self.move(src,dst)

		if mode_str:
			self.changeMode(dst, mode_str, recursive=True)

		# comment out cleanUp here and rely on rsync to do its job
		# and clean up on the next source search iteration.
		# see Issue #10244
		# self.cleanUp(src,method)

	def run_once(self,parent_src_path,cam_host,dest_head,method,mode_str):
		global next_time_start
		global mtime
		names = os.listdir(parent_src_path)
		time.sleep(10)  # wait for any current writes to finish
		time_start = next_time_start
		for name in names:
			src_path = os.path.join(parent_src_path, name)
			_, ext = os.path.splitext(name)
			# skip expired dirs, mrcs
			if name in expired_names:
				continue
			print '**checking', src_path
			# check access instead of wait for files to write. Speeds up interval
			try:
				if not os.access(src_path, os.R_OK):
					print 'not ready. Deferring to next iteration'
					continue
			except Exception as e:
					# There maybe other reason for it to fail.
					print 'error checking access: %s' % e
					continue
			## skip empty directories
			if os.path.isdir(src_path) and not os.listdir(src_path):
				# maybe delete empty dir too?
				continue

			# ignore irrelevent source files or folders
			# gatan k2 summit data ends with '.mrc' or '.tif'
			# de folder starts with '20' through timestamp
			# falcon mrchack stacks ends with '.mrcs'
			if not ext.startswith('.mrc') and ext != '.tif' and  ext !='.eer' and ext != '.frames' and not name.startswith('20'):
				continue

			# adjust next expiration timer to most recent time
			if mtime > next_time_start:
				next_time_start = mtime

			# query for Leginon image
			if ext.startswith('.mrc'):
				ext_len = len(ext)
				frames_name = name[:-ext_len]
				dst_suffix = '.frames.mrc'
			elif ext.startswith('.tif'):
				# tiff format
				ext_len = len(ext)
				frames_name = name[:-ext_len]
				dst_suffix = '.frames.tif'
			elif ext.startswith('.eer'):
				ext_len = len(ext)
				frames_name = name[:-ext_len]
				dst_suffix = '.frames.eer'
			else:
				frames_name = name
				dst_suffix = '.frames'
				## ensure a trailing / on directory
				if os.path.isdir(src_path) and src_path[-1] != os.sep:
					src_path = src_path + os.sep
			imdata = self.query_image_by_frames_name(frames_name,cam_host,dest_head)
			if imdata is None:
				print '%s not from a saved image' % (frames_name)
				# TODO sometimes this query happens before the imagedata is queriable.
				# Need to have a delay before remove.
				if not self.isRecentCreation(src_path):
					self.cleanUp(src_path,method)
				continue
			if imdata == True:
				print ' None of the found imagedata has destination starts with %s. Skipped' % (dest_head)
				continue
			image_path = imdata['session']['image path']
			frames_path = self.getSessionFramePath(imdata)
			# only process destination frames_path starting with chosen head
			if sys.platform != 'win32' and not frames_path.startswith(dest_head):
				print "frames_path = %s"%frames_path
				print '    Destination frame path does not starts with %s. Skipped' % (dest_head)
				continue

			print '**running', src_path
			# determine user and group of leginon data
			filename = imdata['filename']
			if sys.platform == 'win32':
				uid, gid = 100, 100
			else:
				stat = os.stat(image_path)
				uid = stat.st_uid
				gid = stat.st_gid
			# make full dst_path
			imname = filename + dst_suffix
			# full path of frames
			dst_path = os.path.join(frames_path, imname)
			print 'Destination path: %s' %  (dst_path)

			# copy reference if possible
			if self.refcopy:
				try:
					self.refcopy.setFrameDir(frames_path, gid, uid)
					self.refcopy.run(imdata, imname)
				except:
					raise
					print 'reference copying error. skip'
			# skip  and clean up finished ones. Needed when the
			# destination user lost write privilege temporarily.
			if os.path.exists(dst_path):
				if os.path.isfile(dst_path):
					# check files to be identical.
					if filecmp.cmp(src_path, dst_path):
						print 'Destination path %s is good, cleaning up source' % dst_path
						os.remove(src_path)
						return
					else:
						print 'Destination path %s not good, redo transfer' % dst_path
						self.cleanUp(dst_path,method)
				#TODO: directory ?
			# do actual copy and delete
			self.transfer(src_path, dst_path, uid, gid, method, mode_str)
			# de only
			leginon.ddinfo.saveImageDDinfoToDatabase(imdata,os.path.join(dst_path,'info.txt'))
			# falcon3 only, xml file transfer
			xml_src_path = src_path.replace('mrc','xml')
			xml_dst_path = dst_path.replace('mrc','xml')
			if os.path.exists(xml_src_path):
				self.transfer(xml_src_path, xml_dst_path, uid, gid, method, mode_str)

	def run(self):
		self.params = self.parseParams()
		src_path = self.get_source_path()
		print 'Source path:  %s' % (src_path,)
		dst_head = self.get_dst_head()
		if dst_head:
			print "Limit processing to destination frame path started with %s" % (dst_head)
		while True:
			print 'Iterating...'
			self.run_once(src_path,self.params['camera_host'],dst_head,method=self.params['method'], mode_str=self.params['mode_str'])
			print 'Sleeping...'
			time.sleep(check_interval)


if __name__ == '__main__':
		a = RawTransfer()
		a.run()
