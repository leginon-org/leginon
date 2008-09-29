
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
def pdb2vol(pdbfile, apix, box, outfile, dataext="spi"):
	### create volume density file from PDB
	import spyder
	spider_exe = os.popen("which spider").read().strip()
	mySpider = spyder.SpiderSession(spiderexec=spider_exe, dataext=dataext, logo=False)
	### command request: infile, apix, center (y/n), atoms/temperature, boxsize, outfile 
	boxsize = "%i %i %i" %(box, box, box)
	mySpider.toSpider("CP FROM PDB", pdbfile, apix, "Y", "A", boxsize, outfile)
	mySpider.close()
	return
