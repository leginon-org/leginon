
import math
import os
import re
import sys
import types

####
# This is a low-level file with NO database connections
# Please keep it this way
####

writeOut = False
try:
	outFile = os.path.basename(sys.argv[0]).split(".")[0]+".out"
except:
	outFile = "function.out"

def printWarning(text):
	"""
	standardized warning message
	"""
	if writeOut is True:
		try:
			f = open(outFile, "a")
			f.write(" !!! WARNING: "+text+"\n")
			f.close()
		except:
			print "write error"
	sys.stderr.write(colorString("!!! WARNING: "+text,"yellow")+"\n")

def printMsg(text, colorstr=None):
	"""
	standardized log message
	"""
	if writeOut is True:
		try:
			f = open(outFile, "a")
			f.write(" ... "+text+"\n")
			f.close()
		except:
			print "write error"
	sys.stderr.write(" ... "+colorString(text, colorstr)+"\n")
	
def printError(text):
	"""
	standardized error message
	"""
	if writeOut is True:
		try:
			f = open(outFile, "a")
			f.write(" *** ERROR: "+text+"\n")
			f.close()
		except:
			print "write error"
	raise Exception, colorString("\n *** FATAL ERROR ***\n"+text+"\n\a","red")

def printColor(text, colorstr):
	"""
	standardized log message
	"""
	if writeOut is True:
		try:
			f = open(outFile, "a")
			f.write(" ... "+text+"\n")
			f.close()
		except:
			print "write error"
	sys.stderr.write(colorString(text, colorstr)+"\n")
	

def shortenImageName(imgname):
	"""
	takes a long imagename and truncates it for display purposes
	"""
	shortimgname = imgname
	#remove path
	shortimgname = os.path.basename(shortimgname)
	#remove the altas name
	shortimgname = re.sub("^(?P<ses>[0-9][0-9][a-z][a-z][a-z][0-9][0-9][^_]+)_.+(?P<gr>0[^0]gr)",
		"\g<ses>_\g<gr>",shortimgname)
	#remove the version tags
	shortimgname = re.sub("_v[0-9][0-9]","",shortimgname)
	#remove extra leading zeros, but leave one
	shortimgname = re.sub("_00+(?P<num>0[^0])","_\g<num>",shortimgname)
	#first RCT id, keep second
	shortimgname = re.sub("_[0-9][0-9]_(?P<en>[0-9]+en)","_\g<en>",shortimgname)
	#remove double underscores
	shortimgname = re.sub("__","_",shortimgname)
	#remove orphaned underscores
	shortimgname = re.sub("_+$","",shortimgname)
	return shortimgname

def bytes(numbytes):
	numbytes = int(numbytes)
	mult = 1024.0
	if numbytes < mult:
		return "%d B"%(numbytes)
	elif numbytes < mult**2:
		return "%.1f kB"%(numbytes/mult)
	elif numbytes < mult**3:
		return "%.1f MB"%(numbytes/mult**2)
	elif numbytes < mult**4:
		return "%.1f GB"%(numbytes/mult**3)
	elif numbytes < mult**5:
		return "%.1f TB"%(numbytes/mult**4)
	else:
		return "%.1f PB"%(numbytes/mult**5)

def clusterBytes(numbytes):
	numbytes = int(numbytes)
	mult = 1024.0
	if numbytes < mult:
		return "%db"%(math.ceil(numbytes))
	elif numbytes < mult**2:
		return "%dkb"%(math.ceil(numbytes/mult))
	elif numbytes < mult**3:
		return "%dmb"%(math.ceil(numbytes/mult**2))
	elif numbytes < mult**4:
		return "%dgb"%(math.ceil(numbytes/mult**3))
	else:
		return "%dtb"%(math.ceil(numbytes/mult**4))

def orderOfMag(num):
	if num > 1:
		num = int(num)
		if num < 1e3:
			return str(num)
		elif num < 1e6:
			return str(int(num/1e3))+"k"
		elif num < 1e9:
			return str(int(num/1e6))+"M"
		elif num < 1e12:
			return str(int(num/1e9))+"G"
	else:
		return str(num)

def short(imgname):
	# ALIAS to shortenImageName
	return shortenImageName(imgname)

