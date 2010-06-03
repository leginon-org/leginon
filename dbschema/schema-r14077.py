#!/usr/bin/env python
import time
from appionlib import appiondata
from appionlib import apRecon
from appionlib import apProject
import leginon.projectdata
from sinedon import dbupgrade

"""
This is a simple script that will insert 
the number of good and bad particles
for a recon run

and do nothing if it exists already
"""

def getProjectIds():
	projectids = []
	projectq = leginon.projectdata.projects()
	projectdatas = projectq.query()
	if not projectdatas:
		return projectids
	for projectdata in projectdatas:
		projectids.append(projectdata.dbid)
	return projectids

def getReconRunsIds():
	reconrunids = []
	reconrunq = appiondata.ApRefineRunData()
	reconrundatas = reconrunq.query()
	if not reconrundatas:
		return reconrunids
	for reconrundata in reconrundatas:
		reconrunids.append(reconrundata.dbid)
	return reconrunids

def createExcludedColumnByFakeInsert():
	# maketable can not create this column.  Use an insert 
	# without other references.
	fakerunq = appiondata.ApFullTomogramRunData()
	fakerunq['excluded'] = [0]
	fakerunq.insert()

def getTomoAlignmentRuns():
	alignrunids = []
	alignrunq = appiondata.ApTomoAlignmentRunData()
	alignrundatas = alignrunq.query()

	if not alignrundatas:
		return []
	return alignrundatas

def insertTiltsInAlign(alignrun):
	q = appiondata.ApTiltsInAlignRunData()
	q['alignrun'] = alignrun
	q['tiltseries'] = alignrun['tiltseries']
	q['primary_tiltseries'] = True
	q.insert()

def upgradeProjectDB(projectdb,backup=True):
	### set version of database
	selectq = " SELECT * FROM `install` WHERE `key`='version'"
	values = projectdb.returnCustomSQL(selectq)
	if values:
		projectdb.updateColumn("install", "value", "'2.0'", 
			"install.key = 'version'",timestamp=False)
	else:
		insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('version', '2.0')"
		projectdb.executeCustomSQL(insertq)

if __name__ == "__main__":
	projectids = getProjectIds()
	projectdb = dbupgrade.DBUpgradeTools('projectdata', drop=True)
	for projectid in projectids:
		appiondbname = apProject.getAppionDBFromProjectId(projectid, die=False)
		if not projectdb.databaseExists(appiondbname):
			print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
			time.sleep(1)
			continue
		if apProject.setDBfromProjectId(projectid, die=False):
			reconrunids = getReconRunsIds()
			for reconrunid in reconrunids:
				apRecon.setGoodBadParticlesFromReconId(reconrunid)
			# Tomography upgrades
			createExcludedColumnByFakeInsert()
			allalignrundata = getTomoAlignmentRuns()
			for alignrun in allalignrundata:
				insertTiltsInAlign(alignrun)
	upgradeProjectDB(projectdb,backup=False)
