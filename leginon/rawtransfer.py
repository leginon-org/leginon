#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
import time
import numpy
import leginon.leginondata
import leginon.ddinfo
import pyami.fileutil, pyami.mrc

next_time_start = 0
mtime = 0
time_expire = 300  # ignore anything older than 5 minutes
expired_names = {} # directories that should not be transferred
check_interval = 20  # seconds between checking for new frames

class RawTransfer(object):
	def __init__(self):
		self.is_win32 = sys.platform == 'win32'
		# image classes that will be transferred
		self.image_classes = [
			leginon.leginondata.AcquisitionImageData,
			leginon.leginondata.DarkImageData,
			leginon.leginondata.BrightImageData,
			leginon.leginondata.NormImageData,
		]
		self.refcopy = None
		if not self.is_win32:
			self.refcopy = ReferenceCopier()

	def parseParams(self):
		'''
		Use OptionParser to get parameters
		'''
		global check_interval
		if len(sys.argv) == 1 and self.is_win32:
			try:
				from optparse_gui import OptionParser
				use_gui = True
			except:
				raw_input('Need opparse_gui to enter options on Windows')
				sys.exit()
		else:
			from optparse import OptionParser
			use_gui = False

		parser = OptionParser()

		# options
		parser.add_option("--method", dest="method",
			help="method to transfer, e.g. --method=mv", type="choice", choices=['mv','rsync'], default='rsync' if sys.platform != 'win32' else "mv")
		parser.add_option("--source_path", dest="source_path",
			help="Mounted parent path to transfer, e.g. --source_path=/mnt/ddframes", metavar="PATH")
		parser.add_option("--camera_host", dest="camera_host",
			help="Camera computer hostname in leginondb, e.g. --camera_host=gatank2")
		parser.add_option("--destination_head", dest="dest_path_head",
			help="Specific head destination frame path to transfer if multiple frame transfer is run for one source to frame paths not all mounted on the same computer, e.g. --destination_head=/data1", metavar="PATH", default='')
		parser.add_option("--check_interval", dest="check_interval", help="Seconds between checking for new frames", type="int", default=check_interval)

		# parsing options
		(options, optargs) = parser.parse_args(sys.argv[1:])
		if len(optargs) > 0:
			print "Unknown commandline options: "+str(optargs)
		if not use_gui and len(sys.argv) < 2:
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
		if params['camera_host']:
			r = leginon.leginondata.InstrumentData(hostname=params['camera_host']).query()
			if not r:
				sys.stderr.write('Camera host %s not in Leginon database\n' % (params['camera_host']))
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
		return self.getAndValidatePath('dest_path_head')

	def query_image_by_frames_name(self,name,cam_host):
		qccd = leginon.leginondata.InstrumentData(hostname=cam_host)
		qcam = leginon.leginondata.CameraEMData(ccdcamera=qccd)
		qcam['frames name'] = name
		for cls in self.image_classes:
			qim = cls(camera=qcam)
			results = qim.query()
			if results:
				if len(results) > 1:
					# fix for issue #3967. Not to work on the aligned images
					for r in results:
						if r['camera']['align frames']:
							continue
						return r
				else:
					# If there is just one, transfer regardlessly.
					return results[0]
		return None

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
					removeEmptyFolders(fullpath)

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

		else:
			self.removeEmptyFolders(os.path.abspath(src))

	def copy_and_delete(self,src, dst):
		'''
		Use rsync to copy the file.  The sent files are removed
		after copying.
		'''
		cmd = 'rsync -av --remove-sent-files %s %s' % (src, dst)
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
			if not self.is_win32:
				# this function preserves umask of the parent directory
				pyami.fileutil.mkdirs(dirname)
			else:
				# use os.makedirs on 'win32' but it does not preserve umask
				os.makedirs(dirname)
		elif os.path.isfile(dirname):
			print("Error %s is a file"%dirname)

	def _transfer(self,src,dst,method):
		if method == 'rsync' and not self.is_win32:
			# safer method but slower
			self.copy_and_delete(src, dst)
		else:
			# move does only rename and therefore will be faster if on the same device
			# but could have problem if dropped during the process between devices.
			self.move(src,dst)

	def changeOwnership(self,uid,gid,dirname):
		# change ownership of desintation directory and contents
		if not self.is_win32:
			cmd = 'chown -R %s:%s %s' % (uid, gid, dirname)
			print cmd
			p = subprocess.Popen(cmd, shell=True)
			p.wait()

	def transfer(self, src, dst, uid, gid, method):
		'''
		This function at minimal organize and rename the time-stamped file
		to match the Leginon session and integrated image.  If the source is
		saved on the local drive of the camera computer, rsync (default) is
		used to copy the file off and the time-stamped file on the camera
		local drive removed to make room for more data collection.
		'''
		# make destination dirs
		dirname,basename = os.path.split(os.path.abspath(dst))
		self.makeDir(dirname)

		self._transfer(src,dst,method)

		self.changeOwnership(uid,gid,dirname)

		self.cleanUp(src,method)

	def run_once(self,parent_src_path,cam_host,dest_head,method):
		global next_time_start
		global time_expire
		global mtime
		names = os.listdir(parent_src_path)
		time.sleep(10)  # wait for any current writes to finish
		time_start = next_time_start
		for name in names:
			src_path = os.path.join(parent_src_path, name)
			_, ext = os.path.splitext(name)
			## skip empty directories
			if os.path.isdir(src_path) and not os.listdir(src_path):
				# maybe delete empty dir too?
				continue

			# skip expired dirs, mrcs
			if name in expired_names:
				continue
			# ignore irrelevent source files or folders
			# gatan k2 summit data ends with '.mrc'
			# de folder starts with '20'
			# falcon mrchack stacks ends with '.mrcs'
			if not ext.startswith('.mrc') and  ext != '.frames' and not name.startswith('20'):
				continue
			print '**running', src_path

			# adjust next expiration timer to most recent time
			if mtime > next_time_start:
				next_time_start = mtime

			# query for Leginon image
			if ext.startswith('.mrc'):
				ext_len = len(ext)
				frames_name = name[:-ext_len]
				dst_suffix = '.frames.mrc'
			else:
				frames_name = name
				dst_suffix = '.frames'
				## ensure a trailing / on directory
				if src_path[-1] != os.sep:
					src_path = src_path + os.sep
			imdata = self.query_image_by_frames_name(frames_name,cam_host)
			if imdata is None:
				continue
			image_path = imdata['session']['image path']
			frames_path = imdata['session']['frame path']

			# back compatible to sessions without frame path in database
			if image_path and not frames_path and sys.platform != 'win32':
				frames_path = leginon.ddinfo.getRawFrameSessionPathFromSessionPath(image_path)

			# only process destination frames_path starting with chosen head
			if sys.platform != 'win32' and not frames_path.startswith(dest_head):
				print "frames_path = %s"%frames_path
				print '    Destination frame path does not starts with %s. Skipped' % (dest_head)
				continue

			if self.refcopy:
				self.refcopy.setFrameDir(frames_path)

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
					self.refcopy.run(imdata, imname)
				except:
					print 'reference copying error. skip'
			# skip  and clean up finished ones. Needed when the
			# destination user lost write privilege temporarily.
			if os.path.exists(dst_path):
				# TO DO ? Probably should check size
				print 'Destination path %s exists, cleaning up' % dst_path
				self.cleanUp(src_path,method)
				return
			# do actual copy and delete
			self.transfer(src_path, dst_path, uid, gid,method)
			# de only
			leginon.ddinfo.saveImageDDinfoToDatabase(imdata,os.path.join(dst_path,'info.txt'))

	def run(self):
		self.params = self.parseParams()
		src_path = self.get_source_path()
		print 'Source path:  %s' % (src_path,)
		dst_head = self.get_dst_head()
		if dst_head:
			print "Limit processing to destination frame path started with %s" % (dst_head)
		while True:
			print 'Iterating...'
			self.run_once(src_path,self.params['camera_host'],dst_head,method=self.params['method'])
			print 'Sleeping...'
			time.sleep(check_interval)



