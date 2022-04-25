#!/usr/bin/env python

import os
import sys

from appionlib import appionScript
from appionlib import apStack

class focalPairSync(appionScript.AppionScript):

	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --sibstack1=1239 --sibstack2=1240")
		self.parser.add_option("--sibstack1", dest="sibstack1",
			help="Sibling stack 1 id", type='int')
		self.parser.add_option("--sibstack2", dest="sibstack2",
			help="Sibling stack 2 id", type='int')
	def checkConflicts(self):	
		pass	
	def setRunDir(self):
		self.params['rundir']=os.getcwd()
	def start(self):
		stack1data=apStack.getStackParticlesFromId(self.params['sibstack1'])
		stack2data=apStack.getStackParticlesFromId(self.params['sibstack2'])
		
		path1=os.path.join(stack1data[0]['stack']['path']['path'],stack1data[0]['stack']['name'])
		path2=os.path.join(stack2data[0]['stack']['path']['path'],stack2data[0]['stack']['name'])
		
		stack2dict={}
		stack2values=range(0,len(stack2data))
		###This is a little hacky, but is a solution so that stack2data is only looped through once		
		print "making ptcl dict\n"
		for ptcl in stack2values:
			stack2dict[stack2data[ptcl]['particle'].dbid]=ptcl
			
		
		syncstack1name=os.path.splitext(stack1data[0]['stack']['name'])[0]+'.sync1.hed'
		syncstack2name=os.path.splitext(stack2data[0]['stack']['name'])[0]+'.sync2.hed'
		for ptcl1 in stack1data:
			ptcl1_id = ptcl1['particle'].dbid
			if ptcl1_id in stack2dict.keys():
				ptcl2number=stack2dict[ptcl1_id]
				ptcl2=stack2data[ptcl2number]
				command1='proc2d %s %s first=%d last=%d' % (path1,syncstack1name,ptcl1['particleNumber']-1, ptcl1['particleNumber']-1)
				command2='proc2d %s %s first=%d last=%d' % (path2,syncstack2name,ptcl2['particleNumber']-1, ptcl2['particleNumber']-1)
				print command1
				print command2
				os.system(command1)
				os.system(command2)
				print '\n'

if __name__ == '__main__':
	fps=focalPairSync()
	fps.start()
	fps.close()
	
