#!/usr/bin/env python

from appionlib import apParam
from appionlib import apDisplay


packageDict = {
               "xmipp_normalize" : "",
               "embfactor64.exe" : "",
               "proc2d" : "",
               "mpirun" : "For Alignments and Refinements.",
               "xmipp_mpi_ml_align2d" : "",
               "xmipp_ml_align2d" : "",
               "xmipp_mpi_angular_project_library" : "",
               "xmipp_mpi_angular_projection_matching" : "",
               "xmipp_mpi_angular_class_average" : "",
               "xmipp_mpi_reconstruct_wbp" : "",
               "xmipp_mpi_ml_refine3d" : "",
               "can64.exe" : "",
               "ctffind64.exe" : "",
               "ctftilt64.exe" : "",
               "spider" : "",
               "ace2correct.exe" : "",
               "ace2.exe" : "",
               "xmipp_protocols" : "",
               "apChimSnapshot.py" : "Not required.",
               "tomo-refine.sh" : "",
               "tomo-fit.sh" : "",
               "acetilt.py" : "",
               "findem64.exe" : "Also check for which findem32.exe.",
               "rmeasure64.exe" : "Also check for which rmeasure32.exe, rmeasure.exe, or rmeasure.",
               "signature64.exe" : "For Signature Particle Picking. Also check which signature32.exe.",
               }

outString = "The following third party processing packages could not be found...\n"

for nameKey, desc in packageDict.iteritems():
    pathValue = apParam.getExecPath(nameKey, die=False)
    if pathValue is None:
        outString += "%s - %s\n"%(nameKey, desc)

apDisplay.printColor(outString,"cyan")

