#! /usr/bin/env python
# script for making tilt groups from an appion ctf star file
# based on Bill Rice's Tiltgroup Wrangler program 
# write relion 3 starfile output
# authors: Bill Rice and Sargis Dallakyan. Thank you to Bridget Carragher for idea and directing, Huihui Kuang and Kashyap Maruthi for usage and feedback, and all SEMS staff https://semc.nysbc.org/about/staff/ 
# requirements: python 2.7 or 3.X?
# 	numpy
#	scikit-learn
# python2.x needed works with this specific version (won't work with the latest scikit-learn from pip)
# pip install scikit-learn==0.19.2 
# pip install numpy==1.13.3

import os, sys
import re
import numpy as np
from sklearn.cluster import KMeans
import argparse

rln_ctfstring = '_rlnCtfMaxResolution'
rln_micstring = '_rlnMicrographName'
rln_tiltxstring = '_rlnBeamTiltX'
rln_tiltystring = '_rlnBeamTiltY'

N_CLUSTERS = 50 #for sklearn.cluster.KMeans
class TiltWrangler:
	def __init__(self, input):
		self.starlabels = []
		self.stardata = []
		self.maxctfindex = -1
		self.micnameindex = -1
		self.tiltxindex = -1
		self.tiltyindex = -1
		self.DEBUG=0
		self.starfile = input
		
	def relion3write(self):
		starfile="tw_out.star"	
		try:
			f=open(starfile, "w")
		except IOError:
			sys.stderr.write("ERROR", "Cannot open " + starfile + " for writing")
		else:
			with f:	
				f.write("data_\n\n")
				f.write("loop_\n")
				i=1
				for header in self.starlabels:
					f.write(header + " #" + str(i) + "\n")
					i += 1
				if self.tiltxindex >= 0:
					f.write("_rlnBeamTiltClass #" + str(i) + "\n")#thanks to Huihui and Kashyap for finding the missing hash sign
	
				if 1==1:  # zero out the tilt values, keep as string for simplicity
					for i in range (len(self.stardata)):
						self.stardata[i][self.tiltxindex] = str(0)
						self.stardata[i][self.tiltyindex] = str(0)
				if self.tiltxindex >= 0:
					i=0
					for dataline in self.stardata:
						f.write(" ".join(dataline))
						f.write(" " + str(self.grouplabels[i]) + "\n")
						i += 1
				sys.stdout.write("Success: Wrote " + starfile+ "\n")

	def relion31write(self):
		starfile="tw_out.star"	
		try:
			f=open(starfile, "w")
		except IOError:
			# error warning
			sys.stderr.write("ERROR", "Cannot open " + starfile + " for writing")
		else:
			with f:	
				f.write("# optics table \n")
				f.write("# version 30001\n\n")
				f.write("data_optics\n\n")
				f.write("loop_ \n")
				f.write("_rlnOpticsGroupName #1 \n")
				f.write("_rlnOpticsGroup #2 \n")
				f.write("_rlnMicrographPixelSize #3 \n")
				f.write("_rlnMicrographOriginalPixelSize #4 \n")
				f.write("_rlnVoltage #5 \n")
				f.write("_rlnSphericalAberration #6 \n")
				f.write("_rlnAmplitudeContrast #7 \n")
				i=0

				voltage = self.stardata[0][self.voltindex]
				sa = self.stardata[0][self.sa_index]
				amp_cntrst = self.stardata[0][self.amp_index]
				pix_size = self.stardata[0][self.pix_index]
				
				if self.tiltxindex >= 0:
					for i in range(N_CLUSTERS):
						groupname = "opticsGroup" + str(i + 1) 	
						line = "   ".join((groupname,str(i + 1),pix_size,pix_size,voltage,sa,amp_cntrst,"\n"))
						f.write(line)
				else:
					line = "   ".join(("opticsGroup1",str(1),pix_size,pix_size,voltage,sa,amp_cntrst,"\n"))
					f.write(line)
				
				f.write("\n# version 30001\n\n")
				f.write("data_micrographs\n\n")
				f.write("loop_ \n")
				f.write("_rlnMicrographName #1\n")
				f.write("_rlnOpticsGroup #2\n")
				f.write("_rlnCtfImage #3\n") 
				f.write("_rlnDefocusU #4\n") 
				f.write("_rlnDefocusV #5\n") 
				f.write("_rlnCtfAstigmatism #6\n") 
				f.write("_rlnDefocusAngle #7\n") 
				f.write("_rlnCtfFigureOfMerit #8\n") 
				f.write("_rlnCtfMaxResolution #9\n") 
	
				i=0
				for dataline in self.stardata:
					name=dataline[self.micnameindex]
					ctfname=dataline[self.ctfimage_index]
					dfu=dataline[self.dfu_index]
					dfv=dataline[self.dfv_index]
					dfa=dataline[self.dfa_index]
					fom=dataline[self.fom_index]
					ctfmax=dataline[self.maxctfindex]
					astig = str(abs(float(dfu)-float(dfv)))
					if self.tiltxindex >= 0:
						ogroup=str(self.grouplabels[i] + 1)
					else:
						ogroup="1"
					f.write("   ".join((name,ogroup,ctfname,dfu,dfv,astig,dfa,fom,ctfmax,"\n")))
					i += 1
				sys.stdout.write("Success: Wrote " + starfile+ "\n")
				
	def findtiltgroups(self):
		xval = []
		yval=[]
		for micrograph in self.stardata:	
			xval.append(float(micrograph[self.tiltxindex]))
			yval.append(float(micrograph[self.tiltyindex]))
		self.X=np.array(list(zip(xval,yval)))
		self.kmeans=KMeans(n_clusters=N_CLUSTERS)
		self.kmeans=self.kmeans.fit(self.X)
		self.grouplabels=self.kmeans.predict(self.X)
		self.clusters=self.kmeans.cluster_centers_

	def replaceDW(self):
		for i in range(len(self.stardata)):
			self.stardata[i][self.micnameindex] =  re.sub(r'\.mrc$', '-DW.mrc', self.stardata[i][self.micnameindex])
				
	def Readstar(self): 		
		starfile = os.path.abspath(self.starfile)		
		try:
			f=open(starfile)
		except IOError:
			sys.stderr.write("ERROR: File not found: "+starfile+"\n")
		else:
			with f:
				rr = f.read().splitlines()
				self.filelength = len(rr)
				for line in rr:
					if line[0:4] == "_rln":
						self.starlabels.append(line.split()[0])
					else:
						linedata=line.split()
					if len(linedata) >2:
						self.stardata.append(linedata)
			l2 = len(self.starlabels)
			l3 = len(self.stardata)	
			for i in range (l2):
				if self.starlabels[i] == rln_ctfstring:
					self.maxctfindex = i
				elif self.starlabels[i] == rln_micstring:
					self.micnameindex = i
				elif self.starlabels[i] == rln_tiltxstring:
					self.tiltxindex = i
				elif self.starlabels[i] == rln_tiltystring:
					self.tiltyindex = i
				elif self.starlabels[i] == "_rlnVoltage":
					self.voltindex = i
				elif self.starlabels[i] == "_rlnSphericalAberration":
					self.sa_index = i
				elif self.starlabels[i] == "_rlnAmplitudeContrast":
					self.amp_index=i
				elif self.starlabels[i] == "_rlnDetectorPixelSize":
					self.pix_index=i
				elif self.starlabels[i] == "_rlnBeamTiltX":
					self.btiltx_index=i
				elif self.starlabels[i] == "_rlnBeamTiltY":
					self.btilty_index=i
				elif self.starlabels[i] == "_rlnDefocusU":
					self.dfu_index=i
				elif self.starlabels[i] == "_rlnDefocusV":
					self.dfv_index=i
				elif self.starlabels[i] == "_rlnDefocusAngle":
					self.dfa_index=i
				elif self.starlabels[i] == "_rlnCtfFigureOfMerit":
					self.fom_index=i
				elif self.starlabels[i] == "_rlnCtfMaxResolution":
					self.ctfmax_index=i
				elif self.starlabels[i] == "_rlnCtfImage":
					self.ctfimage_index=i					
			if l2 < 5:
				sys.stderr.write("WARNING", "Only " +str(l2) + " columns in star file!")
				
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Tiltgroup Wrangler CLI for making lilt groups from an Appion ctf star file')
	parser.add_argument('input_star_file', help='path to input star file')
	parser.add_argument('-n_kmeans', type=int, default=50, help='number of cluster for k-means (defaults to 50)')
	parser.add_argument('-r_version', choices=['relion31', 'relion3'], default='relion31', help='write output for Relion 3.1 (relion31) or 3.0 (relion3')
		
	args = parser.parse_args()
	input_star = args.input_star_file		
	N_CLUSTERS = args.n_kmeans
	r_version = args.r_version
	
	tilt_wrangler = TiltWrangler(input_star)
	tilt_wrangler.Readstar()
	tilt_wrangler.replaceDW()
	tilt_wrangler.findtiltgroups()
	if r_version == "relion31":
		tilt_wrangler.relion31write()
	else:
		tilt_wrangler.relion3write()
