#!/usr/bin/python -O

import re
import os
import sys
import time
import shutil
import math
from appionlib import apRecon
import sinedon
import numpy
import subprocess
import MySQLdb
from appionlib import apDisplay
from appionlib import apProject



#==================
def getTotalNumParticles(reconid, numiter):
	dbconf = sinedon.getConfig('appiondata')
	db     = MySQLdb.connect(**dbconf)
	# create a cursor
	cursor = db.cursor()
	query = ( " SELECT stackpart.`particleNumber` AS p "
		+" FROM `ApParticleClassificationData` AS reconpart "
		+" LEFT JOIN `ApStackParticlesData` AS stackpart "
		+"   ON (reconpart.`REF|ApStackParticlesData|particle` = stackpart.`DEF_id`) "
		+" LEFT JOIN `ApRefinementData` AS refdat "
		+"   ON (reconpart.`REF|ApRefinementData|refinement` = refdat.`DEF_id`) "
		+" WHERE refdat.`REF|ApRefinementRunData|refinementRun` = '"+str(reconid)+"' "
		+"   AND refdat.`iteration` = '"+str(numiter)+"' " )
	cursor.execute(query)
	numpart = int(cursor.rowcount)
	db.close()
	return numpart

#==================
def getParticlesForIter(reconid, iternum):
	dbconf = sinedon.getConfig('appiondata')
	db     = MySQLdb.connect(**dbconf)
	# create a cursor
	cursor = db.cursor()
	query = ( " SELECT stackpart.`particleNumber` AS p "
		+" FROM `ApParticleClassificationData` AS reconpart "
		+" LEFT JOIN `ApStackParticlesData` AS stackpart "
		+"   ON (reconpart.`REF|ApStackParticlesData|particle` = stackpart.`DEF_id`) "
		+" LEFT JOIN `ApRefinementData` AS refdat "
		+"   ON (reconpart.`REF|ApRefinementData|refinement` = refdat.`DEF_id`) "
		+" WHERE refdat.`REF|ApRefinementRunData|refinementRun` = '"+str(reconid)+"' "
		+"   AND reconpart.`coran_keep` = 1 " # for Coran plot
		#+"   AND reconpart.`thrown_out` IS NULL " # for EMAN plot
		+"   AND refdat.`iteration` = '"+str(iternum)+"' " )
	cursor.execute(query)
	results = cursor.fetchall()
	db.close()
	return results

#==================
def getAllCoranRecons():
	dbconf = sinedon.getConfig('appiondata')
	db     = MySQLdb.connect(**dbconf)
	# create a cursor
	cursor = db.cursor()
	query = ( " SELECT DISTINCT refdat.`REF|ApRefinementRunData|refinementRun` AS reconid "
		+" FROM `ApRefinementData` AS refdat "
		+" WHERE refdat.`SpiCoranGoodClassAvg` IS NOT NULL "
		+"   AND refdat.`iteration` > '7' " )
	cursor.execute(query)
	results = cursor.fetchall()
	db.close()
	reconids = []
	for row in results:
		reconids.append(int(row[0]))
	print "found "+str(len(reconids))+" reconids: ", reconids
	return reconids

#==================
def writeXmGraceData(counts, numpart):
	datastr = "@target G0.S0\n@type xy\n"
	for i in range(8):
		datastr += ( "%.1f\t%d\n" % (float(i)+0.5, counts[i]))
	datastr += "&\n@target G0.S1\n@type xy\n"
	datastr += ( "-0.5\t%d\n0.5\t0\n&\n" % (numpart))
	cutsize = 10.0**int(math.log10(numpart)-0.3)
	upperlimit = (round(numpart/cutsize)+1)*cutsize
	header = re.sub("@    world -0.999999, 1, 8.999999, 110000",
		 "@    world -0.99999, 1, 8.99999, "+str(upperlimit), xmgraceheader)
	gracedata = header.strip()+"\n"+datastr
	return gracedata

