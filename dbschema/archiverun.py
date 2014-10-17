#!/usr/bin/env python
import os
import sys
import subprocess
import shutil
import time
from os.path import expanduser

class ArchiveRun(object):
	def __init__(self):
		# use autoSet now, not user raw input
		#self.setDatabases()
		#self.setDbCopySinedonPath()
		self.autoSet()
		self.normal_dbschema_path = os.path.join(os.path.split(self.normal_sinedon_path)[0],'dbschema')

	def autoSet(self):
		# configuration
		self.old_projectdb = 'projectdb'
		self.old_leginondb = 'leginondb'
		self.new_projectdb = 'archiveprojectdb'
		self.new_leginondb = 'archiveleginondb'
		self.normal_sinedon_path = '/your-myami-trunk/sinedon'
		self.dbcopy_sinedon_path = '/your-myami-dbcopy/sinedon'
		self.projectids = [1,]

	def setDatabases(self):
		self.old_projectdb = raw_input('Enter project database name with data to be used to make the archive:')
		self.old_leginondb = raw_input('Enter leginon database name with data to be used to make the archive:')
		self.new_projectdb = raw_input('Enter project database name where the archive will go to:')
		self.new_leginondb = raw_input('Enter leginon database name where the archive will go to:')

	def setDbCopySinedonPath(self):
		while True:
			self.dbcopy_sinedon_path = raw_input('Enter myami-dbcopy sinedon path')
			if os.path.isdir(self.dbcopy_sinedon_path) and 'sinedon' in self.dbcopy_sinedon_path[-9:]:
				break
			print 'Not an existing directory, try again'

	def runSubProcess(self,cmd):
		print cmd	
		proc = subprocess.Popen(cmd, shell=True, stdout=None)
		stdout_value = proc.communicate()[0]
		while proc.returncode is None:
			time.wait(60)
			stdout_value = proc.communicate()[0]
			print stdout_value
		if proc.returncode != 0:
			print "EXIT WITH ERROR"
			sys.exit(1)

	def runScript(self, pythonfile):
		sinedon_base_path = os.path.split(os.path.abspath(self.dbcopy_sinedon_path))[0]
		cmd = 'export PYTHONPATH=%s:$PYTHONPATH; python %s' % (sinedon_base_path,pythonfile)
		self.runSubProcess(cmd)

	def backupSinedonCfg(self):
		# get the original database host, user info
		import sinedon
		self.globalconfigs = sinedon.getConfig('leginondata')
		print self.globalconfigs
		# make backup
		homepath = expanduser("~")
		self.sinedon_cfg_file = os.path.join(homepath,'sinedon.cfg')
		if os.path.isfile(self.sinedon_cfg_file):
			# make backup
			self.sinedon_cfg_backup = self.sinedon_cfg_file
			while os.path.isfile(self.sinedon_cfg_backup):
				self.sinedon_cfg_backup +='k'
			shutil.move(self.sinedon_cfg_file,self.sinedon_cfg_backup)
		else:
			self.sinedon_cfg_backup = None

	def writeSinedonCfg(self,leginondb,projectdb,importdb=''):
		lines = (
				'[global]',
				'host:%s' % (self.globalconfigs['host']),
				'user:%s' % (self.globalconfigs['user']),
				'passwd:%s' % (self.globalconfigs['passwd']),
				'[leginondata]',
				'db: %s' % leginondb,
				'[projectdata]',
				'db: %s' % projectdb,
				'[importdata]',
				'db: %s' % importdb,
		)

		f = open(self.sinedon_cfg_file,'w')
		f.write('\n'.join(lines))
		f.close()

	def restoreSinedonCfg(self):
		if self.sinedon_cfg_backup:
			shutil.move(self.sinedon_cfg_backup,self.sinedon_cfg_file)
		else:
			os.remove(self.sinedon_cfg_file)

	def archiveLeginonDB(self, projectid):
			self.writeSinedonCfg(self.old_leginondb,self.old_projectdb,self.new_leginondb)
			script_path = os.path.join(self.normal_dbschema_path,'archive_leginondb.py')
			self.runScript('%s %d' % (script_path, projectid,))

	def archiveProjectDB(self, projectid):
			self.writeSinedonCfg(self.new_leginondb,self.old_projectdb,self.new_projectdb)
			script_path = os.path.join(self.normal_dbschema_path,'archive_projectdb.py')
			self.runScript('%s %d' % (script_path, projectid,))

	def activateArchive(self):
			self.writeSinedonCfg(self.new_leginondb,self.new_projectdb)
			script_path = os.path.join(self.normal_dbschema_path,'archive_activate.py')
			self.runScript('%s' % (script_path,))

	def run(self):
		self.backupSinedonCfg()
		for projectid in self.projectids:
			self.archiveLeginonDB(projectid)
			self.archiveProjectDB(projectid)
		self.activateArchive()
		self.restoreSinedonCfg()

if __name__ == "__main__":
	app = ArchiveRun()
	app.run()