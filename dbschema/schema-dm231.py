#!/usr/bin/env python
import schemabase
from leginon import leginondata

VALID_CAMERA_NAMES = ['GatanK2Linear','GatanK2Counting','GatanK2Super','SimFalconFrameCamera',]

class SchemaUpdateDM231(schemabase.SchemaUpdate):
	'''
	This schema change assigns frame rotation and flip to
	GatanK2 CameraEMData that were acquired with DM 2.31 but without
	flip rotation assigned
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.tableExists('SessionData'):
			return
		
		while True:
			while True:
				sessionname = raw_input('Enter the name of the first session of which\n   frames are saved with Gatan K2 Summit under DM 2.31\n   (Press RETURN if none): ')
				if not sessionname:
					return
				results = leginondata.SessionData(name=sessionname).query()
				if not results:
					print '\033[31mSession not found, Try again.\033[0m'
					continue
				self.sessiondata = results[0]
				q = leginondata.CameraEMData(session=self.sessiondata)
				q['save frames'] = True
				results = q.query(results=1)
				if not results:
					print '\033[31mNo image with saved frame found in Session. Try again.\033[0m'
					continue
				camdata = results[0]
				if not camdata['ccdcamera']['name'] in VALID_CAMERA_NAMES:
					print '\033[31mThis is not a camera that needs changing. Try again.\033[0m'
					continue
				first_image = self. getFirstImageInSession()
				if not first_image:
					print '\033[31mThis session has no image saved.  Try agin.\033[0m'
					continue
				k2cameras = self.getRelatedFrameCameras(camdata)
				self.saveFrameOrientation(k2cameras,first_image)
				break
			answer = raw_input('Another K2 camera ? (Y/N)')
			if answer.upper() =='N':
				return

	def getRelatedFrameCameras(self,camdata):
		r = leginondata.InstrumentData(hostname=camdata['ccdcamera']['hostname']).query()
		k2cameras = []
		for instrumentdata in r:
			if instrumentdata['name'] in VALID_CAMERA_NAMES:
				k2cameras.append(instrumentdata)
		return k2cameras

	def getFirstImageInSession(self):
		r = leginondata.AcquisitionImageData(session=self.sessiondata).query()
		if r:
			return r[-1]

	def saveFrameOrientation(self,k2cameras, first_imagedata):
		for k2camdata in k2cameras:
			# First image is not necessary from the said camera,
			# but it marks the image id.
			q = leginondata.K2FrameDMVersionChangeData(k2camera=k2camdata, image=first_imagedata)
			q['dm version'] = [2,31]
			q['frame flip'] = True
			q['frame rotate'] = 0
			q.insert()
			print "\033[32mFrames set to True starting at image '%s.mrc'\033[0m" % (first_imagedata['filename'],)

if __name__ == "__main__":
	update = SchemaUpdateDM231()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.setForceUpdate(True)
	update.run()
