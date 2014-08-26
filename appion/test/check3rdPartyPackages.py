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
               "can64_mp.exe" : (package,""),
               "ace2correct.exe" : (package,"For CTF correction"),
               "ace2.exe" : (package,"For CTF estimation"),
               "acetilt.py" : (package,""),
               "findem64.exe" : (package,"Try 'which findem32.exe' at a command prompt."),
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
package = "Grigorieff Lab"
packageDict.update({
               "ctffind64.exe" : (package,""),
               "ctftilt64.exe" : (package,""),
               "rmeasure64.exe" : (package,"Try 'which rmeasure32.exe'(or rmeasure.exe, or rmeasure) at a command promt."),
               "signature64.exe" : (package,"For Signature Particle Picking. Try 'which signature32.exe' at a command prompt."),
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

outString = "The following third party processing packages could not be found...\n\n"

for nameKey, desc in packageDict.iteritems():
    pathValue = apParam.getExecPath(nameKey, die=False)
    if pathValue is None:
        outString += "|\tFrom %s, (%s) %s\n|\n"%(desc[0], nameKey,  desc[1])
        
outString += "For installation instructions visit:\n\t http://ami.scripps.edu/redmine/projects/appion/wiki/Processing_Server_Installation\n"
apDisplay.printColor(outString,"cyan")

