#!/usr/bin/env python


import os
import re
import sys
import time
import json
import subprocess
from leginon import leginondata
### appion
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apScriptRemake

#=====================
#=====================
class appionRelauncher(basicScript.BasicScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --old-sessionname=<name> --new-sessionname=<name>  "
			+" [options]")
		self.parser.add_option("--old-session", dest="old-sessionname",
			help="old session name to get scripts to remake for the new", metavar="name")
		self.parser.add_option("--new-session", dest="new-sessionname",
			help="new session name to run the old scripts on", metavar="name")
		self.parser.add_option("--no-wait", dest="force-no-wait", default=False,
			action="store_true", help="Force the new session not to wait for more images after completing loop")
		self.parser.add_option("--wait", dest="force-wait", default=False,
			action="store_true", help="Force the new session not to wait for more images after completing loop")
		self.parser.add_option("--runname", dest="runname",
			help="new runname", metavar="name")
		self.parser.add_option("--testing", dest="testing", default=False,
			action="store_true", help="testing mode, only show commands")

	#=====================
	def checkConflicts(self):
		if self.params['force-wait'] and self.params['force-no-wait']:
			apDisplay.printError('You can not force it to both wait and no-wait.')
		old_session_name = self.params['old-sessionname']
		new_session_name = self.params['new-sessionname']
		try:
			self.old_session = leginondata.SessionData(name=old_session_name).query()[0]
		except Exception:
			apDisplay.printError('Session %s not found' % old_session_name)
		try:
			self.new_session = leginondata.SessionData(name=new_session_name).query()[0]
		except Exception:
			apDisplay.printError('Session %s not found' % new_session_name)

	#=====================
	def start(self):
		old = apScriptRemake.OldSessionScripts(self.params['old-sessionname'])
		scripts = old.scripts
		for s in scripts:
			s.setNewRun(self.new_session, self.params['runname'])
			def modifyParams(s):
				# in-place change
				if self.params['force-wait']:
					s.replaceParam('wait', True)
					s.removeParam('limit')
				elif self.params['force-no-wait']:
					s.replaceParam('wait', False)

			modifyParams(s)
			cmds = s.makeCommands()
			if self.params['testing']:
				self.showCommands(s, cmds)
			else:
				self.waitToStart(s)
				self.runCommands(s, cmds)
		if not self.params['testing']:
			self.waitToEnd(scripts)

	def waitToStart(self,script):
		t0 = time.time()
		while True:			
			if 'wait' in script.params and script.params['wait'] == True:
				#appionLoop only need one valid preset image
				if 'preset' in script.params:
					script_preset = script.params['preset']
					pq = leginondata.PresetData(session=self.new_session,name=script_preset)
					images = leginondata.AcquisitionImageData(preset=pq).query()
					if len(images) >=1:
						break
					apDisplay.printMsg('Waiting for some image with %s preset to be saved' % script_preset)
			else:
				if not script.dependencies:
					break
				#wait for dependency to finish.
				alldone = []
				for d in script.dependencies:
					done = False
					returncodes = map((lambda x: x.returncode),d.processes)
					if len(returncodes)>0:
						if not all(map((lambda x: x!= None),returncodes)):
							apDisplay.printMsg('Waiting for %s.py to finish' % d.prog_name)
							for p in d.processes:
								p.communicate()
						done = True
					alldone.append(done)
				if all(alldone):
					break
			time.sleep(10)
		t1 = time.time()
		apDisplay.printMsg('%s waited %.2f min before starting' % (script.prog_name,(t1-t0)/60.0))

	def waitToEnd(self,scripts):
		for s in scripts:
			for p in s.processes:
				if p.returncode == None:
					p.communicate()
			print '%s ended' % (s.prog_name)

	#=====================
	def showCommands(self,script,cmds):
		apDisplay.printMsg('***%s has %d processes***' % (script.prog_name, len(cmds)))
		for i, cmd in enumerate(cmds):
			apDisplay.printMsg('%s\n'%cmd)

	def runCommands(self,script,cmds):
		for i, cmd in enumerate(cmds):
			apParam.createDirectory(script.params['rundir'], warning=(not self.quiet))
			log_path = os.path.join(script.params['rundir'],'%s_%02d.log' % (script.prog_name, i))
			cmd += '>& %s' % (log_path)
			script.appendProcess(self.runCommand(cmd))
			time.sleep(2)

	def runCommand(self,cmd):
		apDisplay.printMsg("launching command:")
		apDisplay.printMsg('%s\n'%cmd)
		return subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

#=====================
if __name__ == "__main__":
	appionLauncher = appionRelauncher()
	appionLauncher.start()
	appionLauncher.close()

