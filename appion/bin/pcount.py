#!/usr/bin/env python
'''
This will count the number of particles and tell you how many are from
reject images versus other images.
usage:    pcount.py <session name> <particle selection run name>
'''

import appiondata
import leginondata
import sys

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "usage: ./pcount.py <session name> <particle selection run name>\n\n"
		sys.exit(1)

	ses_name = sys.argv[1]
	run_name = sys.argv[2]

	# query objects
	qsession = leginondata.SessionData(name=ses_name)
	qrun = appiondata.ApSelectionRunData(session=qsession, name=run_name)
	qpart = appiondata.ApParticleData(selectionrun=qrun)

	# all particles
	particles = qpart.query()

	# Find assessment of image that each particle is from.
	# This is messy because we want to query images without reading MRCs.
	assessments = {}
	akeep = []
	areject = []
	anone = []
	for particle in particles:
		imgref = particle.special_getitem('image', dereference=False)
		imgid = imgref.dbid
		if imgid not in assessments:
			img = leginondata.AcquisitionImageData.direct_query(imgref.dbid, readimages=False)
			qassess = appiondata.ApAssessmentData(image=img)
			assessment = qassess.query(results=1)
			if assessment:
				assessments[imgid] = assessment[0]['selectionkeep']
			else:
				assessments[imgid] = None
		assessment = assessments[imgid]
		if assessment is None:
			anone.append(particle)
		elif assessment:
			akeep.append(particle)
		else:
			areject.append(particle)

	print ' Total Particles:', len(particles)
	print '         Rejected', len(areject)
	print '  Keep or Unknown', len(akeep) + len(anone)

