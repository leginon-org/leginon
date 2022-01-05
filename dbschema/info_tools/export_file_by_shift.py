#!/usr/bin/env python
from leginon import leginondata
from dbschema.info_tools import export_targets

class Exporter(export_targets.Exporter):
	'''
	Export filenames of high magnification
	images of a session.
	'''
	info = 'mrc'
	def __init__(self, sessionname, output_basepath='./', excluded_project_ids=[]):
		super(Exporter, self).__init__(sessionname, output_basepath, excluded_project_ids)

	def getCtfResult(self, imagedata):
		'''
		Get ctf scores
		'''
		ctfresult, conf = ctfdb.getBestCtfValueForImage(imagedata, msg=False)		
		if ctfresult:
			return min(ctfresult['resolution_50_percent'], ctfresult['ctffind4_resolution']), (ctfresult['defocus1']+ctfresult['defocus2'])/2.0

	def writeTargetAndInfo(self, imagedata):
		'''
		Write out Ice values target on hl image if not yet exported.
		'''
		img = imagedata
		target0 = self.getZeroVersionTarget(img['target'])
		parent_preset = target0['image']['preset']['name']
		if parent_preset not in self.targetlist.keys():
			self.targetlist[parent_preset] = []
		self.targetlist[parent_preset].append(target0.dbid)
		filename = '%s.mrc' % img['filename']
		line = '%s' % (filename)
		self.logger.info(line)
		self.writeResults(target0, line)

	def setTitle(self):
		self.result_title ='mrc_name'

if __name__=='__main__':
	session_name = raw_input('Which session ? ')
	base_path = raw_input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = Exporter(session_name, base_path)
	app.run()
