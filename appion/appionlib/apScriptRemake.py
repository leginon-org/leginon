#!/usr/bin/env python
from leginon import leginondata, projectdata
from appionlib import apParam, apProject, appiondata, apScriptLog, apDisplay
from pyami import mysocket

class ScriptRemaker(object):
	"""
	AppionScript command remake for another session. This object holds info
	created from one run.  The parameters and run configuration can then
	modified minimally for another user and session and processing host.
	"""
	valid_dependencies = []
	jobtypes = []
	ignored_params = []
	def __init__(self, prog_name, username, params, usages):
		self.prog_name = prog_name
		self.run_username = username
		self.params = params
		self.removeIgnoredParams()
		self.usage_keys = usages
		self.auto_params = self.getAutoHostParams()
		self.dependencies = [] # ScriptRemaker instance that this one needs to wait for.
		self.processes = [] #subprocess Popen

	def removeIgnoredParams(self):
		"""
		remove params that are not generated from command line so they won't
		create error.
		"""
		for k in self.ignored_params:
			self.removeParam(k)

	def removeParam(self, k):
		"""
		remove a single processing parameter
		"""
		# this avoids exception raise when k is not a key in self.params
		self.params.pop(k, None)

	def addParam(self, k, value, usage_key):
		"""
		add or modify a single processing parameter
		"""
		self.params[k]=value
		self.usage_keys[k]=usage_key

	def getAutoHostParams(self):
		"""
		Return configuration of the current host for autorun the script.
		"""
		hostname = mysocket.gethostname() # use mysocket hostname if possible
		results = projectdata.autohosts(hostname=hostname).query()
		if not results:
			default=projectdata.autohosts(hostname=hostname,
					loop_max=2,  #maximal parallel runs for appionLoop
					ddalign_gpus=[], #available gpuids for dd frame alignment
			)
			return default
		else:
			return results[0]

	def appendRemaker(self, dep_obj):
		"""
		Append ScriptRemaker instance that this one needs to wait to provide input.
		"""
		if dep_obj.__class__.__name__.split('Remaker')[0] in self.valid_dependencies:
			self.dependencies.append(dep_obj)

	def appendProcess(self, proc):
		self.processes.append(proc)

	def makeCommands(self):
		return [self._makeCommand()]

	def _makeCommand(self):
		cmd = '%s.py %s' % (self.prog_name,' '.join(map((lambda x: apParam.ts(x,self.params[x],self.usage_keys[x])),self.params)))
		if self.auto_params['appion_wrapper']:
			cmd = '%s %s' % (self.auto_params['appion_wrapper'],cmd)
		return cmd

	def _replaceParam(self, key, value):
		# do nothing if value is None
		if value == None:
			return
		if key in self.params.keys():
			self.params[key] = value


	def replaceParam(self, key, value):
		apDisplay.printDebug('set param %s to %s' % (key, value))
		self._replaceParam(key, value)

	def _setNewSession(self, session):
		self._replaceParam('expid',session.dbid)
		self._replaceParam('sessionname',session['name'])
		self._setNewProject(session)
		self.new_session = session

	def _setNewProject(self, session):
		r = projectdata.projectexperiments(session=session).query(results=1)
		if r:
			self._replaceParam('projectid',r[0]['project'].dbid)

	def _setRunDir(self, sessionname):
		if 'rundir' in self.params.keys():
			rundir = self.params['rundir']
			if 'sessionname' in self.params.keys():
				rundir = rundir.replace(self.params['sessionname'],sessionname)
			# replace user part if present in rundir
			username = apParam.getUsername()
			if username != 'unknown':
				rundir = rundir.replace(self.run_username,username)
			else:
				if len(rundir.split(self.run_username)) > 1:
					apDisplay.printError('can not determine new username to replace in rundir')
			self.run_username = username
			self.params['rundir'] = rundir

	def _setRunName(self, runname):
		if 'runname':
			if 'runname' in self.params.keys() and runname != None:
				if 'rundir' in self.params.keys():
					rundir = self.params['rundir']
					rundir = rundir.replace(self.params['runname'],runname)
					self.params['rundir'] = rundir
				self._replaceParam('runname',runname)

	def setNewRun(self, session, runname=None):
		sessionname = session['name']
		self._setRunDir(sessionname)
		self._setRunName(runname)
		# do these after rundir is set
		self._setNewSession(session)

class LoopScriptRemaker(ScriptRemaker):
	"""
	AppionLoop script command remake for another session.
	"""
	valid_dependencies = ['Denoiser']
	jobtypes = ['looptest',]
	ignored_params = []
	def __init__(self, prog_name, username, params, usages):
		super(LoopScriptRemaker, self).__init__(prog_name, username, params, usages)
		# initialize wait as True
		if 'wait' not in self.params:
			self.params['wait'] = True
		#	# this is a special case so it can handle False case. See apParam.py
			self.usage_keys['wait'] = 'no-wait'
		self.loop_preset = self.setPreset()
		self.output_preset = self.setOutputPreset()

	def makeCommands(self):
		if 'parallel' in self.params.keys() and self.params['parallel'] is True:
			# duplicate command by loop_max times
			repeat = self.auto_params['loop_max']
		else:
			repeat = 1
		return [self._makeCommand()] * repeat

	def setPreset(self):
		if 'preset' in self.params.keys():
			return self.params['preset']
		return 'manual'

	def setOutputPreset(self):
		return None

