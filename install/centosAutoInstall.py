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
		print flavor
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
		print "(1234) All of the above, or any combination"
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
		self.db_host = "cronus4.scripps.edu"
		self.db_user = "ami_object"
		self.db_pass = "notsosuper"
		self.db_leginon = "dbemdata"
		self.db_project = "project"
		self.cs = 2.0

	#=====================================================
	def extendedInterview(self):
		if not self.database_server:
			value = raw_input("What is the hostname of your database server: ")
			value = raw_input("What is the login to your database server: ")
			value = raw_input("What is the password to your database server: ")
			value = raw_input("What is the name to your project database: ")
			value = raw_input("What is the name to your leginon database: ")
			value = raw_input("What is the prefix to your appion databases: ")
		if not self.process_server:
			value = raw_input("How many processing servers do you have?: ")
			value = raw_input("What is the hostname of your process server 1: ")
			value = raw_input("What is the hostname of your process server 2: ")
		if not self.job_server:
			value = raw_input("What is the hostname of your job server head node: ")

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
		cmd = "rpm -qa --qf '%{NAME}.%{ARCH}\\n' | grep i.86 | wc -l"
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		line = proc.stdout.readline()
		if re.match("^[0-9]", line.strip()):
			self.runCommand("yum -y remove `rpm -qa --qf '%{NAME}.%{ARCH}\\n' | grep i.86`")
		shutil.copy('/etc/yum.conf', '/etc/yum.conf-backup')
		self.runCommand("echo 'exclude=*i686 *i386' >> /etc/yum.conf")

	#=====================================================
	def yumUpdate(self):
		print "Updating system files this can take awhile"
		### install EPEL
		self.runCommand("rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/`uname -i`/epel-release-5-3.noarch.rpm")
		### update yum program
		self.runCommand("yum -y update yum*")
		### install yum tools
		self.yumInstall(['yum-fastestmirror.noarch', 'yum-utils.noarch'])
		### remove old 32bit packages, if 32bit
		self.removeOldPackages()
		### update all programs
		self.runCommand("yum -y update")
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
	def yumInstall(self, packagelist):
		print "Installing system files this can take awhile"
		arch = self.getMachineArch()
		if not packagelist:
			return
		packagestr = ""
		for package in packagelist:
			packagestr += " "+package
			#if arch is not None and not package.endswith("noarch"):
			#	packagestr += "."+arch
		cmd = "yum -y install"+packagestr
		self.runCommand(cmd)
		self.runCommand("updatedb")
		return

	#=====================================================
	def openFirewallPort(self, port):
		### this command is only temporary
		self.runCommand("/sbin/iptables --insert RH-Firewall-1-INPUT --proto tcp --dport %d --jump ACCEPT"%(port))
		#portstr = "-A RH-Firewall-1-INPUT -p tcp -m tcp --dport %d -j ACCEPT"%(port)
		#cmd = "echo '%s' >> /etc/sysconfig/iptables"%(portstr)
		#self.runCommand(cmd)
		self.runCommand("/sbin/iptables-save > /etc/sysconfig/iptables")


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
		self.installPhpSsh2()
		self.installMyamiWeb(myamidir)
		self.editMyamiWebConfig()
		self.runCommand("/sbin/service httpd restart")
		# open port 80 in firewall for web traffic
		self.openFirewallPort(80)
		return

	#=====================================================
	def webServerYumInstall(self):
		packagelist = ['fftw3-devel', 'gcc', 'httpd', 'libssh2-devel', 'php', 
			'php-mysql', 'phpMyAdmin.noarch', 'php-devel', 'php-gd', 'subversion', ]
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
		if os.path.isfile('/etc/php.d/mrc.ini'):
			return
		cwd = os.getcwd()
		phpmrcdir = os.path.join(myamidir, "php_mrc")
		os.chdir(phpmrcdir)
		self.runCommand("phpize")
		self.runCommand("./configure")
		self.runCommand("make")
		module = os.path.join(phpmrcdir, "modules/mrc.so")
		if not os.path.isfile(module):
			print "ERROR mrc.so failed"
			sys.exit(1)
		self.runCommand("make install")
		f = open('/etc/php.d/mrc.ini', 'w')
		f.write('; Enable mrc extension module\n')
		f.write('extension=mrc.so\n')
		f.close()
		os.chdir(cwd)

	#=====================================================
	def installPhpSsh2(self):
		if os.path.isfile('/etc/php.d/ssh2.ini'):
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
			print "ERROR ssh2.so failed"
			sys.exit(1)
		self.runCommand("make install")
		f = open('/etc/php.d/ssh2.ini', 'w')
		f.write('; Enable ssh2 extension module\n')
		f.write('extension=ssh2.so\n')
		f.close()
		os.chdir(cwd)

	#=====================================================
	def installMyamiWeb(self, myamidir):
		svnmyamiwebdir = os.path.join(myamidir, "myamiweb")
		myamiwebdir = "/var/www/html/myamiweb"
		self.runCommand("rsync -rtou %s/ %s/"%(svnmyamiwebdir, myamiwebdir))
		return

	#=====================================================
	def editMyamiWebConfig(self):
		"""
		this is not very good
		"""
		configfile = os.path.join("/var/www/html/myamiweb/config.php")
		inf = open(configfile+".template", "r")
		outf = open(configfile, "w")
		for line in inf:
			rline = line.rstrip()
			if rline.startswith("// --- ") or len(rline) == 0:
				outf.write(rline+"\n")
			elif rline.startswith("define('ENABLE_LOGIN'"):
				outf.write("define('ENABLE_LOGIN', false);\n")
			elif rline.startswith("define('DB_HOST'"):
				outf.write("define('DB_HOST', '%s');\n"%(self.db_host))
			elif rline.startswith("define('DB_USER'"):
				outf.write("define('DB_USER', '%s');\n"%(self.db_user))
			elif rline.startswith("define('DB_PASS'"):
				outf.write("define('DB_PASS', '%s');\n"%(self.db_pass))
			elif rline.startswith("define('DB_LEGINON'"):
				outf.write("define('DB_LEGINON', '%s');\n"%(self.db_leginon))
			elif rline.startswith("define('DB_PROJECT'"):
				outf.write("define('DB_PROJECT', '%s');\n"%(self.db_project))
			elif "addplugin(\"processing\");" in rline:
				outf.write("addplugin(\"processing\");\n")
			elif "// $PROCESSING_HOSTS[]" in rline:
				nproc = self.getNumProcessors() 
				outf.write("$PROCESSING_HOSTS[] = array('host' => 'localhost', 'nproc' => %d);\n"%(nproc))
			elif rline.startswith("define('DEFAULTCS', "):
				outf.write("define('DEFAULTCS', '%.1f');\n"%(self.cs))
			else:
				outf.write(rline+"\n")
		inf.close()
		outf.close()

	#=====================================================
	#=========         DATABASE SERVER             =======
	#=====================================================
	def setupDatabaseServer(self):
		self.databaseServerYumInstall()
		# enable db server
		self.runCommand("/sbin/chkconfig mysqld on")

		### start mysqld
		self.runCommand("/sbin/service mysqld restart")

		self.createSQLDatabase("leginondb")
		self.createSQLDatabase("projectdb")

		### open mysql port
		self.openFirewallPort(3306)

		return

	#=====================================================
	def databaseServerYumInstall(self):
		packagelist = ['mysql-server',]
		self.yumInstall(packagelist)

	#=====================================================
	def editMyCnf(self):
		shutil.copy('/usr/share/mysql/my-huge.cnf', '/etc/my.cnf-backup')
		inf = open('/etc/my.cnf-backup', 'r')
		outf = open('/etc/my.cnf', 'w')
		for line in inf:
			rline = line.rstrip()
			if rline.startswith('#'):
				outf.write(rline+"\n")
			elif rline.startswith('query_cache_type'):
				pass
			elif rline.startswith('query_cache_size'):
				pass
			elif rline.startswith('query_cache_limit'):
				pass
			elif rline.startswith('default-storage-engine'):
				pass
			else:
				outf.write(rline+"\n")
		inf.close()
		outf.write('# custom parameters from CentOS Auto Install script\n')
		outf.write("query_cache_type = 1\n")
		outf.write("query_cache_size = 100M\n")
		outf.write("query_cache_limit = 100M\n")
		outf.write("default-storage-engine = MyISAM\n")
		outf.write('\n')
		outf.close()

	#=====================================================
	def createSQLDatabase(self, dbname):
		cmd = "mysqladmin create %s"%(dbname)
 		self.runCommand(cmd)

	#=====================================================
	def addSQLUser(self, username, password, database):
		"""
		CREATE USER usr_object@'localhost' IDENTIFIED BY 'YOUR PASSWORD';
		GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON leginondb.* TO usr_object@'localhost';
		GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON projectdb.* TO usr_object@'localhost';
		"""
		sys.exit(1)
		cmd = ("echo '%s' | mysql -u %s --password=%s -h %s"
			%(sqlcmd, username, password, database))
 		self.runCommand(cmd)


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
	
