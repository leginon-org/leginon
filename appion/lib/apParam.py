## python
import os
import sys
import re
import socket
import time
import random
import subprocess
import math
from string import lowercase
## appion
import apDisplay

#=====================
def getAppionDirectory():
	"""
	Used by appionLoop
	"""
	appiondir = None

	libdir = os.path.dirname(__file__)
	libdir = os.path.abspath(libdir)
	trypath = os.path.dirname(libdir)
	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	trypath = os.environ.get('APPIONDIR')
	if trypath and os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	user = os.getlogin() #os.environ.get('USER')
	trypath = "/home/"+user+"/pyappion"
	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	apDisplay.printError("environmental variable, APPIONDIR, is not defined.\n"+
		"Did you source useappion.sh?")


#=====================
def makeTimestamp():
	datestamp = time.strftime("%y%b%d").lower()
	hourstamp = lowercase[(time.localtime()[3])%26]
	#mins = time.localtime()[3]*12 + time.localtime()[4]
	#minstamp = lowercase[mins%26]
	minstamp = "%02d"%(time.localtime()[4])
	timestamp = datestamp+hourstamp+minstamp
	return timestamp

#=====================
def getFunctionName(arg=None):
	"""
	Sets the name of the function
	by default takes the first variable in the argument
	"""
	if arg == None:
		arg = sys.argv[0]
	functionname = os.path.basename(arg.strip())
	functionname = os.path.splitext(functionname)[0]
	return functionname

#=====================
def getUsername():
	try:
		user = os.getlogin() #os.environ.get('USER')
	except:
		user = "unknown"
	return user

#=====================
def getHostname():
	host = None
	if len(os.name) > 2:
		host = os.uname()[1]
	if not host:
		try:
			host = socket.gethostname()
			#host = socket.gethostbyaddr(socket.gethostname())[0]
		except:
			host = "unknown"
	return host

#=====================
def getSystemName():
	try:
		system = os.uname()[0].lower()
	except:
		system = "unknown"
	return system

#=====================
def getLinuxDistro():
	flavfile = "/etc/redhat-release"
	try:
		f = open(flavfile, "r")
		flavor = f.readline().strip()
		f.close()
	except:
		flavor = None
	return flavor

#=====================
def getMachineArch():
	try:
		arch = os.uname()[4]
	except:
		arch = None
	return arch

#=====================
def getHostIP(hostname=None):
	try:
		if hostname is None:
			hostname = socket.gethostname()
		ip = socket.gethostbyaddr(hostname)[2][0]
	except:
		ip = None
	return ip

#=====================
def getLogHeader():
	#WRITE INFO
	user = getUsername()
	host = getHostname()
	logheader = "[ "+user+"@"+host+": "+time.asctime()+" ]\n"
	return logheader

#=====================
def writeFunctionLog(cmdlist, logfile=None, msg=True):
	"""
	Used by appionLoop
	"""
	if logfile is not None:
		pass
	else:
		logfile = getFunctionName(sys.argv[0])+".log"
	if msg is True:
		apDisplay.printMsg("Writing function log to: "+logfile)
	timestamp = getLogHeader()
	out=""
	f=open(logfile,'a')
	f.write(timestamp)
	f.write(os.path.abspath(cmdlist[0])+" \\\n  ")
	for arg in cmdlist[1:]:
		if len(out) > 60 or len(out)+len(arg) > 90:
			f.write(out+"\\\n")
			out = "  "
		#if ' ' in arg and ('=' in arg or not '-' in arg):
		if ' ' in arg and '=' in arg:
			elems = arg.split('=')
			out += elems[0]+"='"+elems[1]+"' "
		else:
			out += arg+" "
	f.write(out+"\n")
	f.close()
	return logfile

#=====================
def parseWrappedLines(lines):
	goodlines=[]
	add=False
	for i, line in enumerate(lines):
		if line.count('\\') >0:
			newline = newline+line.strip('\\\n')+' '
			add=True
			continue
		if add==True:
			newline = newline+line
		else:
			newline = line

		if line.count('\\') ==0:
			add=False
		goodlines.append(newline)
		newline=''

	return goodlines

