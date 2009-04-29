
## python
import time
import os
## PIL
import numpy
#import Image
## spider
import spyder
## appion
#from apSpider import operations ### fails
import apImage
import apParam
import apDisplay
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


