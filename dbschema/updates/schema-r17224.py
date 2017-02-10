#!/usr/bin/env python
import schemabase
from leginon import leginondata

class SchemaUpdate17224(schemabase.SchemaUpdate):
	'''
	This schema update only applies to full-sized DE-12 raw frame saved data
	'''

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.columnExists('AcquisitionImageData', 'REF|CorrectorPlanData|corrector plan'):
			self.leginon_dbupgrade.addColumn('AcquisitionImageData', 'REF|CorrectorPlanData|corrector plan', self.leginon_dbupgrade.int)

		results = leginondata.InstrumentData(name='DE12').query(results=1)
		if not results:
			return
		decameradata = results[0]

		dim = {'x':4096,'y':3072}
		camq=leginondata.CameraEMData(ccdcamera=decameradata,dimension=dim)
		plans = leginondata.CorrectorPlanData(camera=camq).query()
		pairs = {}
		ordered_keys = []
		for i, plan in enumerate(plans):
			if i == 0:
				ordered_keys.append(i)
				pairs[i] = (plan.timestamp.now(),plan.timestamp)
			else:
				ordered_keys.append(i)
				pairs[i] = (plans[i-1].timestamp,plan.timestamp)
		camq=leginondata.CameraEMData(ccdcamera=decameradata,dimension=dim)
		camq['save frames'] = True
		imageq = leginondata.AcquisitionImageData(camera=camq)
		print 'Query all DE12 images.  This may take some time...'
		images = imageq.query()
		print 'Total of %d images' % (len(images),)
		for image in images:
			if image['corrector plan']:
				continue
			for key in ordered_keys:
				if image.timestamp > pairs[key][1] and image.timestamp < pairs[key][0]:
					print key,image.dbid,image['filename'],image.timestamp
					status = self.leginon_dbupgrade.updateColumn('AcquisitionImageData','REF|CorrectorPlanData|corrector plan','%d' % plans[key].dbid,'`DEF_id`=%d' % image.dbid,True)
					if not status:
						print break_from_failed_update
		
if __name__ == "__main__":
	update = SchemaUpdate17224()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