class DDAlignerRemaker(LoopScriptRemaker):
	"""
	DD frame alignment command remake for another session.
	"""
	valid_dependencies = []
	jobtypes = ['makeddrawframestack','loopddtest']
	# Need to include both because both Bft and bft was used in the past
	# and mysql query is not case-sensitive so it would having either
	# Bft or bft as haskey.
	ignored_params = ['bft','Bft']

	def makeCommands(self):
		cmds = []
		if 'parallel' in self.params.keys() and self.params['parallel'] is True:
			if 'gpuid' in self.params:
				# specified gpu process
				gpuids = self.auto_params['ddalign_gpus']
				for g in gpuids:
					self._replaceParam('gpuid',g)
					self._replaceParam('gpuids',g)
					cmds.append(self._makeCommand())
				return cmds
		# cpu process
		return super(DDAlignerRemaker, self).makeCommands()

	def setOutputPreset(self):
		if 'alignlabel' in self.params.keys():
			return '%s-%s' % (self.loop_preset,self.params['alignlabel'])

class DenoiserRemaker(LoopScriptRemaker):
	"""
	topaz denoiser command remake for another session.
	"""
	valid_dependencies = []
	jobtypes = ['topazdenoise','bintest']

class AceRemaker(LoopScriptRemaker):
	"""
	auto ctf estimation command remake for another session.
	"""
	jobtypes = ['ctfestimate',]
	valid_dependencies = ['DDAligner','Denoiser']

class LearnRemaker(LoopScriptRemaker):
	"""
	auto learn command remake for another session.
	"""
	jobtypes = ['learn',]
	valid_dependencies = ['Ace',]

class PickerRemaker(LoopScriptRemaker):
	"""
	particle selector estimation command remake for another session.
	"""
	jobtypes = ['dogpicker',]
	valid_dependencies = ['DDAligner','Denoiser']

class StackRemaker(LoopScriptRemaker):
	"""
	particle stack maker command remake for another session.
	"""
	jobtypes = ['makestack',]
	valid_dependencies = ['Picker','Ace']

class OldSessionScripts(object):
	order = ['DDAligner','Denoiser','LoopScript','Ace','Learn','Picker','Stack']
	def __init__(self, session_name):
		try:
			self.session = leginondata.SessionData(name=session_name).query()[0]
		except:
			apDisplay.printError('Old Session (%s) to base the appion script on not found' % session_name)
		self.new_session = None
		apProject.setAppiondbBySessionName(session_name)
		self.dep_map = self.getRemakerMap() 
		self.scripts = [None]*len(self.order)
		self.run()

	def getRemakerMap(self):
		job_map = {}
		for i,o in enumerate(self.order):
			app = globals()[o+'Remaker']('','unknown',{},{})
			for j in app.jobtypes:
				job_map[j] = (i,o)
		return job_map

	def run(self):
		# find program runs from self.session
		expid_param = appiondata.ScriptParamName(name='expid')
		expid_run_values= appiondata.ScriptParamValue(paramname=expid_param, value='%d' % self.session.dbid).query()
		runs = map((lambda x: x['progrun']),expid_run_values)
		prog_params = {}
		for run in runs:
			params = apScriptLog.getScriptParamValuesFromRun(run)
			usages = apScriptLog.getScriptUsageKeysFromRun(run)
			if 'jobtype' not in params.keys():
				apDisplay.printWarning('no jobtype. Ignore')
				continue
			if params['jobtype'] not in self.dep_map:
				apDisplay.printWarning('jobtype %s not known' % params['jobtype'])
				continue
			if params['jobtype'] not in prog_params.keys():
				# only use the latest of a jobtype
				prog_params[params['jobtype']] = {'run': run, 'params': params}
				dep_class_name = self.dep_map[params['jobtype']][1]+'Remaker'
				order_index = self.dep_map[params['jobtype']][0]
				prog_name = run['progname']['name']
				run_user = run['username']['name']
				self.scripts[order_index]=globals()[dep_class_name](prog_name, run_user, params, usages)
		# cleanup None
		for i in range(len(self.scripts)-1,-1,-1):
			if self.scripts[i] == None:
				self.scripts.pop(i)
		# add dependencies
		for p1 in self.scripts:
			for p2 in self.scripts:
				# add dependency script if valid
				p1.appendRemaker(p2)

if __name__=='__main__':
	old_session_name=raw_input('Use appion run from this session to make command = ')
	new_session_name=raw_input('new session to apply appion runs to = ')
	#new_session = leginondata.SessionData().query(results=1)[0]
	#new_session_name = new_session['name']
	try:
		old_session = leginondata.SessionData(name=old_session_name).query()[0]
	except Exception:
		apDisplay.printError('Session %s not found' % old_session_name)
	try:
		new_session = leginondata.SessionData(name=new_session_name).query()[0]
	except Exception:
		apDisplay.printError('Session %s not found' % new_session_name)

	old = OldSessionScripts(old_session_name)
	scripts = old.scripts
	for s in scripts:
		print 'old', s.prog_name
		s.setNewRun(new_session, None)
		# dependencies also got changed since they point to those in earlier execution.
		#for d in s.dependencies:
		#	print d.prog_name, d.params['rundir']
		print s.makeCommands()

