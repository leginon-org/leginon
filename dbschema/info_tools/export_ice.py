#!/usr/bin/env python
import os
from leginon import leginondata
from dbschema.info_tools import export_targets

class IceThicknessExporter(export_targets.Exporter):
	'''
	Export Ice thickness on parent image of high magnification
	images of a session.
	'''
	info = 'ice'
	def getZeroVersionTarget(self, targetdata):
		'''
		Get the original target, not the adjusted newer versions.
		'''
		t = targetdata
		while t['fromtarget']:
			t = t['fromtarget']
		return t

	def getApertureLimitedScatteringIce(self, imagedata):
		'''
		Get Aperture limited scattering ice thickness value
		'''
		r = leginondata.ObjIceThicknessData(image=imagedata).query()
		if r:
			return r[0]['vacuum intensity'],r[0]['mfp'],r[0]['intensity'],r[0]['thickness']

	def getZeroLossIce(self, imagedata):
		'''
		Get Zero loss ice thickness value
		'''
		r = leginondata.ZeroLossIceThicknessData(image=imagedata).query()
		if r:
			return r[0]['slit mean'],r[0]['no slit mean'],r[0]['thickness']

	def getHoleFinderIce(self, target0):
		parent = target0['image']
		if not parent:
			return
		r = leginondata.HoleFinderPrefsData(image=parent).query()
		if not r:
			return
		row0 = int(target0['delta row']+parent['camera']['dimension']['y']//2)
		col0 = int(target0['delta column']+parent['camera']['dimension']['x']//2)
		stats = leginondata.HoleStatsData(prefs=r[0],row=row0,column=col0).query()
		if not stats:
			return
		return stats[0]['mean'],stats[0]['thickness-mean'],r[0]['ice-zero-thickness']

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
				als_ice = self.getApertureLimitedScatteringIce(img)
				zl_ice = self.getZeroLossIce(img)
				hl_ice = self.getHoleFinderIce(target0)
				line = '%d\t%d_%d' % (img.dbid, target0['image'].dbid, target0['number'])
				if als_ice:
					#thickness, intensity, vacuum intensity, mfp
					line += '\t%.4f\t%.3f\t%.3f\t%.3f' % (als_ice[3],als_ice[2],als_ice[0],als_ice[1])
				else:
					line +='\t\t\t\t'
				if zl_ice:
					#thickness, slit mean, no slit mean
					line += '\t%.4f\t%.3f\t%.3f' % (zl_ice[-1],zl_ice[0],zl_ice[1])
				else:
					line +='\t\t\t'
				if hl_ice:
					#thickness-mean, mean, I0
					line += '\t%.4f\t%.3f\t%3.f' % (hl_ice[-1],hl_ice[0],hl_ice[1])
				else:
					line +='\t\t\t'
				line +='\n'
				self.logger.info(line)
				self.writeResults(target0, line)
				self.targetlist[parent_preset].append(target0.dbid)

	def setTitle(self):
					#thickness, intensity, vacuum intensity, mfp
		self.result_title ='ChildImageId\tTargetId_TargetNumber\tALS_Thickness\tALS_I\tALS_I0\tALS_MFP\tZL_Thickness\tZL_I\tZL_I0\thl_Thickness\thl_I\thl_I0'

if __name__=='__main__':
	session_name = input('Which session ? ')
	base_path = input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app = IceThicknessExporter(session_name, base_path)
	app.run()
