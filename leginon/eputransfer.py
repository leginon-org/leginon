#!/usr/bin/env python
"""
This program transfer EPU session from a mount point
to destination and upload the images and frame movies
to the leginon session with the same name.
It requires that the Atlas created under the session
and then assign EPU data under the same name resulting that
Image-Disc1 is under source_path/session_name/session_name
while Atlas is under source_path/session_name/Atlas
"""
import os
import sys
import shutil
import platform
import subprocess
import time
import datetime
import numpy
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import leginon.leginondata
import leginon.ddinfo
import pyami.fileutil, pyami.mrc, pyami.xmlfun, pyami.numpil
import sinedon.directq
try:
	from leginon import epu_meta
except ImportError:
	# find it locally
	import epu_meta
session_timeout = 60 # seconds before timeout
check_interval = 120  # seconds between checking for new frames
# production usage on linux
watch_for_ext = 'mrc'
is_testing = False

preset_order = ['gr','sq','hl','en']
if platform.system() == 'Darwin':
	# testing on Mac OS
	watch_for_ext = 'jpg'
	session_timeout = 10 # seconds before timeout
	check_interval = 10  # seconds between checking for new frames
	is_testing = True

class RawTransfer(object):
	def __init__(self, is_testing):
		# image classes that will be transferred
		self.image_classes = [
			leginon.leginondata.AcquisitionImageData,
		]

		self.session = None
		self.watch_path = '.'
		self.method = None
		self.handler = self.createEventHandler()
		self.t0 = time.time()
		self.meta = epu_meta.EpuMetaMapping()
		self.frame_meta = epu_meta.EpuFractionMapping()
		self.resetForSession()
		self.walked = []
		self.most_recent_dbid = None
		self.is_testing = is_testing

	def resetForSession(self):
		self.gr = {}
		self.sq = {}
		self.hl = {}
		self.en = {}
		self.atlas_list = []
		#TODO separate tiles from different atlas
		self.tile_shifts = {} 
		self.tiles = {}


	def buildTree(self,file_path):
		global watch_for_ext
		watch_for = watch_for_ext
		if os.path.isdir(file_path):
			return
		bits = file_path.split('/')
		basename = bits[-1]
		basedirname = bits[-2]
		base2dirname = bits[-3]
		if not basename.endswith(watch_for):
			return
		bits2 = basename.split('.')[0].split('_')
		if 'Fractions' in bits2[-1]:
			index = -2
		else:
			index = -1
		datetime_string = '_'.join((bits2[index-1],bits2[index]))
		# en images
		if 'Data' == basedirname and basename.startswith('FoilHole'):
			if watch_for_ext == 'mrc' and 'Fractions' not in basename:
				# both fractions and sum have mrc files. only jpg for sum.
				# don't want sum mrc
				return
			# standard mode has hl_name as the first part
			hl_name = basename.split('_')[1]
			# TODO fast mode has unrelated name. handle later
			parent = hl_name
			en_name = hl_name # TODO: what if multiple exposures in a hole ?
			if en_name not in self.en.keys():
				self.en[en_name]=[]
			version = len(self.en[en_name])
			data = parent, version, file_path, datetime_string, 'en'
			self.en[en_name].append(tuple(data))
			#print("en image %s has been transferred %s" % (en_name,data,))
		# hl images
		if 'FoilHoles' == basedirname and basename.startswith('FoilHole'):
			hl_name = basename.split('_')[1]
			sq_name = bits[-3].split('_')[1]
			parent = sq_name
			if hl_name not in self.hl.keys():
				self.hl[hl_name]=[]
			version = len(self.hl[hl_name])
			data = parent, version, file_path, datetime_string, 'hl'
			self.hl[hl_name].append(tuple(data))
			#print("hl image %s has been transferred" % (data,))
		if basename.startswith('GridSquare'):
			sq_name = basedirname.split('_')[1]
			parent = None
			if sq_name not in self.sq.keys():
				self.sq[sq_name]=[]
			version = len(self.sq[sq_name])
			data = parent, version, file_path, datetime_string, 'sq'
			self.sq[sq_name].append(tuple(data))
			#print("sq image %s has been transferred" % (data,))
			
		if basename.startswith('Tile'):
			gr_name = basename.split('_')[1]
			parent = None
			if gr_name not in self.gr.keys():
				self.gr[gr_name]=[]
			version = int(basename.split('_')[2])
			# does not come with datetime_string. Use as early as possible.
			datetime_string = '20200101_000%03d' % version
			data = parent, version, file_path, datetime_string, 'gr'
			self.gr[gr_name].append(tuple(data))
			print("gr image %s:%s has been transferred" % (gr_name,data,))
			atlas_name = base2dirname
			if atlas_name not in self.atlas_list:
				self.atlas_list.append(atlas_name)
				self.tiles[atlas_name] = []
				self.tile_shifts[atlas_name] = []
			

	def on_moved(self,event):
		"""
		rsync temporary file get moved to mrc.
		"""
		self.buildTree(event.dest_path)

	def on_created(self,event):
		"""
		rsync create grid square directory.
		"""
		if not event.is_directory:
			self.buildTree(event.src_path)
			return
		basename = event.src_path.split('/')[-1]
		if not basename:
			basename = event.src_path.split('/')[-2]
		if 'GridSquare' in basename:
			print("A grid square directory %s has been added" % (event.src_path,))

	def createEventHandler(self):
		my_handler = PatternMatchingEventHandler("*","",False,True)
		my_handler.on_moved = self.on_moved
		my_handler.on_created = self.on_created
		return my_handler

	def createObserver(self):
		my_observer = Observer()
		my_observer.schedule(self.handler, self.watch_path, recursive=True)
		return my_observer

	def parseParams(self):
		'''
		Use OptionParser to get parameters
		'''
		global check_interval
		from optparse import OptionParser

		parser = OptionParser()

		# options
		parser.add_option("--method", dest="method",
			help="method to transfer, e.g. --method=rsync", type="choice", choices=['rsync','walk'], default='rsync')
		parser.add_option("--source_path", dest="source_path",
			help="Mounted parent path to transfer, e.g. --source_path=/mnt/ddframes", metavar="PATH")
		parser.add_option("--destination_head_epu", dest="dest_path_head_epu",
			help="Specific a temporary head destination for epu session to transfer to , e.g. --destination_head_epu=/data1", metavar="PATH", default='')
		parser.add_option("--path_mode", dest="mode_str", 
			help="recursive session permission modification by chmod if specified, default means not to modify e.g. --path_mode=g-w,o-rw")
		parser.add_option("--check_interval", dest="check_interval", help="Seconds between checking for new frames", type="int", default=check_interval)

		# parsing options
		(options, optargs) = parser.parse_args(sys.argv[1:])
		if len(optargs) > 0:
			print "Unknown commandline options: "+str(optargs)
		if len(sys.argv) < 2:
			parser.print_help()
			sys.exit()
		params = {}
		for i in parser.option_list:
			if isinstance(i.dest, str):
				params[i.dest] = getattr(options, i.dest)
		self.checkOptionConflicts(params)
		# set global variable check_interval
		check_interval = options.check_interval
		return params

	def checkOptionConflicts(self,params):
		if not params['dest_path_head_epu']:
			sys.stderr.write('Must specify dest_path_head_epu\n')
			sys.exit(1)

	def getAndValidatePath(self,key):
		pathvalue = self.params[key]
		if pathvalue and not os.access(pathvalue, os.R_OK):
			sys.stderr.write('%s not exists or not readable\n' % (pathvalue,))
			sys.exit(1)
		return pathvalue

	def get_source_path(self):
		return self.getAndValidatePath('source_path')

	def get_dst_head(self):
		return self.getAndValidatePath('dest_path_head_epu')

	def cleanUp(self,src):
		abspath = os.path.abspath(src)
		print 'clean up %s from linux' % (abspath)
		if os.path.isdir(abspath) and not os.path.islink(abspath):
			shutil.rmtree(abspath)
			return
		if os.path.isfile(abspath):
			shutil.path.remove(abspath)

	def copy(self,src, dst):
		'''
		Use rsync to copy the files.  The sent files are not removed
		after copying because epu might need it.
		'''
		cmd = 'rsync -av %s %s' % (src, dst)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def move(self,src, dst):
		'''
		Use shutil's move to rename frames
		'''
		######filedir operation########
		print 'moving %s -> %s' % (src, dst)
		shutil.move(src, dst)

	def makeDir(self,dirname):
		print('mkdirs %s'%dirname)
		if not os.path.exists(dirname):
			# this function preserves umask of the parent directory
			pyami.fileutil.mkdirs(dirname)
		elif os.path.isfile(dirname):
			print("Error %s is a file"%dirname)

	def changeOwnership(self,uid,gid,dirname):
		# change ownership of desintation directory and contents
		cmd = 'chown -R %s:%s %s' % (uid, gid, dirname)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def changeMode(self,path,mode_str='g-w,o-rw'):
		# only works on linux
		cmd = 'chmod -R %s %s' % (mode_str, path)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def transferOwner(self, dst, uid, gid, mode_str):
		'''
		transfer ownership of the session path, whether the input is frame or image
		or the directory (rawdata) containing them
		'''
		if os.path.isfile(dst):
			# get path of the session, e.g. /data/frames/joeuser/17nov06a
			dirname,basename = os.path.split(os.path.abspath(dst))
		else:
			# already /data/frames/joeuser/17nove06a/rawdata
			dirname = os.path.abspath(dst)
		sessionpath = os.path.abspath(os.path.join(dirname,'..'))

		self.changeOwnership(uid,gid,sessionpath)
		if mode_str:
			self.changeMode(sessionpath, mode_str)

	def getSessionFramePath(self, imdata):
		'''
		Get frame path.  This returns either frame path in SessionData or
		buffer frame path in BufferFramePathData.
		'''
		image_path = imdata['session']['image path']
		frames_path = imdata['session']['frame path']

		# use buffer frame path
		# buffer server has access to both permanent and buffer frame path.
		# Must be specific here.
		if leginon.ddinfo.getUseBufferFromImage(imdata):
			frames_path = leginon.ddinfo.getBufferFrameSessionPathFromImage(imdata)
		return frames_path

	def addSavedAtlasList(self):
		'''
		Attempt to add atlas_list
		'''
		q = leginon.leginondata.ImageTargetListData(session=self.session,mosaic=True)
		q['label'] = 'U'
		r = q.query()
		if r:
			# atlas was saved in a previous round
			# TODO: This is supposed to be the name of atlas in epu, so it is not always right.
			atlas_name = self.session['name']
			self.atlas_list.append(atlas_name)
			# empty list here triggers loadTileShifts when sq images looking for closest tile to associate.
			self.tiles[atlas_name] = []
			self.tile_shifts[atlas_name] = []
		# TODO: This does not handle screening Sample atlas

	def upload(self):
		'''
		Upload the images recorded in this round of transfer.
		These images are in the same session
		'''
		sorted_epu_infopairs = self.sortEpuInfoPairs()
		self.presets, self.preset_matrices = self.createPresets()
		if not self.atlas_list:
			# self.atlas_list is reset to empty after each run_once. This initiate them again.
			self.addSavedAtlasList()
		self.atlas_image_target_lists = self.makeAtlasImageTargetLists()

		some_uploaded = False
		for epu_infopair in sorted_epu_infopairs:
			presetdata = self.presets[epu_infopair[1][-1]]
			self.tem = presetdata['tem']
			self.ccdcamera = presetdata['ccdcamera']
			# returns imagedata if upload is performed.
			uploaded_image = self.uploadOne(epu_infopair[0], epu_infopair[1], presetdata)
			if not some_uploaded and uploaded_image:
				some_uplodated = uploaded_image
		if some_uploaded:
			# tasks to do if some upload was performed
			self.setOwner(self.session['image path'])
			frames_path = self.getSessionFramePath(some_uploaded)
			self.setOwner(frames_path)
			# reset timeout timer
			self.t0 = time.time()

	def makeAtlasImageTargetLists(self):
		'''
		Create or get ImageTargetListData with moasict=True.
		ImageTargetListData with mosaic=True means it is an atlas.
		Simplify the names.
		'''
		all_dict = {}
		for name in self.atlas_list:
			q = leginon.leginondata.ImageTargetListData(session=self.session)
			if name.lower() == self.session['name']:
				# those under session name is the default.  Does not need a name.
				q['label'] = 'U'
			else:
				# those under SampleX is autoscreen.
				q['label'] = name.replace('Sample','S')
			q['mosaic'] = True
			r = q.query()
			if not r:
				nq = leginon.leginondata.ImageTargetListData(initializer=q)
				nq.insert()
				all_dict[name] = nq
				ilq = leginon.leginondata.ImageListData(session=self.session,targets=nq)
				ilq.insert()
			else:
				all_dict[name] = r[0]
		return all_dict

	def sortEpuInfoPairs(self):
		'''
		Sort EpuInfo so that upload is in the same order as the datetime_string
		Returns epukey,epuinfo as a pair
		'''
		all_info_list = []
		all_time_info_dict = {}
		for attr_name in preset_order:
			this_attr = getattr(self,attr_name)
			for epukey in this_attr.keys():
				time_info_dict = {}
				epuinfos = this_attr[epukey]
				for epuinfo in epuinfos:
					parent, version, file_path, datetime_string, preset_name = epuinfo
					time_info_dict[datetime_string] = [epukey,list(epuinfo)]
				time_list = time_info_dict.keys()
				time_list.sort()
				for i, t in enumerate(time_list):
					# version may be wrong from multi-threading on_moved.
					time_info_dict[t][1][1] = i
					all_time_info_dict[t] = time_info_dict[t]
		all_time_list = all_time_info_dict.keys()
		all_time_list.sort()
		for t in all_time_list:
			all_info_list.append(all_time_info_dict[t])
		return all_info_list

	def getOwnership(self):
		# determine user and group of leginon data
		# rawdata directory is not created if no image is saved in the session, yet.
		session_path = self.session['image path'].replace('/rawdata','')
		stat = os.stat(session_path)
		uid = stat.st_uid
		gid = stat.st_gid
		return uid, gid

	def createPresets(self):
		global preset_order
		presets = {}
		matrices = {}
		for p in preset_order:
			this_attr = getattr(self,p)
			if not this_attr:
				# some rounds of rsync might not have all presets when running live.
				presets[p] = self.getSavedPresetData(p)
				matrices[p] = self.getSavedEpuMatrix(presets[p])
			else:
				# use the matrix of the first entry. matrix is not changed within the session.
				epuinfo = this_attr[list(this_attr.keys())[0]][0]
				is_success = self.setMetaDict(epuinfo)
				if is_success is not False:
					presets[p] = self._setPresetData(p)
					matrices[p] = self.setEpuMatrixFromMeta(presets[p])
				else:
					# xml might not exists in the temp directory, yet
					presets[p] = self.getSavedPresetData(p)
					matrices[p] = self.getSavedEpuMatrix(presets[p])
		return presets, matrices

	def getSavedPresetData(self, preset_name):
		'''
		Get existing PresetData in leginondata
		'''
		q = leginon.leginondata.PresetData(session=self.session,name=preset_name)
		r = q.query(results=1)
		if r:
			return r[0]
		else:
			return None
		
	def getSavedEpuMatrix(self, presetdata):
		'''
		Get existing EpuMatrixData in leginondata
		'''
		if not presetdata:
			return None
		# This query is fairly relaxed.  Allowing matrix from other sessions
		# to be used if no new record from this session exists.
		q = leginon.leginondata.EpuMatrixData()
		q['preset name'] = presetdata['name']
		q['magnification'] = presetdata['magnification']
		r = q.query(results=1)
		if r:
			return r[0]['matrix']
		else:
			return None
		
	def setEpuMatrixFromMeta(self, presetdata):
		'''
		Get EpuMatrix from xml file associated with the current image.
		'''

		matrix = self._setPresetMatrixFromMeta()
		# save matrix
		q = leginon.leginondata.EpuMatrixData(session=self.session)
		q['preset name'] = presetdata['name']
		q['magnification'] = presetdata['magnification']
		q['matrix'] = matrix
		q.insert()
		return matrix

	def _setPresetMatrixFromMeta(self):
		'''
		Set preset transformation matrix based on meta_data_dict
		'''
		m_dict = self.meta.getMatrix(self.meta.meta_data_dict)['m']
		matrix = numpy.array([[m_dict['m11'],m_dict['m12']],
													[m_dict['m21'],m_dict['m22']]])
		return matrix

	def _setPresetData(self, preset_name):
		'''
		Create preset based on meta_data_dict
		'''
		global preset_order
		# We don't care about preset change in EPU session
		r = leginon.leginondata.PresetData(session=self.session,name=preset_name).query(results=1)
		if r:
			return r[0]
		tem = self.getInstrumentData('tem')
		ccdcamera = self.getInstrumentData('ccdcamera')
		# cameradict happens to be just what we need
		cameradict = self.meta.getCameraEMData(self.meta.meta_data_dict['microscopeData'])
		q = leginon.leginondata.PresetData(initializer=cameradict)
		q['session'] = self.session
		q['name'] = preset_name
		q['tem'] = tem
		q['ccdcamera'] = ccdcamera
		scopedict = self.meta.getScopeEMData(self.meta.meta_data_dict['microscopeData'])
		for k in q.keys():
			if k in scopedict.keys():
				q[k] = scopedict[k]
		if not preset_name in preset_order:
			preset_order.apend(preset_name)
		q['number'] = preset_order.index(preset_name)
		q.insert()
		return q
	
	def uploadOne(self, epukey, epuinfo, presetdata): 
		'''
		Upload one image or movie.
		'''
		ready_status = self.setMetaDict(epuinfo)
		if ready_status == False:
			# xml not found.
			return
		print epukey
		print epuinfo
		uploaded_imagedata = self.alreadyUploaded(epukey, epuinfo, presetdata['name'])
		if uploaded_imagedata:
			#already uploaded. nothing to do
			print 'already uploaded'
			return
		parent_imagedata = self.findParentImageData(epuinfo,presetdata['name'])
		if parent_imagedata is False and presetdata['name'] != 'en':
			#parent not uploaded. do this later.
			return
		if parent_imagedata in (None,False) and presetdata['name'] == 'en':
			recent_hl_epudata = self.getClosestHlEpuData(epuinfo)
			if not recent_hl_epudata:
				# not any hl images yet
				return
			epuinfo[0] = recent_hl_epudata['name']
			parent_imagedata = recent_hl_epudata['image']
			print 'assign orphan en image to %s: v%d' %(epuinfo[0], recent_hl_epudata['version'])
		print epukey,epuinfo
		scopedata = self.makeScopeEMData(epuinfo)
		cameradata = self.makeCameraEMData(epuinfo)
		try:
			targetdata = self.makeTargetData(epukey, epuinfo, scopedata, cameradata, parent_imagedata)
		except ValueError, e:
			# give up and try later.
			print e
			return
		# ImageListData needed for myamiweb display of atlas
		imagelistdata = self.getImageListData(targetdata)
		new_filename = self.makeFilename(targetdata,presetdata['name'])
		print new_filename
		q=leginon.leginondata.AcquisitionImageData(session=self.session)
		q['scope'] = scopedata
		q['camera'] = cameradata
		q['preset'] = presetdata
		q['target'] = targetdata
		q['list'] = imagelistdata
		q['filename'] = new_filename
		if targetdata:
			print 'inserting %s with target %d' % (q['filename'],q['target'].dbid)
		# reading image
		q['image'] = self.getImageArray(epuinfo[2],q)
		q.insert()
		self.setOwner(os.path.join(self.session['image path'],q['filename']+'.mrc'))
		# mosaic tile
		if q['target']['list'] and q['target']['list']['mosaic']:
			self. saveMosaicTile(q)
		self.insertEpuData(epukey, epuinfo, q)
		return q

	def getClosestHlEpuData(self,epuinfo):
		'''
		Force assignment of en image to a hole already uploaded.
		'''
		qp = leginon.leginondata.PresetData(session=self.session,name='hl')
		qt = leginon.leginondata.AcquisitionImageTargetData(session=self.session)
		imq = leginon.leginondata.AcquisitionImageData(preset=qp, target=qt)
		epu_results = leginon.leginondata.EpuData(image=imq).query()
		epu_r = []
		all_delta_list = []
		for r in epu_results:
			stage_hl = r['image']['scope']['stage position']
			scopedict = self.meta.getScopeEMData(self.meta.meta_data_dict['microscopeData'])
			stage_delta = scopedict['stage position']['x']-stage_hl['x'], scopedict['stage position']['y']-stage_hl['y']
			all_delta_list.append(stage_delta)
		if not all_delta_list:
			return None
		if len(all_delta_list) > 1:
			deltas = numpy.array(all_delta_list).reshape((len(all_delta_list),2))
			hypot = numpy.sum(deltas*deltas,axis=1)
			closest_index = numpy.argmin(hypot)
			best = epu_results[closest_index]
		else:
			best = epu_results[0]
		# find most recent of it
		newest = best
		results = leginon.leginondata.EpuData(name=best['name'],session=self.session).query()
		for r in results:
			if r['version'] > best['version']:
				newest = r
		return newest

	def setOwner(self, dst):
		self.transferOwner(dst, self.uid, self.gid, self.params['mode_str'])

	def getImageArray(self, filepath, imageq):
		'''
		Read 2D image array for upload.  Sum if a movie.  Also moves
		the frame movie in this function.
		'''
		ext = filepath.split('.')[-1]
		if ext == 'jpg':
			return pyami.numpil.read(filepath)
		elif ext == 'mrc':
			nz = pyami.mrc.readHeaderFromFile(filepath)['nz']
			if nz > 1:
				# frames
				sum_array = pyami.mrc.sumStack(filepath)
				frames_path = self.getSessionFramePath(imageq)
				self.makeDir(frames_path) # This is the frames/SESSION/rawdata directory
				# need to copy otherwise rsync of the falcon server will repeat.
				dst_file_path = os.path.join(frames_path,imageq['filename']+'.frames.mrc')
				self.copy(filepath, dst_file_path)
				self.setOwner(dst_file_path)
				return sum_array
			else:
				return pyami.mrc.read(filepath)
		else:
			raise ValueError('unknown file extension %s' % ext)

	def insertEpuData(self, epukey, epuinfo, imagedata):
		parent, version, file_path, datetime_string, preset_name = epuinfo
		epuq = leginon.leginondata.EpuData(session=self.session)
		epuq['name'] = epukey
		epuq['preset name'] = imagedata['preset']['name']
		epuq['datetime_string'] = datetime_string
		epuq['version'] = version
		epuq['image'] = imagedata
		epuq['parent'] = self.getParentEpuData(parent,imagedata)
		epuq.insert()
		return epuq

	def getParentEpuData(self, parent_epukey, imagedata):
		epuq = leginon.leginondata.EpuData(session=self.session)
		epuq['name'] = parent_epukey
		epuq['image'] = imagedata['target']['image']
		r = epuq.query(results=1)
		if r:
			return r[0]
		else:
			return None

	def makeFilename(self, targetdata, preset_name):
		'''
		Make filename based on parent, target number, and target version
		'''
		if 'image' in targetdata.keys() and targetdata['image']:
			parentname = targetdata['image']['filename']
		else:
			parentname = self.session['name']
		if 'list' in targetdata.keys() and targetdata['list'] and targetdata['list']['mosaic'] and targetdata['list']['label']:
			parentname += "_%s" % (targetdata['list']['label'],)
		target_name = '%05d%s' % (targetdata['number'], preset_name)
		filename = '_'.join([parentname,target_name])
		if targetdata['version'] > 0:
			filename += '_v%02d' % targetdata['version']
		# validate the name:
		r = leginon.leginondata.AcquisitionImageData(session=self.session,filename=filename).query()
		if r:
			raise KeyboardInterrupt('Same file as image %d' % r[0].dbid)
		return filename

	def setMetaDict(self, epuinfo):
		parent, version, file_path, datetime_string, preset_name = epuinfo
		#TODO Fractions xml reads different info.
		#temporary jpg
		global watch_for_ext
		xml_file_path = file_path.replace('.'+watch_for_ext,'.xml')
		if 'Fractions' in xml_file_path:
			self.frame_meta.setXmlFile(xml_file_path)
			meta_xml_file = xml_file_path.replace('_Fractions','')
			if os.path.exists(meta_xml_file):
				self.meta.setXmlFile(meta_xml_file)
			else:
				bits = meta_xml_file.split('/Images-Disc')
				epu_session_name = bits[0].split('/')[-1]
				# convention to save epu session under supfolder of the same session name
				new_path = '%s/%s' % (bits[0],epu_session_name)
				bits[0] = new_path
				new_meta_xml_file = '/Images-Disc'.join(bits)
				if os.path.exists(new_meta_xml_file):
					self.meta.setXmlFile(new_meta_xml_file)
				else:
					bits = new_meta_xml_file.split('/Images-Disc')
					epu_session_name = bits[0].split('/')[-1]
					# convention to save epu session under supfolder of the same session name
					new_new_path = '%s/%s' % (bits[0],epu_session_name)
					bits[0] = new_new_path
					new_new_meta_xml_file = '/Images-Disc'.join(bits)
					if os.path.exists(new_meta_xml_file):
						self.meta.setXmlFile(new_meta_xml_file)
					if self.method == 'walk':
						# In walk method if xml file is not there, this one would be lost.
						return False
					# try again later.
					print('Can not find acquisition meta file as %s or %s or %s' % (meta_xml_file, new_meta_xml_file, new_new_meta_xml_file))
					return False
		else:
			wait_iter = 0
			while not os.path.isfile(xml_file_path):
				if self.method == 'walk':
					return False
				if wait_iter >9:
					print 'waiting for too long'
					return False
				print ('waiting for xml file %s....' % (xml_file_path))
				time.sleep(1)
				wait_iter += 1
			self.meta.setXmlFile(xml_file_path)
		return True

	def getInstrumentData(self, instrument_ref='tem'):
		if instrument_ref == 'tem':
			init_dict = self.meta.getTemData(self.meta.meta_data_dict['microscopeData'])
		else:
			init_dict = self.meta.getCCDCameraData(self.meta.meta_data_dict['microscopeData'])
		r = leginon.leginondata.InstrumentData(initializer=init_dict).query(results=1)
		if not r:
			raise ValueError('Can not get %s' % instrument_ref)
		return r[0]

	def updateDataTimeStamp(self,data,datetime_string):
		class_name = data.__class__.__name__
		d = datetime_string.split('_')[0]
		t = datetime_string.split('_')[1]
		timestamp_string = '%s-%s-%s %s:%s:%s.000000' % (d[:4],d[4:6],d[6:8],t[:2],t[2:4],t[4:6])
		q = "UPDATE `%s` SET `DEF_timestamp` = '%s' where `DEF_id`=%s" % (class_name, timestamp_string, data.dbid)
		sinedon.directq.complexMysqlQuery('leginondata', q)

	def makeScopeEMData(self, epuinfo):
		data_dict = self.meta.getScopeEMData(self.meta.meta_data_dict['microscopeData'])
		scopedata = leginon.leginondata.ScopeEMData(initializer=data_dict)
		scopedata['session']=self.session
		scopedata['tem']=self.tem
		if self.tem['name'].startswith('Diffr'):
			scopedata['projection mode'] = 'diffraction'
		else:
			scopedata['projection mode'] = 'imaging'

		scopedata.insert(force=True)
		parent, version, file_path, datetime_string, preset_name = epuinfo
		self.updateDataTimeStamp(scopedata,datetime_string)
		# redo the query so the timestamp is updated
		return leginon.leginondata.ScopeEMData().direct_query(scopedata.dbid)

	def makeCameraEMData(self, epuinfo):
		data_dict = self.getCameraEMDict(epuinfo)
		cameradata = leginon.leginondata.CameraEMData(initializer=data_dict)
		cameradata['session']=self.session
		cameradata['ccdcamera']=self.ccdcamera
		#TODO set senser pixelsize
		if 'K2' in self.ccdcamera['name']:
			cameradata['pixel size']={'x':5e-6,'y':5e-6}
		elif 'K3' in self.ccdcamera['name']:
			cameradata['pixel size']={'x':2.5e-6,'y':2.5e-6}
		else:
			# default to Ceta Falcon pixel size
			cameradata['pixel size']={'x':1.4e-5,'y':1.4e-5}
		if data_dict['save frames'] == True:
			# add frames name here since cameradict in PresetData does not need this.
			parent, version, file_path, datetime_string, preset_name = epuinfo
			cameradata['frames name'] = os.path.basename(file_path).split('.')[0]
		return cameradata

	def findParentImageData(self, epuinfo, preset_name):
		global preset_order
		parent, version, file_path, datetime_string, preset_name = epuinfo
		if parent:
			index = preset_order.index(preset_name)
			if index == 0:
				raise ValueError('parent preset of gr not possible')
			parent_preset_name = preset_order[index-1]
			q = leginon.leginondata.EpuData(session=self.session, name=parent)
			q['preset name'] = parent_preset_name
			r=q.query()
			if not r:
				print 'no parent epu data',self.session['name'],parent, index, parent_preset_name
				return False
			else:
				return r[0]['image']
		else:
			# No parent
			return None

	def saveMosaicTile(self, imagedata):
		'''
		Save tiles for atlas display.
		'''
		q = leginon.leginondata.MosaicTileData(session=self.session)
		q['image'] = imagedata
		q['list'] = imagedata['list']
		q.insert()
		return q
	def getImageListData(self, targetdata):
		'''
		Get existing ImageListData.  Used for making atlas in imageviewer.
		'''
		if targetdata['list']:
			r = leginon.leginondata.ImageListData(session=self.session, targets=targetdata['list']).query()
			if r:
				return r[0]
		return None
	
	def makeTargetData(self, epukey, epuinfo, scopedata, cameradata, parent_imagedata):
		parent, version, file_path, datetime_string, preset_name = epuinfo
		qt = leginon.leginondata.AcquisitionImageTargetData(session=self.session)
		qt['type']='acquisition'
		qt['status']='done'
		if parent_imagedata:
			if self.method == 'copy' and preset_name == 'en' and parent_imagedata['target']['version']==0:
				# different versions of hl images may not all get copied before its en.
				raise ValueError('en should come from higher version than 0')
			pixel_shift = self.getTargetPixelShift(parent_imagedata, scopedata)
			qt['delta row'] = pixel_shift[1]
			qt['delta column'] = pixel_shift[0]
			qt['image'] = parent_imagedata
			new_number,new_version = self.getTargetNumberVersion(parent_imagedata, epukey, preset_name, version)
			qt['number'] = new_number
			qt['version'] = new_version
			# need these to display footprint in viewer
			qt['camera'] = parent_imagedata['camera']
			qt['scope'] = parent_imagedata['scope']
		else:
			# no new version if no parent
			# fake position
			qt['delta row'] = 0
			qt['delta column'] = 0
			qt['version'] = 0
			bits = file_path.split('/')
			if preset_name == 'gr' and bits[-2] == 'Atlas':
				atlas_name = bits[-3]
				print 'atals_name from path', atlas_name, file_path
				if atlas_name in self.atlas_list:
					# ImageTargetListData needed to display in myamiweb
					qt['list'] = self.atlas_image_target_lists[atlas_name]
					fake_parent_image = self.makeGridReferenceImageData()
					qt['scope'] = fake_parent_image['scope']
					qt['camera'] = fake_parent_image['camera']
					pixel_shift = self.getTargetPixelShift(fake_parent_image, scopedata)
					qt['delta row'] = pixel_shift[1]
					qt['delta column'] = pixel_shift[0]
					qt['number']= self.getNoParentTargetNumber(qt)
					# Save shifts for finding square image relation
					self.tile_shifts[atlas_name].append(pixel_shift)
					self.tiles[atlas_name].append(epukey)
				else:
					raise ValueError('Can not find %s atlas this tile (epu_id=%s) belongs to' % (atlas_name,epukey))
			elif preset_name == 'sq':
				try:
					# set parent image to the closest tile if found
					fake_parent_image = self.makeGridReferenceImageData()
					qt['scope'] = fake_parent_image['scope']
					pixel_shift = self.getTargetPixelShift(fake_parent_image, scopedata)
					parent_imagedata, pixel_shift = self.findClosestTile(pixel_shift)
					if parent_imagedata:
						qt['scope'] = parent_imagedata['scope']
						qt['camera'] = parent_imagedata['camera']
					qt['image'] = parent_imagedata
					qt['delta row'] = pixel_shift[1]
					qt['delta column'] = pixel_shift[0]
					new_number, new_version= self.getTargetNumberVersion(parent_imagedata, epukey, preset_name, qt['version'])
					qt['number'] = new_number
					qt['version'] = new_version
					pixel_shift = self.getTargetPixelShift(parent_imagedata, scopedata)
					# need these to display footprint in viewer
					qt['camera'] = parent_imagedata['camera']
					qt['scope'] = parent_imagedata['scope']
					# Don't save ImageTargetListData. It would make loadTileShifts goes wrong.
				except (ValueError, KeyError) as e:
					qt['list'] = self.getSimulatedTargetList(preset_name)
					qt['number']= self.getNoParentTargetNumber(qt)
			else:
				qt['list'] = self.getSimulatedTargetList(preset_name)
				qt['number']= self.getNoParentTargetNumber(qt)
		qt.insert()
		return qt

	def findClosestTile(self, pixel_shift):
		'''
		Choose a tile that has shortest distance from the pixel_shift
		relative to the center of the stage coordinates on the sample scale.
		'''
		session_atlas = None
		print 'atlas_list before loading', self.atlas_list
		for atlas_name in self.atlas_list:
			if atlas_name.lower() == self.session['name']:
				session_atlas = atlas_name
				break
		if session_atlas is None:
			raise ValueError('We can only handle atlas named as session now')
		tile_shifts = self.tile_shifts[atlas_name]
		if not tile_shifts:
			# already uploaded in previous round.
			self.loadTileShifts(atlas_name)
			tile_shifts = self.tile_shifts[atlas_name]
		print 'atlas_list after loadTileShifts', self.atlas_list
		tile_length = len(tile_shifts)
		if not tile_length:
			print 'No tiles found'
			raise RuntimeError('Can not find tiles')
		# pixel_shift is numpy.matrix
		pixel_shifts_array = numpy.array(tile_length*pixel_shift.tolist())
		tiles = numpy.array(tile_shifts).reshape((tile_length,2))
		sq=pixel_shifts_array.reshape((tile_length,2))
		hypot = numpy.sum((tiles-sq)*(tiles-sq),axis=1)
		on_tile_index = numpy.argmin(hypot)
		print 'tile keys', self.tiles.keys()
		print 'atlas_name', atlas_name
		print self.tiles[atlas_name]
		print 'index', on_tile_index
		tile_epukey =  self.tiles[atlas_name][on_tile_index]
		q = leginon.leginondata.EpuData(session=self.session, name=tile_epukey)
		q['preset name'] = 'gr'
		r = q.query()
		if r:
			if len(r) >= 1:
				# Use the most recent version.
				tile_image = r[0]['image']
				pixel_shift_on_parent = numpy.array((pixel_shift[0]-tile_image['target']['delta column'], pixel_shift[1]-tile_image['target']['delta row']))
				return r[0]['image'], pixel_shift_on_parent
		return None, pixel_shift

	def loadTileShifts(self, epu_atlas_name):
		'''
		Set self.tiles using info from leginondata.
		'''
		qlist = leginon.leginondata.ImageTargetListData(session=self.session,mosaic=True).query()
		for l in qlist:
			qt = leginon.leginondata.AcquisitionImageTargetData(list=l)
			tiles = leginon.leginondata.AcquisitionImageData(target=qt).query()
			for gr_image in tiles:
				scopedata = gr_image['scope']
				fake_parent_image = self.makeGridReferenceImageData()
				print 'fake_parent', fake_parent_image
				pixel_shift = self.getTargetPixelShift(fake_parent_image, scopedata)
				# Save shifts for finding square image relation
				r = leginon.leginondata.EpuData(session=self.session, image=gr_image).query(results=1)
				if not r:
					# Screening session may have non-epu atlas
					continue
				else:
					epudata = r[0]
				if epu_atlas_name not in self.atlas_list:
					self.atlas_list.append(epu_atlas_name)
				self.tile_shifts[epu_atlas_name].append(pixel_shift)
				self.tiles[epu_atlas_name].append(epudata['name'])
		print 'loaded %d tiles for %s' % (len(self.tiles[epu_atlas_name]), epu_atlas_name)
			
	def getSimulatedTargetList(self, preset_name):
		'''
		ImageTargetListData for orphaned images.
		'''
		global preset_order
		p_index = preset_order.index(preset_name)
		q = leginon.leginondata.ImageTargetListData(session=self.session, mosaic=False)
		q.insert()
		return q

	def makeGridReferenceImageData(self):
		'''
		Reference parent image for AcquisitionImageTargetData of the atlas tiles.
		This is positioned at the center of the stage movement so each tile is marked on it virtually.
		'''
		p = self.presets['gr']
		if p is None:
			raise ValueError('session does not have gr preset to build grid reference image data')
		scope = leginon.leginondata.ScopeEMData(session=self.session,tem=p['tem'])
		scope['stage position'] = {'x':0.0,'y':0.0,'z':0.0,'a':0.0,'b':0.0}
		scope.insert()
		camera = leginon.leginondata.CameraEMData(session=self.session,ccdcamera=p['ccdcamera'])
		camera['dimension']=p['dimension']
		camera['binning']=p['binning']
		camera['offset']=p['offset']
		camera.insert()
		q = leginon.leginondata.AcquisitionImageData(session=self.session,preset=p, scope=scope, camera=camera)
		# no need to insert.  Just need camera and scope emdata.
		return q

	def getTargetPixelShift(self, parent_imagedata, scopedata):
		'''
		Get target pixel shift from the center of the parent image using
		stage positions and transformation matrix.
		'''
		my_position = scopedata['stage position']
		parent_position = parent_imagedata['scope']['stage position']
		# Need 180 rotation. Why ?
		physicalpos = (parent_position['x']-my_position['x'], parent_position['y']-my_position['y'])
		if not parent_imagedata['preset']['name'] in self.preset_matrices.keys():
			print 'Error finding pixel shift for parent preset. Assume zero'
			return numpy.array((0,0))
		matrix_inv = numpy.linalg.inv(self.preset_matrices[parent_imagedata['preset']['name']])
		pixel_shift = numpy.dot(matrix_inv, physicalpos)
		return pixel_shift

	def getNoParentTargetNumber(self, targetdata):
		'''
		Create a unique target number when parent is unknown.
		'''
		if targetdata['list']:
			# grid atlas tiles have no parent. Target number is simply incremented by
			# the number of targets in the same list.
			r = leginon.leginondata.AcquisitionImageTargetData(session=self.session, list=targetdata['list']).query()
			if r:
				return len(r)+1
			else:
				return 1
		else:
			return 1

	def getTargetNumberVersion(self, parent_imagedata, epukey, preset_name, version):
		'''
		Get target number and corrected version when parent is known.
		'''
		epuq = leginon.leginondata.EpuData(name=epukey, session=self.session)
		epuq['preset name']=preset_name
		epus = epuq.query()
		for e in epus:
			if e['image']['target'] is None:
				epus.remove(e)
		if epus:
			number = max(map((lambda x:x['image']['target']['number']),epus))
			alt_number = min(map((lambda x:x['image']['target']['number']),epus))
			if number != alt_number:
				print map((lambda x:x['image']['filename']),epus)
				raise ValueError('Bad previous insert')
			latest_version = max(map((lambda x:x['image']['target']['version']),epus))
			return number, latest_version+1
		latest_number = 0
		# find version 0 images of the same parent.
		r = leginon.leginondata.AcquisitionImageTargetData(image=parent_imagedata,version=0).query()
		if r:
			latest_number = max(map((lambda x:x['number']),r))
			if version == 0:
				# version was set to zero in the earlier part of code to force target number incrementation.
				return latest_number+1, 0
			else:
				# have non-zero version value. Must be the same the recent target.
				nr = leginon.leginondata.AcquisitionImageTargetData(image=parent_imagedata,number=latest_number).query()
				latest_version = max(map((lambda x:x['version']),nr))
				return latest_number, latest_version+1
		return 1, 0

	def alreadyUploaded(self, epukey, epuinfo, preset_name):
		parent, version, file_path, datetime_string, preset_name = epuinfo
		if parent:
			pepuq = leginon.leginondata.EpuData(session=self.session,name=parent)
		else:
			pepuq = None
		epuq = leginon.leginondata.EpuData(session=self.session)
		epuq['parent'] = pepuq
		epuq['name'] = epukey
		epuq['preset name'] = preset_name
		epuq['datetime_string'] = datetime_string
		#epuq['version'] = version
		r = epuq.query()
		if r:
			return r[0]
		else:
			return False

	def getCameraEMDict(self, epuinfo):
		# get CamerEMData non-referenced values without inserting	
		cameradict = self.meta.getCameraEMData(self.meta.meta_data_dict['microscopeData'])
		parent, version, file_path, datetime_string, preset_name = epuinfo
		if 'Fractions' in file_path:
			cameradict['save frames'] = True
			if file_path.endswith('.mrc'):
				cameradict['nframes'] = pyami.mrc.readHeaderFromFile(file_path)['nz']
				cameradict['frame time'] = self.frame_meta.getFractionFrameTimeData(self.frame_meta.meta_data_dict)
		else:
			cameradict['save frames'] = False
			cameradict['nframes'] = 1
		return cameradict
	
	def run_once(self,src_epu_session_path,dest_head):
		global session_timeout
		self.method = 'copy'
		dest_epu_head_path = os.path.join(dest_head,'epu') # session will be created by rsync
		self.makeDir(dest_epu_head_path)
		# 1. Create watchdog observer to watch rsync dest_head
		self.watch_path = dest_epu_head_path
		self.observer = self.createObserver()
		self.t0 = time.time()
		self.observer.start()
		try:
			while True:
				time.sleep(5)
				# 2. In a loop do rsync of the session dir to trigger watcher
				self.copy(src_epu_session_path,dest_epu_head_path)
				# On file_moved event add the file info to a list for upload.
				#
				# sort files by timestamp since rsync does not do so.  Need it sorted to display images in order.
				self.upload()
				# Stop oberver if timeout
				if time.time() - self.t0 > session_timeout:
					print 'number of unique holes',len(self.hl.keys())
					print 'en in %d holes ' % len(set(map((lambda x: x[0]),self.en.values())))
					self.observer.stop()
					self.observer.join()
					break
		except KeyboardInterrupt:
			self.observer.stop()
			self.observer.join()

	def walk(self,src_epu_session_path,dest_head):
		'''
		walk through destination temp files already populated
		by rsync and upload them. This is useful in catch up situation
		to decouple rsync and upload.
		'''
		self.method = 'walk'
		dest_epu_head_path = os.path.join(dest_head,'epu') # session already populated by rsync
		self.watch_path = os.path.join(dest_epu_head_path,os.path.basename(src_epu_session_path))
		for root, dirs, files in os.walk(self.watch_path):
			for f in files:
				if f.endswith(watch_for_ext):
					file_path = os.path.join(root, f)
					self.buildTree(file_path)
		self.upload()
		self.walked.append(self.session.dbid)
		print 'Done walking through existing tmp epu folder %s' % (self.watch_path)

	def getValidEpuSessionsAndBestMethods(self, src_epu_path, limit_today):
		'''
		Get EPU sessions named after a Leginon session.
		'''
		epu_session_names = os.listdir(src_epu_path)
		valid_session_dbids = []
		valid_epu_sessions = {}
		valid_sessions = []
		for name in epu_session_names:
			leginon_name = name.lower()
			r=leginon.leginondata.SessionData(name=leginon_name).query()
			if r:
				dbid = r[0].dbid
				valid_session_dbids.append(dbid)
				valid_epu_sessions[dbid] = name
		# sort so that most recent is at the end
		valid_session_dbids.sort()
		valid_dbids = {}
		best_methods = ['copy',]*len(valid_session_dbids)
		if limit_today and len(valid_session_dbids) > 1:
			# redetermine best methods
			best_methods = []
			for i, dbid in enumerate(valid_session_dbids):
				this_session = leginon.leginondata.SessionData().direct_query(dbid)
				images = leginon.leginondata.ScopeEMData(session=this_session).query(results=1)
				if not images:
					# new session takes priority
					recent_timedelta = datetime.datetime.now() - this_session.timestamp
					valid_dbids[int(recent_timedelta.total_seconds())]=(dbid, 'copy')
					best_methods = ['copy',]
					break
				else:
					recent_timedelta = datetime.datetime.now() - images[0].timestamp
				print this_session['name'], recent_timedelta
				walked_timeout_hr = 12
				if recent_timedelta > datetime.timedelta(days=1):
					print 'Old EPU sessions will be removed at the source: %s' % (valid_epu_sessions[dbid])
					clean_path = os.path.join(src_epu_path, valid_epu_sessions[dbid])
					self.cleanUp(clean_path)
				elif recent_timedelta > datetime.timedelta(hours=walked_timeout_hr):
					print 'walked', self.walked
					if dbid in self.walked and (self.most_recent_dbid is not None and self.most_recent_dbid != dbid):
						print '%d hr-old Walked EPU sessions will be removed at the source: %s' % (walked_timeout_hr,valid_epu_sessions[dbid])
						clean_path = os.path.join(src_epu_path, valid_epu_sessions[dbid])
						self.cleanUp(clean_path)
						if dbid in self.walked:
							self.walked.remove(dbid)
					else:
						valid_dbids[int((recent_timedelta.total_seconds())*100000)]=(dbid, 'walk')
				else:
					valid_dbids[int((recent_timedelta.total_seconds())*100000)]=(dbid, 'copy')
					if dbid in self.walked:
						self.walked.remove(dbid)
			keys = valid_dbids.keys()
			# sort to have most_recent first
			keys.sort()
			valid_session_dbids = []
			best_methods = []
			for k in keys:
				valid_session_dbids.append(valid_dbids[k][0])
				best_methods.append(valid_dbids[k][1])
		# make a list of sessiondata
		for i, dbid in enumerate(valid_session_dbids):
			if i == 0:
				self.most_recent_dbid = dbid
			valid_sessions.append((valid_epu_sessions[dbid],leginon.leginondata.SessionData().direct_query(dbid),best_methods[i]))
		return valid_sessions

	def run(self):
		self.params = self.parseParams()
		src_epu_path = self.get_source_path()
		print 'Source epu top path:  %s' % (src_epu_path,)
		dst_head = self.get_dst_head()
		if dst_head:
			print "Limit processing to destination frame path started with %s" % (dst_head)
		# Need to make a flag to turn it on.
		limit_today = False
		iter_count = 0
		while True:
			print 'Iterating...'
			valid_sessions = self.getValidEpuSessionsAndBestMethods(src_epu_path, limit_today)
			if limit_today:
				print 'Work only on the %d most recent Leginon session equivalent' % (len(valid_sessions))
			for valid_pair in valid_sessions:
				epu_session_name, leginon_sessiondata, best_method = valid_pair

				self.session = leginon_sessiondata
				# find ownership once per session
				self.uid, self.gid = self.getOwnership()
				# rawdata directory is not created if no image is saved in leginon.
				self.makeDir(self.session['image path']) # rawdata directory is not created if no image is saved in leginon.
				self.setOwner(self.session['image path'])
				src_epu_session_path = os.path.join(src_epu_path, epu_session_name)
				dbid = self.session.dbid
				if (iter_count == 0 and self.params['method'] == 'walk') or best_method=='walk':
					print 'walking %s' % self.session['name']
					if not self.is_testing:
						self.walk(src_epu_session_path,dst_head)
					else:
						self.walked.append(dbid)
				else:
					print 'copying %s' % self.session['name']
					if dbid in self.walked:
						self.walked.remove(dbid)
					if not self.is_testing:
						self.run_once(src_epu_session_path,dst_head)
				self.resetForSession()
			iter_count += 1
			print 'Sleeping after iteration %d...' % (iter_count)
			time.sleep(check_interval)
			limit_today = True

if __name__ == '__main__':
		a = RawTransfer(is_testing)
		a.run()
