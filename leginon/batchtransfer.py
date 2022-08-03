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

class RawTransfer(filetransfer.FileTransfer):
	def checkOptionConflicts(self,params):
		if params['camera_host']:
			r = leginon.leginondata.InstrumentData(hostname=params['camera_host']).query()
			if not r:
				sys.stderr.write('Camera host %s not in Leginon database\n' % (params['camera_host']))
				sys.exit(1)
		else:
				sys.stderr.write('Must specify camera host for batch transfer\n' % (params['camera_host']))
				sys.exit(1)

	def transfer_dir(self, src_dir, dst_dir, uid, gid, method, mode_str):
		'''
		This function at minimal organize and rename the time-stamped file
		to match the Leginon session and integrated image.  If the source is
		saved on the local drive of the camera computer, rsync (default) is
		used to copy the file off and the time-stamped file on the camera
		local drive removed to make room for more data collection.
		'''
		dirname,basename = os.path.split(os.path.abspath(dst_dir))
		print('transfer directory', src_dir, dst_dir)
		# get path of the session, e.g. /data/frames/joeuser/17nov06a
		sessionpath = os.path.abspath(os.path.join(dirname,'..'))

		self.makeDirWithOwnershipChange(sessionpath,uid,gid)
		self.makeDirWithOwnershipChange(dirname,uid,gid)

		if method == 'rsync' and not self.is_win32:
			# safer method but slower
			self._rsyncWithOwnershipChange(src_dir,dst_dir,uid,gid,method)
		else:
			# move does only rename and therefore will be faster if on the same device
			# but could have problem if dropped during the process between devices.
			src_basedir = os.path.basename(src_dir)
			dst_subdir = os.path.join(dst_dir, src_basedir)
			if os.path.isdir(dst_subdir):
				# shutil.move gives error if the src_basedir of the same
				# name exists on the destination
				files = os.listdir(src_dir)
				# move each files and then remove the src_dir
				for f in files:
					src_path = os.path.join(src_dir, f)
					self.move(src_path, dst_subdir)
				self.removeEmptyFolders(src_dir)
			else:
				self.move(src_dir,dst_dir)

		if mode_str:
			self.changeMode(dst_dir, mode_str, recursive=True)

		# comment out cleanUp here and rely on rsync to do its job
		# and clean up on the next source search iteration.
		# see Issue #10244
		# self.cleanUp(src,method)

	def getSessionImageMaps(self):
		cam_host = self.params['camera_host']
		time_limit = '-%d 0:0:0' % self.params['check_days']
		all_sessions = leginon.leginondata.SessionData().query(timelimit=time_limit)
		sessions = {}
		for s in all_sessions:
			qccd = leginon.leginondata.InstrumentData(hostname=cam_host)
			qcam = leginon.leginondata.CameraEMData(ccdcamera=qccd, session=s)
			qcam['save frames'] = True
			qcam['align frames'] = False
			images_with_frame = leginon.leginondata.AcquisitionImageData(camera=qcam).query()
			images={}
			for a in images_with_frame:
				images[a['camera']['frames name']] = a
			if images:
				print(s['name'],len(images))
				sessions[s['name']] = images
		return sessions	

	def getAndValidatePath(self,key):
		pathvalue = self.params[key]
		if pathvalue and not os.access(pathvalue, os.R_OK):
			sys.stderr.write('%s not exists or not readable\n' % (pathvalue,))
			sys.exit(1)
		return pathvalue

	def get_source_path(self):
		return self.getAndValidatePath('source_path')

	def get_dst_head(self):
		return self.getAndValidatePath('dest_path_head')

	def getSessionFramePath(self, session_name):
		sessionq = leginon.leginondata.SessionData(name=session_name)
		imdata = leginon.leginondata.AcquisitionImageData(session=sessionq).query(results=1)[0]
		image_path = imdata['session']['image path']
		frames_path = imdata['session']['frame path']
		# use buffer frame path
		# buffer server has access to both permanent and buffer frame path.
		# Must be specific here.
		if leginon.ddinfo.getUseBufferFromImage(imdata):
			frames_path = leginon.ddinfo.getBufferFrameSessionPathFromImage(imdata)

		# back compatible to sessions without frame path in database
		if image_path and not frames_path and sys.platform != 'win32':
			frames_path = leginon.ddinfo.getRawFrameSessionPathFromSessionPath(image_path)
		return frames_path

	def get_src_filenames(self, parent_src_path):
		names = os.listdir(parent_src_path)
		for name in names:
			src_path = os.path.join(parent_src_path, name)
			_, ext = os.path.splitext(name)
			# skip expired dirs, mrcs
			if name in expired_names:
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

	def determineFramesName(self, name):
		_, ext = os.path.splitext(name)
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
		return frames_name, dst_suffix

	def getFrameFileMap(self, parent_src_path):
		names = os.listdir(parent_src_path)
		frame_files = {}
		for name in names:
			src_path = os.path.join(parent_src_path, name)
			_, ext = os.path.splitext(name)
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

			# get frames name to query
			frames_name, dst_suffix = self.determineFramesName(name)
			## ensure a trailing / on directory
			if os.path.isdir(src_path) and src_path[-1] != os.sep:
				src_path = src_path + os.sep
			frame_files[frames_name] = {'dir':parent_src_path,
													'name':name,
													'suffix':dst_suffix,
			}
		return frame_files

	def getIntersectionImages(self, image_map, file_map):
		imkeys = set(image_map.keys())
		filekeys = file_map.keys()
		goods = imkeys.intersection(filekeys)
		return map((lambda x: {'image':image_map[x],'file':file_map[x]}), goods)

	def validateDst(self, session_name, dst_head):
		frames_path = self.getSessionFramePath(session_name)
		if sys.platform != 'win32' and not frames_path.startswith(dst_head):
			return False
		else:
			return frames_path

	def runSession(self, session_name, image_file_maps, method, mode_str):
		# 1. make sure destination is valid from params
		dst_head = self.get_dst_head()
		frames_path = self.validateDst(session_name, dst_head)
		if frames_path is False:
			return
		# 2. if there are files in src_path, put them in a directory named by session_name
		if image_file_maps:
			self._moveToSrcSession(session_name, image_file_maps, frames_path)
		# 3. if there are files in src_session_dir, transfer them
		src_path = self.get_source_path()
		src_session_dir = os.path.join(src_path,session_name)
		dst_tmp_dir = os.path.join(frames_path,'tmp')
		if os.path.isdir(src_session_dir):
			self._transferSrcSessionToDstTmp(src_session_dir, dst_tmp_dir, method, mode_str)
		# 4. check and move files in dst_tmp_dir/session_name to the final location.
		self._moveDstTmpToFramesDir(session_name, dst_tmp_dir, frames_path)

	def _moveToSrcSession(self, session_name, image_file_maps, frames_path):
		first = list(image_file_maps)[0]
		dst_suffix = first['file']['suffix']
		imdata = first['image']
		image_path = imdata['session']['image path']
		uid, gid = self._getUidGid(imdata)
		# move to a session temp directory on the same disk and then
		# transfer since rsync is faster when doing the whole directory.
		print('name changing and moved to the src_tmp_dir')
		src_tmp_dir = os.path.join(first['file']['dir'],session_name)
		pyami.fileutil.mkdirs(src_tmp_dir)
		for m in image_file_maps:
			mfile=m['file']
			filename = m['image']['filename']
			dst_frame_name = filename + dst_suffix
			src_path = os.path.join(mfile['dir'],mfile['name'])
			src_tmp_frame_path = os.path.join(src_tmp_dir, dst_frame_name)
			self.move(src_path, src_tmp_frame_path)
			# copy reference if possible
			if self.refcopy:
				try:
					self.refcopy.setFrameDir(frames_path, gid, uid)
					self.refcopy.run(imdata, dst_frame_name)
				except:
					print('reference copying error. skip')
			# de only  TODO: Not sure if the path is correct
			info_path = os.path.join(src_tmp_frame_path,'info.txt')
			if os.path.isfile(info_path):
				imdata = leginon.leginondata.AcquisitionImageData().direct_query(m[0]) # image id
				leginon.ddinfo.saveImageDDinfoToDatabase(imdata,info_path)
			# falcon3 only, xml file transfer
				xml_src_path = src_path.replace('mrc','xml')
				xml_src_tmp_path = src_tmp_frame_path.replace('mrc','xml')
				if os.path.exists(xml_src_path):
					self.move(xm_src_path, xml_src_tmp_path)

	def _transferSrcSessionToDstTmp(self, src_session_dir, dst_tmp_dir, method, mode_str):
		files = os.listdir(src_session_dir)
		first = False
		for f in files:
			try:
				first = leginon.leginondata.AcquisitionImageData(filename=f.split('.')[0]).query(results=1)[0]
				image_path = first['session']['image path']
				break
			except:
				continue
		if first is False:
			# no frames files to process.  May have other junks
			return
		uid, gid = self._getUidGid(first)
		# move the whole session together.
		print('move dir to the dst_tmp_dir', dst_tmp_dir)
		# make temp dst_path
		pyami.fileutil.mkdirs(dst_tmp_dir)
		self.transfer_dir(src_session_dir, dst_tmp_dir, uid, gid, method, mode_str)
		# the results are in dst_tmp_dir/session_name
		if method == 'rsync':
			# rsync leaves src_session_dir in place.
			try:
				os.rmdir(src_session_dir)
			except Exception as e:
				print('Error removing intermediate files: %s' % e)
			

	def _moveDstTmpToFramesDir(self, session_name, dst_tmp_dir,frames_path):
		#move *.* in dst_tmp_dir backout
		dst_tmp_session_dir = os.path.join(dst_tmp_dir, session_name)
		if not os.path.isdir(dst_tmp_session_dir):
			return
		files = os.listdir(dst_tmp_session_dir)
		for f in files:
			tmp_f = os.path.join(dst_tmp_session_dir, f)
			print('final move from', tmp_f)
			self.move(tmp_f, frames_path)
		# clean up tmp_dir
		os.rmdir(dst_tmp_session_dir)
		os.rmdir(dst_tmp_dir)

	def run(self):
		self.params = self.parseParams()
		method = self.params['method']
		mode_str = self.params['mode_str']
		src_path = self.get_source_path()
		print('Source path:  %s' % (src_path,))
		self.hidden_path = self.get_hidden_path()
		file_map = self.getFrameFileMap(src_path)
		dst_head = self.get_dst_head()
		if dst_head:
			print("Limit processing to destination frame path started with %s" % (dst_head))
		session_maps = self.getSessionImageMaps()
		for session_name in session_maps.keys():
			print('Iterating %s' % (session_name))
			intersection_images = self.getIntersectionImages(session_maps[session_name],file_map)
			self.runSession(session_name,intersection_images,method,mode_str)
		names = os.listdir(src_path)
		for name in names:
			bad_path=os.path.join(src_path, name)
			self.handleBadFile(bad_path, method)

if __name__ == '__main__':
		a = RawTransfer()
		a.run()
