#!/usr/bin/env python
from leginon import leginondata
from dbschema.info_tools import export_targets
from appionlib import apProject
from appionlib import appiondata
from appionlib.apCtf import ctfdb

class CtfExporter(export_targets.Exporter):
	'''
	Export Ctf score on parent image of high magnification
	images of a session.
	'''
	info = 'ctf'
	def __init__(self, sessionname, output_basepath='./', excluded_project_ids=[]):
		super(CtfExporter, self).__init__(sessionname, output_basepath, excluded_project_ids)
		apProject.setDBfromProjectId(self.projectdata.dbid)

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
		is_parent = False
		while (img and img['target'] and img['target']['image'] and img['target']['preset']) and not is_parent:
			target0 = self.getZeroVersionTarget(img['target'])
			parent_preset = target0['image']['preset']['name']
			# This will prevent it from descending further.
			is_parent = True
			if parent_preset not in list(self.targetlist.keys()):
				self.targetlist[parent_preset] = []
			if target0.dbid not in self.targetlist[parent_preset]:
				ctf = self.getCtfResult(img)
				line = '%d\t%d_%d' % (img.dbid, target0['image'].dbid, target0['number'])
				if ctf:
					#ace resolution, mean defocus
					line += '\t%.4f\t%.3f' % (ctf[0],ctf[1]*1e6)
				else:
					line +='\t\t'
				line +='\n'
				self.logger.info(line)
				self.writeResults(target0, line)
				self.targetlist[parent_preset].append(target0.dbid)

	def setTitle(self):
		self.result_title ='ChildImageId\tTargetId_TargetNumber\tCtf_Resolution_Ang\tMean_Defocus_um'

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = CtfExporter(session_name, base_path)
	app.run()