#==================
xmgraceheader = """
# Grace project file
#
@version 50121
@page size 792, 612
@page scroll 5%
@page inout 5%
@link page off
@map font 13 to "ZapfDingbats", "ZapfDingbats"
@map font 4 to "Helvetica", "Helvetica"
@map font 6 to "Helvetica-Bold", "Helvetica-Bold"
@map font 5 to "Helvetica-Oblique", "Helvetica-Oblique"
@map font 7 to "Helvetica-BoldOblique", "Helvetica-BoldOblique"
@map font 17 to "Nimbus-Sans-L-Regular-Condensed", "Nimbus-Sans-L-Regular-Condensed"
@map font 18 to "Nimbus-Sans-L-Bold-Condensed", "Nimbus-Sans-L-Bold-Condensed"
@map font 19 to "Nimbus-Sans-L-Regular-Condensed-Italic", "Nimbus-Sans-L-Regular-Condensed-Italic"
@map font 20 to "Nimbus-Sans-L-Bold-Condensed-Italic", "Nimbus-Sans-L-Bold-Condensed-Italic"
@map font 0 to "Times-Roman", "Times-Roman"
@map font 2 to "Times-Bold", "Times-Bold"
@map font 1 to "Times-Italic", "Times-Italic"
@map font 3 to "Times-BoldItalic", "Times-BoldItalic"
@map font 8 to "Courier", "Courier"
@map font 10 to "Courier-Bold", "Courier-Bold"
@map font 9 to "Courier-Oblique", "Courier-Oblique"
@map font 11 to "Courier-BoldOblique", "Courier-BoldOblique"
@map font 29 to "URW-Palladio-L-Roman", "URW-Palladio-L-Roman"
@map font 30 to "URW-Palladio-L-Bold", "URW-Palladio-L-Bold"
@map font 31 to "URW-Palladio-L-Italic", "URW-Palladio-L-Italic"
@map font 32 to "URW-Palladio-L-Bold-Italic", "URW-Palladio-L-Bold-Italic"
@map font 12 to "Symbol", "Symbol"
@map font 34 to "URW-Chancery-L-Medium-Italic", "URW-Chancery-L-Medium-Italic"
@map color 0 to (255, 255, 255), "white"
@map color 1 to (0, 0, 0), "black"
@map color 2 to (200, 0, 0), "red"
@map color 3 to (0, 200, 0), "green"
@map color 4 to (0, 0, 200), "blue"
@map color 5 to (200, 200, 0), "yellow"
@map color 6 to (188, 143, 143), "brown"
@map color 7 to (150, 150, 150), "grey"
@map color 8 to (148, 0, 211), "violet"
@map color 9 to (0, 200, 200), "cyan"
@map color 10 to (200, 0, 200), "magenta"
@map color 11 to (200, 125, 0), "orange"
@map color 12 to (114, 33, 188), "indigo"
@map color 13 to (100, 0, 0), "darkred"
@map color 14 to (0, 0, 100), "darkblue"
@map color 15 to (0, 100, 0), "darkgreen"
@reference date 0
@date wrap off
@date wrap year 1970
@default linewidth 2.0
@default linestyle 1
@default color 1
@default pattern 1
@default font 0
@default char size 1.000000
@default symbol size 0.500000
@default sformat "%.8g"
@background color 0
@page background fill on
@timestamp off
@timestamp 0.03, 0.03
@timestamp color 1
@timestamp rot 0
@timestamp font 0
@timestamp char size 1.000000
@timestamp def "Tue Aug 19 12:43:58 2008"
@r0 off
@link r0 to g0
@r0 type above
@r0 linestyle 1
@r0 linewidth 1.0
@r0 color 1
@r0 line 0, 0, 0, 0
@r1 off
@link r1 to g0
@r1 type above
@r1 linestyle 1
@r1 linewidth 1.0
@r1 color 1
@r1 line 0, 0, 0, 0
@r2 off
@link r2 to g0
@r2 type above
@r2 linestyle 1
@r2 linewidth 1.0
@r2 color 1
@r2 line 0, 0, 0, 0
@r3 off
@link r3 to g0
@r3 type above
@r3 linestyle 1
@r3 linewidth 1.0
@r3 color 1
@r3 line 0, 0, 0, 0
@r4 off
@link r4 to g0
@r4 type above
@r4 linestyle 1
@r4 linewidth 1.0
@r4 color 1
@r4 line 0, 0, 0, 0
@g0 on
@g0 hidden false
@g0 type XY
@g0 stacked false
@g0 bar hgap 0.000000
@g0 fixedpoint off
@g0 fixedpoint type 0
@g0 fixedpoint xy 0.000000, 0.000000
@g0 fixedpoint format general general
@g0 fixedpoint prec 6, 6
@with g0
@    world -0.999999, 1, 8.999999, 110000
@    stack world 0, 0, 0, 0
@    znorm 1
@    view 0.180000, 0.150000, 0.880000, 0.850000
@    title ""
@    title font 0
@    title size 1.500000
@    title color 1
@    subtitle "Coran Refine; Coran Selected Particles"
@    subtitle font 0
@    subtitle size 1.000000
@    subtitle color 1
@    xaxes scale Normal
@    yaxes scale Normal
@    xaxes invert off
@    yaxes invert off
@    xaxis  on
@    xaxis  type zero false
@    xaxis  offset 0.000000 , 0.000000
@    xaxis  bar off
@    xaxis  bar color 1
@    xaxis  bar linestyle 1
@    xaxis  bar linewidth 1.0
@    xaxis  label "Number of Rounds"
@    xaxis  label layout para
@    xaxis  label place auto
@    xaxis  label char size 1.000000
@    xaxis  label font 0
@    xaxis  label color 1
@    xaxis  label place normal
@    xaxis  tick on
@    xaxis  tick major 1
@    xaxis  tick minor ticks 0
@    xaxis  tick default 6
@    xaxis  tick place rounded true
@    xaxis  tick in
@    xaxis  tick major size 1.000000
@    xaxis  tick major color 1
@    xaxis  tick major linewidth 2.0
@    xaxis  tick major linestyle 1
@    xaxis  tick major grid off
@    xaxis  tick minor color 1
@    xaxis  tick minor linewidth 2.0
@    xaxis  tick minor linestyle 1
@    xaxis  tick minor grid off
@    xaxis  tick minor size 0.500000
@    xaxis  ticklabel on
@    xaxis  ticklabel format decimal
@    xaxis  ticklabel prec 0
@    xaxis  ticklabel formula ""
@    xaxis  ticklabel append ""
@    xaxis  ticklabel prepend ""
@    xaxis  ticklabel angle 0
@    xaxis  ticklabel skip 0
@    xaxis  ticklabel stagger 0
@    xaxis  ticklabel place normal
@    xaxis  ticklabel offset auto
@    xaxis  ticklabel offset 0.000000 , 0.010000
@    xaxis  ticklabel start type auto
@    xaxis  ticklabel start 0.000000
@    xaxis  ticklabel stop type auto
@    xaxis  ticklabel stop 0.000000
@    xaxis  ticklabel char size 1.000000
@    xaxis  ticklabel font 0
@    xaxis  ticklabel color 1
@    xaxis  tick place both
@    xaxis  tick spec type none
@    yaxis  on
@    yaxis  type zero false
@    yaxis  offset 0.000000 , 0.000000
@    yaxis  bar off
@    yaxis  bar color 1
@    yaxis  bar linestyle 1
@    yaxis  bar linewidth 1.0
@    yaxis  label "Number of Particles"
@    yaxis  label layout para
@    yaxis  label place auto
@    yaxis  label char size 1.000000
@    yaxis  label font 0
@    yaxis  label color 1
@    yaxis  label place normal
@    yaxis  tick on
@    yaxis  tick major 10000
@    yaxis  tick minor ticks 1
@    yaxis  tick default 6
@    yaxis  tick place rounded true
@    yaxis  tick in
@    yaxis  tick major size 1.000000
@    yaxis  tick major color 1
@    yaxis  tick major linewidth 2.0
@    yaxis  tick major linestyle 1
@    yaxis  tick major grid off
@    yaxis  tick minor color 1
@    yaxis  tick minor linewidth 2.0
@    yaxis  tick minor linestyle 1
@    yaxis  tick minor grid off
@    yaxis  tick minor size 0.500000
@    yaxis  ticklabel on
@    yaxis  ticklabel format engineering
@    yaxis  ticklabel prec 0
@    yaxis  ticklabel formula ""
@    yaxis  ticklabel append ""
@    yaxis  ticklabel prepend ""
@    yaxis  ticklabel angle 0
@    yaxis  ticklabel skip 0
@    yaxis  ticklabel stagger 0
@    yaxis  ticklabel place normal
@    yaxis  ticklabel offset spec
@    yaxis  ticklabel offset 0.000000 , 0.020000
@    yaxis  ticklabel start type auto
@    yaxis  ticklabel start 0.000000
@    yaxis  ticklabel stop type auto
@    yaxis  ticklabel stop 0.000000
@    yaxis  ticklabel char size 1.000000
@    yaxis  ticklabel font 0
@    yaxis  ticklabel color 1
@    yaxis  tick place both
@    yaxis  tick spec type none
@    altxaxis  off
@    altyaxis  off
@    legend on
@    legend loctype view
@    legend 0.85, 0.8
@    legend box color 1
@    legend box pattern 1
@    legend box linewidth 2.0
@    legend box linestyle 1
@    legend box fill color 0
@    legend box fill pattern 1
@    legend font 0
@    legend char size 1.000000
@    legend color 1
@    legend length 4
@    legend vgap 1
@    legend hgap 1
@    legend invert false
@    frame type 0
@    frame linestyle 1
@    frame linewidth 3.0
@    frame color 1
@    frame pattern 1
@    frame background color 0
@    frame background pattern 0
@    s0 hidden false
@    s0 type xy
@    s0 symbol 0
@    s0 symbol size 0.500000
@    s0 symbol color 1
@    s0 symbol pattern 1
@    s0 symbol fill color 1
@    s0 symbol fill pattern 1
@    s0 symbol linewidth 2.0
@    s0 symbol linestyle 0
@    s0 symbol char 65
@    s0 symbol char font 0
@    s0 symbol skip 0
@    s0 line type 3
@    s0 line linestyle 1
@    s0 line linewidth 2.0
@    s0 line color 1
@    s0 line pattern 1
@    s0 baseline type 0
@    s0 baseline off
@    s0 dropline on
@    s0 fill type 2
@    s0 fill rule 0
@    s0 fill color 2
@    s0 fill pattern 1
@    s0 avalue on
@    s0 avalue type 2
@    s0 avalue char size 1.000000
@    s0 avalue font 0
@    s0 avalue color 1
@    s0 avalue rot 0
@    s0 avalue format engineering
@    s0 avalue prec 1
@    s0 avalue prepend ""
@    s0 avalue append ""
@    s0 avalue offset 0.045000 , 0.010000
@    s0 errorbar on
@    s0 errorbar place both
@    s0 errorbar color 1
@    s0 errorbar pattern 1
@    s0 errorbar size 1.000000
@    s0 errorbar linewidth 2.0
@    s0 errorbar linestyle 1
@    s0 errorbar riser linewidth 2.0
@    s0 errorbar riser linestyle 1
@    s0 errorbar riser clip off
@    s0 errorbar riser clip length 0.100000
@    s0 comment "histogram.dat"
@    s0 legend  ""
@    s1 hidden false
@    s1 type xy
@    s1 symbol 0
@    s1 symbol size 0.500000
@    s1 symbol color 1
@    s1 symbol pattern 1
@    s1 symbol fill color 1
@    s1 symbol fill pattern 1
@    s1 symbol linewidth 2.0
@    s1 symbol linestyle 0
@    s1 symbol char 65
@    s1 symbol char font 0
@    s1 symbol skip 0
@    s1 line type 3
@    s1 line linestyle 1
@    s1 line linewidth 2.0
@    s1 line color 1
@    s1 line pattern 1
@    s1 baseline type 0
@    s1 baseline off
@    s1 dropline on
@    s1 fill type 2
@    s1 fill rule 0
@    s1 fill color 4
@    s1 fill pattern 1
@    s1 avalue on
@    s1 avalue type 2
@    s1 avalue char size 1.250000
@    s1 avalue font 2
@    s1 avalue color 0
@    s1 avalue rot 90
@    s1 avalue format engineering
@    s1 avalue prec 1
@    s1 avalue prepend ""
@    s1 avalue append ""
@    s1 avalue offset 0.040000 , -0.400000
@    s1 errorbar on
@    s1 errorbar place both
@    s1 errorbar color 1
@    s1 errorbar pattern 1
@    s1 errorbar size 1.000000
@    s1 errorbar linewidth 2.0
@    s1 errorbar linestyle 1
@    s1 errorbar riser linewidth 2.0
@    s1 errorbar riser linestyle 1
@    s1 errorbar riser clip off
@    s1 errorbar riser clip length 0.100000
@    s1 comment "Editor"
@    s1 legend  ""
"""


