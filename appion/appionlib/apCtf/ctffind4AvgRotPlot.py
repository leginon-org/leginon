
import os
import sys
import math
import numpy
from matplotlib import use
use('Agg')
from matplotlib import pyplot


#====================
#====================
def setPyPlotXLabels(xdata, maxloc, square=True):
	"""
	assumes xdata is in units of 1/Angstroms
	"""
	minloc = xdata.min()
	if maxloc is None:
		maxloc = xdata.max()
	xstd = xdata.std()/4.
	pyplot.xlim(xmin=minloc, xmax=maxloc)
	locs, labels = pyplot.xticks()

	if square is True:
		if 'subplot2grid' in dir(pyplot):
			units = r'$\AA^2$'
		else:
			units = r'$\mathregular{A^2}$'
	else:
		if 'subplot2grid' in dir(pyplot):
			units = r'$\AA$'
		else:
			units = 'A'


	### assumes that x values are 1/Angstroms^2, which give the best plot
	newlocs = []
	newlabels = []
	for loc in locs:
		if loc < minloc + xstd/4:
			continue
		if square is True:
			origres = 1.0/math.sqrt(loc)
		else:
			origres = 1.0/loc
		if origres > 50:
			trueres = round(origres/10.0)*10
		if origres > 25:
			trueres = round(origres/5.0)*5
		elif origres > 12:
			trueres = round(origres/2.0)*2
		elif origres > 7.5:
			trueres = round(origres)
		else:
			trueres = round(origres*2)/2.0

		if square is True:
			trueloc = 1.0/trueres**2
		else:
			trueloc = 1.0/trueres
		if trueloc > maxloc - xstd:
			continue
		if trueres < 10 and (trueres*2)%2 == 1:
			label = r'1/%.1f%s'%(trueres, units)
		else:
			label = r'1/%d%s'%(trueres, units)
		if not label in newlabels:
			newlabels.append(label)
			newlocs.append(trueloc)
	#add final value
	newlocs.append(minloc)
	if square is True:
		minres = 1.0/math.sqrt(minloc)
	else:
		minres = 1.0/minloc
	label = "1/%d%s"%(minres, units)
	newlabels.append(label)

	newlocs.append(maxloc)
	if square is True:
		maxres = 1.0/math.sqrt(maxloc)
	else:
		maxres = 1.0/maxloc
	label = "1/%.1f%s"%(maxres, units)
	newlabels.append(label)

	# set the labels
	pyplot.yticks(fontsize=8)
	pyplot.xticks(newlocs, newlabels, fontsize=7)

	if square is True:
		pyplot.xlabel(r"Resolution ($\mathregular{s^2}$)", fontsize=9)
	else:
		pyplot.xlabel("Resolution (s)", fontsize=9)
	return

#====================
#====================
def line2data(line):
	bits = line.split(' ')
	if len(bits) < 10:
		print bits
		print "error"
		sys.exit(1)
	data = []
	for bit in bits:
		if len(bit) == 0:
			continue
		try:
			d = float(bit)
		except ValueError:
			print bits
			print bit
			sys.exit(1)
		data.append(d)
	#print "line data length %d"%(len(data))
	#skip the first point
	return numpy.array(data[1:], dtype=numpy.float64)

#====================
#====================
def createPlot(avgrotfile):
	print avgrotfile
	output = os.path.splitext(avgrotfile)[0] + ".png"
	f = open(avgrotfile, 'r')
	datasets = []
	for line in f:
		sline = line.strip()
		if sline[0] == '#':
			continue
		data = line2data(sline)
		datasets.append(data)
	print "Found %d of 6 data sets for creating CTFFIND4 plot"%(len(datasets))

	xdata = datasets[0]
	xdatasq = xdata**2
	maxResolutionToShow = 3.5

	quarterpoints = int(len(datasets[2])/4)
	scaleFactor = 0.5/datasets[2][quarterpoints:].max()
	if scaleFactor < 1:
		scaleFactor = 1

	#pyplot.plot(xdatasq, datasets[1], label='Amplitude Spectra')
	pyplot.plot(xdatasq, datasets[2]*scaleFactor, label='Power Spectra', alpha=0.7)
	pyplot.plot(xdatasq, datasets[3], label='CTF Model')
	pyplot.plot(xdatasq, datasets[4], label='Quality of Fit')
	#pyplot.plot(xdatasq, datasets[5], label='unsure')
	pyplot.xlim(xmin=xdatasq[0], xmax=1/maxResolutionToShow**2)
	pyplot.ylim(ymin=-0.1, ymax=1.1)
	pyplot.grid(True, linestyle=':', )
	pyplot.legend()

	setPyPlotXLabels(xdatasq, maxloc=1/maxResolutionToShow**2, square=True)
	pyplot.savefig(output, format="png", dpi=300, orientation='landscape', pad_inches=0.0)
	
	return output