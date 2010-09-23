## python
import os
import re
import math
import sys
import pwd
import time
import random
import socket
import string
import inspect
import subprocess

## appion
from appionlib import apDisplay

####
# This is a low-level file with NO database connections
# Please keep it this way
####


#=====================
def getAppionDirectory():
	"""
	Used by appionLoop
	"""
	appiondir = None
	this_file = inspect.currentframe().f_code.co_filename
	libdir = os.path.dirname(this_file)
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
	hourstamp = string.lowercase[(time.localtime()[3])%26]
	if hourstamp == "x":
		### SPIDER does not like x's
		hourstamp = "z"
	#mins = time.localtime()[3]*12 + time.localtime()[4]
	#minstamp = string.lowercase[mins%26]
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
	userdict = getUserDict()
	if not userdict:
		return "unknown"
	return userdict['username']

#=====================
def getUserDict():
	uid = os.getuid()
	if not uid:
		return None
	userinfo = pwd.getpwuid(uid)
	if not userinfo or len(userinfo) < 6:
		return None
	userdict = {
		'username': userinfo[0],
		'uid': int(userinfo[2]),
		'gid': int(userinfo[3]),
		'fullname': userinfo[4],
		'homedir': userinfo[5],
		'unixshell': os.path.basename(userinfo[6]),
	}
	return userdict

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
def getTotalMemory():
	from pyami import mem
	return mem.total()

#=====================
def getSystemName():
	try:
		system = os.uname()[0].lower()
	except:
		system = "unknown"
	return system

#=====================
def getCPUVendor():
	if not os.path.exists('/proc/cpuinfo'):
		return None
	f = open('/proc/cpuinfo', 'r')
	vendor = None
	for line in f:
		if 'vendor_id' in line:
			if 'Intel' in line:
				vendor = 'Intel'
				break
			elif 'AMD' in line:
				vendor = 'AMD'
				break
			elif ':' in line:
				bits = line.split(':')
				vendor = bits[1].strip()
	f.close()
	return vendor

#=====================
def getGPUVendor():
	cmd = "/sbin/lspci"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	proc.wait()
	lines = proc.stdout.readlines()
	vendor = None
	for line in lines:
		if 'VGA compatible controller:' in line:
			sline = line.strip()
			bits = sline.split(':')
			if len(bits) < 3:
				continue
			vendor = bits[2].strip()
			if vendor.lower().startswith('nvidia'):
				vendor = 'nVidia'
			elif vendor.lower().startswith('ati'):
				vendor = 'ATI'
			elif vendor.lower().startswith('matrox'):
				vendor = 'Matrox'
			elif vendor.lower().startswith('intel'):
				vendor = 'Intel'
			else:
				vendor = re.sub(' .*', '', vendor)
	return vendor

#=====================
def getLinuxDistro():
	### redhat only
	flavfile = "/etc/redhat-release"
	if os.path.exists(flavfile):
		f = open(flavfile, "r")
		flavor = f.readline().strip()
		f.close()
		return flavor

	### more general at least ubuntu/redhat
	flavfile = "/etc/issue"
	if os.path.exists(flavfile):
		f = open(flavfile, "r")
		flavor = f.readline().strip()
		f.close()
		return flavor

	### more general at least ubuntu/redhat
	cmd = "lsb_release -d"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	proc.wait()
	descript = proc.stdout.readline().strip()
	if descript:
		bits = descript.split('\t')
		if len(bits) > 1:
			return bits[1].strip()

	### fall back
	return None

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
def createDirectory(path, mode=0775, warning=True):
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
			sline = re.sub("xorg-x11-server", "", sline).strip()
			m = re.search("\s*([0-9\.]+)", sline)
			if m:
				version = m.groups()[0]
				return versionToNumber(version)
		elif re.match("xorg-server", line):
			sline = re.sub("xorg-server [0-9]+:", "", line).strip()
			m = re.search("\s*([0-9\.]+)", sline)
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
	#random 4 digit port
	port = int(random.random()*9000+1000)
	portstr = str(port)
	apDisplay.printMsg("Opening Xvfb port "+portstr)
	xvfbcmd = (
		"Xvfb :"+portstr
		+" -once -ac -pn -screen 0 1200x1200x24 "
		+fontpath+securfile+rgbfile
		+" &"
	)
	apDisplay.printMsg(xvfbcmd)
	logf.write(xvfbcmd)
	proc = subprocess.Popen(xvfbcmd, shell=True, stdout=logf, stderr=logf)
	os.environ["DISPLAY"] = ":"+portstr
	logf.close()
	return port

