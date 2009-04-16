#!/usr/bin/env python
'''
Find a recon job that died before finishing up.  Perform the last lines of
the job file to move the contents of recon subdir up one level and run
updateAppionDB to change status to D.
Note:  does not use project selection yet.
'''

import sys
import appionData
import subprocess
import os

rjobs = appionData.ApClusterJobData(status='R', jobtype='recon')
rjobs = rjobs.query()

print 'Recon jobs listed as "Running" in the database:'
for i,job in enumerate(rjobs):
	print '   %d:  %s' % (i,job['name'])
print ''
response = raw_input('Choose a number from the list (or just hit enter to cancel): ')
try:
	i = int(response)
	myjob = rjobs[i]
except:
	sys.exit()

print 'Checking if job is actually running on cluster...'

cluster = myjob['cluster']
clusterjobid = myjob['clusterjobid']
# not sure if this is the typical format of job id, but works for me...
jobid = str(clusterjobid) + '.' + cluster
cmd = 'qstat'
s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
qs = s.stdout.read()
qserr = s.stderr.read()
if len(qs) == 0 or len(qserr) > 0:
	print 'qstat error, please run this on the cluster head node'
	sys.exit()
if jobid in qs:
	print 'qstat says job is still running, use qdel to kill it first.'
	sys.exit()

path = myjob['path']['path']
reconsubdir = os.path.join(path,'recon')
if os.path.exists(reconsubdir):
	print '* recon subdir is still present, moving contents to parent dir...'
	cmd = 'mv %s/* %s/.* %s' % (reconsubdir, reconsubdir, path)
	os.system(cmd)
	print '* removing recon subdir...'
	cmd = 'rmdir %s' % (reconsubdir,)
	os.system(cmd)

print '* changing status to "Done" in database'
cmd = 'updateAppionDB.py %s D' % (myjob.dbid,)
os.system(cmd)
print 'Recon should now be ready for upload.'
