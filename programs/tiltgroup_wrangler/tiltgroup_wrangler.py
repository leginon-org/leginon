#! /usr/bin/env python
# script to give  agui for making tilt groups from an appion ctf star file
# allows for filtering based on best CTF fir value
# allws replacement of enn-a with enn-a-DW
# write relion 3 starfile output

# requirements: python 2.7 or 3.X
# 	Tkinter
# 	numpy
# 	matplotlib
#	scikit-learn

# TO DO
# relion 3.1 output
# freeplot to plot any colmnn vs any other column

#from tkinter import *
try: #python 3
	import tkinter as Tk
	from tkinter import messagebox
	from tkinter import filedialog
except: #python 2.7
	import Tkinter as Tk
	import tkMessageBox as messagebox
	import tkFileDialog as filedialog

import os
import re
import numpy as np
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use("TkAgg")  #use TKinter framework
import matplotlib.pyplot as plt


rln_ctfstring = '_rlnCtfMaxResolution'
rln_micstring = '_rlnMicrographName'
rln_tiltxstring = '_rlnBeamTiltX'
rln_tiltystring = '_rlnBeamTiltY'

class Window:
	def __init__(self):
		self.root = Tk.Tk()
		self.root.title('Tilt Group Wrangler')
		self.root.geometry("800x500")

		self.filename=Tk.StringVar()
		self.outstar=Tk.StringVar()
		self.mtffile=Tk.StringVar()
		self.cspfile=Tk.StringVar()
		self.passthrufile=Tk.StringVar()
		self.starlabels = []
		self.stardata = []
		self.maxctfindex = -1
		self.micnameindex = -1
		self.tiltxindex = -1
		self.tiltyindex = -1
		self.DEBUG=0

		self.selectfile_button = Tk.Button( self.root, text="Select File",command = self.selectfile)
		self.selectfile_button.grid(row=1, column=1, padx=10, pady=10)

		self.filelabel = Tk.Entry(self.root, textvariable=self.filename, width=60, borderwidth=5)
		self.filelabel.grid(row=1, column=2,columnspan=3)
		self.filename.trace('w', self.toggle_state)    #this should toggle the state of the read button depending on this variable	
		self.readfile_button = Tk.Button(self.root, text = "Read File", command=self.Readstar, state=Tk.DISABLED)
		self.readfile_button.grid(row=2, column=1, columnspan=1)

		self.fileinfo_button = Tk.Button(self.root, text = "File Info", command=self.fileinfo, state = Tk.DISABLED)
		self.fileinfo_button.grid(row=2, column=2)

		self.tiltgraph_button = Tk.Button(self.root, text = "Plot raw tilts", command = self.tiltgraph, background = '#0C0', state=Tk.DISABLED)
		self.tiltgraph_button.grid(row=3, column=1, padx=10, pady=10)

		self.ctfmaxplot_button = Tk.Button(self.root, text = "Plot CTF Max Resolution", command = self.ctfmaxplot, background = '#0C0', state=Tk.DISABLED)
		self.ctfmaxplot_button.grid(row=3, column=2, padx=10, pady=10)

		self.freeplot_button = Tk.Button(self.root, text = "Free Plot", command = self.freeplot, background = '#0C0', state=Tk.DISABLED)
		self.freeplot_button.grid(row=3, column=3, padx=10, pady=10)

		self.filterctf_button = Tk.Button(self.root, text = "Filter CTF", command = self.filterctf, state=Tk.DISABLED)
		self.filterctf_value = Tk.Entry(self.root, width=10, borderwidth=5)
		self.filterctf_label = Tk.Label(self.root, text = "Maximum CTF Resolution to keep")
		self.filterctf_label.grid(row=4, column=1, padx=10, pady=10)
		self.filterctf_value.grid(row=4, column=2, padx=10, pady=10)
		self.filterctf_button.grid(row=4, column=3, padx=10, pady=10)

		self.restorectf_button = Tk.Button(self.root, text= "Undo CTF Filter", command = self.restorectf, state=Tk.DISABLED)
		self.restorectf_button.grid(row=4, column=4, padx=10, pady=10)
		self.replaceDW_button = Tk.Button(self.root, text = "REPLACE", command = self.replaceDW, state=Tk.DISABLED)
		self.replaceDW_label = Tk.Label(self.root, text = "Replace enn-a with enn-a-DW?")
		self.replaceDW_label.grid(row=5, column=1, padx=10, pady=10)
		self.replaceDW_button.grid(row=5, column=2, padx=10, pady=10)

		self.tiltgroupslider_label = Tk.Label(self.root, text = "Number of tilt groups wanted")
		self.tiltgroupslider_label.grid(row=6, column=1, padx=10, pady=10)
		self.tiltgroupslider = Tk.Scale(self.root, length=200, from_=1, to=200, orient=Tk.HORIZONTAL)
		self.tiltgroupslider.set(50)  # intiialize with a decent value
		self.tiltgroupslider.grid(row=6, column=2, columnspan=1)
		self.tiltgroups_button = Tk.Button(self.root, text = "Find Groups", command = self.findtiltgroups, state=Tk.DISABLED)
		self.tiltgroups_button.grid(row=6, column=3, padx=10, pady=10)
		self.plottilts_button = Tk.Button(self.root, text = "Plot clusters", command = self.plottilts, state=Tk.DISABLED)
		self.plottilts_button.grid(row=6, column=4, padx=10, pady=10)

		self.outfile_label = Tk.Label(self.root, text = "Output filename")
		self.outfile_label.grid(row=7, column =1, padx=10, pady=10)
		self.outfile_entry = Tk.Entry(self.root, textvariable = self.outstar, width=30, borderwidth=5)
		self.outfile_entry.grid(row=7, column=2, padx=10,pady=10)
		self.outstar.trace('w', self.toggle_state)    #this should toggle the state of the read and write  button depending on this variable	
		self.outfile_relion3_button = Tk.Button(self.root, text = "Write Relion 3.0", command=self.relion3write, state=Tk.DISABLED)
		self.outfile_relion3_button.grid(row=7, column=3, padx=10, pady=10)
		self.outfile_relion31_button = Tk.Button(self.root, text = "Write Relion 3.1", command=self.relion31write, state=Tk.DISABLED)
		self.outfile_relion31_button.grid(row=7, column=4, padx=10, pady=10)
		self.mtffile.trace('w', self.toggle_state)    #this should toggle the state of the read and write  button depending on this variable	

		self.cryosparc_button = Tk.Button(self.root, text="Export to cryosparc data", command=self.cryosparc_export, background='teal')
		self.cryosparc_button.grid(row=9, column=1, padx=10, pady=10)
		self.quit_button = Tk.Button(self.root, text="QUIT", bg="red", command=quit)
		self.quit_button.grid(row=10, column=1, padx=10, pady=10, columnspan=1)


