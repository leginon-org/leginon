#!/usr/bin/env python

import os
import re
import sys
import shutil
import subprocess
import platform
import webbrowser
import stat
import time
import sha


class CentosInstallation(object):

	def setReleaseDependantValues(self):
		# need to change to branch when release
		self.svnCmd = "svn co http://ami.scripps.edu/svn/myami/branches/myami-2.2 " + self.svnMyamiDir
		
		#self.svnCmd = "svn co http://ami.scripps.edu/svn/myami/trunk " + self.svnMyamiDir

		# SHA-1 digest of a registration key provided by AMI. When we change the key that we give to
		# registered users, we need to update this value.
		self.regKeyHash = '4\xa3T\xf2KB\x0e\xd7\x1fk1\xfdb\xcd\x04\xdcH>\xcc\x8e'

	def checkDistro(self):

		flavfile = "/etc/redhat-release"
		if not os.path.exists(flavfile):		
			print "This is not CentOS. Exiting installation..."
			self.writeToLog("ERROR: not CentOS ---")
			return False

		f = open(flavfile, "r")
		flavor = f.readline().strip()
		f.close()

		if not flavor.startswith("CentOS"):
			print "This is not CentOS. Exiting installation..."
			self.writeToLog("ERROR: not CentOS ---")
			return False

		print "Current OS Information: " + flavor
		self.writeToLog("CentOS info: " + flavor)
	
	def  determineNumberOfCPUs(self):
		""" Number of virtual or physical CPUs on this system """

		# Python 2.6+
		try:
			import multiprocessing
			return multiprocessing.cpu_count()
		except (ImportError,NotImplementedError):
			pass

		# POSIX
		try:
			res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

			if res > 0:
				return res
		except (AttributeError,ValueError):
			pass

	def checkRoot(self):

		uid = os.getuid()
		if uid != 0:
			print "You must run this program as root. Exiting installation..."
			self.writeToLog("ERROR: root access checked deny ---")
			return False

		print "\"root\" access checked success..."
		self.writeToLog("root access checked success")

	def removeLogFile(self):
		if os.path.isfile(self.logFilename):
			self.writeToLog("remove old log file")
			os.remove(self.logFilename)

	def disableSeLinux(self):
		self.runCommand("/usr/sbin/setenforce 0")
		seLinuxConfig = "/etc/selinux/config"
		seLinuxConfigBackup = "/etc/selinux/config.bck"

		if not os.path.exists(seLinuxConfig):
			print "SeLinux configure file does not exist..."
			self.writeToLog("ERROR: No SeLinux configure file ---")
		return False 

		# make a back up from original config file
		shutil.move(seLinuxConfig, seLinuxConfigBackup)

		inf = open(seLinuxConfigBackup, 'r')
		outf = open(seLinuxConfig, 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('SELINUX=enforcing'):
				outf.write("SELINUX=disabled\n")
			elif line.startswith('SELINUX=permissive'):
				outf.write("SELINUX=disabled\n")
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()
		return True
	
	# if SeLinus is not disable, return false, otherwise good to go.
	def checkSeLinux(self):
		
		proc = subprocess.Popen("/usr/sbin/selinuxenabled")
		returnValue = proc.wait()

		
		if not returnValue:
			print("========================")
			print("ERROR: Please disable SELinux before running this auto installation. Visit http://ami.scripps.edu/redmine/projects/appion/wiki/Install_Appion_and_Leginon_using_the_auto-installation_tool .")
			print("Exiting installation...")
			print("========================")
			return False
		return True

	def setupFilePermission(self):
		# Set umask to 0 so that we can set mode to 0777 later
		originalUmask = os.umask(0)
		
		if not os.path.exists(self.imagesDir):
			self.writeToLog("create images folder - /myamiImages")
			os.makedirs(self.imagesDir, 0777)
		else:
			os.chmod(self.imagesDir, 0777)

		if not os.path.exists(os.path.join(self.imagesDir, "leginon")):
			os.makedirs(os.path.join(self.imagesDir, "leginon"), 0777)
		else:
			os.chmod(os.path.join(self.imagesDir, "leginon"), 0777)
				
		if not os.path.exists(os.path.join(self.imagesDir, "appion")):
			os.makedirs(os.path.join(self.imagesDir, "appion"), 0777)
		else:
			os.chmod(os.path.join(self.imagesDir, "appion"), 0777)
			
		umask = os.umask(originalUmask)


	def yumUpdate(self):
		print "Updating system files...."

		self.runCommand("rpm -Uvh http://dl.fedoraproject.org/pub/epel/5/`uname -i`/epel-release-5-4.noarch.rpm")

		self.runCommand("yum -y update yum*")

		self.yumInstall(['yum-fastestmirror.noarch', 'yum-utils.noarch'])

		self.runCommand("yum -y update")

		#self.runCommand("updatedb")
		self.writeToLog("yum update finished..")

	def runCommand(self, cmd):
		
		self.writeToLog("#===================================================")
		self.writeToLog("Run the following Command:")
		self.writeToLog("%s"%(cmd,))
		print cmd + '\n'
		print 'Please wait......(This may take a few minutes.)\n'

		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdoutResult = proc.stdout.read()
		stderrResult = proc.stderr.read()
		print stdoutResult
		sys.stderr.write(stderrResult)
		returncode = proc.wait()
		if (stderrResult != ""):
			self.writeToLog("--- Run Command Error ---")
			self.writeToLog(stderrResult)
		self.writeToLog("#===================================================\n")
		return stdoutResult

	def yumInstall(self, packagelist):
		
		if not packagelist:
			return
	
		packagestr = ""
		for package in packagelist:
			packagestr += " " + package

		cmd = "yum -y install" + packagestr
		self.runCommand(cmd)
		#self.runCommand("updatedb")

	def openFirewallPort(self, port):
			
		self.runCommand("/sbin/iptables --insert RH-Firewall-1-INPUT --proto tcp --dport %d --jump ACCEPT"%(port))
		self.runCommand("/sbin/iptables-save > /etc/sysconfig/iptables")
		self.runCommand("/etc/init.d/iptables restart")
		self.writeToLog("firewall port %d opened"%(port))

	def setupWebServer(self):
		self.writeToLog("--- Start install Web Server")
		
		packagelist = ['fftw3-devel', 'gcc', 'httpd', 'libssh2-devel', 'php', 'php-mysql', 'phpMyAdmin.noarch', 'php-devel', 'php-gd',]
		self.yumInstall(packagelist)

		self.editPhpIni()
		self.editApacheConfig()
		
		self.installPhpMrc()
		self.installPhpSsh2()
		self.installMyamiWeb()
		self.editMyamiWebConfig()
		
		self.runCommand("/sbin/service httpd stop")
		self.runCommand("/sbin/service httpd start")
		self.runCommand("/sbin/chkconfig httpd on")
		self.openFirewallPort(80)
		return True

	def setupDBServer(self):
		self.writeToLog("--- Start install Database Server")

		self.mysqlYumInstall()
		# turn on auto mysql start

		self.runCommand("/sbin/chkconfig mysqld on")
		
		# start (restart) mysql server
		self.runCommand("/sbin/service mysqld restart")
		
		# run database setup script.
		cmd = os.path.join(self.svnMyamiDir, 'install/newDBsetup.php -L %s -P %s -H %s -U %s -E %s'%(self.leginonDB, self.projectDB, self.dbHost, self.dbUser, self.adminEmail))
		cmd = 'php ' + cmd

		self.runCommand(cmd)

		self.openFirewallPort(3306)
		return True

	def setupProcessServer(self):
		self.writeToLog("--- Start install Processing Server")

		self.processServerYumInstall()
		
		# install all the myami python packages except appion.
		os.chdir(self.svnMyamiDir)
		self.runCommand('./pysetup.sh install')

		# install the appion python packages
		# For the bin scripts, we add an extra directory level below
		# the default location to keep all appion scripts in their
		# own place, rather than cluttering up /usr/bin or whatever.
		pyprefix = self.runCommand('python -c "import sys;print sys.prefix"')
		apbin = os.path.join(pyprefix, 'bin', 'appion')
		os.chdir(self.svnMyamiDir + 'appion')
		self.runCommand('python setup.py install --install-scripts=%s' % (apbin,))
		
		# add a custom search path to appion.sh and appion.csh in profile.d
		for ext,cmd,eq in (('sh','export','='),('csh','setenv',' ')):
			fname = '/etc/profile.d/appion.%s' % (ext,)
			f = open(fname, 'w')
			setcmd = '%s PATH%s${PATH}:%s' % (cmd, eq, apbin,)
			f.write(setcmd)
			f.close()

		# setup Leginon configure file
		self.writeToLog("setup Leginon configure file")
		leginonDir = self.runCommand('python -c "import leginon; print leginon.__path__[0]"')		
		leginonDir = leginonDir.strip()
		self.setupLeginonCfg(leginonDir + '/config')

		# setup Sinedon configure file
		self.writeToLog("setup Sinedon configure file")
		sinedonDir = self.runCommand('python -c "import sinedon; print sinedon.__path__[0]"')
		sinedonDir = sinedonDir.strip()
		self.setupSinedonCfg(sinedonDir)

		# setup instruments configuration
		pyscopeDir = self.runCommand('python -c "import pyscope; print pyscope.__path__[0]"')
		pyscopeDir = pyscopeDir.strip()

		self.setupPyscopeCfg(pyscopeDir)

		os.chdir(self.currentDir)		
		self.enableTorqueComputeNode()
		return True

	def setupJobServer(self):
		self.writeToLog("--- Start install Job Server")

		packagelist = ['torque-server', 'torque-scheduler',]
		self.yumInstall(packagelist)

		
		self.runCommand("/sbin/chkconfig pbs_server on")
		self.runCommand("/sbin/chkconfig pbs_sched on")

		f = open('/var/torque/server_priv/nodes', 'w')
		f.write("%s np=%d"%(self.hostname, self.nproc))
		f.close()

		f = open('/var/torque/server_name', 'w')
		f.write("%s"%(self.hostname))
		f.close()

		# edit /var/hosts file
		self.editHosts()

		# start the Torque server, keep this after any config file editing.
		self.runCommand("/sbin/service pbs_server start")
		self.runCommand("/sbin/service pbs_sched start")
		
		self.runCommand("/sbin/service network restart")


		return True

	def installExternalPackages(self):
		self.writeToLog("--- Start install External Packages")
		
		self.installEman()
		self.installSpider()
		self.installXmipp()

		return True

	def installEman(self):
		self.writeToLog("--- Start install Eman1")
		cwd = os.getcwd()
		
		# select 32 or 64 bit file to download
		if self.machine == "i686" or self.machine == "i386" :
			fileLocation = "http://ami.scripps.edu/redmine/attachments/download/632/eman-linux-x86-cluster-1.9.tar.gz"
			fileName = "eman-linux-x86-cluster-1.9.tar.gz"
		else :
			fileLocation = "http://ami.scripps.edu/redmine/attachments/download/631/eman-linux-x86_64-cluster-1.9.tar.gz"
			fileName = "eman-linux-x86_64-cluster-1.9.tar.gz"

		# download the tar file and unzip it
		command = "wget -c " + fileLocation
		self.runCommand(command)
		command = "tar -zxvf " + fileName
		self.runCommand(command)
		
		# move the unzipped folder to a global location
		self.runCommand("mv -v EMAN /usr/local/")

		# Run the EMAN installer, it sets up the EMAN python module (must be run from the EMAN directory)
		emandir = "/usr/local/EMAN"
		os.chdir(emandir)
		self.runCommand("./eman-installer")

		# set environment variables
		# For BASH, create an eman.sh
		f = open('eman.sh', 'w')
		f.write('''export EMANDIR=/usr/local/EMAN\n
			export PATH=${EMANDIR}/bin:${PATH}\n
			export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${EMANDIR}/lib\n
			export PYTHONPATH=${EMANDIR}/lib''')
		f.close()

		# For C shell, create an eman.csh
		f = open('eman.csh', 'w')
		f.write('''setenv EMANDIR /usr/local/EMAN\n
			setenv PATH ${EMANDIR}/bin:${PATH}\n
			setenv LD_LIBRARY_PATH ${EMANDIR}/lib\n
			setenv PYTHONPATH ${EMANDIR}/lib''')
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		shutil.copy("eman.sh", "/etc/profile.d/eman.sh")
		shutil.copy("eman.csh", "/etc/profile.d/eman.csh")
		os.chmod("/etc/profile.d/eman.sh", 0755)
		os.chmod("/etc/profile.d/eman.csh", 0755)
		
		os.chdir(self.currentDir)
				
		return True

	def installSpider(self):
		self.writeToLog("--- Start install Spider")
		
		fileLocation = "http://ami.scripps.edu/redmine/attachments/download/638/spidersmall.18.10.tar.gz"
		fileName = "spidersmall.18.10.tar.gz"

		# download the tar file and unzip it
		command = "wget -c " + fileLocation
		self.runCommand(command)
		print "-------------done with wget.------------"
		command = "tar -zxvf " + fileName
		self.runCommand(command)
		
		# move the unzipped folder to a global location
		shutil.move("spider", "/usr/local/spider")
		#self.runCommand("mv -v spider /usr/local/")

		# select 32 or 64 bit file to install
		if self.machine == "i686" or self.machine == "i386" :
			if self.nproc == 1:
				fileName = "spider_linux"
			else:
				fileName = "spider_linux_mp_intel"
		else :
			fileName = "spider_linux_mp_opt64"

		# create a link to the selected file in /usr/local/bin
		command = "ln -sv /usr/local/spider/bin/" + fileName + " /usr/local/bin/spider"
		self.runCommand(command)

		# set environment variables
		# For BASH, create an spider.sh
		f = open('spider.sh', 'w')
		f.write('''export SPIDERDIR=/usr/local/spider
export SPBIN_DIR=${SPIDERDIR}/bin/
export SPPROC_DIR=${SPIDERDIR}/proc/
export SPMAN_DIR=${SPIDERDIR}/man/
''')
		f.close()

		# For C shell, create an spider.csh
		f = open('spider.csh', 'w')
		f.write('''setenv SPIDERDIR /usr/local/spider
setenv SPMAN_DIR ${SPIDERDIR}/man/
setenv SPPROC_DIR ${SPIDERDIR}/proc/
setenv SPBIN_DIR ${SPIDERDIR}/bin/''')
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		shutil.copy("spider.sh", "/etc/profile.d/spider.sh")
		shutil.copy("spider.csh", "/etc/profile.d/spider.csh")
		os.chmod("/etc/profile.d/spider.sh", 0755)
		os.chmod("/etc/profile.d/spider.csh", 0755)


	def installXmipp(self):
		self.writeToLog("--- Start install Xmipp")

		cwd = os.getcwd()
		
		dirName = "Xmipp-2.4-src"
		tarFileName = dirName + ".tar.gz"
		tarFileLocation = "http://ami.scripps.edu/redmine/attachments/download/636/" + tarFileName

		# download the source code tar file and unzip it
		command = "wget -c " + tarFileLocation
		self.runCommand(command)
		command = "tar -zxvf " + tarFileName
		self.runCommand(command)

		# change directories to the unzipped xmipp dir
		os.chdir(dirName)

		#
		# prepare Xmipp make files
		# 
		
		# locate the mpi library
		mpifile = "libmpi.so"
		command = "locate " + mpifile
		libMpiPath = self.runCommand(command)

		# format mpi include and lib paths
		if ( mpifile in libMpiPath ):
			matchPattern = "lib/" + mpifile
			libMpiPath = libMpiPath.split( matchPattern )
			libMpiPath = libMpiPath[0]
		
		# make sure the path is what we expect, ending with gcc/
		if ( not libMpiPath.endswith( "gcc/" ) ):
			self.writeToLog("--- Error installing Xmipp. Could not locate and parse the path to %s" % (mpifile, ))
			return False

		includeDir = libMpiPath + "include/"
		libDir = libMpiPath + "lib/"

		# build new lines for the configuration file
		mpiInclude = "opts.Add('MPI_INCLUDE', 'MPI headers dir ', '" + includeDir + "')"
		mpiLibDir = "opts.Add('MPI_LIBDIR', 'MPI libraries dir ', '" + libDir + "')"
		mpiLib = "opts.Add('MPI_LIB', 'MPI library', 'mpi')"

		# create a backup of the SConstruct file and open it for writing
		shutil.copy('SConstruct', 'SConstruct-backup')
		shutil.move('SConstruct', 'SConstruct-tmp')
		inf = open('SConstruct-backup', 'r')
		outf = open('SConstruct', 'w')

		# parse the SConstruct file to replace MPI paths with the new lines
		for line in inf:
			line = line.rstrip()
			if line.startswith("opts.Add('MPI_INCLUDE', 'MPI headers dir ',"):
				outf.write(mpiInclude + "\n")
			elif line.startswith("opts.Add('MPI_LIBDIR', 'MPI libraries dir ',"):
				outf.write(mpiLibDir + "\n")
			elif line.startswith("opts.Add('MPI_LIB', 'MPI library',"):
				outf.write(mpiLib + "\n")
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()
		os.remove('SConstruct-tmp')

		# configure

		mpiCommand = "mpi-selector --verbose --yes --system --set `rpm --qf '%{NAME}-%{VERSION}-gcc-%{ARCH}\n' -q openmpi`"
		self.runCommand(command)

		binDir = libMpiPath + "bin/"
		os.environ["PATH"] = binDir + ':' + os.environ["PATH"]

		command = "./scons.configure"
		output = self.runCommand(command)
		if ( "Checking for MPI ... yes" not in output ):
			self.writeToLog("--- Error installing Xmipp. Could not find MPI during configuration.")
			return False

		# compile
		self.runCommand("./scons.compile")

		# change directories to original working dir
		os.chdir(cwd)

		# move the main source code directory to global location, like /usr/local
		self.writeToLog("--- Moving the Xmipp directory to /usr/local/Xmipp.")
		os.rename(dirName, "/usr/local/Xmipp")

		#
		# set environment variables
		#

		bashFile = "xmipp.sh"
		cShellFile = "xmipp.csh"
		profileDir = "/etc/profile.d/"

		# For BASH, create an xmipp.sh
		f = open(bashFile, 'w')
		f.write('''export XMIPPDIR=/usr/local/Xmipp
export PATH=${XMIPPDIR}/bin:${PATH}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${XMIPPDIR}/lib''')
		f.close()

		# For C shell, create an xmipp.csh
		f = open(cShellFile, 'w')
		f.write('''setenv XMIPPDIR /usr/local/Xmipp
setenv PATH ${XMIPPDIR}/bin:${PATH}
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${XMIPPDIR}/lib''')
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		self.writeToLog("--- Adding xmipp.sh and xmipp.csh to /etc/profile.d/.")
		shutil.copy(bashFile, profileDir + bashFile)
		shutil.copy(cShellFile, profileDir + cShellFile)
		os.chmod(profileDir + bashFile, 0755)
		os.chmod(profileDir + cShellFile, 0755)



	def installFrealign(self):
		self.writeToLog("--- Start install Frealign")
		
		fileLocation = "http://ami.scripps.edu/redmine/attachments/download/740/frealign_v8.09_110505.tar.gz"
		fileName = "frealign_v8.09_110505.tar.gz"

		# download the tar file and unzip it
		command = "wget -c " + fileLocation
		self.runCommand(command)
		print "-------------done with wget.------------"
		command = "tar -zxvf " + fileName
		self.runCommand(command)
		
		# move the unzipped folder to a global location
		shutil.move("frealign_v8.09", "/usr/local/")
		#self.runCommand("mv -v spider /usr/local/")

		# select 32 or 64 bit file to install
		if self.machine == "i686" or self.machine == "i386" :
			if self.nproc == 1:
				fileName = "frealign_v8.exe"
			else:
				fileName = "frealign_v8_mp.exe"
		else :
			fileName = "frealign_v8.exe"

		# create a link to the selected file in /usr/local/bin
		command = "ln -sv /usr/local/frealign_v8.09/bin/" + fileName + " /usr/local/bin/frealign"
		self.runCommand(command)

		# set environment variables
		# For BASH, create an spider.sh
		f = open('spider.sh', 'w')
		f.write('''export SPIDERDIR=/usr/local/spider
export SPBIN_DIR=${SPIDERDIR}/bin/
export SPPROC_DIR=${SPIDERDIR}/proc/
export SPMAN_DIR=${SPIDERDIR}/man/
''')
		f.close()

		# For C shell, create an spider.csh
		f = open('spider.csh', 'w')
		f.write('''setenv SPIDERDIR /usr/local/spider
setenv SPMAN_DIR ${SPIDERDIR}/man/
setenv SPPROC_DIR ${SPIDERDIR}/proc/
setenv SPBIN_DIR ${SPIDERDIR}/bin/''')
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		shutil.copy("spider.sh", "/etc/profile.d/spider.sh")
		shutil.copy("spider.csh", "/etc/profile.d/spider.csh")
		os.chmod("/etc/profile.d/spider.sh", 0755)
		os.chmod("/etc/profile.d/spider.csh", 0755)



	def processServerYumInstall(self):

		packagelist = ['ImageMagick', 'MySQL-python', 'compat-gcc-34-g77', 'fftw3-devel', 'gcc-c++', 'gcc-gfortran', 'gcc-objc', 'gnuplot', 'grace', 'gsl-devel', 'libtiff-devel', 'netpbm-progs', 'numpy', 'openmpi-devel', 'python-devel', 'python-imaging', 'python-matplotlib', 'python-tools', 'scipy', 'wxPython', 'xorg-x11-server-Xvfb','libjpeg-devel','zlib-devel',]
		self.yumInstall(packagelist)

	def enableTorqueComputeNode(self):
		packagelist = ['torque-mom', 'torque-client',]
		self.yumInstall(packagelist)
		self.runCommand("/sbin/chkconfig pbs_mom on")
		
		f = open('/var/torque/mom_priv/config', 'w')
		f.write("$pbsserver localhost # running pbs_server on this host")
		
		self.runCommand('qmgr -c "s s scheduling=true"')
		self.runCommand('qmgr -c "c q batch queue_type=execution"')
		self.runCommand('qmgr -c "s q batch started=true"')
		self.runCommand('qmgr -c "s q batch enabled=true"')
		self.runCommand('qmgr -c "s q batch resources_default.nodes=1"')
		self.runCommand('qmgr -c "s q batch resources_default.walltime=3600"')
		self.runCommand('qmgr -c "s s default_queue=batch"')		
		
		self.runCommand("/sbin/service pbs_mom start")
		
		f.close()

	def mysqlYumInstall(self):
		packagelist = ['mysql-server', 'php', 'php-mysql',]
		self.yumInstall(packagelist)
	
	def setupLeginonCfg(self, leginonCfgDir):
		inf = open(leginonCfgDir + '/default.cfg', 'r')
		outf = open(leginonCfgDir + '/leginon.cfg', 'w')

		for line in inf:
			if line.startswith('path:'):
				outf.write('path: %s/leginon\n'%(self.imagesDir))
			else:
				outf.write(line)
		inf.close()
		outf.close()

	def setupPyscopeCfg(self, pyscopeCfgDir):
		shutil.copy(pyscopeCfgDir +'/instruments.cfg.template', pyscopeCfgDir +'/instruments.cfg')


	def setupSinedonCfg(self, sinedonDir):
		inf = open(self.svnMyamiDir + 'sinedon/examples/sinedon.cfg', 'r')
		outf = open(sinedonDir + '/sinedon.cfg', 'w')

		for line in inf:
			if line.startswith('user: usr_object'):
				outf.write('user: root\n')
			else:
				outf.write(line)
		inf.close()
		outf.close()		

	def editHosts(self):

		# make a back up file
		shutil.copy('/etc/hosts', '/etc/hosts-tmp')
		inf = open('/etc/hosts-tmp', 'r')
		outf = open('/etc/hosts', 'w')

		for line in inf:
			line = line.rstrip()
			if "127.0.0.1" in line:
				outf.write("127.0.0.1		%s localhost.localdomain localhost\n"%(self.hostname))
			else:
				outf.write(line + '\n')
		
		inf.close()
		outf.close()
		os.remove('/etc/hosts-tmp')
			

	def editPhpIni(self):

		# make a back up file
		shutil.copy('/etc/php.ini', '/etc/php.ini-backup')		
		shutil.move('/etc/php.ini', '/etc/php.ini-tmp')
		inf = open('/etc/php.ini-tmp', 'r')
		outf = open('/etc/php.ini', 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith(';'):
				outf.write(line + "\n")
			elif line.startswith('error_reporting'):
				outf.write("error_reporting = E_ALL & ~E_NOTICE\n")
			elif line.startswith('display_error'):
				outf.write("display_error = On\n")
			elif line.startswith('register_argc_argv'):
				outf.write("register_argc_argv = On\n")
			elif line.startswith('short_open_tag'):
				outf.write("short_open_tag = On\n")
			elif line.startswith('max_execution_time'):
				pass
			elif line.startswith('max_input_time'):
				pass
			elif line.startswith('memory_limit'):
				pass
			else:
				outf.write(line + '\n')

		inf.close()
		os.remove('/etc/php.ini-tmp')
		
		outf.write('; custom parameters from CentOS Auto Install script\n')
		outf.write('max_execution_time = 300 ; Maximum execution time of each script, in seconds\n')
		outf.write('max_input_time = 300	 ; Maximum amout of time to spend parsing request data\n')
		outf.write('memory_limit = 1024M	 ; Maximum amount of memory a script may consume\n')
		outf.write('\n')

		outf.close()			
			
	def editApacheConfig(self):
	
		shutil.copy('/etc/httpd/conf/httpd.conf', '/etc/httpd/conf/httpd.conf-backup')
		shutil.move('/etc/httpd/conf/httpd.conf', '/etc/httpd/conf/httpd.conf-tmp')
		inf = open('/etc/httpd/conf/httpd.conf-backup', 'r')
		outf = open('/etc/httpd/conf/httpd.conf', 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('#'):
				outf.write(line + "\n")
			elif line.startswith('DirectoryIndex'):
				outf.write("DirectoryIndex index.html index.php\n")
			elif line.startswith('HostnameLookups'):
				outf.write("HostnameLookups On\n")
			elif line.startswith('UseCanonicalName'):
				outf.write("UseCanonicalName On\n")
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()
		os.remove('/etc/httpd/conf/httpd.conf-tmp')

	def installPhpMrc(self):
		
		if os.path.isfile('/etc/php.d/mrc.ini'):
			return

		phpmrcdir = os.path.join(self.svnMyamiDir, "programs/php_mrc")
		os.chdir(phpmrcdir)
		self.runCommand("phpize")
		self.runCommand("./configure")
		self.runCommand("make")
		module = os.path.join(phpmrcdir, "modules/mrc.so")

		if not os.path.isfile(module):
			self.writeToLog("ERROR: mrc.so failed")
			sys.exit(1)

		self.runCommand("make install")
		f = open("/etc/php.d/mrc.ini", "w")
		f.write("; Enable mrc extension module\n")
		f.write("extension=mrc.so\n")
		f.close()
		os.chdir(self.currentDir)

	def installPhpSsh2(self):
		if os.path.isfile("/etc/php.d/ssh2.ini"):
			return
		
		cwd = os.getcwd()
		self.runCommand("wget -c http://pecl.php.net/get/ssh2-0.11.0.tgz")
		self.runCommand("tar zxvf ssh2-0.11.0.tgz")
		sshdir = os.path.join(cwd, "ssh2-0.11.0")
		os.chdir(sshdir)
		self.runCommand("phpize")
		self.runCommand("./configure")
		self.runCommand("make")

		module = "modules/ssh2.so"
		if not os.path.isfile(module):
			self.writeToLog("ERROR ssh2.so failed")
			sys.exit(1)

		self.runCommand("make install")

		f = open('/etc/php.d/ssh2.ini', 'w')
		f.write('; Enable ssh2 extension module\n')
		f.write('extension=ssh2.so\n')
		f.close()
		os.chdir(self.currentDir)

	def getServerName(self):
		return platform.node()

	def getNumProcessors(self):
		if not os.path.exists('/proc/cpuinfo'):
			return None
		f = open('/proc/cpuinfo', 'r')
		nproc = 0
		for line in f:
			if line.startswith('processor'):
				nproc += 1
		f.close()
		return nproc
		
	def installMyamiWeb(self):
		svnMyamiwebDir = os.path.join(self.svnMyamiDir, "myamiweb")
		centosWebDir = "/var/www/html"
		self.runCommand("cp -rf %s %s"%(svnMyamiwebDir, centosWebDir))

	def editMyamiWebConfig(self):
	
		configFile = os.path.join("/var/www/html/myamiweb/config.php")

		inf = open(configFile+".template", 'r')
		outf = open(configFile, 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('// --- ') or len(line) == 0:
				outf.write(line + "\n")
			elif line.startswith("define('ENABLE_LOGIN'"):
				outf.write("define('ENABLE_LOGIN', %s);\n"%(self.enableLogin))
			elif line.startswith("define('DB_HOST'"):
				outf.write("define('DB_HOST', '%s');\n"%(self.dbHost))
			elif line.startswith("define('DB_USER'"):
				outf.write("define('DB_USER', '%s');\n"%(self.dbUser))
			elif line.startswith("define('DB_PASS'"):
				outf.write("define('DB_PASS', '%s');\n"%(self.dbPass))
			elif line.startswith("define('ADMIN_EMAIL'"):
				outf.write("define('ADMIN_EMAIL', '%s');\n"%(self.adminEmail))
			elif line.startswith("define('DB_LEGINON'"):
				outf.write("define('DB_LEGINON', '%s');\n"%(self.leginonDB))
			elif line.startswith("define('DB_PROJECT'"):
				outf.write("define('DB_PROJECT', '%s');\n"%(self.projectDB))
			elif line.startswith("define('MRC2ANY'"):
				outf.write("define('MRC2ANY', '%s');\n"%(self.mrc2any))
			elif "addplugin(\"processing\");" in line:
				outf.write("addplugin(\"processing\");\n")
			elif "// $PROCESSING_HOSTS[]" in line:
				outf.write("$PROCESSING_HOSTS[] = array('host' => '%s', 'nproc' => %d,'nodesmax' => '1','ppndef' => '1','ppnmax' => '1','reconpn' => '1','walltimedef' => '48','walltimemax' => '240','cputimedef' => '1000','cputimemax' => '10000','memorymax' => '','appionbin' => '/usr/','appionlibdir' => '/usr/lib/python2.4/site-packages/','baseoutdir' => '/appion','localhelperhost' => '','dirsep' => '/','wrapperpath' => '','loginmethod' => 'USERPASSWORD','loginusername' => '','passphrase' => '','publickey' => '','privatekey' => ''	);\n"%(self.dbHost, self.nproc))
			elif "// $CLUSTER_CONFIGS[]" in line:
				outf.write("$CLUSTER_CONFIGS[] = 'default_cluster';\n")
			elif line.startswith("define('TEMP_IMAGES_DIR', "):
				outf.write("define('TEMP_IMAGES_DIR', '/tmp');\n")
			elif line.startswith("define('DEFAULTCS', "):
				outf.write("define('DEFAULTCS', '%.1f');\n"%(self.csValue))		
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()

	def writeToLog(self, message):
		logfile = open(self.currentDir + "/" + self.logFilename, 'a')
		logfile.write(message + '\n')
		logfile.close()
			
	def getMyami(self):
		self.runCommand(self.svnCmd)

	def getDefaultValues(self):

		print "===================================="
		print "Installing job submission server"
		print "Installing processing server"
		print "Installing database server"
		print "Installing web server"
		print "===================================="
		print ""
		
		value = raw_input("Please enter the registration key. You must be registered at http://ami.scripps.edu/redmine to recieve a registration key: ")
		value = value.strip()

		self.regKey = value
		# Note to user: We try to collect a small amount of information about who installs our software
		# so that we may recieve funding for its continued support and development. We also pass this information
		# on to the providers of EMAN, XMIPP, and SPIDER, which we install with this script, 
		# to ensure their continued development as well. If you remove this check for the reg key, please
		# remember to appropriatly cite any software that you find useful while processing your data.
		result = self.checkRegistrationKey()
		if result is False:
			return False


		value = raw_input("Please enter an email address: ")
		value = value.strip()

		self.adminEmail = value

		# the Cs value is no longer needed in 2.2
		#print ""
		#print "What is the spherical aberration (Cs) constant for the microsope (in millimeters)."
		#print "Example : 2.0"
		#print ""
		#value = raw_input("Please enter the spherical aberration (Cs) value : ")
		#value = float (value.strip())

		self.csValue = 2.0#value
		
		#print ""
		#print ""
		#print ""		
		password = raw_input("Please enter the system root password: ")
		password = password.strip()
		self.serverRootPass = password

		value = ""
		while (value != "Y" and value != "y" and value != "N" and value != "n"): 
			value = raw_input("Would you like to install EMAN, Xmipp, and Spider at this time?(Y/N): ")
			value = value.strip()

		if (value == "Y" or value == "y"):
			self.doInstallExternalPackages = True
		else:
			self.doInstallExternalPackages = False
		
		
	def downloadSampleImages(self):
	   
		getImageCmd = "wget -P/tmp/images http://ami.scripps.edu/redmine/attachments/download/112/06jul12a_00015gr_00028sq_00004hl_00002en.mrc http://ami.scripps.edu/redmine/attachments/download/113/06jul12a_00015gr_00028sq_00023hl_00002en.mrc http://ami.scripps.edu/redmine/attachments/download/114/06jul12a_00015gr_00028sq_00023hl_00004en.mrc http://ami.scripps.edu/redmine/attachments/download/115/06jul12a_00022gr_00013sq_00002hl_00004en.mrc http://ami.scripps.edu/redmine/attachments/download/116/06jul12a_00022gr_00013sq_00003hl_00005en.mrc http://ami.scripps.edu/redmine/attachments/download/109/06jul12a_00022gr_00037sq_00025hl_00004en.mrc http://ami.scripps.edu/redmine/attachments/download/110/06jul12a_00022gr_00037sq_00025hl_00005en.mrc http://ami.scripps.edu/redmine/attachments/download/111/06jul12a_00035gr_00063sq_00012hl_00004en.mrc"

		print getImageCmd
		proc = subprocess.Popen(getImageCmd, shell=True)
		proc.wait()

	def checkRegistrationKey(self):
		# using sha-1. This has been deprecated as of python 2.5. When AMI supports a newer version of python,
		# we should use the hashlib instead: http://docs.python.org/library/hashlib.html#module-hashlib
		if (sha.new(self.regKey).digest() != self.regKeyHash):
			print "The registration key provided is incorrect. Exiting installation..."
			self.writeToLog("ERROR: registration key (%s) is incorrect ---" % (self.regKey,))
			return False

		print "Registration Key confirmed."
		self.writeToLog("Registration Key confirmed.")
		return True
		
		
	def run(self):

		self.currentDir = os.getcwd()
		self.logFilename = 'installation.log'
		self.svnMyamiDir = '/tmp/myami/'
		self.enableLogin = 'false'
		self.dbHost = 'localhost'
		self.dbUser = 'root'
		self.dbPass = ''
		self.serverRootPass = ''
		self.leginonDB = 'leginondb'
		self.projectDB = 'projectdb'
		self.adminEmail = ''
		self.csValue = ''
		self.mrc2any = '/usr/bin/mrc2any'
		self.imagesDir = '/myamiImages'

		self.setReleaseDependantValues()

		self.hostname = self.getServerName()
		self.nproc = self.getNumProcessors()
		# Don't think we need this anymore
		#self.numCPUs = self.determineNumberOfCPUs()
		self.machine = platform.machine()

		result = self.checkDistro()
		if result is False:
			sys.exit(1)
		
		result = self.checkRoot()
		if result is False:
			sys.exit(1)

		self.removeLogFile()
		self.setupFilePermission()
			
		result = self.checkSeLinux()
		if result is False:
			sys.exit(1)

		result = self.getDefaultValues()
		if result is False:
			sys.exit(1)
		

		self.yumUpdate()
		self.yumInstall(['subversion'])
		self.getMyami()
		
		result = self.setupJobServer()
		if result is False:
			sys.exit(1)
		
		result = self.setupProcessServer()
		if result is False:
			sys.exit(1)

		result = self.setupDBServer()
		if result is False:
			sys.exit(1)

		result = self.setupWebServer()
		if result is False:
			sys.exit(1)

		if (self.doInstallExternalPackages):
			self.installExternalPackages()
					
		self.downloadSampleImages()

		self.writeToLog("Installation Complete.")

		print("========================")
		print("Installation Complete.")
		print("Appion will launch in your web browser momentarily.")
		print("You may launch Leginon with the following command: start-leginon.py")
		print("========================")

				
		setupURL = "http://localhost/myamiweb/setup/autoInstallSetup.php?password=" + self.serverRootPass
		webbrowser.open_new(setupURL)
		self.writeToLog("Myamiweb Started.")
		
		subprocess.Popen("start-leginon.py")
		self.writeToLog("Leginon Started")
		
if __name__ == "__main__":
	a = CentosInstallation()
	a.run()
