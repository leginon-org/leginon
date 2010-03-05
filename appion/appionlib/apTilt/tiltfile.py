#!/usr/bin/python -O

#python
import time
import os
import re
import pprint
import cPickle
#appion
from appionlib import apXml
from appionlib import apDisplay
from appionlib.apSpider import operations


imagetypes = ['spider', 'text', 'xml', 'pickle', 'box', 'pik',]
imagetypesel = (
	"All Files (*.*)|*.*"
	+ "|MRC Files (*.mrc)|*.mrc" 
	+ "|Spider Files (*.spi)|*.spi" 
	+ "|PNG Files (*.png)|*.png" 
	+ "|TIFF Files (*.tif)|*.tif"
	+ "|JPEG Files (*.jpg)|*.jpg"
	)
filetypes = ['spider', 'text', 'xml', 'pickle', 'box', 'pik',]
filetypesel = (
	"Spider Files (*.spi)|*.spi" 
	+ "|Text Files (*.txt)|*.txt" 
	+ "|Python Pickle File (*.pickle)|*.pickle" 
	+ "|XML Files (*.xml)|*.xml"
#	+ "|EMAN Box File (*.box)|*.box" 
#	+ "|Pik File (*.pik)|*.pik" 
	)

#---------------------------------------	
"""
Each file should have at a minimum the following information

1. Theta (tilt) angle
2. Gamma (image 1 rotation) angle
3. Phi (image 2 rotation) angle
4. List of image 1 particles
5. List of image 2 particles

"""

#---------------------------------------
def guessFileType(filename):
	if filename is None or filename == "":
		return None
	ext = os.path.splitext(filename)[1]
	if ext == ".txt":
		filetype = "text"
	elif ext == ".xml":
		filetype = "xml"
	elif ext == ".spi":
		filetype = "spider"
	elif ext == ".pickle":
		filetype = "pickle"
	elif ext == ".pik":
		filetype = "pickle"
	elif ext == ".box":
		filetype = "box"
	else:
		apDisplay.printError("Could not determine filetype of picks file, unknown extension: "+ext)
	return filetype