# all the functions
	def cryosparc_export(self):
		try:
			import dataset  #NEEDED for reading and writing cryosparc cs files
		except:
			response=messagebox.showerror("ERROR", "Cannot import required cryosparc library")
		else:
			self.cswindow = Tk.Toplevel()
			self.cswindow.title("Cryosparc Export")
			self.cswindow.geometry("800x400")

			self.readcsp_label = Tk.Label(self.cswindow, text="Input .cs particle file")
			self.readcsp_label.grid(row=1, column=3)
			self.readcsp_button = Tk.Button(self.cswindow, text="Select file", command=self.selectcsfile)
			self.readcsp_button.grid(row=1, column=1, padx=10, pady=10)
			self.readcsp_entry = Tk.Entry(self.cswindow, textvariable = self.cspfile, width=60, borderwidth=5)
			self.readcsp_entry.grid(row=1, column=2)

			self.readpassthru_label = Tk.Label(self.cswindow, text="Input .cs passthrough file")
			self.readpassthru_label.grid(row=2, column=3)
			self.readpassthru_button = Tk.Button(self.cswindow, text="Select file", command=self.selectpassthrufile)
			self.readpassthru_button.grid(row=2, column=1, padx=10, pady=10)
			self.readpassthru_entry = Tk.Entry(self.cswindow, textvariable = self.passthrufile, width=60, borderwidth=5)
			self.readpassthru_entry.grid(row=2, column=2)



			self.readcsp_button= Tk.Button(self.cswindow, text="Add groups", command=self.readcspfile)
			self.readcsp_button.grid(row=3, column=1, padx=10, pady=10)

			self.writecsp_label = Tk.Label(self.cswindow, text="Output filename")
			self.writecsp_label.grid(row=4,column=1, padx=10, pady=10)
			self.writecsp_entry = Tk.Entry(self.cswindow, width=30, borderwidth=5)
			self.writecsp_entry.grid(row=4, column=2)

			self.writecsp_button = Tk.Button(self.cswindow, text="Write file", command=self.writecspfile)
			self.writecsp_button.grid(row=4, column=3)

			
	def writecspfile(self):
		try:
			import dataset  #NEEDED for reading and writing cryosparc cs files
		except:
			response=messagebox.showerror("ERROR", "Cannot import required cryosparc library")
		else:
			outfile = self.writecsp_entry.get()
			self.particleset.to_file(outfile)
			response=messagebox.showinfo("Success", "Wrote " + outfile)

	def readcspfile(self):
		try:
			import dataset  #NEEDED for reading and writing cryosparc cs files
		except:
			response=messagebox.showerror("ERROR", "Cannot import required cryosparc library")
		else:
			self.particleset = dataset.Dataset().from_file(self.cspfile.get())
			self.passthruset = dataset.Dataset().from_file(self.passthrufile.get())
			if 'ctf/exp_group_id' in self.passthruset.data.keys():
				self.particleset = self.passthruset
				response=messagebox.showinfo("IMPORTANT","CTF information is in the passthrough file.\n Replace that file in cryosparc directory")
			elif 'ctf/exp_group_id' in self.particleset.data.keys():
				response=messagebox.showinfo("IMPORTANT","CTF information is in the particleset file.\n Replace that file in cryosparc directory")
			else:
				response=messagebox.showerror("ERROR","No CTF information found! Cannot group")
			groupdata={}
			for i, dataline in enumerate(self.stardata):
				filename = os.path.basename(dataline[self.micnameindex])
				groupdata[filename] = self.grouplabels[i]
			keys = groupdata.keys()
			if 'location/micrograph_path' in self.passthruset.data.keys():
				numbad=0
				for i in range(len(self.particleset.data)):
					filename = self.passthruset.data['location/micrograph_path'][i]
					basename =os.path.basename(filename)
					if basename in keys:
						self.particleset.data['ctf/exp_group_id'][i] = groupdata[basename]
					else: #no appion ctf data for this micrograph, put them all in their own tilt group
						#print ("error, no key found for " + basename)	
						self.particleset.data['ctf/exp_group_id'][i] = len(self.grouplabels) +1 
						numbad += 1
				if (numbad >0):
					response=messagebox.showwarning("WARNING", "Number of particles without good appion ctf data:\n" + str(numbad))
			else:
				response=messagebox.showerror("ERROR","No Micrograph filename information found! Cannot group")


	def selectpassthrufile(self):
		f = filedialog.askopenfilename(initialdir="./", title="Select a file", filetypes=(("cs files", "*.cs"), ("all files", "*.*")))
		self.readpassthru_entry.delete(0,Tk.END)
		self.readpassthru_entry.insert(0,f)

	def selectcsfile(self):
		f = filedialog.askopenfilename(initialdir="./", title="Select a file", filetypes=(("cs files", "*.cs"), ("all files", "*.*")))
		self.readcsp_entry.delete(0,Tk.END)
		self.readcsp_entry.insert(0,f)

	def relion31write(self):
		starfile=self.outfile_entry.get()	
		try:
			f=open(starfile, "w")
		except IOError:
			# error warning
			response=messagebox.showerror("ERROR", "Cannot open " + starfile + " for writing")
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
					for i in range(self.numgroups):
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
				response=messagebox.showinfo("Success", "Wrote " + starfile)


	def freeplot(self):
		response=messagebox.showinfo("Sorry", "Not yet implemented!")

	def relion3write(self):
		starfile=self.outfile_entry.get()	
		try:
			f=open(starfile, "w")
		except IOError:
			# error warning
			response=messagebox.showerror("ERROR", "Cannot open " + starfile + " for writing")
		else:
			with f:	
				f.write("data_\n\n")
				f.write("loop_\n")
				i=1
				for header in self.starlabels:
					f.write(header + " #" + str(i) + "\n")
					i += 1
				if self.tiltxindex >= 0:
					f.write("_rlnBeamTiltClass #" + str(i) + "\n")
	
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
				response=messagebox.showinfo("Success", "Wrote " + starfile)

	
	def plottilts(self):
		xval = []
		yval=[]
		for micrograph in self.stardata:
			xval.append(float(micrograph[self.tiltxindex]))
			yval.append(float(micrograph[self.tiltyindex]))
		xarr = np.array(xval)
		yarr = np.array(yval)
		# this block does the background colouring to show the grouping of the raw data
		h=0.01  # colour plot smoothness
		x_min, x_max = xarr.min() - 1, xarr.max() + 1
		y_min, y_max = yarr.min() - 1, yarr.max() + 1
		xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
		Z = self.kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
		Z = Z.reshape(xx.shape)
		plt.imshow(Z, interpolation='nearest',
           		extent=(xx.min(), xx.max(), yy.min(), yy.max()),
           		cmap=plt.cm.Paired,
           		aspect='auto', origin='lower')

		plt.plot(xarr, yarr, 'bo')
		plt.title('Beam tilts, centroids with red cross')
		plt.ylabel('Uncorrected beam tilt X /mrad')
		plt.xlabel('Uncorrected beam tilt y /mrad')
		plt.scatter(self.clusters[:,0], self.clusters[:,1],marker='x',color='r', linewidths=3, zorder=10, )
		plt.show()
	

	def findtiltgroups(self):
		xval = []
		yval=[]
		for micrograph in self.stardata:
			xval.append(float(micrograph[self.tiltxindex]))
			yval.append(float(micrograph[self.tiltyindex]))
		self.X=np.array(list(zip(xval,yval)))
		self.numgroups =self.tiltgroupslider.get() 
		self.kmeans=KMeans(n_clusters=self.numgroups)
		self.kmeans=self.kmeans.fit(self.X)
		self.grouplabels=self.kmeans.predict(self.X)
		self.clusters=self.kmeans.cluster_centers_
		self.plottilts_button['state'] = 'normal'

	def tiltgraph(self):
		xval = []
		yval=[]
		for micrograph in self.stardata:
			xval.append(float(micrograph[self.tiltxindex]))
			yval.append(float(micrograph[self.tiltyindex]))
		xarr = np.array(xval)
		yarr = np.array(yval)
		plt.plot(xarr, yarr, 'bo')
		plt.title('Beam Tilts')
		plt.ylabel('Uncorrected beam tilt X /mrad')
		plt.xlabel('Uncorrected beam tilt y /mrad')
		plt.show()

	def toggle_state(self,*_):    # *_ means ignore any further arguments sent to the function
		# activates/ deactivates the read button depending on whether there is a file for it to look for
		if self.filename.get():
			self.readfile_button['state'] = 'normal'
		else:
			self.readfile_button['state'] = 'disabled'
		if self.outstar.get():
			self.outfile_relion3_button['state'] = 'normal'
			self.outfile_relion31_button['state'] = 'normal'
		else:
			self.outfile_relion3_button['state'] = 'disabled'
			self.outfile_relion31_button['state'] = 'disabled'

	def selectfile(self):
		f = filedialog.askopenfilename(initialdir="./", title="Select a file", filetypes=(("star files", "*.star"), ("all files", "*.*")))
		self.filelabel.delete(0,Tk.END)
		self.filelabel.insert(0,f)
		
	def filterctf(self):
		self.originalstardata = self.stardata
		try:
			ctfmax = float(self.filterctf_value.get())
		except:
			response=messagebox.showerror("ERROR", "Bad CTF Max")
		self.stardata = []
		removed=0
		kept=0
		for micrograph in self.originalstardata:
			if float(micrograph[self.maxctfindex]) <= ctfmax:
				self.stardata.append(micrograph)
				kept += 1
			else:
				removed += 1
		response=messagebox.showinfo("CTF Filter", "Removed "+ str(removed) + "\nKept " + str(kept))
		self.restorectf_button['state'] = 'normal' 

	def restorectf(self):
		self.stardata = self.originalstardata
		self.restorectf_button['state'] = 'disabled' 

	def replaceDW(self):
		if self.DEBUG:
			top = Tk.Toplevel()
			top.title("debug info")
			fileinfo_label = Tk.Label(top, text="first file: " + self.stardata[0][self.micnameindex])
			fileinfo_label.grid(row=1, column=1, padx=10, pady=10)
		for i in range(len(self.stardata)):
			self.stardata[i][self.micnameindex] =  re.sub(r'\.mrc$', '-DW.mrc', self.stardata[i][self.micnameindex])
		self.replaceDW_button['state'] = 'disabled' 
		response=messagebox.showinfo("DW Replacement", "Done!")


	def ctfmaxplot(self):
		cval = []
		for micrograph in self.stardata:
			cval.append(float(micrograph[self.maxctfindex]))
		arr = np.array(cval)
		plt.title('Max CTF Resolution')
		plt.plot(arr, 'bo')
		plt.ylabel('CTF max Res /A')
		plt.xlabel('Micrograph index')
		plt.show()
	
	def Readstar(self):
		#starfile = self.filelabel.get()
		starfile = self.filename.get()
		try:
			f=open(starfile)
		except IOError:
			# error warning
			response=messagebox.showerror("ERROR", "File not found")
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
			self.tiltgraph_button['state'] = 'normal' 
			self.fileinfo_button['state'] = 'normal' 
			self.freeplot_button['state'] = 'normal' 
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

			if self.maxctfindex >=0:
				self.filterctf_button['state'] = 'normal' 
				self.ctfmaxplot_button['state'] = 'normal' 
			if self.micnameindex >=0:
				self.replaceDW_button['state'] = 'normal'
			if self.tiltxindex  >=0:
				self.tiltgroups_button['state'] = 'normal'
			if l2 < 5:
				response=messagebox.showwarning("WARNING", "Only " +str(l2) + " columns in star file!")

	def fileinfo(self):
		top = Tk.Toplevel()
		top.title("File info")
		l2 = len(self.starlabels)
		l3 = len(self.stardata)
		fileinfo_label = Tk.Label(top, text="File has " + str(self.filelength) + " lines")
		fileinfo_label.grid(row=1, column=1, padx=10, pady=10)
		fileinfo_label2 = Tk.Label(top, text="File has " + str(l2) + " relion columns")
		fileinfo_label2.grid(row=2, column=1, padx=10, pady=10)
		fileinfo_label3 = Tk.Label(top, text="File has " + str(l3) + " relion data lines")
		fileinfo_label3.grid(row=3, column=1, padx=10, pady=10)
		for i in range(l2):
			r=4+i
			lb = Tk.Label(top, text = "index " + str (i) + "\t" + self.starlabels[i])
			lb.grid(row=r, column=1, padx=10, pady=0)
		try:
			fileinfo_label4 = Tk.Label(top, text="resolution index: " + str(self.maxctfindex))
			fileinfo_label4.grid(row=20, column=1, padx=10, pady=10)
		except:
			pass

		fileinfo_miclabel = Tk.Label(top, text="first file: " + self.stardata[0][self.micnameindex])
		fileinfo_miclabel.grid(row=22, column=1, padx=10, pady=10)

 

if __name__ == '__main__':
	window = Window()
	Tk.mainloop()

