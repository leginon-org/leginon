#!/usr/bin/env python

import json

def returnCommand(settingsdict, command=None):
	commandroot=command.split()[0]
	cmdlst=[]
	if commandroot in list(settingsdict['GlobalJobParameters'].keys()):
		#setup defaults
		cmdlst.append(settingsdict['GlobalJobParameters']['defaultScheduler']['execCommand'])
		#override defaults for app specific options
		for key in settingsdict['GlobalJobParameters'][commandroot]['options']:
			settingsdict['GlobalJobParameters']['defaultScheduler']['options'][key] = settingsdict['GlobalJobParameters'][commandroot]['options'][key]
		
		#finish setting up scheduler command
		for key in settingsdict['GlobalJobParameters']['defaultScheduler']['options']:
			cmdlst.append(key)
			cmdlst.append(settingsdict['GlobalJobParameters']['defaultScheduler']['options'][key])
		
	#append command
	for option in command.split():
		cmdlst.append(option)
	return cmdlst


if __name__ == '__main__':
	f=open('Settings.json')
	settingsdict=json.load(f)
	f.close()

	command='gctf.py --blah blah --blah2 blah2 --blah3 blah3'
	newcommand=returnCommand(settingsdict, command=command)
	print(newcommand)
	print('\n\n')
	
	command='motioncor2.py --blah4 blah4 --blah5 blah5 --blah6 blah6'
	newcommand=returnCommand(settingsdict, command=command)
	print(newcommand)
	print('\n\n')

	command='makestack.py --blah7 blah7 --blah8 blah8 --blah9 blah9'
	newcommand=returnCommand(settingsdict, command=command)
	print(newcommand)