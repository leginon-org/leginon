#!/usr/bin/env python

import sys
import gonmodel
#import pymat
import Numeric

def scale_model(inval, scale):
	return inval * scale

def plot_result(data, model, inc):
	# create the model data

	xdata = data.gonpos
	x1 = min(xdata)
	x2 = max(xdata)

	#xmod = range(x1,x2,inc)
	ran = (x2 - x1) // inc
	xmod = Numeric.arrayrange(ran)
	xmod = xmod * inc + x1
	ymod = map(model.eval, xmod)
	a0 = data.maginfo.get('modavg')

	ymod = Numeric.array(ymod)
	ymod = ymod / a0

	#scalearray = Numeric.ones(len(ymod))
	#scalearray /= a0
	#ymod = map(scale_model, ymod, scalearray)
	
	ymodmax = max(ymod)
	ymodmin = min(ymod)

	ydata = data.pixpertick
	ydatamin = min(ydata)
	ydatamax = max(ydata)
	ydata2 = data.othergonpos
	ydata2min = min(ydata2)
	ydata2max = max(ydata2)


	y1 = min(ymodmin,ydatamin)
	y2 = max(ymodmax,ydatamax)

	## normalize ydata2 data
	ydata2norm = ydatamin + (ydatamax-ydatamin) * (ydata2-ydata2min) / (ydata2max-ydata2min)

	# send to matlab
	mlab = pymat.open()

	pymat.put(mlab, 'xmod', xmod)
	pymat.put(mlab, 'ymod', ymod)
	pymat.put(mlab, 'xdata', xdata)
	pymat.put(mlab, 'ydata', ydata)
	pymat.put(mlab, 'ydata2norm', ydata2norm)
	pymat.eval(mlab, "plot(xmod,ymod,'g')")
	pymat.eval(mlab, "hold")
	pymat.eval(mlab, "plot(xdata,ydata,'ro')")
	#pymat.eval(mlab, "plot(xdata,ydata2norm,'bo')")
	ax = 'axis([' + `x1` + ' ' + `x2` + ' ' + `y1` + ' ' + `y2` + '])'
	pymat.eval(mlab, ax)

	sys.stdin.readline()

	pymat.close(mlab)

if len(sys.argv) != 5:
	print "usage:  ", sys.argv[0], "datfile magfile modfile terms"
	sys.exit()

datfile = sys.argv[1]
magfile = sys.argv[2]
modfile = sys.argv[3]
terms = int(sys.argv[4])

mydat = gonmodel.GonData(datfile, magfile)
mydat.read_data(datfile)
mymod = gonmodel.GonModel()
mymod.fit_data(mydat, terms)
mymod.write_gonshelve(modfile)
#plot_result(mydat, mymod, 0.000000500 )
