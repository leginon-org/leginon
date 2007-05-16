#!/usr/bin/env python

import os, sys
import appionData
import apStack
import apDB

apdb=apDB.apdb

def scaleStack(stackdata,params):
	origpath=os.path.join(stackdata[0]['stackparams']['stackPath'],stackdata[0]['stackparams']['name'])
	newstackpath=os.path.join(params['newstackpath'],params['newstackname'])
	
	if os.path.exists(newstackpath):
		print "Error: A file with the name", params['newstackname']," already exists in this location."
		sys.exit()
		
	bin=params['bin']
	command=('proc2d %s %s shrink=%d' % (origpath,newstackpath,bin))
	os.system(command)
	return

def commitScaledStack(stackdata,params):
	newstackparamsq=appionData.ApStackParamsData()
	for key in newstackparamsq.keys():
		if key not in ['stackPath', 'name','description','bin']:
			newstackparamsq[key]=stackdata[0]['stackparams'][key]
	newstackparamsq['stackPath']=params['newstackpath']
	newstackparamsq['name']=params['newstackname']
	newstackparamsq['description']=params['description']
	newstackparamsq['bin']=params['bin']
	newstackparamsdata=apdb.query(newstackparamsq)

	if newstackparamsdata:
		print "A stack with these parameters already exists"
		return

		
	#loop in reverse order so that order of ptcls in db is like that of orig
	for particle in range(len(stackdata)-1,-1,-1):
		stackparticleq=appionData.ApStackParticlesData()
		for key in stackparticleq:
			if key != 'stackparams':
				stackparticleq[key] = stackdata[particle][key]
		stackparticleq['stackparams']=newstackparamsq
		#print stackparticleq
		apdb.insert(stackparticleq)
	return
	

if __name__=='__main__':
	#parse params
	params={}
	params['description']='temporary description'
	params['stackid']=sys.argv[1]
	params['newstackname']=sys.argv[2]
	params['bin']=int(sys.argv[3])
	params['newstackpath']=os.getcwd()
	
	#get stackdata
	stackdata=apStack.getStackFromId(params['stackid'])
	
	#do operations on stack
	print "Scaling stack"
	scaleStack(stackdata,params)
	
	#commit new stack to db
	print "Commiting new stack to db"
	commitScaledStack(stackdata,params)
	
	print "Done!"