#=====================
def closeFunctionLog(functionname=None, logfile=None, msg=True, stats=None):
	"""
	Used by appionLoop
	"""
	if logfile is not None:
		pass
	elif functionname is not None:
		logfile = functionname+".log"
	else:
		logfile = "function.log"
	if msg is True:
		apDisplay.printMsg("Closing out function log: "+logfile)
	if stats is not None and stats['count'] > 3:
		timesum = stats['timesum']
		timesumsq = stats['timesumsq']
		count = stats['count']
		timeavg = float(timesum)/float(count)
		timestdev = math.sqrt(float(count*timesumsq - timesum**2) / float(count*(count-1)))
		avgtimestr = "average time: "+apDisplay.timeString(timeavg,timestdev)+"\n"
	else:
		avgtimestr = ""

	#WRITE INFO
	timestamp = "["+time.asctime()+"]\n"
	out="finished run"
	if functionname is not None:
		out += " of "+functionname
	out += "\n"
	f=open(logfile,'a')
	f.write(timestamp)
	f.write(avgtimestr)
	f.write(out)
	f.close()

#=====================
def createDirectory(path, mode=0777, warning=True):
	"""
	Used by appionLoop
	"""
	if os.path.isdir(path):
		if warning is True:
			apDisplay.printWarning("directory \'"+path+"\' already exists.")
		return False
	try:
		os.makedirs(path, mode=mode)
		#makedirs(path, mode=mode)
	except:
		apDisplay.printError("Could not create directory, '"+path+"'\nCheck the folder write permissions")
	return True

#=====================
def makedirs(name, mode=0777):
	"""
	Works like mkdir, except that any intermediate path segment (not
	just the rightmost) will be created if it does not exist.  This is
	recursive.
	"""
	"""
	This is broken since curdir is not defined.  Not sure how to fix
	it.  Use createDirectory instead.  AC
	"""
	head, tail = os.path.split(name)
	if not tail:
		head, tail = os.path.split(head)
	if head and tail and not os.path.exists(head):
		makedirs(head, mode)
		if tail == curdir:
			return
	if not os.path.isdir(name):
		os.mkdir(name, mode)
		#os.lchmod(name, mode)
		os.chmod(name, mode)
	return

#=====================
def convertParserToParams(parser):
	parser.disable_interspersed_args()
	(options, args) = parser.parse_args()
	if len(args) > 0:
		apDisplay.printError("Unknown commandline options: "+str(args))
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")

	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	return params

