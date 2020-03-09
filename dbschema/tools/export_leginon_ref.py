#!/usr/bin/env python
import sys
import shutil

from leginon import leginondata
from pyami import jsonfun

class ReferenceJsonMaker(jsonfun.DataJsonMaker):
	def __init__(self,params):
		super(ReferenceJsonMaker,self).__init__(leginondata)
		try:
			self.validateInput(params)
		except ValueError, e:
			print "Error: %s" % e.message
			self.close(1)

	def validateInput(self, params):
		if len(params) != 4:
			print "Usage export_leginon_ref.py source_database_hostname source_camera_hosthame camera_name"
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		self.tem = None
		self.cam = self.getSourceCameraInstrumentData(params[2],params[3])

	def getSourceCameraInstrumentData(self, from_hostname,from_camname):
		kwargs = {'hostname':from_hostname,'name':from_camname}
		q = self.makequery('InstrumentData',kwargs)
		result = self.research(q,True)
		if not result:
			print "ERROR: incorrect hostname...."
			r = leginondata.InstrumentData(name=from_camname).query(results=1)
			if r:
				raise ValueError("Try %s instead" % r[0]['hostname'])
			else:
				raise ValueError("  No %s camera found" % from_camname)
			sys.exit()
		return result

	def getCameraShape(self):
		'''
		get shape.  Not used yet.  may need this to get more specific query.
		'''
		binning = {'x':1,'y':1}
		offset = {'x':0,'y':0}
		results = leginondata.CameraEMData(ccdcamera=self.cam).query(results=10)
		# camera is at least this big
		dim = {'x':2048,'y':2048}
		for r in results:
			for axis in ('x','y'):
				dim[axis] = max(dim[axis],r['dimension'][axis])
		return dim

	def printReferenceQuery(self):
		# check common binnings
		bins = [1,2,4,8]
		for b in bins:
			normids = []
			offset_channels = []
			binning = {'x':b,'y':b}
			camq = leginondata.CameraEMData(ccdcamera=self.cam, binning=binning)
			# get 10 results and see if it is enough to catch some with offset.
			# if this does not work, will need to determine common camera configurations.
			results = leginondata.NormImageData(camera=camq).query(results=10)
			for r in results:
				if '%d-%d' % (r['camera']['offset']['x'], r['channel']) not in offset_channels:
					offset_channels.append('%d-%d' % (r['camera']['offset']['x'],r['channel']))
					normids.append(r.dbid)
			print "bin and number of normids", b, normids
			for dbid in normids:
				normdata = leginondata.NormImageData().direct_query(dbid)
				self.publishNormData(normdata)

	def modifyReferenceDict(self, datadict, name, file_prefix, plandict, camdict, scopedict):
		'''
		create association between reference mrc images by moving the saved images under a
    consistent naming scheme.
		'''
		datadict['corrector plan'] = plandict
		datadict['camera'] = camdict
		datadict['scope'] = scopedict
		# set value in referenced image to be the same as norm
		old_filename = datadict['filename']
		new_filename = file_prefix+'_'+name
		datadict['filename'] = new_filename
		shutil.move(old_filename+'.mrc', new_filename+'.mrc')
		# place holder for image
		datadict['image'] = [[1,0],[0,1]]
		return datadict

	def publishNormData(self,normdata):
		'''
		save brigh, dark, norm images in the same name scheme
		'''
		if not self.tem:
			self.tem = normdata['scope']['tem']
		file_prefix = '%d' % normdata.dbid
		camdict = self.makeClassDict(normdata['camera'])
		scopedict = self.makeClassDict(normdata['scope'])
		plandict = self.makeClassDict(normdata['corrector plan'])
		if plandict is not None:
			plandict['camera'] = camdict
		#self.alldata.append({'CorrectorPlanData':plandict})
		# set value in referenced image to be the same as norm
		darkdict = self.makeClassDict(normdata['dark'])
		darkdict = self.modifyReferenceDict(darkdict, 'dark', file_prefix, plandict, camdict, scopedict)
		#
		brightdict = self.makeClassDict(normdata['bright'])
		brightdict = self.modifyReferenceDict(brightdict, 'bright', file_prefix, plandict, camdict, scopedict)
		#
		normdict = self.makeClassDict(normdata)
		normdict = self.modifyReferenceDict(normdict, 'norm', file_prefix, plandict, camdict, scopedict)
		# make it into json format dictionaries in dictionary.
		normdict['dark'] = darkdict
		normdict['bright'] = brightdict
		self.alldata.append({'NormImageData':normdict})

	def run(self):
		self.shape = self.getCameraShape()
		self.printReferenceQuery()
		json_filename = 'ref_%s+%s+%s+%s.json' % (self.tem['hostname'],self.tem['name'],self.cam['hostname'],self.cam['name'])
		self.writeJsonFile(json_filename)

	def close(self, status=0):
		if status:
			print "Exit with Error"
			sys.exit(1)
		raw_input('hit enter when ready to quit')

if __name__=='__main__':
	app = ReferenceJsonMaker(sys.argv)
	app.run()
	app.close()
	 
