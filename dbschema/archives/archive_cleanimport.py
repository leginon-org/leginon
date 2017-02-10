#!/usr/bin/env python

import sys
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata

# This will clean up ImportMappingData after a project is imported.
# This is necessary because the query needs to check all entries and
# thus take up too much memory when it gets big
including_tablenames = ['ScopeEMData','CameraEMData','EMTargetData','AcquisitionImageTargetData','DriftData','QueueData','FocuserResultData','AcquisitionImageStatsData','AcquisitionImageData','DriftMonitorResultData','DDDinfoValueData','DequeuedImageTargetListData']

def cleanImportMappingData(database):
	if not database.tableExists('ImportMappingData'):
		return
	for tablename in including_tablenames:

			q = 'DELETE FROM `ImportMappingData` WHERE class_name like "%s";' % (tablename,)
			database.executeCustomSQL(q)

if __name__ == "__main__":
	projectdb = dbupgrade.DBUpgradeTools('projectdata')
	cleanImportMappingData(projectdb)
	leginondb = dbupgrade.DBUpgradeTools('leginondata')
	cleanImportMappingData(leginondb)