#=====================
def getXversion():
	xcmd = "X -version"
	proc = subprocess.Popen(xcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()
	for line in proc.stderr:
		if re.match("Build ID:", line):
			sline = re.sub("Build ID:", "", line).strip()
			m = re.search("\s([0-9\.]+)", sline)
			if m:
				version = m.groups()[0]
				return versionToNumber(version)	
	return None


#=====================
def versionToNumber(version):
	num = 0
	nums = version.split(".")
	if nums:
		for i,val in enumerate(nums):
			num += float(val)/(100**i)
	return num

#=====================
def resetVirtualFrameBuffer(killall=False):
	logf = open("xvfb.log", "a")
	if killall is True:
		xvfbcmd = "killall Xvfb\n"
		logf.write(xvfbcmd)
		proc = subprocess.Popen(xvfbcmd, shell=True, stdout=logf, stderr=logf)
		proc.wait()
	port = 1
	fontpath = getFontPath()
	securfile = getSecureFile()
	rgbfile = getRgbFile()
	while (port%10 == 0 or port%10 == 1):
		port = int(random.random()*90+2)
	#port = str("5")
	portstr = str(port)
	apDisplay.printMsg("Opening Xvfb port "+portstr)
	xvfbcmd = (
		"Xvfb :"+portstr
		+" -kb -once -ac -pn -screen 0 1200x1200x24 "
		+fontpath+securfile+rgbfile
		+" &"
	)
	apDisplay.printMsg(xvfbcmd)
	logf.write(xvfbcmd)
	proc = subprocess.Popen(xvfbcmd, shell=True, stdout=logf, stderr=logf)
	time.sleep(1)
	os.environ["DISPLAY"] = ":"+portstr
	time.sleep(2)
	logf.close()
	return port

#=====================
def killVirtualFrameBuffer(port=None):
	if port is None:
		xvfbcmd = "killall Xvfb\n"
		proc = subprocess.Popen(xvfbcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		proc.wait()
		return
	xvfbcmd = "ps -ef | grep -i xvfb | grep %d"%(port)
	proc = subprocess.Popen(xvfbcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	stdout = proc.stdout
	proc.wait()
	lines = proc.stdout.readlines()
	for line in lines:
		if 'Xvfb' in line:
			bits = line.strip().split()
			if len(bits) > 0:
				xvfbcmd = "kill -9 "+bits[1]
				proc = subprocess.Popen(xvfbcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				proc.wait()
				apDisplay.printMsg("Killed Xvfb on port %d"%(port))
				return
	return

#=====================
def getFontPath(msg=True):
	pathlist = [
		"/usr/share/X11/fonts/misc",
		"/usr/share/fonts/X11/misc",
		"/usr/X11R6/lib64/X11/fonts/misc",
		"/usr/X11R6/lib/X11/fonts/misc",
	]
	for path in pathlist:
		alias = os.path.join(path, "fonts.alias")
		if os.path.isdir(path) and os.path.isfile(alias):
			return " -fp "+path
	apDisplay.printWarning("Xvfb: could not find Font Path")
	return " "

#=====================
def getSecureFile(msg=True):
	"""
	This file comes with xorg-x11-server-Xorg in Fedora 7,8
	missing in Fedora 9
	"""
	filelist = [
		"/usr/X11R6/lib64/X11/xserver/SecurityPolicy",
		"/usr/lib64/xserver/SecurityPolicy",
		"/usr/X11R6/lib/X11/xserver/SecurityPolicy",
		"/usr/lib/xserver/SecurityPolicy",
	]
	for securfile in filelist:
		if os.path.isfile(securfile):
			return " -sp "+securfile
	apDisplay.printWarning("Xvfb: could not find Security File")
	return " "

#=====================
def getRgbFile(msg=True):
	"""
	This file comes with xorg-x11-server-Xorg in Fedora 7,8
	missing in Fedora 9
	"""
	#return " "
	filelist = [
		"/usr/share/X11/rgb",
		"/usr/X11R6/lib64/X11/rgb",
		"/usr/X11R6/lib/X11/rgb",
	]
	xversion = getXversion()
	if xversion > 1.02:
		return " "
	for rgbfile in filelist:
		if os.path.isfile(rgbfile+".txt"):
			return " -co "+rgbfile
	apDisplay.printWarning("Xvfb: could not find RGB File")
	return " "

#=====================
def getNumProcessors(msg=True):
	proc = subprocess.Popen("cat /proc/cpuinfo | grep processor", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	proc.wait()
	nproc = len(proc.stdout.readlines())
	if msg is True:
		apDisplay.printMsg("Found "+str(nproc)+" processors on this machine")
	return nproc

#=====================
def setUmask(msg=False):
	if os.getgid() == 773:
		prev = os.umask(002)
		curr = os.umask(002)
	else:
		prev = os.umask(000)
		curr = os.umask(000)
	if msg is True:
		apDisplay.printMsg("Umask changed from "+str(prev)+" to "+str(curr))

#=====================
def getExecPath(exefile, die=False):
	proc = subprocess.Popen("which "+exefile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out = proc.stdout
	proc.wait()
	path = out.readline().strip()
	if len(path) < 1:
		if die is False:
			return None
		apDisplay.printError("Cound not find "+exefile+" in your PATH")
	return path









