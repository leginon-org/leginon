#!/usr/bin/env python
import datetime
import scandb
from appionlib import appiondata, apDisplay

class ScanCtf(scandb.ScanDB):
	'''
	This checks for most recent stack making and ctf estimation runs
	'''
	def __init__(self,backup=False):
		super(ScanCtf, self).__init__()
		self.deltadays = -1
		self.checktime = datetime.datetime.now() + datetime.timedelta(days=self.deltadays)

	def scanAppionDB(self):
		if self.appion_dbtools.tableExists('ApCtfData'):
			results = appiondata.ApCtfData().query(results=1)
			if results:
				ctfdata = results[0]
				if ctfdata.timestamp > self.checktime:
					print "\033[35m%s has new ApCtfData in %d day\033[0m" % (self.appion_dbtools.getDatabaseName(),-self.deltadays)
		if self.appion_dbtools.tableExists('ApStackRunData'):
			results = appiondata.ApStackRunData().query(results=1)
			if results:
				stackrundata = results[0]
				if stackrundata['stackParams']['phaseFlipped']:
					stackpartr = appiondata.ApStackParticleData(stackRun=stackrundata).query(results=1)
					if stackpartr:
						stackpartdata = stackpartr[0]
						if stackpartdata.timestamp > self.checktime:
							print "\033[35m%s has new particle inserted to Stack with phase flip in %d day\033[0m" % (self.appion_dbtools.getDatabaseName(),-self.deltadays)

if __name__ == "__main__":
	update = ScanCtf()
	update.run()
