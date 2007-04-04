
import math
import os
import re
import types

def printWarning(text):
	print color(" !!! WARNING: "+text,"brown")

def printMsg(text):
	print " ... "+text

def printError(text):
	raise color("\n *** FATAL ERROR ***\n\t"+text+"\n","red")

def shortenImageName(imgname):
	#remove the version tags
	shortimgname = re.sub("_v[0-9][0-9]","",imgname)
	#remove extra leading zeros, but leave one
	shortimgname = re.sub("_00+(?P<num>0[^0])","_\g<num>",shortimgname)
	#remove double underscores
	shortimgname = re.sub("__","_",shortimgname)
	#remove orphaned underscores
	shortimgname = re.sub("_+$","",shortimgname)
	return shortimgname


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

def printDataBox(labellist,numlist,typelist):
	if len(labellist) != len(numlist) or len(typelist) != len(numlist):
		print "\nERROR: in _printWindow() list lengths are off"
		print len(labellist)," != ",len(numlist)," != ",len(typelist)
		sys.exit(1)
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
		if typelist[i] == 1:
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
	if val == None:
		return color("None","red")
	elif val == True:
		return color("True","purple")
	elif val == False:
		return color("False","purple")
	elif type(val) == type(0.33):
		return color(val,"cyan")
	elif type(val) == type(512):
		return color(val,"green")
	elif type(val) == type("hello"):
		return color("'"+val+"'","brown")	
	return val

def colorProb(num,red=0.50,green=0.80):
	if(num == None):
		return None
	elif(num > green and num <= 1):
		numstr = "%1.3f" % num
		return color(numstr,"green")
	elif(num < red and num >= 0):
		numstr = "%1.3f" % num
		return color(numstr,"red")
	else:
		numstr = "%1.3f" % num
		return numstr

def color(text, fg, bg=None):
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
	if os.environ["TERM"] == "xterm": 
		xterm = 1
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
