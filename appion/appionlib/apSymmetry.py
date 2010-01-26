#!/usr/bin/env python

#python
import re
import sys
#appion
from appionlib import apDisplay
from appionlib import appiondata

#===========================
def findSymmetry(symtext, msg=True):
	apDisplay.printMsg("Looking up symmetry for input: %s"%(symtext))
	symdata = None
	if isinstance(symtext, int) or re.match("^[0-9]+$", symtext):
		### text is a number and probably a symm id
		symdata = getSymmetryDataFromID(symtext, msg)
	elif len(symtext) > 0:
		### text is not a number and probably a symm name
		symdata = getSymmetryDataFromName(symtext, msg)
	if not symdata:
		printSymmetries()
	return symdata

#===========================
def getSymmetryDataFromName(symtext='c1', msg=True):
	# find the symmetry entry in the database
	# based on the text version from EMAN
	# first convert to lower case
	symtext = symtext.lower()
	symdataq = appiondata.ApSymmetryData(eman_name=symtext)
	symdatas = symdataq.query()
	if not symdatas:
		apDisplay.printError("No symmetry named %s was found"%(symtext))
	# select oldest match
	symdata = symdatas[len(symdatas)-1]
	if msg is True:
		apDisplay.printMsg("Selected symmetry group: "
			+apDisplay.colorString("%s -- %s"%(symdata['eman_name'].upper(), symdata['symmetry']), "cyan"))
	return symdata

#===========================
def getSymmetryDataFromID(symid, msg=True):
	symdata = appiondata.ApSymmetryData.direct_query(int(symid))
	if not symdata:
		printSymmetries()
		apDisplay.printError("no symmetry associated with this id: "+str(symid))
	if msg is True:
		apDisplay.printMsg("Selected symmetry group: "
			+apDisplay.colorString("%s -- %s"%(symdata['eman_name'].upper(), symdata['symmetry']), "cyan"))
	return symdata

#===========================
def compSymm(a, b):
	if a.dbid > b.dbid:
		return 1
	else:
		return -1

#===========================
def printSymmetries():
	symq = appiondata.ApSymmetryData()
	syms = symq.query()
	sys.stderr.write("ID  NAME  DESCRIPTION\n")
	sys.stderr.write("--  ----  -----------\n")
	syms.sort(compSymm)
	for s in syms:
		name = s['eman_name']
		name = re.sub('Icosahedral', 'Icos', name)
		sys.stderr.write(
			apDisplay.colorString(apDisplay.rightPadString(s.dbid,3),"green")+" "
			+apDisplay.rightPadString(name,5)+" "
			+apDisplay.rightPadString(s['description'],60)+"\n"
		)

#=====================
def getSymmetryFromReconRunId(reconrunid, msg=True):
	"""
	get the symmetry from the last iteration of a refinement
	"""
	refrundata = appiondata.ApRefinementRunData.direct_query(reconrunid)
	refdataq = appiondata.ApRefinementData()
	refdataq['refinementRun'] = refrundata
	refdata = refdataq.query()
	uniqsym = refdata[0]['refinementParams']['symmetry']
	if uniqsym is None:
		apDisplay.printWarning("symmetry is not saved during reconstruction!")
		apDisplay.printWarning("Using the symmetry of the initial model")
		modeldata = refrundata['initialModel']
		uniqsym = modeldata['symmetry']
	else:
		for data in refdata:
			if uniqsym != data['refinementParams']['symmetry']:
				apDisplay.printWarning("symmetry is not consistent throughout reconstruction!")
				apDisplay.printWarning("Using symmetry of last iteration")
			uniqsym = data['refinementParams']['symmetry']
	if msg is True:
		apDisplay.printMsg("selected symmetry group: "
			+apDisplay.colorString("'"+uniqsym['eman_name']+"'", "cyan")
			+" for recon run: "+str(reconrunid))
	return uniqsym


#===========================
#===========================
if __name__ == "__main__":
	printSymmetries()







