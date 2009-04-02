#!/usr/bin/env python

#python
import re
import sys
#appion
import apDisplay
import appionData

#===========================
def parseSymmetry(symtext):
	if re.match("^[0-9]+$", symtext):
		### text is a number and probably a symm id
		symdata = getSymmetryData(symtext)
	elif len(symtext) > 0:
		### text is not a number and probably a symm name
		symdata = findSymmetry(symtext)
	else:
		printSymmetries()
	return symdata

#===========================
def findSymmetry(symtext='c1'):
	# find the symmetry entry in the database
	# based on the text version from EMAN
	# first convert to lower case
	symtext = symtext.lower()
	symdataq = appionData.ApSymmetryData(eman_name=symtext)
	symdata = symdataq.query(results=1)
	if not symdata:
		apDisplay.printError("No symmetry named %s was found"%(symtext))
	return symdata[0]

#===========================
def getSymmetryData(symid, msg=True):
	symdata = appionData.ApSymmetryData.direct_query(symid)
	if not symdata:
		printSymmetries()
		apDisplay.printError("no symmetry associated with this id: "+str(symid))
	if msg is True:
		apDisplay.printMsg("Selected symmetry group: "
			+apDisplay.colorString(str(symdata['symmetry']), "cyan"))
	return symdata

#===========================
def compSymm(a, b):
	if a.dbid > b.dbid:
		return 1
	else:
		return -1

#===========================
def printSymmetries():
	symq = appionData.ApSymmetryData()
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


#===========================
#===========================
if __name__ == "__main__":
	printSymmetries()