def timeString(avg, stdev=0):
	""" 
	returns a string with the length of time scaled for clarity
	"""
	avg = float(avg)
	stdev = float(stdev)
	#less than 0.5 microseconds
	if avg < 0.5e-6:
		if stdev > 0.0:
			timestr = str(round(avg*1e9,2))+" +/- "+str(round(stdev*1e9,2))+" nsec"
		else:
			timestr = str(round(avg*1e9,2))+" nsec"
	#less than 0.5 milliseconds
	elif avg < 0.5e-3:
		if stdev > 0.0:
			timestr = str(round(avg*1e6,2))+" +/- "+str(round(stdev*1e6,2))+" usec"
		else:
			timestr = str(round(avg*1e6,2))+" usec"
	#less than 0.5 seconds
	elif avg < 0.5:
		if stdev > 0.0:
			timestr = str(round(avg*1e3,2))+" +/- "+str(round(stdev*1e3,2))+" msec"
		else:
			timestr = str(round(avg*1e3,2))+" msec"
	#less than 70 seconds
	elif avg < 70.0:
		if stdev > 0.0:
			timestr = str(round(avg,2))+" +/- "+str(round(stdev,2))+" sec"
		else:
			timestr = str(round(avg,2))+" sec"
	#less than 70 minutes
	elif avg < 4200.0:
		subbase = 1.0
		base = subbase * 60.0
		majorunit = "min"
		minorunit = "sec"
		if stdev > 0.0:
			timestr = str(round(avg/base, 2))+" +/- "+str(round(stdev/base, 2))+" "+majorunit
		else:
			timestr = ( str(int(math.floor(avg/base)))+" "+majorunit+" "
				+str(int(round( (avg % base)/subbase )))+" "+minorunit )
	#less than 28 hours
	elif avg < 100800.0:
		subbase = 60.0
		base = subbase * 60.0
		majorunit = "hr"
		minorunit = "min"
		if stdev > 0.0:
			timestr = str(round(avg/base, 2))+" +/- "+str(round(stdev/base, 2))+" "+majorunit
		else:
			timestr = ( str(int(math.floor(avg/base)))+" "+majorunit+" "
				+str(int(round( (avg % base)/subbase )))+" "+minorunit )
	#more than 28 hours (1.2 days)
	else:
		subbase = 3600.0
		base = subbase * 24.0
		majorunit = "days"
		minorunit = "hr"
		if stdev > 0.0:
			timestr = str(round(avg/base, 2))+" +/- "+str(round(stdev/base, 2))+" "+majorunit
		else:
			timestr = ( str(int(math.floor(avg/base)))+" "+majorunit+" "
				+str(int(round( (avg % base)/subbase )))+" "+minorunit )
	return str(timestr)

def printDataBox(labellist,numlist,typelist=None):
	"""
	prints a data box, used in pyace
	"""
	if( len(labellist) != len(numlist) 
	 or ( typelist!=None and len(typelist) != len(numlist) ) ):
		print len(labellist)," != ",len(numlist)," != ",len(typelist)
		printError("printDataBox() list lengths are off")
	sys.stderr.write(_headerStr(labellist)+"\n")
	labelstr = " "
	for lab in labellist:
		labelstr += "| "+lab+" "
		if len(lab) < 5:
			for i in range(5-len(lab)):
				labelstr += " "
	sys.stderr.write(labelstr+"|\n")

	datastr = " "
	for i in range(len(labellist)):
		datastr += "| "
		if typelist==None or typelist[i] == 1:
			numstr = colorProb(numlist[i])
		elif numlist[i] < 0:
			numstr = "%2.2f" % numlist[i]
		else:
			numstr = "%1.3f" % numlist[i]
		pad = len(labellist[i])-5
		if pad % 2 == 1:
			datastr += " "
			pad -= 1
		pad/=2
		if(pad > 0):
			for i in range(pad):
				datastr += " "
		datastr += numstr
		if(pad > 0):
			for i in range(pad):
				datastr += " "
		datastr += " "
	sys.stderr.write(datastr+"|\n")
	sys.stderr.write(_headerStr(labellist)+"\n")