#---------------------------------------	
def saveData(savedata, filename, filetype=None):
	"""
	savedata = {}
	savedata['theta'] = self.data['theta']
	savedata['gamma'] = self.data['gamma']
	savedata['phi'] = self.data['phi']
	savedata['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
	savedata['filetype'] = tiltfile.filetypes[self.data['filetypeindex']]
	savedata['picks1'] = self.getArray1()
	savedata['picks2'] = self.getArray2()
	savedata['align1'] = self.getAlignedArray1()
	savedata['align2'] = self.getAlignedArray2()
	savedata['rmsd'] = self.getRmsdArray()
	savedata['image1name'] = self.panel1.filename
	savedata['image2name'] = self.panel2.filename
	"""

	if filetype is None:
		filetype = guessFileType(filename)

	savedata['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
	savedata['filetype'] = filetype
	savedata['filename'] = os.path.basename(filename)

	if filetype == 'text':
		saveToTextFile(savedata, filename)
	elif filetype == 'xml':
		saveToXMLFile(savedata, filename)
	elif filetype == 'spider':
		saveToSpiderFile(savedata, filename)
	elif filetype == 'pickle':
		saveToPickleFile(savedata, filename)
	elif filetype == 'box':
		saveToBoxFile(savedata, filename)
	else:
		return False
		apDisplay.printWarning("unknown file type")

#---------------------------------------
def saveToTextFile(savedata, filename):
	f = open(filename, "w")
	f.write( "program: \tparticles picked with ApTiltPicker\n")
	for i in savedata:
		if isinstance(savedata[i], str):
			f.write("DATA "+str(i)+": "+str(savedata[i])+"\n")
	f.write( "date: \t%sf\n"  % ( savedata['savetime'], ))
	f.write( "theta:\t%.5f\n" % ( savedata['theta'], ))
	f.write( "gamma:\t%.5f\n" % ( savedata['gamma'], ))
	f.write( "phi:  \t%.5f\n" % ( savedata['phi'], ))
	f.write( "shiftx:  \t%.5f\n" % ( savedata['shiftx'], ))
	f.write( "shifty:  \t%.5f\n" % ( savedata['shifty'], ))
	#IMAGE 1
	f.write( "image 1: \t%s\n"  % ( savedata['image1name'], ))
	for i in range(len(savedata['picks1'])):
		f.write( '%d,%d, ' % (savedata['picks1'][i][0], savedata['picks1'][i][1],) )
		if i < len(savedata['align1']):
			f.write( '%.1f,%.1f, ' % (savedata['align1'][i][0], savedata['align1'][i][1],) )
		if i < len(savedata['rmsd']):
			f.write(' %.3f, ' % ( savedata['rmsd'][i] ) )
		f.write('\n')

	#IMAGE 2
	f.write( "image 2: \t%s\n"  % ( savedata['image2name'], ))
	for i in range(len(savedata['picks2'])):
		f.write( '%d,%d, ' % (savedata['picks2'][i][0], savedata['picks2'][i][1],) )
		if i < len(savedata['align2']):
			f.write( '%.1f,%.1f, ' % (savedata['align2'][i][0], savedata['align2'][i][1],) )
		if i < len(savedata['rmsd']):
			f.write(' %.3f, ' % ( savedata['rmsd'][i] ) )
		f.write('\n')
	f.close()

	return True

#---------------------------------------
def saveToXMLFile(savedata, filename):
	apXml.writeDictToXml(savedata, filename, title='aptiltpicker')
	return True

#---------------------------------------
def saveToSpiderFile(savedata, filename):
	f = open(filename, "w")
	f.write( " ; particles picked with ApTiltPicker\n")
	f.write( " ; http://appion.org\n")
	f.write( " ; "+savedata['savetime']+"\n")
	for i in savedata:
		if isinstance(savedata[i], str) or isinstance(savedata[i], int) or isinstance(savedata[i], float):
			f.write(" ; DATA "+str(i)+": "+str(savedata[i])+"\n")
	#PARAMETERS
	f.write(" ; \n ; \n ; PARAMETERS\n")
	f.write(operations.spiderOutputLine(1, 6, 0.0, 0.0, 0.0, 0.0, 111.0, 1.0))
	f.write(" ; FITTED FLAG\n")
	f.write(operations.spiderOutputLine(2, 6, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0))
	f.write(" ; (X0,Y0) FOR LEFT IMAGE1, (X0s,Y0s) FOR RIGHT IMAGE2, REDUCTION FACTOR\n")
	f.write(operations.spiderOutputLine(3, 6, 
		savedata['picks1'][0][0], savedata['picks1'][0][1], 
		savedata['picks2'][0][0], savedata['picks2'][0][1], 
		1.0, 0.0))
	f.write(" ; TILT ANGLE (THETA), LEFT IMAGE1 ROTATION (GAMMA), RIGHT IMAGE2 ROTATION (PHI)\n")
	f.write(operations.spiderOutputLine(4, 6, 
		savedata['theta'], savedata['gamma'], savedata['phi'],
		0.0, 0.0, 0.0))

	#IMAGE 1
	f.write( " ; LEFT IMAGE 1: "+savedata['image1name']+" columns: num pickx picky alignx aligny rmsd\n" )
	for i in range(len(savedata['picks1'])):
		if i < len(savedata['align1']):
			line = operations.spiderOutputLine(i+1, 6, i+1, 
				savedata['picks1'][i][0], savedata['picks1'][i][1], 
				savedata['align1'][i][0], savedata['align1'][i][1],
				savedata['rmsd'][i])
		else:
			line = operations.spiderOutputLine(i+1, 6, i+1, 
				savedata['picks1'][i][0], savedata['picks1'][i][1], 
				0.0, 0.0, 0.0)
		f.write(line)

	#IMAGE 2
	f.write( " ; RIGHT IMAGE 2: "+savedata['image2name']+" columns: num pickx picky alignx aligny rmsd\n" )
	for i in range(len(savedata['picks2'])):
		if i < len(savedata['align2']):
			line = operations.spiderOutputLine(i+1, 6, i+1, 
				savedata['picks2'][i][0], savedata['picks2'][i][1], 
				savedata['align2'][i][0], savedata['align2'][i][1],
				savedata['rmsd'][i])
		else:
			line = operations.spiderOutputLine(i+1, 6, i+1, 
				savedata['picks2'][i][0], savedata['picks2'][i][1], 
				0.0, 0.0, 0.0)
		f.write(line)

	f.close()

	return True


#---------------------------------------
def saveToPickleFile(savedata, filename):
	f = open(filename, 'w')
	cPickle.dump(savedata, f)
	f.close()
	return True

#---------------------------------------	
#---------------------------------------	
#---------------------------------------	
#---------------------------------------	
#---------------------------------------	
#---------------------------------------	


#---------------------------------------	
def readData(filename, filetype=None):
	"""
	savedata = {}
	savedata['theta'] = self.data['theta']
	savedata['gamma'] = self.data['gamma']
	savedata['phi'] = self.data['phi']
	savedata['shiftx'] = self.data['shiftx']
	savedata['shifty'] = self.data['shifty']
	savedata['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
	savedata['filetype'] = tiltfile.filetypes[self.data['filetypeindex']]
	savedata['picks1'] = self.getArray1()
	savedata['picks2'] = self.getArray2()
	savedata['align1'] = self.getAlignedArray1()
	savedata['align2'] = self.getAlignedArray2()
	savedata['rmsd'] = self.getRmsdArray()
	savedata['filepath'] = os.path.join(self.data['dirname'], self.data['outfile'])
	savedata['image1name'] = self.panel1.filename
	savedata['image2name'] = self.panel2.filename
	"""
	if not os.path.isfile(filename):
		apDisplay.printWarning("file "+filename+" does not exist")
		return None

	if filetype is None:
		filetype = guessFileType(filename)

	if filetype == 'text':
		savedata = readFromTextFile(filename)
	elif filetype == 'xml':
		savedata = readFromXMLFile(filename)
	elif filetype == 'spider':
		savedata = readFromSpiderFile(filename)
	elif filetype == 'pickle':
		savedata = readFromPickleFile(filename)
	else:
		apDisplay.printWarning("unknown file type")
		return None

	savedata['filename'] = os.path.basename(filename)
	savedata['loadtime'] = time.asctime()+" "+time.tzname[time.daylight]
	savedata['shiftx'] = 0.0
	savedata['shifty'] = 0.0
	savedata['scale'] = 1.0
	return savedata

#---------------------------------------
def readFromTextFile(filename):
	f = open(filename, "r")
	savedata = {
		'picks1': [],
		'picks2': [],
		'align1': [],
		'align2': [],
		'rmsd': [],
	}
	imgnum = 0
	for line in f:
		sline = line.strip()
		### check if line start with text
		if re.match("^[a-zA-Z]", sline):
			if re.match("^image", sline):
				imgnum+=1
				key = "image"+str(imgnum)+"name"
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata[key] = tabs[0]
				#pprint.pprint( savedata )
			elif re.match("^gamma", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['gamma'] = float(tabs[0])
			elif re.match("^theta", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['theta'] = float(tabs[0])
			elif re.match("^phi", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['phi'] = float(tabs[0])
			elif re.match("^shiftx", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['shiftx'] = float(tabs[0])
			elif re.match("^shifty", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['shifty'] = float(tabs[0])
		elif re.match("^[0-9]", sline):
			bits = sline.split(",")
			pick = [int(float(bits[0])), int(float(bits[1]))]
			align = [float(bits[2]), float(bits[3])]
			savedata['picks'+str(imgnum)].append(pick)
			savedata['align'+str(imgnum)].append(align)
			savedata['rmsd'].append(float(bits[4]))
	f.close()
	#pprint.pprint( savedata )
	return savedata

#---------------------------------------
def readFromSpiderFile(filename):
	f = open(filename, "r")
	savedata = {
		'picks1': [],
		'picks2': [],
		'align1': [],
		'align2': [],
		'rmsd': [],
	}
	mode = "none"
	imgnum = 0
	for line in f:
		sline = line.strip()
		### check if line start with text
		if sline[0] == ";":  
			if re.match("^; PARAMETERS", sline):
				mode = "init"
				#print sline
			elif re.match("^; left image", sline, re.IGNORECASE) or re.match("^; right image", sline, re.IGNORECASE):
				mode = "picks"
				imgnum+=1
				key = "image"+str(imgnum)+"name"
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata[key] = tabs[0]
			elif re.match("^; DATA shiftx", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['shiftx'] = float(tabs[0])
			elif re.match("^; DATA shifty", sline):
				bits = sline.split(":")
				tabs = bits[1].strip().split(" ")
				savedata['shifty'] = float(tabs[0])
		elif mode == "init":
			bits = sline.split()
			if int(bits[0]) == 3:
				#print bits
				pass
			elif int(bits[0]) == 4:
				#print bits
				if float(bits[2]) != 0.0:
					savedata['theta'] = float(bits[2])
				if float(bits[3]) != 0.0:
					savedata['gamma'] = float(bits[3])
				if float(bits[4]) != 0.0:
					savedata['phi']   = float(bits[4])
		elif mode == "picks":
			bits = sline.split()
			pick = [int(float(bits[3])), int(float(bits[4]))]
			align = [float(bits[5]), float(bits[6])]
			savedata['picks'+str(imgnum)].append(pick)
			savedata['align'+str(imgnum)].append(align)
			savedata['rmsd'].append(float(bits[7]))
	f.close()
	return savedata


#---------------------------------------
def readFromPickleFile(filename):
	f = open(filename, 'r')
	savedata = cPickle.load(f)
	f.close()
	return savedata

#---------------------------------------
def readFromXMLFile(filename):
	savedata = apXml.readDictAndConvertFromXml(filename)
	return savedata

if __name__ == "__main__":
	savedata = readData("rawu0picks2.xml")
	savedata = readData("rawu0picks.txt")
	savedata = readData("rawu0picks.spi")
	saveData(savedata, "rawu0picks2.spi")
	saveData(savedata, "rawu0picks2.pickle")
	saveData(savedata, "rawu0picks2.txt")
	saveData(savedata, "rawu0picks2.xml")




