#!/usr/bin/env python

import os
import re
import sys
import shutil
import subprocess

### TODO ###
# request list of processing nodes
# add more interview questions at the start
# setup edit config.php for myami

#=====================================================
#=====================================================
class CentosAutoInstall(object):
	#=====================================================
	def checkDistro(self):
		flavfile = "/etc/redhat-release"
		if not os.path.exists(flavfile):
			print "This is not CentOS, exiting..."
			sys.exit(1)
		f = open(flavfile, "r")
		flavor = f.readline().strip()
		f.close()
		if not flavor.startswith("CentOS"):
			print "This is not CentOS, exiting..."
			sys.exit(1)
		return flavor

	#=====================================================
	def checkRoot(self):
		uid = os.getuid()
		if uid != 0:
			print "you must run this program as root, exiting..."
			sys.exit(1)
		return

	#=====================================================
	def selectInstallType(self):
		self.web_server = False
		self.database_server = False
		self.process_server = False
		self.job_server = False
		print "Select which type of install to do:"
		print "(1) Web server"
		print "(2) Database server"
		print "(3) Processing host"
		print "(4) Job submission head node"
		print "(1234) All of the above, or any compination"
		print "(0) Exit"
		value = raw_input("Please select an option: ")
		svalue = value.strip()
		if not re.match("^[0-9]*$", svalue):
			print "unknown answer, exiting..."
			sys.exit(1)
		if '0' in value:
			print "exiting..."
			sys.exit(1)
		if '1' in value:
			print "1. installing web server"
			self.web_server = True
		if '2' in value:
			print "2. installing database server"
			self.database_server = True
		if '3' in value:
			print "3. installing processing server"
			self.process_server = True
		if '4' in value:
			print "4. installing job submission server"
			self.job_server = True

	#=====================================================
	def runCommand(self, cmd):
		print "#==========================================="
		print cmd
		print "#==========================================="
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()

	#=====================================================
	def removeOldPackages(self):
		arch = self.getMachineArch()
		if arch != "x86_64":
			return
		self.runCommand("yum -y remove `rpm -qa --qf '%{NAME}.%{ARCH}\n' | grep i.86`")
		shutil.move('/etc/yum.conf', '/etc/yum.conf-backup')
		self.runCommand("echo 'exclude=*i686 *i386' >> /etc/yum.conf")

	#=====================================================
	def yumUpdate(self):
		print "Updating system files this can take awhile"
		### install EPEL
		self.runCommand("rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/`uname -i`/epel-release-5-3.noarch.rpm")
		### update yum program
		self.runCommand("yum -y update yum*")
		### install yum tools
		self.yumInstall(['yum-fastestmirror.noarch', 'yum-utils.noarch'], clean=False)
		### update all programs
		self.runCommand("yum -y update")
		### clean up
		self.runCommand("yum clean all")
		### index drive
		self.runCommand("updatedb") 
		return

	#=====================================================
	def getMachineArch(self):
		try:
			arch = os.uname()[4]
		except:
			return None
		if arch == "i686":
			return "i386"
		return arch

	#=====================================================
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

	#=====================================================
	def getHostname(self):
		host = os.uname()[1]
		return host

	#=====================================================
	def yumInstall(self, packagelist, clean=True):
		print "Installing system files this can take awhile"
		arch = self.getMachineArch()
		if not packagelist:
			return
		packagestr = ""
		for package in packagelist:
			packagestr += " "+package
			if arch is not None and not package.endswith("noarch"):
				packagestr += "."+arch
		cmd = "yum -y install"+packagestr
		self.runCommand(cmd)
		if clean is True:
			self.runCommand("yum clean all")
		self.runCommand("updatedb")
		return

	#=====================================================
	#=========             WEB SERVER              =======
	#=====================================================
	def setupWebServer(self):
		self.webServerYumInstall()
		# enable web server
		self.runCommand("/sbin/chkconfig httpd on")
		self.editPhpIni()
		self.editHttpdConf()
		myamidir = self.getMyami()
		self.installPhpMrc(myamidir)
		self.installMyamiWeb(myamidir)
		#self.editMyamiWebConfig()
		return

	#=====================================================
	def webServerYumInstall(self):
		packagelist = ['fftw3-devel', 'httpd', 'libssh2-devel', 'php', 'php-mysql', 'phpMyAdmin.noarch', 'php-devel', 'php-gd', 'subversion', ]
		self.yumInstall(packagelist)

	#=====================================================
	def editPhpIni(self):
		shutil.move('/etc/php.ini', '/etc/php.ini-backup')
		inf = open('/etc/php.ini-backup', 'r')
		outf = open('/etc/php.ini', 'w')
		for line in inf:
			rline = line.rstrip()
			if rline.startswith(';'):
				outf.write(rline+"\n")
			elif rline.startswith('error_reporting'):
				outf.write("error_reporting = E_ALL & ~E_NOTICE\n")
			elif rline.startswith('display_errors'):
				outf.write("display_errors = On\n")
			elif rline.startswith('register_argc_argv'):
				outf.write("register_argc_argv = On\n")
			elif rline.startswith('short_open_tag'):
				outf.write("short_open_tag = On\n")
			elif rline.startswith('max_execution_time'):
				pass
			elif rline.startswith('max_input_time'):
				pass
			elif rline.startswith('memory_limit'):
				pass
			else:
				outf.write(rline+"\n")
		inf.close()
		outf.write('; custom parameters from CentOS Auto Install script\n')
		outf.write('max_execution_time = 300 ; Maximum execution time of each script, in seconds\n')
		outf.write('max_input_time = 300     ; Maximum amount of time to spend parsing request data\n')	
		outf.write('memory_limit = 1024M     ; Maximum amount of memory a script may consume\n')
		outf.write('\n')
		outf.close()

	#=====================================================
	def editHttpdConf(self):
		shutil.move('/etc/httpd/conf/httpd.conf', '/etc/httpd/conf/httpd.conf-backup')
		inf = open('/etc/httpd/conf/httpd.conf-backup', 'r')
		outf = open('/etc/httpd/conf/httpd.conf', 'w')
		for line in inf:
			rline = line.rstrip()
			if rline.startswith('#'):
				outf.write(rline+"\n")
			elif rline.startswith('DirectoryIndex'):
				outf.write("DirectoryIndex index.html index.php\n")
			elif rline.startswith('HostnameLookups'):
				outf.write("HostnameLookups On\n")
			elif rline.startswith('UseCanonicalName'):
				outf.write("UseCanonicalName On\n")
			else:
				outf.write(rline+"\n")
		inf.close()
		outf.close()

	#=====================================================
	def getMyami(self):
		cmd = "wget xxx"
		cmd = "tar -zxvf xxx" 
		cmd = "svn co http://ami.scripps.edu/svn/myami/branches/myami-2.0/ /tmp/myami-2.0/"
		self.runCommand(cmd)
		return "/tmp/myami-2.0/"

	#=====================================================
	def installPhpMrc(self, myamidir):
		phpmrcdir = os.path.join(myamidir, "php_mrc")
		os.chdir(phpmrcdir)
		self.runCommand("phpize")
		self.runCommand("./configure")
		self.runCommand("make")
		self.runCommand("make install")
		f = open('/etc/php.d/mrc.ini', 'w')
		f.write('; Enable mrc extension module')
		f.write('extension=mrc.so')
		f.close()

	#=====================================================
	def installMyamiWeb(self, myamidir):
		svnmyamiwebdir = os.path.join(myamidir, "myamiweb")
		myamiwebdir = "/var/www/html/myamiweb"
		shutil.copytree(svnmyamiwebdir, myamiwebdir)
		return

	#=====================================================
	#=========         DATABASE SERVER             =======
	#=====================================================
	def setupDatabaseServer(self):
		self.databaseServerYumInstall()
		# enable db server
		self.runCommand("/sbin/chkconfig mysqld on")
		return

	#=====================================================
	def databaseServerYumInstall(self):
		packagelist = ['mysql-server',]
		self.yumInstall(packagelist)


	#=====================================================
	#=========        PROCESSING SERVER            =======
	#=====================================================
	def setupProcessServer(self):
		self.processServerYumInstall()
		self.enableTorqueComputeNode()
		return

	#=====================================================
	def enableTorqueComputeNode(self):
		if self.job_server is False:
			value = raw_input("Enter the hostname of your torque headnode (hit enter for None): ")
			svalue = value.strip()
			if not svalue:
				return
		# enable pbs mom client
		packagelist = ['torque-mom', 'torque-client']
		self.yumInstall(packagelist)
		self.runCommand("/sbin/chkconfig pbs_mom on")
		f = open('/var/torque/mom_priv/config', 'w')
		if self.job_server is True:
			f.write("$pbsserver localhost # running pbs_server on this host")
		else:
			f.write("$pbsserver %s # pbs_server hostname"%(svalue))
		f.close()

	#=====================================================
	def processServerYumInstall(self):
		packagelist = ['ImageMagick', 'MySQL-python', 'compat-gcc-34-g77', 'fftw3-devel', 'gcc-c++', 'gcc-gfortran', 'gcc-objc', 'gnuplot', 'grace', 'gsl-devel', 'libtiff-devel', 'netpbm-progs', 'numpy', 'openmpi-devel', 'python-devel', 'python-imaging', 'python-matplotlib', 'python-tools', 'scipy', 'subversion', 'wxPython', 'xorg-x11-server-Xvfb']
		self.yumInstall(packagelist)

	#=====================================================
	#=========         HEADNODE SERVER             =======
	#=====================================================
	def setupJobServer(self):
		## install and setup
		self.jobServerYumInstall()
		self.runCommand("/sbin/chkconfig pbs_server on")
		self.runCommand("/sbin/chkconfig pbs_sched on")
		self.runCommand("/usr/share/doc/torque-2.3.10/torque.setup root")

		## write nodes to file
		f = open('/var/torque/server_priv/nodes', 'w')
		if self.process_server is True:
			nproc = self.getNumProcessors()
			if nproc is not None:
				f.write("localhost np=%d"%(nproc))
		f.close()

		## start the service
		self.runCommand("/sbin/service pbs_server restart")
		self.runCommand("/sbin/service pbs_sched start")
		return

	#=====================================================
	def processServerYumInstall(self):
		packagelist = ['torque-server', 'torque-scheduler',]
		self.yumInstall(packagelist)

	#=====================================================
	#=========          MAIN SECTION               =======
	#=====================================================

	#=====================================================
	def run(self):
		self.checkDistro()
		self.checkRoot()
		self.selectInstallType()
		self.removeOldPackages()
		self.yumUpdate()
		if self.web_server is True:
			self.setupWebServer()
		if self.database_server is True:
			self.setupDatabaseServer()
		if self.process_server is True:
			self.setupProcessServer()
		if self.job_server is True:
			self.setupJobServer()

#=====================================================
#=====================================================
if __name__ == "__main__":
	a = CentosAutoInstall()
	a.run()
	
