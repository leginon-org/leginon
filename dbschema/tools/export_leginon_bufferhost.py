#!/usr/bin/env python
import sys
import shutil

from leginon import leginondata
from pyami import jsonfun

class BufferHostJsonMaker(jsonfun.DataJsonMaker):
	def __init__(self,params):
		super(BufferHostJsonMaker,self).__init__(leginondata)
		try:
			self.validateInput(params)
		except ValueError as e:
			print(("Error: %s" % e.message))
			self.close(1)

	def validateInput(self, params):
		if len(params) < 4:
			print("Usage export_leginon_bufferhost.py source_database_hostname source_camera_hosthame camera_name")
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
			print("ERROR: incorrect hostname....")
			r = leginondata.InstrumentData(name=from_camname).query(results=1)
			if r:
				raise ValueError("Try %s instead" % r[0]['hostname'])
			else:
				raise ValueError("  No %s camera found" % from_camname)
			sys.exit()
		return result

	def printBufferHostQuery(self):
		camq = leginondata.BufferHostData(ccdcamera=self.cam)
		results = camq.query(results=1)
		if results:
			r = results[0]
			self.publishBufferHostData(r)

	def publishBufferHostData(self, bufferhostdata):
		# TODO corrector plan does not come from normdata
		if bufferhostdata is not None:
			camdict = self.makeClassDict(bufferhostdata['ccdcamera'])
			datadict = self.makeClassDict(bufferhostdata)
			datadict['ccdcamera'] = camdict
			self.alldata.append({'BufferHostData':datadict})

	def run(self):
		self.printBufferHostQuery()
		json_filename = 'bufferhost_%s+%s.json' % (self.cam['hostname'],self.cam['name'])
		self.writeJsonFile(json_filename)

	def close(self, status=0):
		if status:
			print("Exit with Error")
			sys.exit(1)

if __name__=='__main__':
	app = BufferHostJsonMaker(sys.argv)
	app.run()
	app.close()
	 
