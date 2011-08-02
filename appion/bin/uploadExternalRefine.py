#!/usr/bin/env python

# python
import os

# appion
from appionlib import reconUploader

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
			for j in range(self.runparams['numberOfReferences']):
										
				### make chimera snapshot of volume
				vol = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration, j+1))
				self.createChimeraVolumeSnapshot(vol, iteration, j+1)
				
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

