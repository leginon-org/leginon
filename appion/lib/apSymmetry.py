import project
import sys
import os
import re
import apDisplay
import appionData
import apDatabase
import leginondata
import string
import apFile
from pyami import mrc


#===========================
def parseSymmetry(symtext):

	return

#===========================
def findSymmetry(symtext):
	# find the symmetry entry in the database
	# based on the text version from EMAN
	# first convert to lower case
	symtext = string.lower(symtext)
	symdataq = appionData.ApSymmetryData(eman_name=symtext)
	symdata = symdataq.query(results=1)
	if not symdata:
		apDisplay.printWarning("No symmetry found, assuming c1 (asymmetric)")
		symdataq = appionData.ApSymmetryData(eman_name = 'c1')
		symdata = symdataq.query(results=1)
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
	sys.stderr.write("ID   NAME         DESCRIPTION\n")
	sys.stderr.write("--   ----         -----------\n")
	syms.sort(compSymm)
	for s in syms:
		name = s['symmetry']
		name = re.sub('Icosahedral', 'Icos', name)
		sys.stderr.write( 
			apDisplay.colorString(apDisplay.rightPadString(s.dbid,3),"green")+" "
			+apDisplay.rightPadString(name,13)+" "
			+apDisplay.rightPadString(s['description'],60)+"\n"
		)









