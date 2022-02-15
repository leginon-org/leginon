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
			if l2 < 5:
				sys.stderr.write("WARNING", "Only " +str(l2) + " columns in star file!")
				
if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.stderr.write("Usage: python tiltgroup_wrangler_cli.py input_star_file n_kmeans (optional: defaults to 50)\n")
		sys.exit(1)
	elif len(sys.argv) > 2:
		N_CLUSTERS = int(sys.argv[2])
	input_star = sys.argv[1]	
	tilt_wrangler = TiltWrangler(input_star)
	tilt_wrangler.Readstar()
	tilt_wrangler.replaceDW()
	tilt_wrangler.findtiltgroups()
	tilt_wrangler.relion3write()
