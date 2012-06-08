#!/usr/bin/env python
import schemabase
from appionlib import appiondata, apDisplay
import sys,os

class SchemaUpdate16446(schemabase.SchemaUpdate):
	'''
	This will cp excluded imageid list from ApFullTomogramRunData to ApFullTomogramData
	'''

	def upgradeAppionDB(self):
		if self.appion_dbupgrade.tableExists('ApFullTomogramRunData') and self.appion_dbupgrade.tableExists('ApFullTomogramData'):
			if (not self.appion_dbupgrade.columnExists('ApFullTomogramRunData','SEQ|excluded')):
				apDisplay.printWarning('No excluded image column available, not need for column move')
				return

			if (not self.appion_dbupgrade.columnExists('ApFullTomogramData','SEQ|excluded')):
				self.appion_dbupgrade.addColumn('ApFullTomogramData', 'SEQ|excluded', self.appion_dbupgrade.str)
			q = appiondata.ApFullTomogramData()
			results = q.query()
			for qdata in results:
				rundata = qdata['reconrun']
				try:
					runid = rundata.dbid
				except:
					apDisplay.printWarning('No associated ApFullTomgramRunData. Skip')
					continue
				tid = qdata.dbid
				query = "Select `SEQ|excluded` from %s.`ApFullTomogramRunData` where `DEF_id`=%d;" % (self.appion_dbupgrade.dbname,runid)
				results = self.appion_dbupgrade.returnCustomSQL(query)
				excludetext = results[0][0]
				try:
					existing_excludetext = results[0][0]
				except IndexError:
					apDisplay.printWarning('No excluded image info available, not need for column move')
					continue

				# only do the schema upgrade if ApFullTomogramData has no value in SEQ|excluded'
				existing_excludetext = None
				query = "Select `SEQ|excluded` from %s.`ApFullTomogramData` where `DEF_id`=%d;" % (self.appion_dbupgrade.dbname,runid)
				results = self.appion_dbupgrade.returnCustomSQL(query)
				try:
					existing_excludetext = results[0][0]
				except IndexError:
						pass
				if (excludetext and not existing_excludetext):
					query = "Update ApFullTomogramData set `SEQ|excluded`='%s' WHERE ApFullTomogramData.`DEF_id`=%d;" % (excludetext,tid)
					self.appion_dbupgrade.executeCustomSQL(query)

if __name__ == "__main__":
	update = SchemaUpdate16446()
	# update only appion database
	update.setRequiredUpgrade('appion')
	update.run()

