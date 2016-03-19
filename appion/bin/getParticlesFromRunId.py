#!/usr/bin/env python

from appionlib import appiondata
import sinedon
import optparse
import sys

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--projectid', '-p', dest='projectid', type='int', help='project id')
	parser.add_option('--selectionrunid', dest='runid', type='int', help='run id')
	parser.add_option('--outlist', dest='outlist', type='str', help='output file with particle coordinates')
	options, args=parser.parse_args()

	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options

if __name__ == "__main__":
	options=parseOptions()
	sinedon.setConfig('appiondata',db=('ap%d' % options.projectid))
	q=appiondata.ApParticleData()
	rundata=appiondata.ApSelectionRunData.direct_query(options.runid)
	q['selectionrun']=rundata
	print "Querying for particles"
	ptcls=q.query()
	print len(ptcls),'returned'
	f=open(options.outlist,'w')
	f.write('particle#\tx_coord\ty_coord\timage_name\n')
	for ptcl in ptcls:
		n=ptcl.dbid
		x=ptcl['xcoord']
		y=ptcl['ycoord']
		name=ptcl['image']['filename']
		f.write('%d\t%d\t%d\t%s\n' % (n, x, y,name))
	f.close()
	print 'Done!'
	