class ReferenceCopier(object):
	'''
	Copy references and modify orientation if needed for archiving
	'''

	def setFrameDir(self, framedir):
		self.framedir = framedir
		self.refdir = os.path.join(framedir,'references')
		self.reflistpath = os.path.join(self.refdir,'reference_list.txt')
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
					reffilename = refdata_reffilepath[:-4]
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
					
		# check if the image is already there
		fileobj = open(self.reflistpath,'r')
		if frame_dst_name in fileobj.read():
			print('frame references recorded already')
			fileobj.close()
			return
		else:
			fileobj.close()
			# write in the list
			fileobj2 = open(self.reflistpath,'a')
			linestr = '\t'.join(linelist)
			fileobj2.write(linestr+'\n')
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
				new_bad_rows = map((lambda x:shape[0]-x),bad_col)
				new_bad_col = original_bad_rows
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
	imagedata = leginon.leginondata.AcquisitionImageData.direct_query(1871)
	app.setFrameDir('/Users/acheng/testdata/frames/15dec04y/rawdata/')
	app.run(imagedata,imagedata['filename']+'.frames.mrc')
	app.setImage(imagedata)
	print app.modifyCorrectorPlan(imagedata['image'].shape,[0,],[0,],[(1000,54),])

if __name__ == '__main__':
		a = RawTransfer()
		a.run()
		#testRefCopy()
