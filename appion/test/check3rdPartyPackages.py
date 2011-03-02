#!/usr/bin/env python

from appionlib import apParam
from appionlib import apDisplay

package = "Unknown"
packageDict = {
               "embfactor64.exe" : (package,""),
               "mpirun" : (package,"For Alignments and Refinements."),
	}
package = "Appion"
packageDict.update({
               "can64.exe" : (package,""),
               "ace2correct.exe" : (package,"For CTF correction"),
               "ace2.exe" : (package,"For CTF estimation"),
               "acetilt.py" : (package,""),
               "findem64.exe" : (package,"Also check for which findem32.exe."),
	})
package = "EMAN"
packageDict.update({
							 "proc2d" : (package,"For Image Manipulation"),
	})
package = "SPIDER"
packageDict.update({
							 "spider" : (package,"For Alignments and Refinements."),
	})
package = "XMIPP"
packageDict.update({
               "xmipp_normalize" : (package,""),
               "xmipp_mpi_ml_align2d" : (package,""),
               "xmipp_ml_align2d" : (package,""),
               "xmipp_mpi_angular_project_library" : (package,""),
               "xmipp_mpi_angular_projection_matching" : (package,""),
               "xmipp_mpi_angular_class_average" : (package,""),
               "xmipp_mpi_reconstruct_wbp" : (package,""),
               "xmipp_mpi_ml_refine3d" : (package,""),
               "xmipp_protocols" : (package,""),
	})
package = "Gregoriff Lab"
packageDict.update({
               "ctffind64.exe" : (package,""),
               "ctftilt64.exe" : (package,""),
               "rmeasure64.exe" : (package,"Also check for which rmeasure32.exe, rmeasure.exe, or rmeasure."),
               "signature64.exe" : (package,"For Signature Particle Picking. Also check which signature32.exe."),
	})
package = "IMOD"
packageDict.update({
               "imod" : (package,"For Tomography Alignment and Reconstruction"),
	})
package = "PROTOMO"
packageDict.update({
               "tomo-refine.sh" : (package,"For Tomography Alignment"),
               "tomo-fit.sh" : (package,"For Tomography Alignment"),
	})

outString = "The following third party processing package could not be found...\n"

for nameKey, desc in packageDict.iteritems():
    pathValue = apParam.getExecPath(nameKey, die=False)
    if pathValue is None:
        outString += "%s - From %s - %s\n"%(nameKey, desc[0], desc[1])

apDisplay.printColor(outString,"cyan")

