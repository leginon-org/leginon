#!/usr/bin/env python

from appionlib import appiondata
from appionlib import apRecon
from appionlib import apProject
import leginon.projectdata

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

if __name__ == "__main__":
	projectids = getProjectIds()
	for projectid in projectids:
		if apProject.setDBfromProjectId(projectid, die=False):
			reconrunids = getReconRunsIds()
			for reconrunid in reconrunids:
				apRecon.setGoodBadParticlesFromReconId(reconrunid)
