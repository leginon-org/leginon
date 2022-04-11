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
import pyami.scriptrun

class FileTransfer(pyami.scriptrun.ScriptRun):
	def __init__(self):
		# image classes that will be transferred
		self.image_classes = [
			leginon.leginondata.AcquisitionImageData,
			leginon.leginondata.DarkImageData,
			leginon.leginondata.BrightImageData,
			leginon.leginondata.NormImageData,
		]
		super(FileTransfer, self).__init__()
		self.refcopy = None
		if not self.is_win32:
			self.refcopy = ReferenceCopier()

	def setOptions(self, parser):
		# options
		parser.add_option("--method", dest="method",
			help="method to transfer, e.g. --method=mv", type="choice", choices=['mv','rsync'], default='rsync' if sys.platform != 'win32' else "mv")
		parser.add_option("--source_path", dest="source_path",
			help="Mounted parent path to transfer, e.g. --source_path=/mnt/ddframes", metavar="PATH")
		parser.add_option("--camera_host", dest="camera_host",
			help="Camera computer hostname in leginondb, e.g. --camera_host=gatank2")
		parser.add_option("--destination_head", dest="dest_path_head",
			help="Specific head destination frame path to transfer if multiple frame transfer is run for one source to frame paths not all mounted on the same computer, e.g. --destination_head=/data1", metavar="PATH", default='')
		parser.add_option("--path_mode", dest="mode_str", 
			help="recursive session permission modification by chmod if specified, default means not to modify e.g. --path_mode=g-w,o-rw")
		parser.add_option("--check_days", dest="check_days", help="Number of days to query database", type="int", default=10)


	def checkOptionConflicts(self,params):
		if params['camera_host']:
			r = leginon.leginondata.InstrumentData(hostname=params['camera_host']).query()
			if not r:
				sys.stderr.write('Camera host %s not in Leginon database\n' % (params['camera_host']))
				sys.exit(1)

	def get_source_path(self):
		return self.getAndValidatePath('source_path')

	def get_dst_head(self):
		return self.getAndValidatePath('dest_path_head')

	def removeEmptyFolders(self,path):
		if not os.path.isdir(path):
			return

		print 'found', path
		# remove empty subfolders
		files = os.listdir(path)
		if len(files):
			for f in files:
				fullpath = os.path.join(path, f)
				if os.path.isdir(fullpath):
					self.removeEmptyFolders(fullpath)

		# if folder empty, delete it
		files = os.listdir(path)
		if len(files) == 0:
			print "Removing empty folder:", path
			######filedir operation########
			os.rmdir(path)

	def cleanUp(self,src, method):
		if method == 'rsync' and not self.is_win32:
			# remove empty .frames dir from source
			# does not work on Windows
			abspath = os.path.abspath(src)
			print 'clean up %s from linux' % (abspath)
			dirpath,basename = os.path.split(abspath)
			if os.path.isdir(src):
				cmd = 'find %s -type d -empty -prune -exec rmdir --ignore-fail-on-non-empty -p \{\} \;' % (basename,)
				print 'cd', dirpath
				os.chdir(dirpath)
				print cmd
				p = subprocess.Popen(cmd, shell=True, cwd=dirpath)
				p.wait()
			if os.path.isfile(src):
				cmd = 'rm -f %s' % abspath
				print cmd
				p = subprocess.Popen(cmd, shell=True, cwd=dirpath)
				p.wait()

		else:
			if os.path.isfile(src):
				print 'os.remove(%s)' % src
				os.remove(src)
			else:
				self.removeEmptyFolders(os.path.abspath(src))

	def move(self,src, dst):
		'''
		Use shutil's move to rename frames
		'''
		######filedir operation########
		print 'moving %s -> %s' % (src, dst)
		shutil.move(src, dst)

	def makeDirWithOwnershipChange(self,dirname,uid,gid):
		print('mkdirs %s'%dirname)
		if not os.path.exists(dirname):
			if not self.is_win32:
				# this function preserves umask of the parent directory
				pyami.fileutil.mkdirs(dirname)
				self.changeDirOwnership(uid,gid,dirname)
			else:
				# use os.makedirs on 'win32' but it does not preserve umask
				os.makedirs(dirname)
		elif os.path.isfile(dirname):
			print("Error %s is a file"%dirname)

	def _rsyncWithOwnershipChange(self,src,dst,uid,gid,method):
		'''
		Use rsync to copy the file.  The sent files are removed
		after copying.
		'''
		cmd = 'rsync -av --owner=%s:%s --remove-sent-files %s %s' % (uid, gid, src, dst)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	def changeDirOwnership(self,uid,gid,dirname, recursive=False):
		# change ownership of desintation directory and contents
		if not self.is_win32:
			# default not recursive so it does not go through all every time.
			pyami.fileutil.unixChangeOwnership(uid,gid,dirname, recursive)

	def changeMode(self,path,mode_str='g-w,o-rw', recursive=False):
		if not self.is_win32:
			pyami.fileutil.unixChangeMode(path, mode_str, recursive)

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

	def getSessionFramePath(self, imdata):
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

	def _getUidGid(self, image_path):
		# Get user id and group id of the image path to be used for frames_path
		if sys.platform == 'win32':
			uid, gid = 100, 100
		else:
			stat = os.stat(image_path)
			uid = stat.st_uid
			gid = stat.st_gid
		return uid, gid

	def run(self):
		method = self.params['method']
		mode_str = self.params['mode_str']
		src_path = self.get_source_path()
		print 'Source path:  %s' % (src_path,)
		file_map = self.getFrameFileMap(src_path)
		dst_head = self.get_dst_head()
		if dst_head:
			print "Limit processing to destination frame path started with %s" % (dst_head)
		raise NotImplemented('Need to be defined in the subclass')


