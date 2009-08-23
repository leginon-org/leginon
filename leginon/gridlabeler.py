def getGridLabel(griddata):
	if griddata is None:
		return ''
	parts = []
	gridname = ''
	if 'emgrid' in griddata and griddata['emgrid'] is not None and griddata['emgrid']['name']:
		# new, shorter style with grid name
		if griddata['emgrid']['project'] is not None:
			gridname = ('Prj%03d'% griddata['emgrid']['project'])+'_'
		gridname = (gridname + griddata['emgrid']['name']).replace(' ','_')
		leadlabels = ['','i']
	else:
		# old style
		gridname = '%05d' % griddata['grid ID']
		leadlabels = ['Grid','Insertion']
	grididstr = leadlabels[0]+gridname
	parts.append(grididstr)
	if 'insertion' in griddata and griddata['insertion'] is not None:
		insertionstr = '%s%03d' % (leadlabels[1],griddata['insertion'])
		parts.append(insertionstr)
	sep = '_'
	label = sep.join(parts)
	return label