#=====================
def killVirtualFrameBuffer(port=None):
	### port is unknown kill all virtual frame buffers
	if port is None:
		xvfbcmd = "killall Xvfb\n"
		proc = subprocess.Popen(xvfbcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		proc.wait()
		return

	### find specific virtual frame buffer
	xvfbcmd = "ps -ef | grep -i xvfb | grep %d"%(port)
	proc = subprocess.Popen(xvfbcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	stdout = proc.stdout
	proc.wait()
	lines = proc.stdout.readlines()
	for line in lines:
		if 'Xvfb' in line:
			bits = line.strip().split()
			if len(bits) > 0:
				### kill the frame buffer
				pid = int(bits[1])
				xvfbcmd = "kill %d"%(pid)
				proc = subprocess.Popen(xvfbcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				proc.wait()
				### delete this file can cause problems with user permissions
				rmxfile = "/bin/rm -fv /tmp/.X11-unix/X%d"%(port)
				proc = subprocess.Popen(rmxfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
		"/etc/X11/xserver/SecurityPolicy"
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
	filelist = [
		"/usr/share/X11/rgb",
		"/usr/X11R6/lib64/X11/rgb",
		"/usr/X11R6/lib/X11/rgb",
	]
	xversion = getXversion()
	print "X version", xversion
	if xversion is None or xversion > 1.0109:
		return " "
	for rgbfile in filelist:
		if os.path.isfile(rgbfile+".txt"):
			return " -co "+rgbfile
	apDisplay.printWarning("Xvfb: could not find RGB File")
	return " "

#=====================
def getNumProcessors(msg=True):
	if not os.path.exists('/proc/cpuinfo'):
		return None
	f = open('/proc/cpuinfo', 'r')
	nproc = 0
	for line in f:
		if line.startswith('processor'):
			nproc += 1
	f.close()
	if msg is True:
		apDisplay.printMsg("Found "+str(nproc)+" processors on this machine")
	return nproc

#=====================
def setUmask(msg=False):
	newUmask = 002
	prev = os.umask(newUmask)
	if msg is True:
		apDisplay.printMsg("Umask changed from "+str(prev)+" to "+str(newUmask))
	return

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

#=====================
def runCmd(cmd, package="", verbose=False, showcmd=True, logfile=None, fail=False):
	"""
	executes a command from any processing package in a controlled fashion
	"""
	waited = False
	if showcmd is True:
		sys.stderr.write(apDisplay.colorString(str(package)+": ","magenta")+cmd+"\n")
	t0 = time.time()
	try:
		if logfile is not None:
			logf = open(logfile, 'a')
			proc = subprocess.Popen(cmd, shell=True, 
				stdout=logf, stderr=logf)
		elif verbose is False:
			devnull = open('/dev/null', 'w')
			proc = subprocess.Popen(cmd, shell=True, 
				stdout=devnull, stderr=devnull)
		else:
			proc = subprocess.Popen(cmd, shell=True)
		if verbose is True:
			out, err = proc.communicate()
			if out is not None and err is not None:
				print "error", out, err
		else:
			out, err = proc.communicate()
			### continuous check
			waittime = 2.0
			while proc.poll() is None:
				if waittime > 10:
					waited = True
					sys.stderr.write(".")
				waittime *= 1.1
				time.sleep(waittime)
	except:
		apDisplay.printWarning("could not run command: "+cmd)
		raise
	tdiff = time.time() - t0
	if tdiff > 20:
		apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
	elif waited is True:
		print ""


#================
def randomString(length):
	"""
	return a string of random letters and numbers of defined length
	"""
	mystr = ""
	### allow hexidemical chars
	chars = string.letters[:6] + string.digits
	for i in range(length):
		mystr += random.choice(chars)
	return mystr

####
# This is a low-level file with NO database connections
# Please keep it this way
####












