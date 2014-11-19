#!/usr/bin/env python

# python
import os

# appion
from appionlib import reconUploader
from appionlib import apDisplay

#======================
#======================

class uploadExternalPackageScript(reconUploader.generalReconUploader):
	
	def __init__(self):
		###	DEFINE THE NAME OF THE PACKAGE
		self.package = "external_package"
		super(uploadExternalPackageScript, self).__init__()

	#=====================
	def start(self):
						
		### determine which iterations to upload; last iter is defaulted to infinity
		uploadIterations = self.verifyUploadIterations()				
					
		### upload each iteration
		for iteration in uploadIterations:
			for j in range(self.runparams['NumberOfReferences']):
										
				### general error checking, these are the minimum files that are needed
				vol = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration, j+1))
				particledatafile = os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol%.3d.txt" % (self.params['timestamp'], iteration, j+1))
				if not os.path.isfile(vol):
					apDisplay.printError("you must have an mrc volume file in the 'external_package_results' directory")
				if not os.path.isfile(particledatafile):
					apDisplay.printError("you must have a particle data file in the 'external_package_results' directory")										
										
				### make chimera snapshot of volume
				try:
					self.createChimeraVolumeSnapshot(vol, iteration, j+1)
				except:
					apDisplay.printWarning("could not create Chimera volume snapshots")
				
				### instantiate database objects
				self.insertRefinementRunData(iteration, j+1)
				self.insertRefinementIterationData(iteration, j+1)
				
		### calculate Euler jumps
		self.calculateEulerJumpsAndGoodBadParticles(uploadIterations)			
			
		
#=====================
if __name__ == "__main__":
	refine3d = uploadExternalPackageScript()
	refine3d.start()
	refine3d.close()

