#!/usr/bin/env python
import os
from leginon import leginondata
from dbschema.info_tools import export_targets

class ChildImagePathExporter(export_targets.Exporter):
	'''
	Export ChildImagePath score on parent image of high magnification
	images of a session.
	'''
	info = 'child_path'

	def getChildImagePathResult(self, imagedata):
		'''
		Get child_path scores
		'''
		img_format='mrc'
		return os.path.join(imagedata['session']['image path'],'%s.%s' % (imagedata['filename'], img_format))

	def writeTargetAndInfo(self, imagedata):
		'''
		Write out Ice values target on hl image if not yet exported.
		'''
		img = imagedata
		is_parent = False
		while (img and img['target'] and img['target']['image'] and img['target']['preset']) and not is_parent:
			target0 = self.getZeroVersionTarget(img['target'])
			parent_preset = target0['image']['preset']['name']
			# This will prevent it from descending further.
			is_parent = True
			if parent_preset not in list(self.targetlist.keys()):
				self.targetlist[parent_preset] = []
			if target0.dbid not in self.targetlist[parent_preset]:
				child_path = self.getChildImagePathResult(img)
				line = '%d\t%d_%d' % (img.dbid, target0['image'].dbid, target0['number'])
				if child_path:
					#ace resolution, mean defocus
					line += '\t%s' % (child_path,)
				else:
					line +='\t'
				line +='\n'
				self.logger.info(line)
				self.writeResults(target0, line)
				self.targetlist[parent_preset].append(target0.dbid)

	def setTitle(self):
		self.result_title ='ChildImageId\tTargetId_TargetNumber\tChildImagePath'

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = (input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = ChildImagePathExporter(session_name, base_path)
	app.run()
