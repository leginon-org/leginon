
## python
import time
import os
import numpy
## spider
from appionlib import spyder
## appion
#from apSpider import operations ### fails
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
try:
	from pyami import spider
except:
	print "could not import spider from pyami"

"""
A collection of volume-related SPIDER functions

syntax/nomenclature:

volume file:
        *****vol.spi
image file: 
	*****img.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

"""


#===============================
def pdb2vol(pdbfile, apix, box, outfile, dataext=".spi"):
	outfile = spyder.fileFilter(outfile)
	### create volume density file from PDB
	if not os.path.isfile(pdbfile):
		apDisplay.printError("Can not find PDB file for conversion: "+pdbfile)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	### command request: infile, apix, center (y/n), atoms/temperature, boxsize, outfile 
	boxsize = "%i, %i, %i" %(box, box, box)
	mySpider.toSpider("CP FROM PDB", 
		spyder.fileFilter(pdbfile), 
		str(round(apix,5)), 
		"Y", "A", 
		boxsize, 
		spyder.fileFilter(outfile))
	mySpider.close()
	if not os.path.isfile(outfile+dataext):
		apDisplay.printError("SPIDER could not create density file: "+outfile+dataext)

	return

#===============================
def rotAndShiftVol(invol,outvol,rot=(0,0,0),center=(0,0,0),shift=(0.0,0.0,0.0),dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext, logo=False, log=True)
	else:
		mySpi=inMySpi
	vol1=spyder.fileFilter(invol)
	tmpvol=spyder.fileFilter('temp')
	vol3=spyder.fileFilter(outvol)
	cleanlist = []
	invol = vol1
	if rot != (0,0,0):
		outvol = tmpvol
		rot = tuple(map((lambda x: float(x)), rot))
		rotstr = '%.2f,%.2f,%.2f' % rot
		center = tuple(map((lambda x: float(x)), center))
		centerstr = '%.1f,%.1f,%.1f' % center
		mySpi.toSpider("RT 3A",invol,outvol,rotstr,centerstr)
		cleanlist.append(invol)
		invol = tmpvol
	if shift != (0,0,0):
		outvol = vol3
		shift = tuple(map((lambda x: float(x)), shift))
		shiftstr = '%f.1,%f.1,%f.1' % shift
		mySpi.toSpider("SH",invol,outvol,shiftstr)
		cleanlist.append(invol)
		invol = outvol
	if outvol != vol3:
		mySpi.toSpider("CP",invol,vol3)
		
	if inMySpi is False:
		mySpi.close()
	for cleanfile in cleanlist:
		os.remove(cleanfile+'.spi')
