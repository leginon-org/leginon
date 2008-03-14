## python
import os
import sys
import re
import socket
import time
import random
## sinedon
#import sinedon.data as data
## pyami
#from pyami import mem
## pyappion
#import apVersion
import apDisplay

def getAppionDirectory():
	"""
	Used by appionLoop
	"""
	appiondir = None

	trypath = os.environ.get('APPIONDIR')
	if trypath and os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	libdir = os.path.dirname(__file__)
	libdir = os.path.abspath(libdir)
	trypath = os.path.dirname(libdir)
 	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	user = os.getlogin() #os.environ.get('USER')
	trypath = "/home/"+user+"/pyappion"
 	if os.path.isdir(trypath):
		appiondir = trypath
		return appiondir

	apDisplay.printError("environmental variable, APPIONDIR, is not defined.\n"+
		"Did you source useappion.sh?")

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

def writeFunctionLog(cmdlist, params=None, logfile=None):
	"""
	Used by appionLoop
	"""
	if logfile is not None:
		pass
	elif params is not None and 'functionLog' in params and params['functionLog'] is not None:
		logfile = params['functionLog']
	else:
		logfile = getFunctionName(sys.argv[0])+".log"
	apDisplay.printMsg("writing function log to: "+logfile)
	#WRITE INFO
	try:
		user = os.getlogin() #os.environ.get('USER')
	except:
		user = "user.unknown"
	try:
		host = socket.gethostname()
	except:
		host = "host.unknown"
	timestamp = "[ "+user+"@"+host+": "+time.asctime()+" ]\n"
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
			
def closeFunctionLog(params=None, logfile=None):
	"""
	Used by appionLoop
	"""
	if logfile is not None:
		pass
	elif params is not None and params['functionLog'] is not None:
		logfile = params['functionLog']
	else:
		logfile = "function.log"
	apDisplay.printMsg("closing out function log: "+logfile)
	#WRITE INFO
	timestamp = "["+time.asctime()+"]\n"
	out="finished run"
	if 'functionname' in params:
		out += " of "+params['functionname']
	out += "\n"
	f=open(logfile,'a')
	f.write(timestamp)
	f.write(out)
	f.close()

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

def makedirs(name, mode=0777):
	"""
	Works like mkdir, except that any intermediate path segment (not
	just the rightmost) will be created if it does not exist.  This is
	recursive.
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
		os.chmod(name, mode)
	return

def removefiles(path,patterns):
	allfiles = os.listdir(path)
	files = allfiles[:]
	for pattern in patterns:
		files = filter((lambda x: x.find(pattern)>=0),files)
	patterns_line = ('","'.join(patterns))
	apDisplay.printWarning('%d files with the patterns ("%s") will be removed in %s' % (len(files),patterns_line,path))
	for file in files:
		fullpath = os.path.join(path,file)
		try:
			os.remove(fullpath)
		except:
			apDisplay.printError('%s can not be removed' % fullpath)

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

def resetVirtualFrameBuffer():
	blue = "\033[34m"
	clear = "\033[0m"
	sys.stderr.write(blue)
	apDisplay.printMsg("ignore following errors in blue")
	#user = os.getlogin() #os.environ["USER"]
	os.popen("killall Xvfb");
	#os.system("kill `ps -U "+user+" | grep Xvfb | sed \'s\/pts.*$\/\/\'`");
	time.sleep(1);
	port = 1
	while (port%10 == 0 or port%10 == 1):
		port = int(random.random()*30+2)
	port = str(port)
	port = str("5")
	apDisplay.printMsg("opening Xvfb port "+port)
	os.popen("Xvfb :"+port+" -screen 0 800x800x8 &");
	time.sleep(1);
	os.environ["DISPLAY"] = ":"+port
	time.sleep(2)
	sys.stderr.write(clear)
	#if 'bash' in os.environ.get("SHELL"):
	#	system("export DISPLAY=':1'");	
	#else
	#	system("setenv DISPLAY :1");

def getNumProcessors(msg=True):
	f = os.popen("cat /proc/cpuinfo | grep processor")
	nproc = len(f.readlines())
	if msg is True:
		apDisplay.printMsg("Found "+str(nproc)+" processors on this machine")
	return nproc

def setUmask():
	if os.getgid() == 773:
		os.umask(002)
	else:
		os.umask(000)








