#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
import subprocess
import shutil
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
#appion
from appionlib import appionScript
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import apChimera
from appionlib import apEulerJump
from appionlib import apEulerCalc
from appionlib import apStack
from appionlib import apModel
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apSymmetry
from appionlib import apRecon
from appionlib import apFrealign
from appionlib import reconUploader
from appionlib import apFile
from appionlib import starFile
from appionlib import apParticle
from appionlib import apCtf

'''
Written for Relion 2.1
'''

class UploadRelion3DRefine(reconUploader.generalReconUploader):
	
	#======================================================
	def setupParserOptions(self):
		self.parser.set_usage("Usage:\nuploadRelion3DRefine.py <starfile> --session=09dec07a\n")
		self.parser.add_option("-s", "--session", dest="sessionname", type="str", 
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("--starfile", dest="starfile", type="str",
			help="Full directory to converged Relion 3D auto-refine .star file, which has the name run_data.star. Other required inputs will be scrapped from the same directory.", metavar="FILE")
		self.parser.add_option("--recenter", dest="recenter", help="Option to recenter the particles based on shifts during 3D auto-refine (OriginX and OriginY).", action="store_true",default=False)
		self.parser.add_option("--noinsert", dest="noinsert", default=False, help="Option to turn off insert.", action="store_true")

	#======================================================	
	def checkConflicts(self):
		# get list of input images, since wildcards are supported
		if self.params['starfile'] is None:
			apDisplay.printError("Please enter the image names with picked particle files")
		elif os.path.basename(self.params['starfile']) != "run_data.star":
			print (os.path.basename(self.params['starfile']))
			apDisplay.printError("Please select a run_data.star from the Relion 3D Refine directory")
		if self.params['sessionname'] is None:
			apDisplay.printError("Please enter Name of session to upload to, e.g., --session=09dec07a")
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
	
	#======================================================	
	def Read01_runjob(self):
		relion_directory = os.path.dirname(self.params['starfile'])
		
		## Extract diameter and symmetry from run.job
		if (os.path.isfile(os.path.join(relion_directory,"run.job")) == False):
			apDisplay.printError("Could not find file: " + os.path.join(relion_directory,"run.job"))
		else:
			shutil.copy(os.path.join(relion_directory,"run.job"),self.params['rundir'])
			Input01_RunJob = os.path.join(self.params['rundir'],"run.job")
			a = open(Input01_RunJob)
			b = a.readlines()
			for c in b:
				if (c[:21] == "Mask diameter (A): =="):
					particle_diameter = int(c[22:])
				if (c[:12] == "Symmetry: =="):
					particle_symmetry = str(c[13:])
			a.close()
			
		return particle_diameter,particle_symmetry
		
	#======================================================	
	def Read02_modelstar(self):
		relion_directory = os.path.dirname(self.params['starfile'])
		
		## Extract pixel size and current resolution from model.star
		if (os.path.isfile(os.path.join(relion_directory,"run_model.star")) == False):
			apDisplay.printError("Could not find file: " + os.path.join(relion_directory,"run_model.star"))
		else:
			shutil.copy(os.path.join(relion_directory,"run_model.star"),self.params['rundir'])
			Input02_ModelStar = os.path.join(self.params['rundir'],"run_model.star")
			starData = starFile.StarFile(Input02_ModelStar)
			starData.read()
			dataBlock = starData.getDataBlock("data_model_general")
			pixelsize = float(dataBlock.getLabelDict()["_rlnPixelSize"])
			current_resolution = float(dataBlock.getLabelDict()["_rlnCurrentResolution"])
		
		return pixelsize,current_resolution
		
	#======================================================	
	def Read03_rundatastar(self,particle_diameter,pixelsize):
		#relion_directory = os.path.dirname(self.params['starfile'])
		
		## Extract information from run_data.star
		if (os.path.isfile(self.params['starfile']) == False):
			apDisplay.printError("Could not find file: " + self.params['starfile'])
		else:
			shutil.copy(self.params['starfile'],self.params['rundir'])
			Input03_StarFile = os.path.join(self.params['rundir'],"run_data.star")
			preset_used,micrograph_dimensions,defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb = self.readPartStarFile(Input03_StarFile,particle_diameter,pixelsize)
		
		return preset_used,micrograph_dimensions,defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb

	#======================================================				
	def Read04_maps(self,pixelsize):
		relion_directory = os.path.dirname(self.params['starfile'])
		
		if (os.path.isfile(os.path.join(relion_directory,"run_half1_class001_unfil.mrc")) == False):
			apDisplay.printError("Could not find file: " + os.path.isfile(os.path.join(relion_directory,"run_half1_class001_unfil.mrc")))
		elif (os.path.isfile(os.path.join(relion_directory,"run_half2_class001_unfil.mrc")) == False):
			apDisplay.printError("Could not find file: " + os.path.isfile(os.path.join(relion_directory,"run_half2_class001_unfil.mrc")))
		elif (os.path.isfile(os.path.join(relion_directory,"run_class001.mrc")) == False):
			apDisplay.printError("Could not find file: " + os.path.isfile(os.path.join(relion_directory,"run_class001.mrc")))		
		else:
			shutil.copy(os.path.join(relion_directory,"run_half1_class001_unfil.mrc"),self.params['rundir'])
			shutil.copy(os.path.join(relion_directory,"run_half2_class001_unfil.mrc"),self.params['rundir'])
			shutil.copy(os.path.join(relion_directory,"run_class001.mrc"),self.params['rundir'])
			half1 = os.path.join(self.params['rundir'],"run_half1_class001_unfil.mrc")
			half2 = os.path.join(self.params['rundir'],"run_half2_class001_unfil.mrc")
			
		emancmd = 'proc3d %s %s apix=%f fsc=eman.fsc' % (half1, half2, pixelsize)
		apEMAN.executeEmanCmd(emancmd, verbose=True)

	#======================================================				
	def Read05_bild(self):
		relion_directory = os.path.dirname(self.params['starfile'])
		
		if (os.path.isfile(os.path.join(relion_directory,"run_class001_angdist.bild")) == False):
			apDisplay.printError("Could not find file: " + os.path.isfile(os.path.join(relion_directory,"run_class001_angdist.bild")))
		else:
			shutil.copy(os.path.join(relion_directory,"run_class001_angdist.bild"),self.params['rundir'])

	#======================================================				
	def Read06_logs(self):
		relion_directory = os.path.dirname(self.params['starfile'])
		
		if (os.path.isfile(os.path.join(relion_directory,"run.out")) == False):
			apDisplay.printError("Could not find file: " + os.path.isfile(os.path.join(relion_directory,"run.out")))
		elif (os.path.isfile(os.path.join(relion_directory,"run.err")) == False):
			apDisplay.printError("Could not find file: " + os.path.isfile(os.path.join(relion_directory,"run.err")))
		else:
			try: ## Relion makes these run.err unreadable by others sometimes
				shutil.copy(os.path.join(relion_directory,"run.err"),self.params['rundir'])
				shutil.copy(os.path.join(relion_directory,"run.out"),self.params['rundir'])
			except:
				apDisplay.printError("Do not have permissions to read the run.err and run.out files. Change file permissions.")

	#======================================================
	def readPartStarFile(self, inputfile, particle_diameter, pixelsize):
		starData = starFile.StarFile(inputfile)
		starData.read()
		
		if not starData.getDataBlock('data_images'):
			dataBlock = starData.getDataBlock('data_')
		else:
			dataBlock = starData.getDataBlock('data_images')
		
		particleTree = dataBlock.getLoopDict()
		
		if len(particleTree) < 1:
			apDisplay.printError("Did not find any particles in star file: "+inputfile)
		
		apDisplay.printMsg("Reading %d particles..." % len(particleTree))
		
		## looplabels = ["_rlnCoordinateX", "_rlnCoordinateY","_rlnMicrographName","_rlnOriginX","_rlnOriginY","_rlnDefocusU","_rlnDefocusV","_rlnDefocusAngle"]		
		
		## Will save and process the .star file for Appion
		
		## Particles will be grouped by images in order to minimize number of queries for ImageData (which is slow)
		peaktree = {} # For uploading
		
		# For analysis
		defocusU = []
		defocusV = []
		astig = []
		coordX = []
		coordY = []
		anglePsi = []
		angleRot = []
		angleTilt = []
		maxProb = []
		# scaling factor for recentering
		scalefactor = None
		
		for particle in particleTree:
			micrograph = (os.path.splitext(os.path.basename(particle['_rlnMicrographName']))[0])
			if not peaktree.get(micrograph):
				peaktree[micrograph] = []
			#imgdatalist.append(apDatabase.getImageData(os.path.splitext(os.path.basename(particle['_rlnMicrographName']))[0]))
			
			defocusU.append(float(particle['_rlnDefocusU']))
			defocusV.append(float(particle['_rlnDefocusV']))
			astig.append(float(particle['_rlnDefocusAngle']))
			coordX.append(float(particle['_rlnCoordinateX']) + float(particle['_rlnOriginX']))
			coordY.append(float(particle['_rlnCoordinateY']) + float(particle['_rlnOriginY']))
			anglePsi.append(float(particle['_rlnAnglePsi']))
			angleRot.append(float(particle['_rlnAngleRot']))
			angleTilt.append(float(particle['_rlnAngleTilt']))
			maxProb.append(float(particle['_rlnMaxValueProbDistribution']))
			
			if (self.params['recenter'] is True):
				if not scalefactor:
					orig_apix = apDatabase.getPixelSize(apDatabase.getImageData(micrograph))
					scalefactor = pixelsize/orig_apix
				peakdict = {
					'diameter': particle_diameter,
					'xcoord': float(particle['_rlnCoordinateX']) - (scalefactor*float(particle['_rlnOriginX'])),
					'ycoord': float(particle['_rlnCoordinateY']) - (scalefactor*float(particle['_rlnOriginY'])),
					'peakarea': 10,
				}
			else:
				peakdict = {
					'diameter': particle_diameter,
					'xcoord': float(particle['_rlnCoordinateX']),
					'ycoord': float(particle['_rlnCoordinateY']),
					'peakarea': 10,
				}
			peaktree[micrograph].append(peakdict)
				
		# Run another loop to insert particles. Not able to nest the loop previously because the Relion .star might not have particles sorted by micrograph
		micrographs = peaktree.keys()
		preset_used = apDatabase.getImageData(micrographs[0])['preset']['name']
		micrograph_dimensions = (apDatabase.getImageData(micrographs[0])['preset']['dimension']['x'],apDatabase.getImageData(micrographs[0])['preset']['dimension']['y'])
		
		if self.params['noinsert'] is False:
			apDisplay.printMsg("Insert particle picks")
			for micrograph in micrographs:
				imagedata = (apDatabase.getImageData(micrograph))
				if imagedata['session']['name'] != self.sessiondata['name']:
					apDisplay.printError("Session and Image do not match "+imgtree[0]['filename'])	
				if self.params['commit'] is True:
					apParticle.insertParticlePeaks(peaktree[micrograph], imagedata, self.params['runname'], msg=True)

		return preset_used,micrograph_dimensions,defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb
				
	#======================================================
	def insertManualParams(self,particle_diameter):

		runq = appiondata.ApSelectionRunData()
		runq['name'] = self.params['runname']
		runq['session'] = self.sessiondata
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['program'] = 'relion'
		rundatas = runq.query(results=1)
		if rundatas and rundatas[0]['params']['diam'] != particle_diameter:
			apDisplay.printError("upload diameter not the same as last run")

		manparams = appiondata.ApSelectionParamsData()
		manparams['diam'] = particle_diameter
		runq['params'] = manparams

		if self.params['commit'] is True:
			apDisplay.printColor("Inserting manual selection run into database", "green")
			runq.insert()

		return runq
	
	#======================================================	
	def GetBestCTFValues(self,preset_used):
		imgtree = apDatabase.getImagesFromDB(self.sessiondata['name'],preset_used)
		BestAppiondefocus1 = []
		BestAppiondefocus2 = []
		for micrograph in imgtree:
			try:
				BestAppiondefocus1.append((apCtf.ctfdb.getBestCtfValueForImage(micrograph, msg=False)[0]['defocus1'])*(10**10))
				BestAppiondefocus2.append((apCtf.ctfdb.getBestCtfValueForImage(micrograph, msg=False)[0]['defocus2'])*(10**10))
			except:
				continue
		
		return BestAppiondefocus1,BestAppiondefocus2
		
	#======================================================
	def plot1dhistogram(self,inputlist1,inputlist2,name,xaxis,title):
	
		# the histogram of the data
		maxvalue = max(max(inputlist1),max(inputlist2))
		minvalue = min(min(inputlist1),min(inputlist2))
		plt.hist(inputlist1, range=(minvalue, maxvalue), bins=50, normed=1, facecolor='blue', alpha=1)
		plt.hist(inputlist2, range=(minvalue, maxvalue), bins=50, normed=1, facecolor='yellow', alpha=0.5)
		
		plt.xlabel(xaxis)
		plt.ylabel('Fraction of Data')
		plt.title(title)
		#plt.axis([40, 160, 0, 0.03])
		plt.grid(True)

		plt.savefig(os.path.join(self.params['rundir'],name + ".png"))
		shutil.move(os.path.join(self.params['rundir'],name + ".png"),os.path.join(self.params['rundir'],name + ".gif"))
		plt.close()

	#======================================================
	def plot2dhexplot(self,inputlist1,inputlist2,micrograph_dimensions,name,title):
		
		hb = plt.hexbin(inputlist1, inputlist2, gridsize=50, cmap='inferno')
		plt.xlim(0,micrograph_dimensions[0])
		plt.ylim(0,micrograph_dimensions[1])
		plt.title(title)
		legend = plt.colorbar(hb)
		legend.set_label('Number of particles')
		#plt.axis([40, 160, 0, 0.03])
		plt.grid(True)

		plt.savefig(os.path.join(self.params['rundir'],name + ".png"))
		shutil.move(os.path.join(self.params['rundir'],name + ".png"),os.path.join(self.params['rundir'],name + ".gif"))
		plt.close()

	#======================================================
	def plotfsc(self,spatialfreq_data,fsc_data):
		fscplot = plt.plot(spatialfreq_data,fsc_data)
		plt.xlabel('Spatial Frequency (1/A)')
		plt.ylabel('FSC')
		plt.title('Fourier Shell Correlation')
		plt.grid(True)
		plt.savefig(os.path.join(self.params['rundir'],"fsc.png"))
		shutil.move(os.path.join(self.params['rundir'],"fsc.png"),os.path.join(self.params['rundir'],"fsc.gif"))
		plt.close()

	#======================================================
	def calculateCorrelation(self,defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb):
		## Would be so easy with pandas...
		
		input = [defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb]
		length = len(input)
		
		w, h = length, length
		spearmancorr = [[0 for x in range(w)] for y in range(h)]
		pearsoncorr = [[0 for x in range(w)] for y in range(h)]
		
		
		for i in range(length):
			for j in range(length):
				rho, pvalue = scipy.stats.spearmanr(input[i],input[j])
				r, pvalue = scipy.stats.pearsonr(input[i],input[j])
				spearmancorr[i][j] = rho
				pearsoncorr[i][j] = r
	
		ax = plt.imshow(spearmancorr, interpolation="nearest", cmap='Blues',vmin=0,vmax=1)
		plt.grid(True)
		plt.title('Spearman Correlation')
		labels=["defocusU","defocusV","astig","coordX","coordY","anglePsi","angleRot","angleTilt","maxProb"]
		plt.xticks([0,1,2,3,4,5,6,7,8],labels,rotation=45,size=6)
		plt.yticks([0,1,2,3,4,5,6,7,8],labels,size=6)
		plt.colorbar(ax)
		plt.savefig(os.path.join(self.params['rundir'],"SpearmanCorrelation.png"))
		shutil.move(os.path.join(self.params['rundir'],"SpearmanCorrelation.png"),os.path.join(self.params['rundir'],"SpearmanCorrelation.gif"))
		plt.show()
		plt.close()
		
		## Negative values problem
		ax = plt.imshow(pearsoncorr, interpolation="nearest", cmap='seismic_r',vmin=-1,vmax=1)
		plt.grid(True)
		plt.title('Pearson Correlation')
		labels=["defocusU","defocusV","astig","coordX","coordY","anglePsi","angleRot","angleTilt","maxProb"]
		positions = [0,1,2,3,4,5,6,7,8]
		plt.xticks([0,1,2,3,4,5,6,7,8],labels,rotation=45,size=6)
		plt.yticks([0,1,2,3,4,5,6,7,8],labels,size=6)
		plt.colorbar(ax)
		plt.savefig(os.path.join(self.params['rundir'],"PearsonCorrelation.png"))
		shutil.move(os.path.join(self.params['rundir'],"PearsonCorrelation.png"),os.path.join(self.params['rundir'],"PearsonCorrelation.gif"))
		plt.show()
		plt.close()
	
	#======================================================
	def plotEulerAngleDistribution(self,angleRot,angleTilt):
		color_map = plt.cm.Spectral_r
		points = [angleRot,angleTilt]
	
		xbnds = np.array([0,360.0])
		ybnds = np.array([0,360.0])
		extent = [xbnds[0],xbnds[1],ybnds[0],ybnds[1]]

		fig=plt.figure(figsize=(10,9))
		ax = fig.add_subplot(111)
		plt.title('Euler Angle Distribution')

		image = plt.hexbin(angleRot,angleTilt,cmap=color_map,gridsize=20,extent=extent,mincnt=1,bins='log')

		counts = image.get_array()
		ncnts = np.count_nonzero(np.power(10,counts))
		verts = image.get_offsets()
		for offc in xrange(verts.shape[0]):
			binx,biny = verts[offc][0],verts[offc][1]
			if counts[offc]:
				plt.plot(binx,biny,'k.',zorder=100)
		ax.set_xlim(xbnds)
		ax.set_ylim(ybnds)
		plt.grid(True)
		plt.xlabel("Rot Angle (Degrees)")
		plt.ylabel("Tilt Angle (Degrees)")
		cb = plt.colorbar(image,spacing="uniform",extend="max",label="log(Number of Particles)")
		plt.savefig(os.path.join(self.params['rundir'],"EulerAngleDistribution.png"))
		shutil.move(os.path.join(self.params['rundir'],"EulerAngleDistribution.png"),os.path.join(self.params['rundir'],"EulerAngleDistribution.gif"))
		plt.show()
		plt.close()

	#======================================================
	def ThreeDFSC(self,pixelsize):
		import Image
		import ImageDraw
		
		img = Image.new('RGB', (200, 100))
		d = ImageDraw.Draw(img)
		d.text((20, 20), '3DFSC Coming Soon', fill=(255, 0, 0))
		
		img.save(os.path.join(self.params['rundir'],"ThreeDFSC.png"))
		shutil.move(os.path.join(self.params['rundir'],"ThreeDFSC.png"),os.path.join(self.params['rundir'],"ThreeDFSC.gif"))
		
	#======================================================
	def start(self):
		## Get diameter from run.job
		if self.params['recenter'] is True:
			apDisplay.printMsg("Recentering particles")
		apDisplay.printMsg("01: Reading run.job")
		particle_diameter,particle_symmetry = self.Read01_runjob()
		
		## Get pixel size and current resolution from run_model.star
		apDisplay.printMsg("02: Reading run_model.star")
		pixelsize,current_resolution = self.Read02_modelstar()
		
		## Insert params for manual picking
		apDisplay.printMsg("03: Setup manual picking session")
		rundata = self.insertManualParams(particle_diameter)
		
		## Insert particles from refinement as manual pick run
		apDisplay.printMsg("04: Reading run_data.star")
		preset_used,micrograph_dimensions,defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb = self.Read03_rundatastar(particle_diameter,pixelsize)
		
		## Copy over the maps and logs for display
		self.Read04_maps(pixelsize)
		self.Read05_bild()
		#self.Read06_logs()
		
		## Obtain best CTF values for the preset (All images)
		BestAppiondefocus1,BestAppiondefocus2 = self.GetBestCTFValues(preset_used)
		
		## Plot figures
		apDisplay.printMsg("05: Plotting analysis figures")
		self.plot1dhistogram(defocusU,BestAppiondefocus1,"DefocusU","Defocus ($\AA$)","DefocusU Values of All Micrographs (Yellow)\nversus Relion 3D Refine (Blue)")
		self.plot1dhistogram(defocusV,BestAppiondefocus2,"DefocusV","Defocus ($\AA$)","DefocusV Values of All Micrographs (Yellow)\nversus Relion 3D Refine (Blue)")
		self.plot2dhexplot(coordX,coordY,micrograph_dimensions,"XYcoordinates","Particle location on micrograph")
		self.plotEulerAngleDistribution(angleRot,angleTilt)
		self.ThreeDFSC(pixelsize)
		
		## Calculate Pearson and Spearman Correlations
		self.calculateCorrelation(defocusU,defocusV,astig,coordX,coordY,anglePsi,angleRot,angleTilt,maxProb)

		## Plot FSC Curve
		if not os.path.isfile(os.path.join(self.params['rundir'],"eman.fsc")):
			apDisplay.printMsg("eman.fsc file does not exists; self.Read04_maps() may not have completed properly.")

		f = open(os.path.join(self.params['rundir'],"eman.fsc"),"r")
		lines = f.readlines()
		spatialfreq_data = []
		fsc_data = []
		for line in lines:
			spatialfreq_data.append(line.split('\t')[0])
			fsc_data.append(line.split('\t')[1])

		self.plotfsc(spatialfreq_data,fsc_data)
		
		#apDisplay.printMsg("Getting image data from database")
		#imgtree = apDatabase.getSpecificImagesFromDB(boxfiles)
		#if imgtree[0]['session']['name'] != self.sessiondata['name']:
		#	apDisplay.printError("Session and Image do not match "+imgtree[0]['filename'])	

if __name__ == '__main__':
	UploadRelion3DRefine = UploadRelion3DRefine()
	UploadRelion3DRefine.start()
	UploadRelion3DRefine.close()