#==================
#==================
def makeCoranKeepPlot(reconid):
	### prelim stuff
	numiter = apRecon.getNumIterationsFromRefineRunID(reconid)
	if numiter < 4:
		apDisplay.printWarning("Cannot create coran keep plot, not enough iterations (%d)"%(numiter))
		return None
	else:
		apDisplay.printMsg("found "+str(numiter)+" iterations")
	numpart = getTotalNumParticles(reconid, numiter-1)
	if numpart < 2000:
		apDisplay.printWarning("Cannot create coran keep plot, not enough particles")
		return None
	else:
		apDisplay.printMsg("found "+str(numpart)+" particles")

	### run through last 8 iterations summarizing particles
	iter1 = numiter-7
	iter2 = numiter+1
	maxpart = 0
	partdict = {}
	for iternum in range(iter1, iter2):
		results = getParticlesForIter(reconid, iternum)
		for row in results:
			partnum = int(row[0])
			if partnum > maxpart:
				maxpart = partnum
			if partnum in partdict:
				partdict[partnum] += 1
			else:
				partdict[partnum] = 1

	print "maxpart=", maxpart
	#print str(partdict)[:80]
	### summarize results
	counts = numpy.zeros((8), dtype=numpy.int32)
	for key in partdict.keys():
		numtimes = partdict[key]
		for i in range(numtimes):
			counts[i] += 1
	print counts
	print numpy.around(100.0*numpy.asarray(counts, dtype=numpy.float32)/float(numpart), 4)

	gracefile = "corankeepplot-"+str(reconid)+".agr"
	gracedata = writeXmGraceData(counts, numpart)
	f = open(gracefile, "w")
	f.write(gracedata)
	f.close()

	epsfile = "corankeepplot-"+str(reconid)+".eps"
	proc = subprocess.Popen("xmgrace "+gracefile+" -printfile "+epsfile+" -hardcopy -hdevice EPS", shell=True)
	proc.wait()
	time.sleep(1)

	if not os.path.isfile(epsfile):
		apDisplay.printWarning("Grace failed to create EPS file, is grace installed?")
		return

	pngfile = "corankeepplot-"+str(reconid)+".png"
	proc = subprocess.Popen("convert -resize 1024x1024 -trim "+epsfile+" "+pngfile, shell=True)
	proc.wait()
	time.sleep(1)
	os.remove(epsfile)

	if os.path.isfile(pngfile):
		apDisplay.printColor("Successfully created the Coran Keep Plot: "+pngfile, "green")


#==================
#==================
#==================
if __name__ == '__main__':
	print "Usage: apCoranPlot.py <reconid> <projectid>"

	### setup correct database after we have read the project id
	if len(sys.argv) > 2:
		projectid = int(sys.argv[2])
	else:
		projectid = None
	if projectid is not None:
		apDisplay.printWarning("Using split database")
		# use a project database
		newdbname = apProject.getAppionDBFromProjectId(projectid)
		sinedon.setConfig('appiondata', db=newdbname)
		apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")

	### run the program
	if len(sys.argv) > 1:
		reconid = int(sys.argv[1])
		makeCoranKeepPlot(reconid)
	else:
		reconids = getAllCoranRecons()
		for reconid in reconids:
			recondata = apRecon.getRefineRunDataFromID(reconid)
			reconpath = recondata['path']['path']
			print reconpath
			os.chdir(reconpath)
			try:
				makeCoranKeepPlot(reconid)
			except:
				pass





