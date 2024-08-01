#!/usr/bin/env python
import os
from leginon import leginondata, projectdata, calibrationclient
from sinedon import directq
import pyami.fileutil
import pyami.jpg
from pyami import mrc

PRESET_PIXEL_SIZE_MAX = 5e-10 #meters
MIN_NUMBER_OF_IMAGES_AT_PRESET = 1

class Logger(object):
	def info(self,msg):
		print(msg)
	def warning(self,msg):
		print(('WARNING:',msg))
	def error(self,msg):
		raise ValueError(msg)

class Exporter(object):
	'''
	Export target coordinates on parent image of high magnification
	images of a session.
	'''
	info = 'info'

	def __init__(self, sessionname, output_basepath='./', excluded_project_ids=[]):
		self.logger = Logger()
		self.output_basepath = output_basepath
		self.setSession(sessionname, excluded_project_ids)
		self.setTitle()
		self.calclient = {
			'pixel': calibrationclient.PixelSizeCalibrationClient(self),
		}
		self.targetlist = {} # list of target for each preset

	def research(self, datainstance, results=None, readimages=True, timelimit=None):
		'''
		find instances in the database that match the 
		given datainstance
		'''
		try:
			resultlist = datainstance.query(results=results, readimages=readimages, timelimit=timelimit)
		except (IOError, OSError) as e:
			raise ResearchError(e)
		return resultlist

	def setSession(self, sessionname, excluded_project_ids):
		'''
		Set sessiondata of the exporter. Check session existance
		and whether it is in a project that should be excluded.
		Raise ValueError if not good.
		'''
		# find session
		r = leginondata.SessionData(name=sessionname).query()
		if len(r) != 1:
			raise ValueError('Invalid session. Found %d sessions named %s' % (len(r),sessionname))
		self.sessiondata = r[0] #sessiondata sinedon data object
		# find project the session belongs to
		r = projectdata.projectexperiments(session=self.sessiondata).query()
		if len(r) != 1:
			raise ValueError('Invalid session. Found %d project associated with %s' % (len(r),sessionname))
		self.projectdata = r[0]['project'] #projectdata sinedon data object
		if self.projectdata.dbid in excluded_project_ids:
			raise ValueError("Invalid session. %s is in an excluded project '%s'" % (sessionname, self.project['name']))
		self.logger.info("Processing %s in project '%s'...." % (self.sessiondata['name'],self.projectdata['name']))
		return

	def getFinalPresetNames(self):
		'''
		get preset names for final images.
		'''
		# faster with direct query output is a list of dictionary with the selected key
		q = 'SELECT name from PresetData where `REF|sessiondata|session`=%d GROUP BY name;' % self.sessiondata.dbid
		results = directq.complexMysqlQuery('leginondata',q)
		final_presetnames = []
		# check with the most recent preset pixel size
		for pdict in results:
			pname = pdict['name']
			last_preset = leginondata.PresetData(name=pname,session=self.sessiondata).query(results=1)[0]
			campixelsize = self.calclient['pixel'].getPixelSize(last_preset['magnification'],last_preset['tem'],last_preset['ccdcamera'])
			binning = last_preset['binning']
			pixelsize = {'x':campixelsize*binning['x'],'y':campixelsize*binning['y']}
			if max(pixelsize['x'],pixelsize['y']) < PRESET_PIXEL_SIZE_MAX:
				final_presetnames.append(pname)
		final_presetnames.sort(reverse=True)
		return final_presetnames

	def hasPresetImages(self, pname):
		'''
		Make sure the preset has some image.
		Some preset are not really used for data collection but alignment
		etc.
		'''
		presetq = leginondata.PresetData(name=pname, session=self.sessiondata)
		images = leginondata.AcquisitionImageData(preset=presetq).query()
		if len(images) >= MIN_NUMBER_OF_IMAGES_AT_PRESET:
			return True
		return False

	def chooseBestFinalPreset(self, presetnames):
		'''
		Choose preset for target and parent export.
		'''
		if not presetnames:
			return None
		for p in presetnames:
			if '-DW' in p and self.hasPresetImages(p):
				#top priority -DW dose-weighted aligned image
				
				break
			if '-' in p and self.hasPresetImages(p):
				#second priority non-dose-weighted aligned image
				break
			if p.startswith('e') and self.hasPresetImages(p):
				# usual exposure starts with 'e'
				break
		if p.startswith('f') or not self.hasPresetImages(p):
			# only focus presets
			return None
		return p

	def filterImages(self, images):
		'''
		Filter images not hidden or trashed.
		'''
		good_images = []
		self.logger.info('Filtering according to ViewerImageStatus....')
		for img in images:
			vq = leginondata.ViewerImageStatus(session=self.sessiondata, image=img).query()
			if len(vq) > 0 and vq[0]['status'] in ('hidden','trash'):
				continue
			good_images.append(img)
		self.logger.info('final image count is %d' % len(good_images))
		return good_images

	def getFinalImages(self):
		'''
		Choose final exposure images. Criteria is based on image size, and pixel size. Excluding hidden and trash.
		'''
		presetnames = self.getFinalPresetNames()

		final_presetname = self.chooseBestFinalPreset(presetnames)
		if not final_presetname:
			self.logger.error('No valid high mag preset found. Not processable')
		self.logger.info('Export targets and parents derived from preset %s' % (final_presetname,))
		# main query
		presetq = leginondata.PresetData(name=final_presetname, session=self.sessiondata)
		images = leginondata.AcquisitionImageData(preset=presetq).query()
		# filter out bad images
		good_images = self.filterImages(images)
		return good_images

	def getZeroVersionTarget(self, targetdata):
		'''
		Get the original target, not the adjusted newer versions.
		'''
		t = targetdata
		while t['fromtarget']:
			t = t['fromtarget']
		return t

	def writeResults(self, target0, line):
		presetdir = os.path.join(self.output_basepath, target0['image']['preset']['name'])
		pyami.fileutil.mkdirs(presetdir)
		targetfile_path = os.path.join(presetdir,'%s.txt' % self.info)
		if not os.path.exists(targetfile_path):
			write_mode = 'w'
			fobj = open(targetfile_path, write_mode)
			fobj.write(self.result_title+'\n')
			fobj.close()
		fobj = open(targetfile_path, 'a')
		fobj.write(line+'\n')
		fobj.close()
		self._moreResults(presetdir, target0)

	def _moreResults(self, presetdir, target0):
		# for subclass
		pass

	def writeTargetAndInfo(self, imagedata):
		'''
		Write out target and parent image. See subclasses for filtered write.
		'''
		line = '%d\t%d_%d\t%s' % (img.dbid, target0['image'].dbid, target0['number'], target0['image']['filename'])
		self.logger.info(line)
		self.writeResults(target0, line)

	def setTitle(self):
		self.result_title = 'ChildImageId\tTargetId_TargetNumber\tLeginonImageFilename'

	def run(self):
		good_final_images = self.getFinalImages()
		for imagedata in good_final_images:
			self.writeTargetAndInfo(imagedata)
		self.logger.info('output targets.txt format is:')
		self.logger.info(self.result_title)
			
