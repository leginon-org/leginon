
import math
import os
import re
import sys
import types

def printWarning(text):
	"""
	standardized warning message
	"""
	try:
		f = open("function.out","a")
		f.write(" !!! WARNING: "+text+"\n")
		f.close()
	except:
		print "write error"
	print colorString("!!! WARNING: "+text,"brown")

def printMsg(text):
	"""
	standardized log message
	"""
	try:
		f = open("function.out","a")
		f.write(" ... "+text+"\n")
		f.close()
	except:
		print "write error"
	print " ... "+text

def printError(text):
	"""
	standardized error message
	"""
	try:
		f = open("function.out","a")
		f.write(" *** ERROR: "+text+"\n")
		f.close()
	except:
		print "write error"
	raise colorString("\n *** FATAL ERROR ***\n"+text+"\n","red")

def printColor(text, colorstr):
	"""
	standardized log message
	"""
	try:
		f = open("function.out","a")
		f.write(" ... "+text+"\n")
		f.close()
	except:
		print "write error"
	print colorString(text, colorstr)
	

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

def short(imgname):
	# ALIAS to shortenImageName
	return shortenImageName(imgname)

def timeString(avg,stdev=0):
	""" 
	returns a string with the length of time scaled for clarity
	"""
	avg = float(avg)
	stdev = float(stdev)
	#less than 75 seconds
	if avg < 75.0:
		if stdev > 0.0:
			timestr = str(round(avg,2))+" +/- "+str(round(stdev,2))+" sec"
		else:
			timestr = str(round(avg,2))+" sec"
	#less than 75 minutes
	elif avg < 4500.0:
		if stdev > 0.0:
			timestr = str(round(avg/60.0,2))+" +/- "+str(round(stdev/60.0,2))+" min"
		else:
			timestr = str(int(avg/60.0))+" min "+str(int((avg/60.0-int(avg/60.0))*60.0+0.5))+" sec"
	#more than 1.5 hours
	else:
		if stdev > 0.0:
			timestr = str(round(avg/3600.0,2))+" +/- "+str(round(stdev/3600.0,2))+" hrs"
		else:
			timestr = str(int(avg/3600.0))+" hrs "+str(int((avg/3600.0-int(avg/3600.0))*60.0+0.5))+" min"
	return str(timestr)

def printDataBox(labellist,numlist,typelist=None):
	"""
	prints a data box, used in pyace
	"""
	if( len(labellist) != len(numlist) 
	 or ( typelist!=None and len(typelist) != len(numlist) ) ):
		print len(labellist)," != ",len(numlist)," != ",len(typelist)
		printError("printDataBox() list lengths are off")
	print _headerStr(labellist)
	labelstr = " "
	for lab in labellist:
		labelstr += "| "+lab+" "
		if len(lab) < 5:
			for i in range(5-len(lab)):
				labelstr += " "
	print labelstr+"|"

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
	print datastr+"|"

	print _headerStr(labellist)

	
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

def rightPadString(s,n=10):
	n = int(n)
	if(len(s) > n):
		return s[:n]
	while(len(s) < n):
		s += " "
	return s


def leftPadString(s,n=10):
	n = int(n)
	if(len(s) > n):
		return s[:n]
	while(len(s) < n):
		s = " "+s
	return s

def colorType(val):
	"""
	colors a value based on type
	"""
	if val is None:
		return colorString("None","red")
	elif val is True:
		return colorString("True","purple")
	elif val is False:
		return colorString("False","purple")
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

def colorString(text, fg, bg=None):
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
		"blue"  :"34",
		"purple":"35",
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

def matlabError():
	env = {}
	env['PATH'] = "/ami/sw/packages/matlab73/bin:/home/$USER/pyappion/ace:/bin:/usr/bin"
	env['MATLAB'] = "/ami/sw/packages/matlab73"
	if os.environ.get("APPIONDIR") is not None:
		env['MATLABPATH'] = os.path.join(os.environ.get("APPIONDIR"),"ace")
	else:
		env['MATLABPATH'] = "/home/$USER/pyappion/ace"
	env['PYTHONPATH'] = "/home/$USER/pyleginon:/home/$USER/pyappion/lib:/ami/sw/32-pythonhome/lib/python2.4/site-packages"
	if os.path.isdir("/usr/lib/python2.4/site-packages"):
		env['PYTHONPATH'] = "/usr/lib/python2.4/site-packages:" + env['PYTHONPATH']
	env['LD_LIBRARY_PATH'] = "/ami/sw/packages/matlab73/bin/glnx86:/lib:/usr/lib"
	env['LM_LICENSE_FILE'] = "/ami/sw/packages/matlab/etc/license.dat"
	print colorString("MATLAB failed to open.\nCheck your environmental variables:","red")
	if os.path.basename(os.environ.get("SHELL")) == "bash":
		for var in env.keys():
			print colorString(" export "+var+"="+env[var],"red")
	else:
		for var in env.keys():
			print colorString(" setenv "+var+" "+env[var],"red")
	print "sometimes the PATH is the problem move matlab73/bin to the end"
	sys.exit(1)

