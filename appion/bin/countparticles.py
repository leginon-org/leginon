#!/usr/bin/env python

import sys
import leginon.leginondata
import appionlib.appiondata

if __name__ == "__main__":
	session_name = sys.argv[1]
	squery= leginon.leginondata.SessionData(name=session_name)
	runquery = appionlib.appiondata.ApSelectionRunData(session=squery)
	partquery = appionlib.appiondata.ApParticleData(selectionrun=runquery)

	particles = partquery.query()

	counts = {}
	label_order = []
	run_order = []
	for particle in particles:
		run = particle['selectionrun']
		runname = run['name']
		if runname not in counts:
			counts[runname] = {}
			run_order.append(runname)

		label = particle['label']
		if label not in label_order:
			label_order.append(label)
		if label in counts[runname]:
			counts[runname][label] += 1
		else:
			counts[runname][label] = 1
	label_order.reverse()
	run_order.reverse()

	totals = {}
	for runname in run_order:
		print '%s:' % (runname)
		labelcounts = counts[runname]
		for label in label_order:
			if label in labelcounts:
				count = labelcounts[label]
				print '  %s:  %s' % (label, count)
				if label in totals:
					totals[label] += count
				else:
					totals[label] = count
	print 'Total:'
	for label,count in totals.items():
		print '  %s:  %s' % (label, count)