def _headerStr(labellist):
	headstr = " "
	for lab in labellist:
		headstr += "+"
		leng = len(lab)
		if leng < 5: leng = 5
		for i in range(leng+2):
			headstr += "-"
	headstr += "+"
	return headstr

def rightPadString(s,n=10,fill=" "):
	n = int(n)
	s = str(s)
	if(len(s) > n):
		return s[:n]
	while(len(s) < n):
		s += fill
	return s

def leftPadString(s,n=10,fill=" "):
	n = int(n)
	s = str(s)
	if(len(s) > n):
		return s[:n]
	while(len(s) < n):
		s = fill+s
	return s

def colorType(val):
	"""
	colors a value based on type
	"""
	if val is None:
		return colorString("None","red")
	elif val is True:
		return colorString("True","green")
	elif val is False:
		return colorString("False","red")
	elif type(val) == type(0.33):
		return colorString(val,"cyan")
	elif type(val) == type(512):
		return colorString(val,"green")
	elif type(val) == type("hello"):
		return colorString("'"+val+"'","brown")	
	return val

def colorProb(num,red=0.50,green=0.80):
	"""
	colors a probability based on score
	"""
	if(num == None):
		return None
	elif(num >= green and num <= 1):
		numstr = "%1.3f" % num
		return colorString(numstr,"green")
	elif(num < red and num >= 0):
		numstr = "%1.3f" % num
		return colorString(numstr,"red")
	elif num >= red and num < green:
		numstr = "%1.3f" % num
		return colorString(numstr,"brown")
	elif num < 0:
		numstr = "%2.2f" % num
		return colorString(numstr,"purple")		
	else:
		numstr = "%2.2f" % num
		return colorString(numstr,"blue")

def color(text, fg, bg=None):
	return colorString(text, fg, bg)

def clearColor():
	opencol = "\033["
	closecol = "m"
	clear = opencol + "0" + closecol
	return clear	

def colorString(text, fg=None, bg=None):
	"""Return colored text.
	Uses terminal color codes; set avk_util.enable_color to 0 to
	return plain un-colored text. If fg is a tuple, it's assumed to
	be (fg, bg). Both colors may be 'None'.
	"""
	colors = {
		"black" :"30",
		"red"   :"31",
		"green" :"32",
		"brown" :"33",
		"orange":"33",
		"blue"  :"34",
		"violet":"35",
		"purple":"35",
		"magenta":"35",
		"maroon":"35",
		"cyan"  :"36",
		"lgray" :"37",
		"gray"  :"1;30",
		"lred"  :"1;31",
		"lgreen":"1;32",
		"yellow":"1;33",
		"lblue" :"1;34",
		"pink"  :"1;35",
		"lcyan" :"1;36",
		"white" :"1;37"
	}
	if fg is None:
		return text
	if type(fg) in (types.TupleType, types.ListType):
		fg, bg = fg
	if not fg:
		return text
	opencol = "\033["
	closecol = "m"
	clear = opencol + "0" + closecol
	xterm = 0
	if os.environ.get("TERM") is not None and os.environ.get("TERM") == "xterm": 
		xterm = True
	else:
		xterm = False
	b = ''
	# In xterm, brown comes out as yellow..
	if xterm and fg == "yellow": 
		fg = "brown"
	f = opencol + colors[fg] + closecol
	if bg:
		if bg == "yellow" and xterm: 
			bg = "brown"
		try: 
			b = colors[bg].replace('3', '4', 1)
			b = opencol + b + closecol
		except KeyError: 
			pass
	return "%s%s%s%s" % (b, f, text, clear)

def environmentError():
	env = []
	env.append("APPIONDIR")
	env.append('PATH')
	env.append('MATLAB')
	env.append('MATLABPATH')
	env.append('PYTHONPATH')
	env.append('LD_LIBRARY_PATH')
	env.append('LM_LICENSE_FILE')
	print colorString("Check your environmental variables and the Appion documentation.\nThese are your current environment values:","red")
	for name in env:
		if name in os.environ:
			value = os.environ[name]
		else:
			value = '*** NOT SET ***'
		print colorString("%-20s -> %s" % (name, value), "red")


####
# This is a low-level file with NO database connections
# Please keep it this way
####