class TargetExporter(Exporter):
	info = 'targets'

	def writeTargetAndInfo(self, imagedata):
		'''
		Write out target and parent image if not yet exported.
		'''
		img = imagedata
		while (img and img['target'] and img['target']['image'] and img['target']['preset']):
			target0 = self.getZeroVersionTarget(img['target'])
			parent_preset = target0['image']['preset']['name']
			if parent_preset not in list(self.targetlist.keys()):
				self.targetlist[parent_preset] = []
			if target0.dbid not in self.targetlist[parent_preset]:
				parentdim = target0['image']['camera']['dimension']
				p_center = parentdim['y']//2, parentdim['x']//2 #(row, col)
				line = '%d\t%d_%d\t%.2f\t%.2f\t%s\t%s' % (img.dbid, target0['image'].dbid, target0['number'], target0['delta row']+p_center[0], target0['delta column']+p_center[1], img['scope'].timestamp.strftime("%Y-%m-%d %H:%M:%S"), target0['image']['filename'])
				self.logger.info(line)
				self.writeResults(target0, line)
				self.targetlist[parent_preset].append(target0.dbid)
			img = target0['image']

	def setTitle(self):
		self.result_title ='ChildImageId\tTargetId_TargetNumber\tYCoord\tXCoord\tTimeStamp\tLeginonImageFilename'

	def _moreResults(self, presetdir, target0):
		# also writes mrc file
		mrc_name = '%d.mrc' % (target0['image'].dbid,)
		mrc_path = os.path.join(presetdir,'%s' % (mrc_name,))
		if not os.path.exists(mrc_path):
			self.logger.info('Writing %s....' %(mrc_name,))
			mrc.write(target0['image']['image'], mrc_path)

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = TargetExporter(session_name, base_path)
	app.run()
