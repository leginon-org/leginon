#!/usr/bin/env python
import schemabase
import leginon.leginondata
import sys,os

class SchemaUpdate16182(schemabase.SchemaUpdate):
	'''
	This will change DD raw frame directories to the new format
	'''

	def getSessionsWithSavedRawFrames(self):
		if (not self.leginon_dbupgrade.columnExists('CameraEMData', 'frames name')) or (not self.leginon_dbupgrade.columnExists('CameraEMData', 'save frames')):
			return []

		groupSQL = (" Select `REF|SessionData|session` as sessionid " +
				" from CameraEMData where `frames name` is not null  " +
				" and `frames name` not like '' and `save frames`=1 " +
				" group by `REF|SessionData|session` ;")
		result = self.leginon_dbupgrade.returnCustomSQL(groupSQL)
		return result

	def moveDDRawImages(self,sessionid):
		q = leginon.leginondata.SessionData()
		sessiondata = q.direct_query(sessionid)
		qcam = leginon.leginondata.CameraEMData(session=sessiondata)
		qcam['save frames']=True
		rcams = qcam.query()
		for cam in rcams:
			if cam['frames name']:
				oldrawpath = os.path.join(sessiondata['image path'],'rawframes',cam['frames name'])
				if os.path.isdir(oldrawpath):
					print oldrawpath
					qimage = leginon.leginondata.AcquisitionImageData(camera=cam)
					rimages = qimage.query()
					if rimages and len(rimages) > 1:
						print 'Error ',cam.dbid, 'belongs to  %d images' % len(rimage)
						sys.exit(1)
					newrawpath = os.path.join(sessiondata['image path'],rimages[0]['filename']+'.frames')
					try:
						os.renames(oldrawpath,newrawpath)
					except:
						return sessiondata
		return None

	def upgradeLeginonDB(self):
		sessions = self.getSessionsWithSavedRawFrames()
		badimagepaths = []
		for sessionid in sessions:
			badsession = self.moveDDRawImages(sessionid[0])
			if badsession:
				badimagepaths.append(badsession['image path'])
		print badimagepaths

if __name__ == "__main__":
	update = SchemaUpdate16182()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()

