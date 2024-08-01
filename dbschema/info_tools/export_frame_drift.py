#!/usr/bin/env python
from leginon import leginondata
from dbschema.info_tools import export_targets
from appionlib import apProject
from appionlib import appiondata
from appionlib import apDDResult

class DDExporter(export_targets.Exporter):
	'''
	Export DD score on parent image of high magnification
	images of a session.
	'''
	info = 'drift'
	def __init__(self, sessionname, output_basepath='./', excluded_project_ids=[]):
		super(DDExporter, self).__init__(sessionname, output_basepath, excluded_project_ids)
		apProject.setDBfromProjectId(self.projectdata.dbid)

	def getDDResult(self, imagedata):
		'''
		Get drift scores
		'''
		try:
			dd_obj = apDDResult.DDResults(imagedata)
			shifts = dd_obj.getAngstromShiftsBetweenFrames()
			return shifts
		except ValueError as e:
			return []

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
				drift = self.getDDResult(img)
				line = '%d\t%d_%d' % (img.dbid, target0['image'].dbid, target0['number'])
				if drift:
					#values
					drift_str = list(map((lambda x: '%.4f' % x), drift))
					frame_time_s = img['camera']['frame time']/1000.0
					line += '\t%.4f\t%s' % (frame_time_s, ','.join(drift_str))
				else:
					line +='\t\t'
				line +='\n'
				self.logger.info(line)
				self.writeResults(target0, line)
				self.targetlist[parent_preset].append(target0.dbid)

	def setTitle(self):
		self.result_title ='ChildImageId\tTargetId_TargetNumber\tFrame_Time\tDrifts_between_Frames_in_Angstrom'

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = DDExporter(session_name, base_path)
	app.run()