class ReferenceCopier(object):
	'''
	Copy references and modify orientation if needed for archiving
	'''

	def setFrameDir(self, framedir, uid, gid):
		self.framedir = framedir
		self.refdir = os.path.join(framedir,'references')
		self.reflistpath = os.path.join(self.refdir,'reference_list.txt')
		self.badreflistpath = os.path.join(self.refdir,'failed_reference_read.txt')
		self.badrefs = []
		self.uid = uid
		self.gid = gid
		self.setupRefDir()
		self.corrector_plans = {}

	def setupRefDir(self):
		if not os.path.isdir(self.refdir):
				pyami.fileutil.mkdirs(self.refdir)
		if not os.path.isfile(self.reflistpath):
			fileobj = open(self.reflistpath,'w')
			header = 'image_name\tflip\trotate\tdark_scale\tnorm_image\tdark_image\tdefect_plan\n'
			fileobj.write(header)
			fileobj.close()
		if not os.path.isfile(self.badreflistpath):
			fileobj = open(self.badreflistpath,'w')
			header = 'unreadable references\n'
			fileobj.write(header)
			fileobj.close()

	def getRefDir(self):
		return self.refdir

	def setImage(self,imagedata):
		self.image = imagedata
		self.plan = imagedata['corrector plan']

	def run(self, imagedata, frame_dst_name):
		self.setImage(imagedata)
		linelist = []
		linelist.append(frame_dst_name)
		# modifications
		flip,rotate = self.getImageFrameOrientation()
		dark_scale = self.getDarkScale()
		geometry_modified = self.needGeometryModified()
		linelist.append(str(flip)[0])
		linelist.append('%d' % (int(rotate)*90))
		linelist.append('%d' % (dark_scale))
		# reference images
		for reftype in ('norm','dark'):
			refdata = imagedata[reftype]
			if not refdata:
				linelist.append('')
			else:
				scale_modified = self.needScaleModified(reftype)
				# reference file
				reffilename = refdata['filename']
				reffilepath = os.path.join(self.refdir,reffilename+'.mrc')
				refdata_reffilepath = os.path.join(refdata['session']['image path'],refdata['filename']+'.mrc')
				if not os.access(refdata_reffilepath, os.R_OK):
					print('Error: %s reference for image %s not readable....' % (reftype,imagedata['filename']))
					print('%s not readable' % (refdata_reffilepath+'.mrc'))
					self.writeUniqueLineToFile(self.badreflistpath, refdata_reffilepath,refdata_reffilepath)
					if geometry_modified or scale_modified:
						# record modified reference any way
						reffilename = reffilename+'_mod'
				elif not os.path.isfile(reffilepath):
					print('Copying %s reference for image %s ....' % (reftype, imagedata['filename']))
					refimage = refdata['image']
					# write the original in its original name
					pyami.mrc.write(refimage,reffilepath)
					refimage = self.modifyRefImage(refimage)
					# scale dark image if needed to one frame
					if reftype == 'dark' and not (refimage.max() == refimage.min() and refimage.mean() == 0):
						darkscale = refdata['camera']['nframes']
						if darkscale != 1 and darkscale != 0:
							print('  scaling dark image by %d' % (darkscale,))
							refimage /= darkscale
					if geometry_modified or scale_modified:
						# record modified reference and save
						reffilename = reffilename+'_mod'
						reffilepath = os.path.join(self.refdir,reffilename+'.mrc')
						pyami.mrc.write(refimage,reffilepath)
				else:
					print('%s reference for image %s already copied, skipping....' % (reftype,imagedata['filename']))
					if geometry_modified or scale_modified:
						# record modified reference any way
						reffilename = reffilename+'_mod'
				linelist.append(reffilename+'.mrc')

		# writing Corrector Plan if any
		if self.plan:
				plan_id = self.plan.dbid
				planfilename = 'defect_plan%04d' % (plan_id)
				planfilepath = os.path.join(self.refdir,planfilename+'.txt')
				self.writePlanFile(planfilepath,self.plan['bad_cols'],self.plan['bad_rows'],self.plan['bad_pixels'])

				# modify plan
				if geometry_modified:
					bad_cols,bad_rows,bad_pixels = self.modifyCorrectorPlan(imagedata['image'].shape,self.plan['bad_cols'],self.plan['bad_rows'],self.plan['bad_pixels'])
					planfilename += '_mod'
					planfilepath = os.path.join(self.refdir,planfilename+'.txt')
					self.writePlanFile(planfilepath,bad_cols,bad_rows,bad_pixels)
				linelist.append(planfilename+'.txt')
					
		linestr = '\t'.join(linelist)
		linestr += '\n'
		self.writeUniqueLineToFile(self.reflistpath, frame_dst_name,linestr)
		pyami.fileutil.unixChangeOwnership(self.uid,self.gid,self.refdir,recursive=True)

	def writeUniqueLineToFile(self,filepath, match_string,line_string):
		# check if the match_string is already there
		fileobj = open(filepath,'r')
		if match_string in fileobj.read():
			print('%s recorded already' % (match_string))
			fileobj.close()
			return
		else:
			fileobj.close()
			# write in the list
			fileobj2 = open(filepath,'a')
			if '\n' != line_string[-1]:
				line_string += '\n'
			fileobj2.write(line_string)
			fileobj2.close()

	def writePlanFile(self, planfilepath, bad_cols, bad_rows, bad_pixels):
		if not os.path.isfile(planfilepath):
			print('Writing the correction plan %s....' % planfilepath)
			planfile = open(planfilepath,'w')
			plantxt = '%s\n%s\n%s\n' % (bad_cols,bad_rows,bad_pixels)
			planfile.write(plantxt)
			planfile.close()

	def getImageFrameOrientation(self):
		frame_flip = self.image['camera']['frame flip']
		frame_rotate = self.image['camera']['frame rotate']
		return frame_flip, frame_rotate

	def needGeometryModified(self):
		frame_flip, frame_rotate = self.getImageFrameOrientation()
		return frame_flip or frame_rotate

	def getDarkScale(self):
		darkscale = 1
		try:
			if self.image['dark']:
					refimage = self.image['dark']['image']
					if not (refimage.max() == refimage.min() and refimage.mean() == 0):
						darkscale = self.image['dark']['camera']['nframes']
		except:
			pass
		if darkscale == 0:
			darkscale = 1
		return darkscale

	def needScaleModified(self,reftype):
		if reftype == 'norm':
			return False
		darkscale = self.getDarkScale()
		return darkscale != 1 and darkscale != 0

	def modifyCorrectorPlan(self,shape,bad_cols,bad_rows,bad_pixels):
		a = numpy.zeros(shape)
		# convert bad pixel coords to array
		for b in bad_pixels:
			# bad pixels are written in (x,y)
			a[b[1],b[0]] = 1
		frame_flip, frame_rotate = self.getImageFrameOrientation()
		if frame_flip:
			if frame_rotate and frame_rotate == 2:
				# Faster to just flip left-right than up-down flip + rotate
				print("  flipping the plan left-right")
				bad_cols = map((lambda x: shape[1]-1-x),bad_cols)
				frame_rotate = 0
				a = numpy.fliplr(a)
			else:
				print("  flipping the plan up-down")
				bad_rows = map((lambda x: shape[0]-1-x),bad_rows)
				a = numpy.flipud(a)
		if frame_rotate:
			# We are rotating the plans here.  Therefore, do it in the other way.
			frame_rotate = 4 - frame_rotate
			print("  rotating the plan by %d degrees" % (frame_rotate*90,))
			a = numpy.rot90(a,frame_rotate)
			for rotate in range(frame_rotate):
				original_bad_rows = bad_rows
				new_bad_rows = map((lambda x:shape[0]-x),bad_cols)
				new_bad_cols = original_bad_rows
				bad_rows = tuple(new_bad_rows)	
				bad_cols = tuple(new_bad_cols)
		# convert bad pixel arrays to list of coords
		bad_coord_list = map((lambda x:x.tolist()),numpy.where(a))
		# bad pixels are written in (x,y)
		bad_pixels = zip(bad_coord_list[1],bad_coord_list[0])	
		return bad_cols, bad_rows, bad_pixels

	def modifyRefImage(self,a):
		a = numpy.asarray(a,dtype=numpy.float32)
		frame_flip, frame_rotate = self.getImageFrameOrientation()
		if frame_flip:
			if frame_rotate and frame_rotate == 2:
				# Faster to just flip left-right than up-down flip + rotate
				print("  flipping the image left-right")
				a = numpy.fliplr(a)
				frame_rotate = 0
			else:
				print("  flipping the image up-down")
				a = numpy.flipud(a)
		if frame_rotate:
			# We are rotating the references here.  Therefore, do it in the other way.
			frame_rotate = 4 - frame_rotate
			print("  rotating the image by %d degrees" % (frame_rotate*90,))
			a = numpy.rot90(a,frame_rotate)
		return a

def testRefCopy():
	app = ReferenceCopier()
	imagedata = leginon.leginondata.AcquisitionImageData.direct_query(618664)
	app.setFrameDir('/home/acheng/tests/test_copyref/')
	app.run(imagedata,imagedata['filename']+'.frames.mrc')
	app.setImage(imagedata)
	print app.modifyCorrectorPlan(imagedata['image'].shape,[0,],[0,],[(1000,54),])

if __name__ == '__main__':
		a = RawTransfer()
		a.run()
		#testRefCopy()
